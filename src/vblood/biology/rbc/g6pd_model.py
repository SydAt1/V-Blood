"""
RBC G6PD-Glutathione Redox Model — Version 2.0.0 (Task 6).

Replaces the simplified PPP surrogate with an evidence-grounded, bi-substrate
G6PD kinetic rate law with competitive NADPH product inhibition and total
pyridine nucleotide pool conservation:

    [NADP+] = max(0, [NADP]_tot - [NADPH])

Reactions implemented:
- R1: GPx1 (bimolecular approximation)
- R2: Glutathione reductase (bi-substrate Michaelis-Menten)
- R3: Active GSSG export
- R4: De novo GSH synthesis
- R5: G6PD-catalyzed NADPH regeneration (Option A)
- R6: Endogenous H2O2 production
- R7: Passive H2O2 removal
- R8: Oxidative damage index accumulation (synthetic proxy)

Scientific references:
- Gaetani et al. (1994) Blood 84:2018-2024
- Kirkman & Gaetani (1986) J. Biol. Chem. 261:4033-4038
- Yoshida (1973) Science 179:532-537
- Mulquiney & Kuchel (1999) Biochem. J. 342:567-584
"""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np

from vblood.biology.base import BiologicalModel, ModelMetadata
from vblood.biology.rbc.g6pd_parameters import DEFAULT_G6PD_PARAMETERS, G6PDParameters
from vblood.biology.rbc.gsh_redox_model import (
    IDX_D,
    IDX_GSH,
    IDX_GSSG,
    IDX_H2O2,
    IDX_NADPH,
    N_STATE_VARS,
    RBCGSHRedoxModel,
)
from vblood.biology.rbc.parameters import DEFAULT_PARAMETERS
from vblood.schemas.simulation import RBCGSHInitialConditions


class G6PDRateLaw:
    """Isolated, testable G6PD kinetic rate component."""

    @staticmethod
    def v_g6pd(
        nadph: float,
        vmax_g6pd: float,
        km_g6p: float,
        km_nadp: float,
        ki_nadph: float,
        nadp_total: float,
        g6p_conc: float,
        activity_fraction: float = 1.0,
    ) -> float:
        """Compute the reaction rate of G6PD in human erythrocytes (mM s⁻¹).

        Rate law:
            v_G6PD = alpha * Vmax * [G6P] * [NADP+] /
                     (Km(G6P)*Km(NADP+)*(1 + [NADPH]/Ki) +
                      Km(NADP+)*[G6P] + Km(G6P)*[NADP+] + [G6P]*[NADP+])

        Where:
            [NADP+] = max(0, nadp_total - [NADPH])

        Args:
            nadph: Intracellular [NADPH] in mM.
            vmax_g6pd: Maximal G6PD activity in mM s⁻¹.
            km_g6p: Michaelis constant for G6P in mM.
            km_nadp: Michaelis constant for NADP+ in mM.
            ki_nadph: Competitive inhibition constant for NADPH in mM.
            nadp_total: Total intracellular NADP(H) pool in mM.
            g6p_conc: Intracellular [G6P] in mM.
            activity_fraction: Relative enzyme activity alpha in [0, 1].

        Returns:
            G6PD flux in mM s⁻¹. Always >= 0.
        """
        if activity_fraction <= 0.0 or vmax_g6pd <= 0.0:
            return 0.0

        nadph_eff = max(0.0, float(nadph))
        nadp_plus = max(0.0, float(nadp_total) - nadph_eff)
        g6p_eff = max(0.0, float(g6p_conc))

        if nadp_plus <= 0.0 or g6p_eff <= 0.0:
            return 0.0

        # Competitive inhibition factor on NADP+ binding
        inhibition_term = 1.0 + (nadph_eff / max(1e-12, ki_nadph))

        numerator = activity_fraction * vmax_g6pd * g6p_eff * nadp_plus
        denominator = (
            km_g6p * km_nadp * inhibition_term
            + km_nadp * g6p_eff
            + km_g6p * nadp_plus
            + g6p_eff * nadp_plus
        )

        if denominator <= 0.0:
            return 0.0

        return float(numerator / denominator)


class RBCG6PDGSHModel(BiologicalModel):
    """RBC G6PD-Glutathione Redox Model (rbc-g6pd-gsh-v2).

    Extends the 5-variable framework with explicit, evidence-backed G6PD kinetics.
    Replaces the simplified PPP surrogate with G6PDRateLaw, preserving reaction
    coupling and enabling quantitative study of reduced G6PD activity scenarios.
    """

    _METADATA = ModelMetadata(
        model_id="rbc-g6pd-gsh-v2",
        version="2.0.0",
        name="RBC G6PD-Glutathione Redox Model",
        description=(
            "5-variable mechanistic ODE model of human erythrocyte redox homeostasis "
            "incorporating evidence-backed G6PD kinetics with competitive NADPH product "
            "inhibition and total NADP(H) pool conservation. Supports G6PD deficiency scenarios."
        ),
        state_variable_names=("GSH", "GSSG", "H2O2", "NADPH", "D"),
        state_variable_units=("mM", "mM", "mM", "mM", "dimensionless"),
        compartment="RBC cytosol",
        assumptions_doc="docs/model_specification.md",
        literature_sources=(
            "Gaetani et al. (1994) Blood 84:2018",
            "Kirkman & Gaetani (1986) J. Biol. Chem. 261:4033",
            "Yoshida (1973) Science 179:532",
            "Mulquiney & Kuchel (1999) Biochem. J. 342:567",
            "Flohé (1979) Ciba Found. Symp. 65:95",
            "Worthington & Rosemeyer (1974) Eur. J. Biochem. 48:167",
        ),
    )

    @property
    def metadata(self) -> ModelMetadata:
        return self._METADATA

    def initial_state(self, initial_conditions: RBCGSHInitialConditions) -> np.ndarray:
        y0 = np.zeros(N_STATE_VARS)
        y0[IDX_GSH] = initial_conditions.gsh_0
        y0[IDX_GSSG] = initial_conditions.gssg_0
        y0[IDX_H2O2] = initial_conditions.h2o2_0
        y0[IDX_NADPH] = initial_conditions.nadph_0
        y0[IDX_D] = initial_conditions.damage_0
        return y0

    def default_parameters(self) -> dict[str, float]:
        """Combine baseline redox parameters with G6PD kinetic parameters."""
        p = DEFAULT_PARAMETERS.to_dict()
        p.update(DEFAULT_G6PD_PARAMETERS.to_dict())
        return p

    def validate_params(self, params: dict[str, Any]) -> list[str]:
        """Validate parameter ranges and bounds."""
        errors: list[str] = []
        required_keys = [
            "k_gpx", "vmax_gr", "km_gssg_gr", "km_nadph_gr", "k_export", "k_synth",
            "k_h2o2_prod", "k_h2o2_rem", "vmax_g6pd", "km_g6p", "km_nadp",
            "ki_nadph", "nadp_total", "g6p_conc", "g6pd_activity_fraction"
        ]
        for k in required_keys:
            if k not in params:
                errors.append(f"Missing required parameter '{k}'")
            elif params[k] < 0.0:
                errors.append(f"Parameter '{k}' cannot be negative, got {params[k]}")

        if "g6pd_activity_fraction" in params:
            frac = params["g6pd_activity_fraction"]
            if frac < 0.0 or frac > 5.0:
                errors.append(f"g6pd_activity_fraction must be in [0.0, 5.0], got {frac}")

        return errors

    def rhs(self, t: float, y: np.ndarray, params: dict[str, Any]) -> np.ndarray:
        """Compute ODE derivatives dy/dt with G6PD-dependent NADPH regeneration."""
        gsh = max(0.0, float(y[IDX_GSH]))
        gssg = max(0.0, float(y[IDX_GSSG]))
        h2o2 = max(0.0, float(y[IDX_H2O2]))
        nadph = max(0.0, float(y[IDX_NADPH]))
        d = min(1.0, max(0.0, float(y[IDX_D])))

        # 1. GPx1 reaction (R1)
        r_gpx = RBCGSHRedoxModel.v_gpx(gsh, h2o2, params["k_gpx"])

        # 2. Glutathione reductase (R2)
        r_gr = RBCGSHRedoxModel.v_gr(
            gssg, nadph,
            params["vmax_gr"],
            params["km_gssg_gr"],
            params["km_nadph_gr"],
        )

        # 3. GSSG export (R3)
        r_export = RBCGSHRedoxModel.v_export(gssg, params["k_export"])

        # 4. De novo GSH synthesis (R4)
        r_synth = RBCGSHRedoxModel.v_synth(params["k_synth"])

        # 5. G6PD-catalyzed NADPH regeneration (R5 - replaces simplified PPP surrogate)
        r_g6pd = G6PDRateLaw.v_g6pd(
            nadph=nadph,
            vmax_g6pd=params["vmax_g6pd"],
            km_g6p=params["km_g6p"],
            km_nadp=params["km_nadp"],
            ki_nadph=params["ki_nadph"],
            nadp_total=params["nadp_total"],
            g6p_conc=params["g6p_conc"],
            activity_fraction=params.get("g6pd_activity_fraction", 1.0),
        )

        # 6. Endogenous H2O2 production (R6)
        r_h2o2_prod = RBCGSHRedoxModel.v_h2o2_prod(params["k_h2o2_prod"])

        # 7. Passive H2O2 removal (R7)
        r_h2o2_rem = RBCGSHRedoxModel.v_h2o2_rem(h2o2, params["k_h2o2_rem"])

        # 8. Damage accumulation (R8)
        k_damage = params.get("k_damage", 1e-4)
        k_repair = params.get("k_repair", 5e-6)
        gsh_ref = params.get("gsh_0", 2.5)
        d_damage = k_damage * (max(0.0, gsh_ref - gsh) / max(1e-6, gsh_ref)) * h2o2
        d_repair = k_repair * d

        # ODE system
        dgsh_dt = 2.0 * r_gr - 2.0 * r_gpx + r_synth
        dgssg_dt = r_gpx - r_gr - r_export
        dh2o2_dt = r_h2o2_prod - r_gpx - r_h2o2_rem
        dnadph_dt = r_g6pd - r_gr
        dd_dt = d_damage - d_repair

        return np.array([dgsh_dt, dgssg_dt, dh2o2_dt, dnadph_dt, dd_dt])

    def check_constraints(
        self,
        t: float,
        y: np.ndarray,
        params: dict[str, Any],
    ) -> list[str]:
        """Check scientific constraints on the state vector during integration."""
        violations = RBCGSHRedoxModel().check_constraints(t, y, params)
        nadph = y[IDX_NADPH]
        nadp_total = params.get("nadp_total", 0.040)
        if nadph > nadp_total + 1e-6:
            violations.append(
                f"t={t:.2f}s: [NADPH] = {nadph:.6f} mM exceeds total NADP pool {nadp_total:.6f} mM."
            )
        return violations

    @staticmethod
    def estimated_hemolysis_pct(damage: float) -> float:
        """Estimate hemolysis percentage from cumulative damage index D."""
        return RBCGSHRedoxModel.estimated_hemolysis_pct(damage)
