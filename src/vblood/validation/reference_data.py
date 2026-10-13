"""
L2 Reference Data Ingestion and Schemas for RBC Physiological Validation.

Defines trustworthy published reference ranges for normal resting human erythrocytes.
Every measurement carries full literature provenance, measurement units,
compartment specification, and evidence status.

Literature sources:
- Sies, H. (1999) Free Radic. Biol. Med. 27:916-921 ([GSH] in human tissues).
- Anderson, M. E. (1998) Chem. Biol. Interact. 111-112:1-14 (Glutathione physiology).
- Giustarini, D. et al. (2013) Free Radic. Biol. Med. 65:1248-1262 (RBC GSSG and GSH/GSSG ratio).
- Antunes, F. & Cadenas, E. (2000) FEBS Lett. 475:121-126 (Intracellular H2O2 steady-state).
- Gaetani, G. F. et al. (1994) Blood 84:2018-2024 / Blood 87:1595 (RBC NADPH and catalase kinetics).
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EvidenceStatus(str, Enum):
    """Evidence status of a biological measurement."""

    EXPERIMENTAL = "EXPERIMENTAL"
    LITERATURE_DERIVED = "LITERATURE_DERIVED"
    CALIBRATED_ESTIMATE = "CALIBRATED_ESTIMATE"
    SYNTHETIC = "SYNTHETIC"


class ValidationLevel(str, Enum):
    """Validation hierarchy levels from docs/validation_plan.md."""

    L0_SOFTWARE = "L0_SOFTWARE"
    L1_QUALITATIVE = "L1_QUALITATIVE"
    L2_STEADY_STATE = "L2_STEADY_STATE"
    L3_DYNAMIC = "L3_DYNAMIC"
    L4_EXTERNAL = "L4_EXTERNAL"
    L5_CROSS_MODEL = "L5_CROSS_MODEL"


class PhysiologicalReference(BaseModel):
    """A single physiological reference measurement for human RBCs."""

    model_config = ConfigDict(frozen=True)

    variable: str = Field(description="Name of the physiological variable or state.")
    units: str = Field(description="Measurement units, e.g. 'mM'.")
    compartment: str = Field(default="RBC cytosol", description="Biological compartment.")
    reference_min: float = Field(description="Normal lower bound for resting human erythrocyte.")
    reference_max: float = Field(description="Normal upper bound for resting human erythrocyte.")
    typical_mean: float | None = Field(default=None, description="Typical central/mean reported value.")
    tolerance_min: float = Field(
        description="Relaxed lower bound below which a model prediction fails L2 validation."
    )
    tolerance_max: float = Field(
        description="Relaxed upper bound above which a model prediction fails L2 validation."
    )
    literature_source: str = Field(description="Full literature citation.")
    evidence_status: EvidenceStatus = Field(
        default=EvidenceStatus.LITERATURE_DERIVED,
        description="Evidence grading for this reference value.",
    )
    notes: str = Field(default="", description="Scientific notes on methodology or assay specificity.")


# Trustworthy L2 Reference Measurements (Literature-Derived)
L2_RBC_REFERENCES: dict[str, PhysiologicalReference] = {
    "GSH": PhysiologicalReference(
        variable="GSH",
        units="mM",
        compartment="RBC cytosol",
        reference_min=1.5,
        reference_max=3.0,
        typical_mean=2.2,
        tolerance_min=0.5,
        tolerance_max=5.0,
        literature_source="Sies (1999) Free Radic. Biol. Med. 27:916; Anderson (1998) Chem. Biol. Interact. 111:1",
        evidence_status=EvidenceStatus.LITERATURE_DERIVED,
        notes="Standard intracellular reduced glutathione in healthy adult human erythrocytes.",
    ),
    "GSSG": PhysiologicalReference(
        variable="GSSG",
        units="mM",
        compartment="RBC cytosol",
        reference_min=0.010,
        reference_max=0.040,
        typical_mean=0.025,
        tolerance_min=0.001,
        tolerance_max=0.100,
        literature_source="Giustarini et al. (2013) Free Radic. Biol. Med. 65:1248-1262",
        evidence_status=EvidenceStatus.LITERATURE_DERIVED,
        notes="True resting GSSG measured with NEM thiol-blocking to prevent artifactual ex vivo GSH oxidation.",
    ),
    "GSH_GSSG_RATIO": PhysiologicalReference(
        variable="GSH_GSSG_RATIO",
        units="dimensionless",
        compartment="RBC cytosol",
        reference_min=30.0,
        reference_max=300.0,
        typical_mean=100.0,
        tolerance_min=5.0,
        tolerance_max=1e9,
        literature_source="Giustarini et al. (2013) Free Radic. Biol. Med. 65:1248-1262",
        evidence_status=EvidenceStatus.LITERATURE_DERIVED,
        notes="GSH/GSSG ratio in unstressed erythrocytes is typically > 30 and often ~50-150. Failure criterion is < 5.",
    ),
    "H2O2": PhysiologicalReference(
        variable="H2O2",
        units="mM",
        compartment="RBC cytosol",
        reference_min=0.00001,  # 10 nM
        reference_max=0.00100,  # 1000 nM (1 µM)
        typical_mean=0.00010,   # 100 nM
        tolerance_min=1e-5,
        tolerance_max=0.010,    # 10 µM
        literature_source="Antunes & Cadenas (2000) FEBS Lett. 475:121; Winterbourn & Metodiewa (1999) Free Radic. Biol. Med. 27:322",
        evidence_status=EvidenceStatus.LITERATURE_DERIVED,
        notes="Basal intracellular H2O2 in erythrocytes under normal oxygen tension.",
    ),
    "NADPH": PhysiologicalReference(
        variable="NADPH",
        units="mM",
        compartment="RBC cytosol",
        reference_min=0.010,
        reference_max=0.050,
        typical_mean=0.030,
        tolerance_min=0.002,
        tolerance_max=0.200,
        literature_source="Gaetani et al. (1994) Blood 84:2018-2024",
        evidence_status=EvidenceStatus.LITERATURE_DERIVED,
        notes="Concentration of reduced NADPH in normal erythrocytes (total NADP(H) pool is ~0.04-0.06 mM).",
    ),
}


def get_l2_references() -> dict[str, PhysiologicalReference]:
    """Return dictionary of all curated L2 reference measurements."""
    return dict(L2_RBC_REFERENCES)
