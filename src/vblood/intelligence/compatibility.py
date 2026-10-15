"""
Mechanism Compatibility and Evidence Grading Interfaces (Milestone 6).

Defines clean, non-intrusive protocols to assess whether proposed chemical
mechanisms map to active V-Blood biological models, and evaluates evidence tiers.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from vblood.scenarios.mechanisms import EvidenceLevel, MechanismType

SUPPORTED_MECHANISMS: set[MechanismType] = {
    MechanismType.DIRECT_OXIDANT,
    MechanismType.GSH_CONJUGATOR,
    MechanismType.REDOX_CYCLER,
    MechanismType.ENZYME_INHIBITOR,
    MechanismType.NADPH_DRAIN,
}


class ChemicalCompatibilityAssessment(BaseModel):
    """Evaluation of chemical mechanism compatibility with active ODE models."""

    model_config = ConfigDict(frozen=True)

    is_compatible: bool = Field(description="True if mechanism is supported by current models.")
    mechanism_type: str = Field(description="Mechanistic class of the compound.")
    supported_models: list[str] = Field(description="Model IDs supporting this mechanism.")
    unmodeled_aspects: list[str] = Field(
        default_factory=list,
        description="Aspects of compound pharmacology not captured by V-Blood ODEs.",
    )
    notes: str = Field(description="Detailed explanation of compatibility status.")


class EvidenceTierEvaluation(BaseModel):
    """Evaluation of literature citations and kinetic provenance."""

    model_config = ConfigDict(frozen=True)

    evidence_level: EvidenceLevel = Field(description="Graded evidence tier (CURATED, ESTIMATED, UNVERIFIED).")
    has_doi_or_citation: bool = Field(description="True if literature reference is provided.")
    has_experimental_kinetic_rates: bool = Field(description="True if rates are measured in erythrocytes.")
    justification: str = Field(description="Scientific rationale for assigned evidence level.")


def evaluate_evidence_tier(
    literature_reference: str | None,
    parameters: dict[str, Any],
    is_human_erythrocyte_validated: bool = False,
) -> EvidenceTierEvaluation:
    """Evaluate and grade the evidence tier of a compound based on provenance."""
    has_ref = bool(literature_reference and len(literature_reference.strip()) > 5)

    if is_human_erythrocyte_validated and has_ref:
        return EvidenceTierEvaluation(
            evidence_level=EvidenceLevel.CURATED,
            has_doi_or_citation=True,
            has_experimental_kinetic_rates=True,
            justification="Parameters backed by peer-reviewed human erythrocyte experimental data.",
        )
    elif has_ref:
        return EvidenceTierEvaluation(
            evidence_level=EvidenceLevel.ESTIMATED,
            has_doi_or_citation=True,
            has_experimental_kinetic_rates=False,
            justification="Parameters extrapolated from related cell types or analogous chemical quinones.",
        )
    else:
        return EvidenceTierEvaluation(
            evidence_level=EvidenceLevel.UNVERIFIED,
            has_doi_or_citation=False,
            has_experimental_kinetic_rates=False,
            justification="Synthetic placeholder or exploratory candidate without peer-reviewed erythrocyte kinetics.",
        )


class CompoundCompatibilityChecker:
    """Validator for chemical exposures against active ODE model capabilities."""

    def check_mechanism(
        self,
        mechanism_type: MechanismType | str,
        target_model: str = "rbc-g6pd-gsh-v2",
    ) -> ChemicalCompatibilityAssessment:
        """Check if a mechanism type is mathematically supported in target_model."""
        if isinstance(mechanism_type, str):
            try:
                m_enum = MechanismType(mechanism_type)
            except ValueError:
                return ChemicalCompatibilityAssessment(
                    is_compatible=False,
                    mechanism_type=mechanism_type,
                    supported_models=[],
                    unmodeled_aspects=["Unknown mechanism type."],
                    notes=f"Mechanism '{mechanism_type}' is unrecognized by the scenario engine.",
                )
        else:
            m_enum = mechanism_type

        is_compat = m_enum in SUPPORTED_MECHANISMS
        unmodeled = [
            "Membrane permeation kinetics (instantaneous cytosolic availability assumed).",
            "Whole-body hepatic/renal clearance.",
        ]

        if m_enum == MechanismType.ENZYME_INHIBITOR:
            models = ["rbc-g6pd-gsh-v2"]  # G6PD and GR inhibition
        else:
            models = ["rbc-gsh-redox-v1", "rbc-g6pd-gsh-v2"]

        notes = (
            f"Mechanism '{m_enum.value}' is fully integrated into {', '.join(models)}."
            if is_compat
            else f"Mechanism '{m_enum.value}' is not yet implemented."
        )

        return ChemicalCompatibilityAssessment(
            is_compatible=is_compat,
            mechanism_type=m_enum.value,
            supported_models=models if is_compat else [],
            unmodeled_aspects=unmodeled,
            notes=notes,
        )
