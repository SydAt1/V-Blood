"""
Mechanism Preset Library for Chemical-Biological Scenarios (Milestone 4 - Task 1).

Defines typed Pydantic specifications mapping chemical exposure mechanisms
to kinetic rate terms and enzyme parameter modifiers.

Supported mechanism classes:
1. Direct oxidant: H2O2-like bolus or continuous influx.
2. GSH conjugator: Direct electrophilic consumption of reduced glutathione.
3. Redox cycler: NADPH-dependent catalytic generation of H2O2.
4. Enzyme inhibitor: Competitive or non-competitive inhibition of G6PD or GR.
5. NADPH drain: Non-GR catalytic consumption of the cellular NADPH pool.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable
from pydantic import BaseModel, ConfigDict, Field, model_validator


class EvidenceLevel(str, Enum):
    """Evidence classification of compounds, parameters, and mechanisms."""

    CURATED = "CURATED"        # Experimentally verified and literature-grounded
    ESTIMATED = "ESTIMATED"    # Biologically grounded proxy or literature-derived estimate
    UNVERIFIED = "UNVERIFIED"  # Synthetic placeholder or unvalidated estimate (flagged)


class MechanismType(str, Enum):
    """Categorical mechanism classification."""

    DIRECT_OXIDANT = "DIRECT_OXIDANT"
    GSH_CONJUGATOR = "GSH_CONJUGATOR"
    REDOX_CYCLER = "REDOX_CYCLER"
    ENZYME_INHIBITOR = "ENZYME_INHIBITOR"
    NADPH_DRAIN = "NADPH_DRAIN"


class ParameterSpec(BaseModel):
    """Metadata-annotated parameter specification for mechanism kinetics."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(description="Parameter name.")
    value: float = Field(description="Numeric value in specified units.")
    units: str = Field(description="Physical units string.")
    min_bound: float = Field(ge=0.0, description="Physiologically or physically allowable minimum.")
    max_bound: float = Field(gt=0.0, description="Physiologically or physically allowable maximum.")
    provenance: str = Field(description="Scientific citation or rationale.")
    evidence_level: EvidenceLevel = Field(default=EvidenceLevel.CURATED)
    confidence_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score in [0.0, 1.0]. UNVERIFIED entries receive <= 0.3.",
    )

    @model_validator(mode="after")
    def validate_bounds(self) -> "ParameterSpec":
        if self.min_bound > self.max_bound:
            raise ValueError(f"min_bound ({self.min_bound}) exceeds max_bound ({self.max_bound}).")
        if not (self.min_bound <= self.value <= self.max_bound):
            raise ValueError(
                f"value {self.value} is outside allowable range [{self.min_bound}, {self.max_bound}]."
            )
        return self


# --------------------------------------------------------------------------- #
# Typed Mechanism Specifications
# --------------------------------------------------------------------------- #


class DirectOxidantSpec(BaseModel):
    """Direct oxidant mechanism (e.g. H2O2, cumene hydroperoxide, t-butyl hydroperoxide)."""

    model_config = ConfigDict(frozen=True)

    mechanism_type: MechanismType = MechanismType.DIRECT_OXIDANT
    bolus_mM: float = Field(default=0.0, ge=0.0, description="Instantaneous bolus at start_time_s.")
    influx_rate_mM_s: float = Field(default=0.0, ge=0.0, description="Continuous zero-order infusion flux.")
    start_time_s: float = Field(default=0.0, ge=0.0, description="Onset time of oxidant exposure.")
    duration_s: float = Field(default=3600.0, gt=0.0, description="Duration of infusion flux.")
    evidence_level: EvidenceLevel = EvidenceLevel.CURATED
    provenance: str = "Standard in vitro oxidant exposure protocol."


class GSHConjugatorSpec(BaseModel):
    """GSH-depleting conjugator mechanism (e.g. CDNB, NEM, NAPQI).

    Consumes GSH directly without producing GSSG:
        GSH + Compound -> GS-Conjugate
        v_conj = k_conj * [GSH] * [Compound]
    """

    model_config = ConfigDict(frozen=True)

    mechanism_type: MechanismType = MechanismType.GSH_CONJUGATOR
    compound_conc_mM: float = Field(ge=0.0, description="Extracellular/intracellular compound concentration.")
    rate_constant_mM_s: float = Field(
        default=0.05,
        ge=0.0,
        description="Second-order conjugation rate constant k_conj in mM⁻¹ s⁻¹.",
    )
    evidence_level: EvidenceLevel = EvidenceLevel.CURATED
    provenance: str = "Glutathione S-transferase / direct electrophilic addition kinetics."


class RedoxCyclerSpec(BaseModel):
    """Redox cycling mechanism (e.g. Menadione, Doxorubicin, Primaquine quinone).

    Consumes NADPH and generates H2O2 via catalytic cycling:
        NADPH + O2 + H+ -> NADP+ + H2O2
        v_cycle = k_cycle * [Compound] * [NADPH] / (Km + [NADPH])
    """

    model_config = ConfigDict(frozen=True)

    mechanism_type: MechanismType = MechanismType.REDOX_CYCLER
    compound_conc_mM: float = Field(ge=0.0, description="Intracellular cycling compound concentration.")
    catalytic_rate_s: float = Field(
        default=0.01,
        ge=0.0,
        description="Apparent turnover rate constant k_cycle in s⁻¹.",
    )
    km_nadph_mM: float = Field(
        default=0.010,
        gt=0.0,
        description="Affinity constant for NADPH reduction in mM.",
    )
    evidence_level: EvidenceLevel = EvidenceLevel.CURATED
    provenance: str = "Flavoenzyme/diaphorase catalyzed quinone cycling kinetics."


class InhibitionType(str, Enum):
    COMPETITIVE = "COMPETITIVE"
    NON_COMPETITIVE = "NON_COMPETITIVE"


class EnzymeTarget(str, Enum):
    G6PD = "G6PD"
    GR = "GR"


class EnzymeInhibitorSpec(BaseModel):
    """Enzyme inhibitor mechanism targeting G6PD or Glutathione Reductase.

    Competitive: multiplies Km by (1 + [I]/Ki).
    Non-competitive: divides Vmax by (1 + [I]/Ki).
    """

    model_config = ConfigDict(frozen=True)

    mechanism_type: MechanismType = MechanismType.ENZYME_INHIBITOR
    target_enzyme: EnzymeTarget = Field(description="Enzyme targeted by inhibitor.")
    inhibition_type: InhibitionType = Field(default=InhibitionType.COMPETITIVE)
    compound_conc_mM: float = Field(ge=0.0, description="Inhibitor concentration [I] in mM.")
    ki_mM: float = Field(gt=0.0, description="Inhibition constant Ki in mM.")
    evidence_level: EvidenceLevel = EvidenceLevel.CURATED
    provenance: str = "Enzyme kinetics inhibition model."


class NADPHDrainSpec(BaseModel):
    """Direct cellular NADPH drain (e.g. aldose reductase flux, surrogate reductase).

    Consumes NADPH without producing H2O2:
        NADPH -> NADP+
        v_drain = k_drain * [Compound] * [NADPH] / (Km + [NADPH])
    """

    model_config = ConfigDict(frozen=True)

    mechanism_type: MechanismType = MechanismType.NADPH_DRAIN
    compound_conc_mM: float = Field(ge=0.0, description="Substrate/compound concentration in mM.")
    drain_rate_s: float = Field(
        default=0.005,
        ge=0.0,
        description="Apparent maximal drain rate constant in s⁻¹.",
    )
    km_nadph_mM: float = Field(
        default=0.010,
        gt=0.0,
        description="Affinity constant for NADPH in mM.",
    )
    evidence_level: EvidenceLevel = EvidenceLevel.CURATED
    provenance: str = "Cellular NADPH consumption pathway surrogate."


# Union type for mechanisms
MechanismSpec = DirectOxidantSpec | GSHConjugatorSpec | RedoxCyclerSpec | EnzymeInhibitorSpec | NADPHDrainSpec


# --------------------------------------------------------------------------- #
# Scenario Dynamic Hook and Rate Evaluator
# --------------------------------------------------------------------------- #


class ScenarioMechanismHooks:
    """Computes dynamic ODE rate contributions and parameter modifications for active mechanisms."""

    def __init__(self, specs: list[MechanismSpec]):
        self.specs = specs

    def modify_parameters(self, params: dict[str, Any]) -> dict[str, Any]:
        """Apply parameter modifications (e.g. enzyme inhibitors) to a copy of params."""
        modified = dict(params)

        for spec in self.specs:
            if isinstance(spec, EnzymeInhibitorSpec):
                conc = spec.compound_conc_mM
                ki = spec.ki_mM
                if conc <= 0.0 or ki <= 0.0:
                    continue

                factor = 1.0 + (conc / ki)

                if spec.target_enzyme == EnzymeTarget.G6PD:
                    if spec.inhibition_type == InhibitionType.COMPETITIVE:
                        if "km_nadp" in modified:
                            modified["km_nadp"] = float(modified["km_nadp"] * factor)
                        if "km_nadph_ppp" in modified:
                            modified["km_nadph_ppp"] = float(modified["km_nadph_ppp"] * factor)
                    else:  # NON_COMPETITIVE
                        if "vmax_g6pd" in modified:
                            modified["vmax_g6pd"] = float(modified["vmax_g6pd"] / factor)
                        if "vmax_ppp" in modified:
                            modified["vmax_ppp"] = float(modified["vmax_ppp"] / factor)

                elif spec.target_enzyme == EnzymeTarget.GR:
                    if spec.inhibition_type == InhibitionType.COMPETITIVE:
                        if "km_gssg_gr" in modified:
                            modified["km_gssg_gr"] = float(modified["km_gssg_gr"] * factor)
                    else:  # NON_COMPETITIVE
                        if "vmax_gr" in modified:
                            modified["vmax_gr"] = float(modified["vmax_gr"] / factor)

        return modified

    def compute_rates(self, t: float, y: Any) -> dict[str, float]:
        """Compute additional rate fluxes at time t for state vector y.

        State order: [GSH, GSSG, H2O2, NADPH, D]

        Returns:
            Dictionary with:
            - v_oxidant_influx: mM/s added to H2O2
            - v_gsh_conjugation: mM/s subtracted from GSH
            - v_redox_cycle: mM/s added to H2O2 and subtracted from NADPH
            - v_nadph_drain: mM/s subtracted from NADPH
        """
        gsh = max(0.0, float(y[0]))
        nadph = max(0.0, float(y[3]))

        v_oxidant_influx = 0.0
        v_gsh_conjugation = 0.0
        v_redox_cycle = 0.0
        v_nadph_drain = 0.0

        for spec in self.specs:
            if isinstance(spec, DirectOxidantSpec):
                if spec.start_time_s <= t <= (spec.start_time_s + spec.duration_s):
                    v_oxidant_influx += spec.influx_rate_mM_s

            elif isinstance(spec, GSHConjugatorSpec):
                v_gsh_conjugation += spec.rate_constant_mM_s * spec.compound_conc_mM * gsh

            elif isinstance(spec, RedoxCyclerSpec):
                sat = nadph / (spec.km_nadph_mM + nadph) if (spec.km_nadph_mM + nadph) > 0 else 0.0
                v_redox_cycle += spec.catalytic_rate_s * spec.compound_conc_mM * sat

            elif isinstance(spec, NADPHDrainSpec):
                sat = nadph / (spec.km_nadph_mM + nadph) if (spec.km_nadph_mM + nadph) > 0 else 0.0
                v_nadph_drain += spec.drain_rate_s * spec.compound_conc_mM * sat

        return {
            "v_oxidant_influx": v_oxidant_influx,
            "v_gsh_conjugation": v_gsh_conjugation,
            "v_redox_cycle": v_redox_cycle,
            "v_nadph_drain": v_nadph_drain,
        }
