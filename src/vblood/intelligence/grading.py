"""
Evidence Grading Service (Milestone 7 - Step 5).

Extends Milestone 6's evidence grading interfaces to provide finding-level
and compound-level evidence grading with rigorous rubrics for human erythrocyte directness.
"""

from __future__ import annotations

from typing import Any

from vblood.intelligence.compatibility import EvidenceTierEvaluation
from vblood.intelligence.schemas import EvidenceFinding
from vblood.scenarios.mechanisms import EvidenceLevel


class EvidenceGradingService:
    """Grades scientific evidence findings and overall compound confidence."""

    def grade_finding(
        self,
        finding: EvidenceFinding,
        has_doi_or_citation: bool = True,
    ) -> tuple[EvidenceLevel, str]:
        """Grade a single evidence finding based on species, experimental system, and quantitative rigor.

        Rubric:
        - CURATED: Primary human erythrocyte in vitro/ex vivo assay with quantitative kinetic/redox measurements.
        - ESTIMATED: Human whole blood, related mammalian cells (e.g. hepatocytes), or chemical quinone analogies.
        - UNVERIFIED: Non-biological, computational, cell-free synthetic lead, or missing kinetic values.
        """
        is_human_rbc = finding.is_human_erythrocyte or (
            "human" in finding.biological_system.lower()
            and any(term in finding.biological_system.lower() for term in ["erythrocyte", "red blood cell", "rbc"])
        )
        has_quant = bool(finding.quantitative_measurements or finding.concentration is not None)

        if is_human_rbc and has_quant and has_doi_or_citation:
            return (
                EvidenceLevel.CURATED,
                "Direct experimental measurement in human erythrocytes with published quantitative kinetics.",
            )
        elif is_human_rbc and has_doi_or_citation:
            return (
                EvidenceLevel.ESTIMATED,
                "Human erythrocyte study with qualitative or semi-quantitative redox outcomes.",
            )
        elif has_doi_or_citation:
            return (
                EvidenceLevel.ESTIMATED,
                "Extrapolated from related mammalian tissue, whole-blood proxy, or analogous chemical redox system.",
            )
        else:
            return (
                EvidenceLevel.UNVERIFIED,
                "Exploratory observation without peer-reviewed erythrocyte kinetics or DOI citation.",
            )

    def grade_compound(
        self,
        findings: list[EvidenceFinding],
        literature_count: int,
    ) -> EvidenceTierEvaluation:
        """Synthesize overall compound evidence level from individual findings.

        A high quantity of weak evidence does not outweigh high-quality human erythrocyte evidence.
        """
        if not findings or literature_count == 0:
            return EvidenceTierEvaluation(
                evidence_level=EvidenceLevel.UNVERIFIED,
                has_doi_or_citation=False,
                has_experimental_kinetic_rates=False,
                justification="No peer-reviewed literature or experimental findings available.",
            )

        curated_findings = [f for f in findings if f.finding_evidence_level == EvidenceLevel.CURATED.value]
        estimated_findings = [f for f in findings if f.finding_evidence_level == EvidenceLevel.ESTIMATED.value]

        if curated_findings:
            return EvidenceTierEvaluation(
                evidence_level=EvidenceLevel.CURATED,
                has_doi_or_citation=True,
                has_experimental_kinetic_rates=True,
                justification=(
                    f"Supported by {len(curated_findings)} peer-reviewed direct human erythrocyte findings "
                    f"with measured redox kinetics."
                ),
            )
        elif estimated_findings:
            return EvidenceTierEvaluation(
                evidence_level=EvidenceLevel.ESTIMATED,
                has_doi_or_citation=True,
                has_experimental_kinetic_rates=False,
                justification=(
                    f"Supported by {len(estimated_findings)} findings extrapolated from related cell types "
                    f"or analogous quinone kinetics."
                ),
            )
        else:
            return EvidenceTierEvaluation(
                evidence_level=EvidenceLevel.UNVERIFIED,
                has_doi_or_citation=bool(literature_count > 0),
                has_experimental_kinetic_rates=False,
                justification="Parameters based on unvalidated synthetic approximations or exploratory models.",
            )
