"""
RBC Glutathione Redox ODE Model — Version 1.0.0

Implements the 5-variable mechanistic ODE system for red blood cell
oxidative stress as described in docs/model_specification.md.

State variables (in order):
  0: GSH   — reduced glutathione [mM]
  1: GSSG  — oxidised glutathione [mM]
  2: H2O2  — hydrogen peroxide [mM]
  3: NADPH — reduced NADPH [mM]
  4: D     — cumulative oxidative damage index [0, 1]

All concentrations are in mM of intracellular RBC water.

Scientific references and parameter provenance are in
src/vblood/biology/rbc/parameters.py and
docs/assumptions_and_limitations.md.

IMPORTANT:
- This model must never be used to make clinical, regulatory, or safety
  decisions.
- Parameters labelled SYNTHETIC have no experimental basis and must not be
  used for biological predictions.
- The bimolecular GPx approximation is invalid at [H2O2] > 0.5 mM.
"""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np

from vblood.biology.base import BiologicalModel, ModelMetadata
from vblood.biology.rbc.parameters import DEFAULT_PARAMETERS, RBCGSHParameters
from vblood.schemas.simulation import RBCGSHInitialConditions

# --------------------------------------------------------------------------- #
# State variable indices — centralised so that they never silently diverge
# from the actual order in the state vector.
# --------------------------------------------------------------------------- #
IDX_GSH = 0
IDX_GSSG = 1
IDX_H2O2 = 2
IDX_NADPH = 3
IDX_D = 4

N_STATE_VARS = 5

# Warning thresholds
GPX_BIMOLECULAR_VALIDITY_LIMIT_mM = 0.5  # mM H2O2 above which approximation is unreliable
GSH_CRISIS_THRESHOLD_FRACTION = 0.10     # GSH below 10% of initial = oxidative crisis


class RBCGSHRedoxModel(BiologicalModel):
    """
    RBC Glutathione Redox ODE Model (rbc-gsh-redox-v1).

    Implements Reactions R1–R8 from docs/model_specification.md.

    The model tracks:
    - Reduced glutathione (GSH) — primary antioxidant
    - Oxidised glutathione (GSSG) — product of GPx reaction
    - Hydrogen peroxide (H2O2) — model oxidant challenge
    - NADPH — cofactor for GR, produced by PPP surrogate
    - D — cumulative oxidative damage index (SYNTHETIC parameters)

    Usage::

        model = RBCGSHRedoxModel()
        ic = RBCGSHInitialConditions(gsh_0=2.5, h2o2_0=0.001)
        y0 = model.initial_state(ic)
        params = DEFAULT_PARAMETERS.to_dict()
        dydt = model.rhs(0.0, y0, params)

    """

    _METADATA = ModelMetadata(
        model_id="rbc-gsh-redox-v1",
        version="1.0.0",
        name="RBC Glutathione Redox Model",
        description=(
            "5-variable ODE model of the glutathione redox cycle in human erythrocytes "
            "under oxidative stress. Tracks GSH, GSSG, H2O2, NADPH, and a cumulative "
            "damage index. Parameterised from published literature. "
            "Damage index uses SYNTHETIC parameters (see parameter provenance)."
        ),
        state_variable_names=("GSH", "GSSG", "H2O2", "NADPH", "D"),
        state_variable_units=("mM", "mM", "mM", "mM", "dimensionless"),
        compartment="RBC cytosol",
        assumptions_doc="docs/assumptions_and_limitations.md",
        literature_sources=(
            "Mulquiney & Kuchel (1999) Biochem. J. 342:567",
            "Nakayama et al. (2005) Biosystems 83:91",
            "Flohé (1979) Ciba Found. Symp. 65:95",
            "Worthington & Rosemeyer (1974) Eur. J. Biochem. 48:167",
            "Gaetani et al. (1994) Blood 87:1595",
        ),
    )

    @property
    def metadata(self) -> ModelMetadata:
        """Return static metadata for this model."""
        return self._METADATA

    # ------------------------------------------------------------------
    # State vector interface
    # ------------------------------------------------------------------

    def initial_state(self, initial_conditions: RBCGSHInitialConditions) -> np.ndarray:
        """Convert initial conditions schema into the state vector y0.

        Args:
            initial_conditions: Validated :class:`RBCGSHInitialConditions` object.

        Returns:
            1-D numpy array [GSH, GSSG, H2O2, NADPH, D].
        """
        y0 = np.zeros(N_STATE_VARS)
        y0[IDX_GSH] = initial_conditions.gsh_0
        y0[IDX_GSSG] = initial_conditions.gssg_0
        y0[IDX_H2O2] = initial_conditions.h2o2_0
        y0[IDX_NADPH] = initial_conditions.nadph_0
        y0[IDX_D] = initial_conditions.damage_0
        return y0

    # ------------------------------------------------------------------
    # Reaction rate expressions (public for direct testability)
    # ------------------------------------------------------------------

    @staticmethod
    def v_gpx(gsh: float, h2o2: float, k_gpx: float) -> float:
        """Rate of GPx1 reaction (R1) — bimolecular approximation.

        H2O2 + 2 GSH → GSSG + 2 H2O

        v_GPx = k_gpx * [H2O2] * [GSH]

        Valid when [H2O2] << Km(H2O2) for GPx1 (approximately < 0.5 mM).
        This approximation is derived from the limiting case of the
        ping-pong bi-bi mechanism at sub-saturating peroxide concentrations.

        Args:
            gsh: [GSH] in mM. Must be >= 0.
            h2o2: [H2O2] in mM. Must be >= 0.
            k_gpx: Effective bimolecular rate constant in mM⁻¹ s⁻¹.

        Returns:
            Reaction rate in mM s⁻¹. Always >= 0.
        """
        return k_gpx * max(0.0, h2o2) * max(0.0, gsh)

    @staticmethod
    def v_gr(gssg: float, nadph: float, vmax_gr: float, km_gssg: float, km_nadph: float) -> float:
        """Rate of glutathione reductase (GR) reaction (R2).

        GSSG + NADPH → 2 GSH + NADP+

        Modelled as bi-substrate Michaelis-Menten kinetics (product of
        saturation terms — valid approximation for independent substrate binding).

        Args:
            gssg: [GSSG] in mM. Must be >= 0.
            nadph: [NADPH] in mM. Must be >= 0.
            vmax_gr: Maximum reaction rate in mM s⁻¹.
            km_gssg: Michaelis constant for GSSG in mM.
            km_nadph: Michaelis constant for NADPH in mM.

        Returns:
            Reaction rate in mM s⁻¹. Always >= 0.
        """
        gssg_sat = max(0.0, gssg) / (km_gssg + max(0.0, gssg))
        nadph_sat = max(0.0, nadph) / (km_nadph + max(0.0, nadph))
        return vmax_gr * gssg_sat * nadph_sat

    @staticmethod
    def v_export(gssg: float, k_export: float) -> float:
        """Rate of GSSG active export out of the cell (R3).

        v_export = k_export * [GSSG]

        First-order approximation valid when [GSSG] is below transporter Km.

        Args:
            gssg: [GSSG] in mM. Must be >= 0.
            k_export: First-order rate constant in s⁻¹.

        Returns:
            Reaction rate in mM s⁻¹. Always >= 0.
        """
        return k_export * max(0.0, gssg)

    @staticmethod
    def v_synth(k_synth: float) -> float:
        """Rate of de novo GSH synthesis (R4) — constant.

        Args:
            k_synth: Zero-order rate constant in mM s⁻¹.

        Returns:
            Reaction rate in mM s⁻¹.
        """
        return k_synth

    @staticmethod
    def v_ppp(nadph: float, vmax_ppp: float, km_nadph_ppp: float) -> float:
        """Rate of NADPH production by the pentose phosphate pathway surrogate (R5).

        v_PPP = Vmax_PPP * Km / (Km + [NADPH])

        This form captures product inhibition: flux is maximal when [NADPH]
        is depleted and decreases as [NADPH] rises. It is a simplified
        surrogate for G6PD/PPP kinetics.

        Args:
            nadph: [NADPH] in mM. Must be >= 0.
            vmax_ppp: Maximum flux in mM s⁻¹.
            km_nadph_ppp: Half-saturation constant in mM.

        Returns:
            Reaction rate in mM s⁻¹. Always >= 0.
        """
        return vmax_ppp * km_nadph_ppp / (km_nadph_ppp + max(0.0, nadph))

    @staticmethod
    def v_h2o2_prod(k_h2o2_prod: float) -> float:
        """Rate of endogenous H2O2 production (R6) — constant.

        Represents haemoglobin autoxidation and other baseline sources.

        Args:
            k_h2o2_prod: Zero-order rate constant in mM s⁻¹.

        Returns:
            Reaction rate in mM s⁻¹.
        """
        return k_h2o2_prod

    @staticmethod
    def v_h2o2_rem(h2o2: float, k_h2o2_rem: float) -> float:
        """Rate of passive H2O2 removal (R7) — first-order.

        Represents non-enzymatic removal, membrane permeation, and catalase
        under moderate stress.

        Args:
            h2o2: [H2O2] in mM. Must be >= 0.
            k_h2o2_rem: First-order rate constant in s⁻¹.

        Returns:
            Reaction rate in mM s⁻¹. Always >= 0.
        """
        return k_h2o2_rem * max(0.0, h2o2)

    # ------------------------------------------------------------------
    # ODE right-hand side
    # ------------------------------------------------------------------

    def rhs(
        self,
        t: float,
        y: np.ndarray,
        params: dict[str, Any],
    ) -> np.ndarray:
        """Compute dy/dt for the RBC glutathione redox system.

        This is the function passed to scipy.integrate.solve_ivp.

        Reactions implemented (see docs/model_specification.md):
        - R1: GPx1: H2O2 + 2 GSH → GSSG + 2 H2O
        - R2: GR:   GSSG + NADPH → 2 GSH + NADP+
        - R3: GSSG export
        - R4: GSH de novo synthesis
        - R5: NADPH supply (PPP surrogate)
        - R6: H2O2 endogenous production
        - R7: H2O2 passive removal
        - R8: Oxidative damage accumulation

        Args:
            t: Current time in seconds.
            y: State vector [GSH, GSSG, H2O2, NADPH, D].
            params: Parameter dict from RBCGSHParameters.to_dict().

        Returns:
            Derivative vector dy/dt with the same shape as y.
        """
        gsh = y[IDX_GSH]
        gssg = y[IDX_GSSG]
        h2o2 = y[IDX_H2O2]
        nadph = y[IDX_NADPH]
        d = y[IDX_D]

        # Clamp to non-negative to prevent runaway derivatives near zero
        # (integrator may briefly step below zero; physical minimum is 0)
        gsh = max(0.0, gsh)
        gssg = max(0.0, gssg)
        h2o2 = max(0.0, h2o2)
        nadph = max(0.0, nadph)
        d = min(1.0, max(0.0, d))

        # Reaction rates
        r_gpx = self.v_gpx(gsh, h2o2, params["k_gpx"])
        r_gr = self.v_gr(
            gssg, nadph,
            params["vmax_gr"],
            params["km_gssg_gr"],
            params["km_nadph_gr"],
        )
        r_export = self.v_export(gssg, params["k_export"])
        r_synth = self.v_synth(params["k_synth"])
        r_ppp = self.v_ppp(nadph, params["vmax_ppp"], params["km_nadph_ppp"])
        r_h2o2_prod = self.v_h2o2_prod(params["k_h2o2_prod"])
        r_h2o2_rem = self.v_h2o2_rem(h2o2, params["k_h2o2_rem"])

        # Differential equations (from model specification §5)
        dgsh_dt = 2.0 * r_gr - 2.0 * r_gpx + r_synth
        dgssg_dt = r_gpx - r_gr - r_export
        dh2o2_dt = r_h2o2_prod - r_gpx - r_h2o2_rem
        dnadph_dt = r_ppp - r_gr

        # Damage accumulation (R8) — SYNTHETIC parameters
        # GSH₀ is stored in params for this computation; defaults to 2.5 mM
        gsh_0 = params.get("gsh_0", 2.5)
        gsh_depletion_fraction = max(0.0, 1.0 - gsh / gsh_0) if gsh_0 > 0 else 0.0
        dd_dt = (
            params["k_damage"] * h2o2 * gsh_depletion_fraction
            - params["k_repair"] * d * (1.0 - d)
        )

        # Hard constraint: D is bounded to [0, 1]
        # If D is at the boundary and the derivative would push it further out,
        # clamp the derivative to zero.
        if d >= 1.0 and dd_dt > 0:
            dd_dt = 0.0
        if d <= 0.0 and dd_dt < 0:
            dd_dt = 0.0

        dydt = np.zeros(N_STATE_VARS)
        dydt[IDX_GSH] = dgsh_dt
        dydt[IDX_GSSG] = dgssg_dt
        dydt[IDX_H2O2] = dh2o2_dt
        dydt[IDX_NADPH] = dnadph_dt
        dydt[IDX_D] = dd_dt

        return dydt

    # ------------------------------------------------------------------
    # Validation and constraint checking
    # ------------------------------------------------------------------

    def validate_params(self, params: dict[str, Any]) -> list[str]:
        """Validate a parameter dictionary for this model.

        Args:
            params: Dict of parameter names to values.

        Returns:
            List of error messages. Empty means valid.
        """
        errors = []
        required_keys = {
            "k_gpx", "vmax_gr", "km_gssg_gr", "km_nadph_gr",
            "k_export", "k_synth", "vmax_ppp", "km_nadph_ppp",
            "k_h2o2_prod", "k_h2o2_rem", "k_damage", "k_repair",
        }
        for key in required_keys:
            if key not in params:
                errors.append(f"Missing required parameter: '{key}'")
            elif not isinstance(params[key], (int, float)):
                errors.append(f"Parameter '{key}' must be numeric, got {type(params[key])}.")
            elif params[key] < 0:
                errors.append(f"Parameter '{key}' must be non-negative, got {params[key]}.")

        # Specific value checks
        if "k_gpx" in params and params["k_gpx"] == 0:
            errors.append("k_gpx is zero: GPx reaction will be inactive.")
        if "vmax_gr" in params and params["vmax_gr"] == 0:
            errors.append("vmax_gr is zero: GR reaction will be inactive.")

        return errors

    def check_constraints(
        self,
        t: float,
        y: np.ndarray,
        params: dict[str, Any],
    ) -> list[str]:
        """Check scientific constraints on the current state.

        Args:
            t: Current time in seconds.
            y: Current state vector.
            params: Model parameters.

        Returns:
            List of violation messages. Empty means no violations.
        """
        violations = []

        gsh = y[IDX_GSH]
        gssg = y[IDX_GSSG]
        h2o2 = y[IDX_H2O2]
        nadph = y[IDX_NADPH]
        d = y[IDX_D]

        # Negativity checks
        if gsh < -1e-9:
            violations.append(f"t={t:.2f}s: [GSH] = {gsh:.6f} mM < 0 (integration failure).")
        if gssg < -1e-9:
            violations.append(f"t={t:.2f}s: [GSSG] = {gssg:.6f} mM < 0 (integration failure).")
        if h2o2 < -1e-9:
            violations.append(f"t={t:.2f}s: [H2O2] = {h2o2:.6f} mM < 0 (integration failure).")
        if nadph < -1e-9:
            violations.append(f"t={t:.2f}s: [NADPH] = {nadph:.6f} mM < 0 (integration failure).")
        if not (-1e-9 <= d <= 1.0 + 1e-9):
            violations.append(
                f"t={t:.2f}s: Damage index D = {d:.6f} outside [0, 1]."
            )

        # GPx approximation validity
        if h2o2 > GPX_BIMOLECULAR_VALIDITY_LIMIT_mM:
            violations.append(
                f"t={t:.2f}s: [H2O2] = {h2o2:.3f} mM > "
                f"{GPX_BIMOLECULAR_VALIDITY_LIMIT_mM} mM. "
                "The bimolecular GPx approximation is not valid at this concentration. "
                "Results should not be interpreted as reliable predictions."
            )

        # Oxidative crisis check (informational)
        gsh_0 = params.get("gsh_0", 2.5)
        if gsh_0 > 0 and gsh / gsh_0 < GSH_CRISIS_THRESHOLD_FRACTION:
            violations.append(
                f"t={t:.2f}s: [GSH] = {gsh:.4f} mM is below "
                f"{GSH_CRISIS_THRESHOLD_FRACTION * 100:.0f}% of initial "
                f"({gsh_0 * GSH_CRISIS_THRESHOLD_FRACTION:.4f} mM). "
                "Severe oxidative crisis; model applicability is uncertain."
            )

        return violations

    # ------------------------------------------------------------------
    # Derived output quantities
    # ------------------------------------------------------------------

    @staticmethod
    def estimated_hemolysis_pct(
        damage: float,
        d_half: float = 0.5,
        hill_n: float = 3.0,
    ) -> float:
        """Estimate haemolysis percentage from the damage index.

        Uses a Hill-type sigmoidal function:
            H(D) = 100 * D^n / (d_half^n + D^n)

        WARNING: The damage index D uses SYNTHETIC parameters (k_damage,
        k_repair). This haemolysis estimate is a mechanistic proxy only.
        It has not been calibrated against experimental haemolysis data.
        Do not use this value for any biological prediction.

        Args:
            damage: Cumulative damage index D in [0, 1].
            d_half: Hill half-maximum (dimensionless). Default 0.5 (synthetic).
            hill_n: Hill coefficient (cooperativity). Default 3.0 (synthetic).

        Returns:
            Estimated haemolysis as a percentage [0, 100].
        """
        d = min(1.0, max(0.0, damage))
        if d == 0:
            return 0.0
        d_n = d ** hill_n
        d_half_n = d_half ** hill_n
        return 100.0 * d_n / (d_half_n + d_n)
