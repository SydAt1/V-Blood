"""
Pydantic schemas for experimental records and data ingestion (Task 4).

Captures published experimental measurements and observations relevant to the
RBC oxidative-stress model with full provenance, biological context,
and measurement uncertainty.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class EvidenceStatus(str, Enum):
    """Quality classification of the evidence."""

    EXPERIMENTAL = "EXPERIMENTAL"
    LITERATURE_DERIVED = "LITERATURE_DERIVED"
    CALIBRATED_ESTIMATE = "CALIBRATED_ESTIMATE"
    SYNTHETIC = "SYNTHETIC"


class ReviewStatus(str, Enum):
    """Review or validation status of the record."""

    UNREVIEWED = "UNREVIEWED"
    PEER_REVIEWED = "PEER_REVIEWED"
    CURATED = "CURATED"
    SUSPECT = "SUSPECT"
    FLAGGED = "FLAGGED"


class SampleType(str, Enum):
    """Biological sample matrix."""

    WHOLE_BLOOD = "WHOLE_BLOOD"
    ISOLATED_RBCS = "ISOLATED_RBCS"
    PACKED_RBCS = "PACKED_RBCS"
    RBC_SUSPENSION = "RBC_SUSPENSION"
    PLASMA = "PLASMA"
    LYSATE = "LYSATE"
    OTHER = "OTHER"


class ExposureProfile(str, Enum):
    """Temporal chemical exposure profile."""

    BOLUS = "BOLUS"
    CONTINUOUS_INFUSION = "CONTINUOUS_INFUSION"
    STATIC_INCUBATION = "STATIC_INCUBATION"
    NONE = "NONE"


class EndpointType(str, Enum):
    """Biological or toxicological measurement endpoint."""

    GSH = "GSH"
    GSSG = "GSSG"
    GSH_GSSG_RATIO = "GSH_GSSG_RATIO"
    H2O2 = "H2O2"
    NADPH = "NADPH"
    HEMOLYSIS = "HEMOLYSIS"
    OXIDATIVE_DAMAGE = "OXIDATIVE_DAMAGE"
    OTHER = "OTHER"


class ExperimentalRecord(BaseModel):
    """Traceable, immutable record of a published biological measurement.

    Rules:
    - Missing fields must remain None (never zero-filled or guessed).
    - Physical concentrations and counts must be non-negative.
    - Evidence status must be clearly distinguished (SYNTHETIC vs EXPERIMENTAL).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    # 1. Identity & Provenance
    record_id: str = Field(description="Unique record identifier, e.g. 'REC-GAETANI-1994-01'.")
    study_id: str = Field(description="Study or publication identifier, e.g. 'STUDY-GAETANI-1994'.")
    experiment_id: str | None = Field(default=None, description="Experiment or assay identifier within the study.")
    publication_title: str = Field(description="Title of primary source publication.")
    authors: str = Field(description="Author list or citation shorthand (e.g. 'Gaetani et al.').")
    publication_year: int = Field(ge=1800, le=2100, description="Year of publication.")
    doi_or_url: str = Field(description="Digital Object Identifier or stable URL.")
    data_extraction_notes: str | None = Field(default=None, description="Notes on how data was extracted or transcribed.")
    evidence_status: EvidenceStatus = Field(description="Evidence grading for this observation.")
    review_status: ReviewStatus = Field(default=ReviewStatus.UNREVIEWED, description="Curator review status.")
    schema_version: str = Field(default="1.0.0", description="Schema version.")

    # 2. Chemical Information
    chemical_name: str = Field(description="Name of test chemical or stressor (e.g. 'Hydrogen peroxide').")
    pubchem_cid: int | None = Field(default=None, ge=1, description="PubChem Compound ID if available.")
    inchikey: str | None = Field(default=None, description="Standard InChIKey if available.")
    smiles: str | None = Field(default=None, description="SMILES structure representation if available.")
    exposure_concentration: float | None = Field(default=None, ge=0.0, description="Applied concentration.")
    exposure_concentration_unit: str | None = Field(default=None, description="Unit of applied concentration, e.g. 'mM'.")

    # 3. Biological Context
    sample_type: SampleType = Field(description="Type of biological sample matrix.")
    biological_compartment: str = Field(default="RBC cytosol", description="Cellular compartment.")
    species: str = Field(default="Homo sapiens", description="Species under investigation.")
    population_characteristics: str | None = Field(default=None, description="Donor age, sex, health, or G6PD genotype.")
    exposure_duration_s: float | None = Field(default=None, ge=0.0, description="Exposure duration in seconds.")
    exposure_profile: ExposureProfile = Field(default=ExposureProfile.NONE, description="Exposure administration mode.")
    temperature_celsius: float | None = Field(default=None, ge=0.0, le=100.0, description="Incubation temperature in °C.")
    ph: float | None = Field(default=None, ge=0.0, le=14.0, description="Assay pH if reported.")
    experimental_conditions: str | None = Field(default=None, description="Additional context or buffer details.")

    # 4. Measurement Information
    endpoint: EndpointType = Field(description="Target biological measurement endpoint.")
    original_value: float = Field(description="Direct reported measurement value.")
    original_unit: str = Field(description="Original measurement unit as published.")
    normalized_value: float | None = Field(
        default=None,
        description="Value converted to canonical model units (mM for metabolites, % for hemolysis).",
    )
    normalized_unit: str | None = Field(default=None, description="Standard canonical unit (e.g. 'mM', '%').")
    assay_method: str | None = Field(default=None, description="Assay technique (e.g. 'HPLC', 'DTNB Ellman', 'Spectrophotometry').")
    replicate_count: int | None = Field(default=None, ge=1, description="Number of independent replicates (n).")
    uncertainty_value: float | None = Field(default=None, ge=0.0, description="Reported error/uncertainty magnitude.")
    uncertainty_type: str | None = Field(default=None, description="Uncertainty metric: 'SD', 'SEM', or 'CI95'.")
    control_baseline_value: float | None = Field(default=None, description="Reported unexposed control or baseline value.")
    statistical_notes: str | None = Field(default=None, description="Significance or statistical details.")

    @field_validator("original_value")
    @classmethod
    def validate_positive_measurements(cls, v: float, info) -> float:
        """Physical concentrations and counts must be non-negative."""
        if v < 0.0:
            raise ValueError(f"Measurement original_value cannot be negative, got {v}")
        return v

    @model_validator(mode="after")
    def validate_hemolysis_bounds(self) -> "ExperimentalRecord":
        """Hemolysis values should be between 0 and 100%."""
        if self.endpoint == EndpointType.HEMOLYSIS:
            if self.original_unit in ("%", "pct", "percent"):
                if self.original_value > 105.0:  # Allow slight calibration margin
                    raise ValueError(f"Hemolysis percentage exceeds 100%: {self.original_value}")
        return self
