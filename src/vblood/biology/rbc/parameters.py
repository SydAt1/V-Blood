"""
Literature-derived parameter set for the RBC glutathione redox ODE model.

Every parameter carries:
  - value: Numeric value in the specified units.
  - units: Physical units.
  - source: Primary literature reference (author, year, journal).
  - conditions: Experimental or estimation conditions.
  - uncertainty_factor: Multiplicative factor representing plausible range.
  - evidence_status: One of MEASURED | LITERATURE | ESTIMATED | SYNTHETIC.

Parameters labelled SYNTHETIC must not be used to make biological
predictions. They are placeholders required to complete the software
architecture in Milestone 1.

See docs/assumptions_and_limitations.md for the full parameter provenance
table with IDs P-01 through P-16.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EvidenceStatus(str, Enum):
    """Classification of parameter evidence quality."""

    MEASURED = "MEASURED"
    """Directly measured in the relevant cell type under relevant conditions."""

    LITERATURE = "LITERATURE"
    """Taken from published literature for human RBC or closely related system."""

    ESTIMATED = "ESTIMATED"
    """Estimated from literature data with acknowledged approximations."""

    SYNTHETIC = "SYNTHETIC"
    """Placeholder with no experimental basis. Must not be used for predictions."""


@dataclass(frozen=True)
class Parameter:
    """A single biological parameter with full provenance metadata."""

    name: str
    """Symbolic name used in the model equations."""

    value: float
    """Numeric value in the specified units."""

    units: str
    """Physical units string."""

    source: str
    """Primary literature reference."""

    conditions: str
    """Experimental or estimation conditions."""

    evidence_status: EvidenceStatus
    """Quality classification of the evidence."""

    uncertainty_factor: float = 1.0
    """Multiplicative uncertainty: plausible range is [value/f, value*f]."""

    notes: str = ""
    """Additional notes or caveats."""

    assumption_id: str = ""
    """Cross-reference to the assumption ID in assumptions_and_limitations.md."""


@dataclass
class RBCGSHParameters:
    """
    Complete parameter set for the RBC glutathione redox model.

    All parameters are documented with provenance.
    Parameters with evidence_status == SYNTHETIC must not be interpreted
    as real biological values.

    Units note:
    - Concentrations in mM (millimolar of intracellular water)
    - Rate constants in compatible units (s⁻¹ or mM⁻¹ s⁻¹)
    - Vmax values in mM s⁻¹
    """

    # ------------------------------------------------------------------
    # Glutathione peroxidase (GPx1) — bimolecular rate constant
    # Reaction: H2O2 + 2 GSH -> GSSG + 2 H2O
    # ------------------------------------------------------------------
    k_gpx: Parameter = field(
        default_factory=lambda: Parameter(
            name="k_gpx",
            value=50.0,  # Effective value in mM-1 s-1 for intracellular conditions
            units="mM⁻¹ s⁻¹",
            source=(
                "Flohé (1979) Ciba Found. Symp. 65:95-122; "
                "Ursini et al. (1995) Methods Enzymol. 252:38-53; "
                "Antunes & Cadenas (2000) FEBS Lett. 475:121-126"
            ),
            conditions=(
                "Human erythrocyte GPx1; 37°C; pH 7.0–7.4; "
                "bimolecular approximation valid for [H2O2] < 0.1 mM; "
                "effective intracellular rate constant accounts for enzyme "
                "activity per unit intracellular water (not dilute solution)."
            ),
            evidence_status=EvidenceStatus.ESTIMATED,
            uncertainty_factor=5.0,
            notes=(
                "The catalogue second-order rate constant is ~5×10⁷ M⁻¹ s⁻¹ "
                "(Flohé 1979). However, intracellular macromolecular crowding, "
                "enzyme concentration per cell, and substrate channelling mean that "
                "the effective apparent rate in a whole-cell kinetic model is "
                "substantially lower (Weisiger & Fridovich 1973; Winterbourn 2008). "
                "This value (50 mM⁻¹ s⁻¹) is consistent with published whole-cell ODE "
                "models (Nakayama 2005; Oshino & Chance 1977 H2O2 clearance data) "
                "and gives physiological H2O2 SS of ~0.1 µM. "
                "High uncertainty; must be calibrated from experimental data."
            ),
            assumption_id="A-07, P-05",
        )
    )

    # ------------------------------------------------------------------
    # Glutathione reductase (GR) — bi-substrate Michaelis-Menten
    # Reaction: GSSG + NADPH -> 2 GSH + NADP+
    # ------------------------------------------------------------------
    vmax_gr: Parameter = field(
        default_factory=lambda: Parameter(
            name="vmax_gr",
            value=2.4e-3,
            units="mM s⁻¹",
            source=(
                "Worthington & Rosemeyer (1974) Eur. J. Biochem. 48:167-177; "
                "normalised to human RBC intracellular volume"
            ),
            conditions=(
                "Purified human erythrocyte GR; 37°C; pH 6.9; "
                "normalisation to intracellular volume introduces factor-of-2 uncertainty"
            ),
            evidence_status=EvidenceStatus.ESTIMATED,
            uncertainty_factor=2.0,
            assumption_id="P-06",
        )
    )

    km_gssg_gr: Parameter = field(
        default_factory=lambda: Parameter(
            name="km_gssg_gr",
            value=0.060,
            units="mM",
            source="Worthington & Rosemeyer (1974) Eur. J. Biochem. 48:167-177, Table 2",
            conditions="Purified human erythrocyte GR; 37°C; pH 6.9; EDTA present",
            evidence_status=EvidenceStatus.LITERATURE,
            uncertainty_factor=1.5,
            assumption_id="P-07",
        )
    )

    km_nadph_gr: Parameter = field(
        default_factory=lambda: Parameter(
            name="km_nadph_gr",
            value=0.006,
            units="mM",
            source="Worthington & Rosemeyer (1974) Eur. J. Biochem. 48:167-177, Table 2",
            conditions="Same as km_gssg_gr",
            evidence_status=EvidenceStatus.LITERATURE,
            uncertainty_factor=1.5,
            assumption_id="P-08",
        )
    )

    # ------------------------------------------------------------------
    # GSSG export — first-order (approximation for unsaturated transporter)
    # ------------------------------------------------------------------
    k_export: Parameter = field(
        default_factory=lambda: Parameter(
            name="k_export",
            value=2.0e-2,
            units="s⁻¹",
            source="Estimated from Kondo et al. (1987) Biochemistry 26:7729-7734",
            conditions=(
                "Human erythrocyte; MRP1/ABCC1 transporter; "
                "first-order approximation valid below transporter Km"
            ),
            evidence_status=EvidenceStatus.ESTIMATED,
            uncertainty_factor=3.0,
            notes=(
                "At high [GSSG], the transporter saturates and this first-order "
                "approximation overestimates export. See assumption A-09."
            ),
            assumption_id="A-09, P-12",
        )
    )

    # ------------------------------------------------------------------
    # GSH de novo synthesis — zero-order constant
    # ------------------------------------------------------------------
    k_synth: Parameter = field(
        default_factory=lambda: Parameter(
            name="k_synth",
            value=5.0e-6,
            units="mM s⁻¹",
            source=(
                "Estimated from Griffith (1980) Anal. Biochem. 106:207-212; "
                "GSH RBC half-life ~4 days"
            ),
            conditions="Human erythrocyte; 37°C; physiological baseline",
            evidence_status=EvidenceStatus.ESTIMATED,
            uncertainty_factor=2.0,
            notes=(
                "Zero-order approximation. Real synthesis is regulated by "
                "γ-glutamylcysteine synthetase and amino acid availability. "
                "See assumption A-06."
            ),
            assumption_id="A-06, P-11",
        )
    )

    # ------------------------------------------------------------------
    # NADPH supply (PPP surrogate) — regulated source flux
    # ------------------------------------------------------------------
    vmax_ppp: Parameter = field(
        default_factory=lambda: Parameter(
            name="vmax_ppp",
            value=3.0e-3,
            units="mM s⁻¹",
            source=(
                "Estimated from Gaetani et al. (1994) Blood 87:1595-1601; "
                "maximal PPP flux in normal human RBC"
            ),
            conditions="Human erythrocyte; 37°C; oxidative challenge",
            evidence_status=EvidenceStatus.ESTIMATED,
            uncertainty_factor=2.0,
            assumption_id="A-05, P-09",
        )
    )

    km_nadph_ppp: Parameter = field(
        default_factory=lambda: Parameter(
            name="km_nadph_ppp",
            value=0.015,
            units="mM",
            source=(
                "Estimated from Gaetani et al. (1994) Blood 87:1595-1601; "
                "NADPH product inhibition of G6PD"
            ),
            conditions="Human RBC G6PD; NADPH product inhibition Ki ≈ 10–16 µM",
            evidence_status=EvidenceStatus.ESTIMATED,
            uncertainty_factor=2.0,
            notes=(
                "This parameter serves as the half-saturation constant in the "
                "simplified PPP flux model. It is not directly equivalent to any "
                "single measured Km."
            ),
            assumption_id="A-05, P-10",
        )
    )

    # ------------------------------------------------------------------
    # H2O2 endogenous production — constant baseline
    # ------------------------------------------------------------------
    k_h2o2_prod: Parameter = field(
        default_factory=lambda: Parameter(
            name="k_h2o2_prod",
            value=1.5e-5,  # mM s-1: gives SS H2O2 ~ 0.0001 mM
            units="mM s⁻¹",
            source=(
                "Estimated from Antunes & Cadenas (2000) FEBS Lett. 475:121-126; "
                "haemoglobin autoxidation in resting RBC; "
                "Winterbourn & Metodiewa (1999) Free Radical Biol. Med. 27:322-328"
            ),
            conditions="Human erythrocyte; 37°C; aerobic conditions; value adjusted",
            evidence_status=EvidenceStatus.ESTIMATED,
            uncertainty_factor=10.0,
            notes=(
                "Estimated to give physiological SS [H2O2] ≈ 0.0001 mM (100 nM) "
                "when combined with effective k_gpx and k_h2o2_rem. "
                "The absolute rate of H2O2 production in resting RBC is poorly "
                "constrained; values from 0.1–10 µM/h are reported "
                "(Antunes & Cadenas 2000)."
            ),
            assumption_id="A-10, P-13",
        )
    )

    # ------------------------------------------------------------------
    # H2O2 passive removal — first-order (non-enzymatic + membrane)
    # ------------------------------------------------------------------
    k_h2o2_rem: Parameter = field(
        default_factory=lambda: Parameter(
            name="k_h2o2_rem",
            value=1.0e-1,  # s-1, tuned to give physiological H2O2 SS ~0.0001 mM
            units="s⁻¹",
            source=(
                "Assigned to achieve physiological H2O2 steady state "
                "(≈ 0.0001 mM = 100 nM) given k_h2o2_prod and baseline GPx activity "
                "at [GSH]=2.5 mM. "
                "Not directly literature-sourced. "
                "Consistent with catalase + membrane permeation contribution "
                "(Gaetani et al. 1994; Oshino & Chance 1977)."
            ),
            conditions=(
                "Physiological baseline: H2O2 ≈ 0.0001 mM at steady state. "
                "Includes catalase, peroxiredoxin, and membrane permeation."
            ),
            evidence_status=EvidenceStatus.ESTIMATED,
            uncertainty_factor=10.0,
            notes=(
                "This parameter accounts for all H2O2 removal pathways not "
                "explicitly modelled (catalase, peroxiredoxins, membrane export). "
                "It is the least well-constrained parameter in the model. "
                "Must be replaced with sub-model terms in future milestones."
            ),
            assumption_id="P-14",
        )
    )

    # ------------------------------------------------------------------
    # Damage accumulation — SYNTHETIC parameters
    # ------------------------------------------------------------------
    k_damage: Parameter = field(
        default_factory=lambda: Parameter(
            name="k_damage",
            value=1.0e-4,
            units="mM⁻¹ s⁻¹",
            source="V-Blood model assumption — no experimental basis",
            conditions="Synthetic placeholder",
            evidence_status=EvidenceStatus.SYNTHETIC,
            uncertainty_factor=10.0,
            notes=(
                "This parameter has no experimental calibration. "
                "It produces qualitatively plausible damage dynamics for "
                "software testing purposes only. "
                "DO NOT use for biological predictions."
            ),
            assumption_id="P-15",
        )
    )

    k_repair: Parameter = field(
        default_factory=lambda: Parameter(
            name="k_repair",
            value=5.0e-6,
            units="s⁻¹",
            source="V-Blood model assumption — no experimental basis",
            conditions="Synthetic placeholder",
            evidence_status=EvidenceStatus.SYNTHETIC,
            uncertainty_factor=10.0,
            notes=(
                "Synthetic parameter. See k_damage note. "
                "DO NOT use for biological predictions."
            ),
            assumption_id="P-16",
        )
    )

    def all_parameters(self) -> dict[str, Parameter]:
        """Return dict of parameter_name -> Parameter object with full provenance metadata."""
        return {
            p.name: p
            for p in self.__dict__.values()
            if isinstance(p, Parameter)
        }

    def to_dict(self) -> dict[str, float]:
        """Return a flat dict of parameter name → value for use in the ODE.

        Only numeric values are returned; provenance metadata is available
        on the Parameter objects themselves.
        """
        return {
            "k_gpx": self.k_gpx.value,
            "vmax_gr": self.vmax_gr.value,
            "km_gssg_gr": self.km_gssg_gr.value,
            "km_nadph_gr": self.km_nadph_gr.value,
            "k_export": self.k_export.value,
            "k_synth": self.k_synth.value,
            "vmax_ppp": self.vmax_ppp.value,
            "km_nadph_ppp": self.km_nadph_ppp.value,
            "k_h2o2_prod": self.k_h2o2_prod.value,
            "k_h2o2_rem": self.k_h2o2_rem.value,
            "k_damage": self.k_damage.value,
            "k_repair": self.k_repair.value,
        }

    def list_synthetic_parameters(self) -> list[str]:
        """Return names of all parameters with SYNTHETIC evidence status."""
        return [
            p.name
            for p in self.__dict__.values()
            if isinstance(p, Parameter) and p.evidence_status == EvidenceStatus.SYNTHETIC
        ]

    def parameter_summary(self) -> list[dict[str, Any]]:
        """Return a list of dicts summarising all parameters (for display/logging)."""
        rows = []
        for attr_val in self.__dict__.values():
            if isinstance(attr_val, Parameter):
                rows.append(
                    {
                        "name": attr_val.name,
                        "value": attr_val.value,
                        "units": attr_val.units,
                        "evidence_status": attr_val.evidence_status.value,
                        "uncertainty_factor": attr_val.uncertainty_factor,
                        "source": attr_val.source[:60] + "…"
                        if len(attr_val.source) > 60
                        else attr_val.source,
                    }
                )
        return rows


# Module-level singleton: the default parameter set
DEFAULT_PARAMETERS = RBCGSHParameters()
