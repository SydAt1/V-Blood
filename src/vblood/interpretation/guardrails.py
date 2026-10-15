"""
Scientific Guardrails and Grounding Verifier (Milestone 6).

Enforces mathematical fidelity, verifies numerical claims against raw simulation
endpoints, checks evidence disclosure, and ensures scientific boundary integrity.
"""

from __future__ import annotations

import re
from typing import Any

from vblood.interpretation.schemas import (
    CohortInterpretationResponse,
    GroundingEvaluation,
    PlaygroundInterpretationResponse,
)

FORBIDDEN_HALLUCINATIONS = [
    (r"\bmitochondri", "Erythrocytes lack mitochondria; mitochondrial processes cannot be claimed as simulated."),
    (r"\bnuclear\s+transcription\b", "Erythrocytes are enucleated; transcriptional responses cannot be claimed."),
    (r"\brenal\s+(clearance|excretion)\b", "V-Blood does not model in vivo renal clearance."),
    (r"\bhepatic\s+metabolism\b", "V-Blood does not model in vivo hepatic first-pass metabolism."),
    (r"\bclinical\s+safety\s+certified\b", "In silico simulation outputs cannot certify clinical safety."),
]

MANDATORY_DISCLAIMER_KEYWORDS = [
    "in vitro",
    "adme",
    "pharmacokinetics",
    "surrogate",
    "model",
]

UNVERIFIED_COMPOUND_NOTICE = (
    "NOTICE: This scenario incorporates unverified chemical parameters (UNVERIFIED evidence tier) "
    "lacking formal peer-reviewed erythrocyte kinetics. Numerical outcomes must be interpreted "
    "as speculative mechanistic hypotheses."
)


class GroundingGuardrail:
    """Validates and enforces scientific grounding on interpretation responses."""

    def verify_playground(
        self,
        response: PlaygroundInterpretationResponse,
        context: dict[str, Any],
    ) -> GroundingEvaluation:
        """Inspect and verify a single-cell playground interpretation response."""
        flags: list[str] = []
        checked: dict[str, Any] = {}
        all_text = " ".join([
            response.executive_summary,
            response.nadir_analysis,
            response.pathway_flux_breakdown,
            response.control_comparison,
            response.uncertainty_and_limitations,
        ]).lower()

        endpoints = context.get("endpoints", {})

        # 1. Check numerical values if explicitly mentioned
        min_gsh = endpoints.get("gsh_min_mM")
        if min_gsh is not None:
            checked["gsh_min_mM"] = min_gsh
            # Search for numbers close to min_gsh in nadir_analysis
            # E.g. if min_gsh is 0.42, verify that numbers like 1.95 aren't claimed as the nadir
            numbers_found = [float(x) for x in re.findall(r"\b\d+\.\d+\b", response.nadir_analysis)]
            if numbers_found and not any(abs(n - min_gsh) <= max(0.05, min_gsh * 0.1) for n in numbers_found):
                flags.append(f"Report nadir analysis mentions numbers {numbers_found[:3]} but simulated min [GSH] was {min_gsh} mM.")

        # 2. Check for forbidden biological hallucinations in substantive claims
        claims_text = " ".join([
            response.executive_summary,
            response.nadir_analysis,
            response.pathway_flux_breakdown,
            response.control_comparison,
        ]).lower()
        for pattern, explanation in FORBIDDEN_HALLUCINATIONS:
            if re.search(pattern, claims_text):
                flags.append(f"Forbidden biological claim detected ({pattern}): {explanation}")
            elif re.search(r"\bclinical\s+safety\s+certified\b", all_text):
                flags.append("In silico simulation outputs cannot certify clinical safety.")

        # 3. Check for boundary keywords
        has_boundary_words = any(kw in all_text for kw in MANDATORY_DISCLAIMER_KEYWORDS)
        if not has_boundary_words:
            flags.append("Mandatory model boundary and in vitro suspension keywords missing from report.")

        # 4. Check for unverified compound notice
        has_unverified = context.get("has_unverified_compounds", False)
        unverified_present = (
            "unverified" in all_text or "preliminary candidate" in all_text
        ) if has_unverified else True

        if has_unverified and not unverified_present:
            flags.append("Scenario contains unverified compounds, but explicit unverified evidence disclaimer is missing.")

        passed = len(flags) == 0

        return GroundingEvaluation(
            passed=passed,
            checked_metrics=checked,
            disclaimers_present=has_boundary_words,
            unverified_compound_warning_present=unverified_present,
            flags=flags,
        )

    def verify_cohort(
        self,
        response: CohortInterpretationResponse,
        context: dict[str, Any],
    ) -> GroundingEvaluation:
        """Inspect and verify a cohort interpretation response."""
        flags: list[str] = []
        checked: dict[str, Any] = {}
        all_text = " ".join([
            response.executive_summary,
            response.tail_risk_analysis,
            response.g6pd_interaction_analysis,
            response.lysis_risk_evaluation,
            response.uncertainty_and_limitations,
        ]).lower()

        endpoints = context.get("distribution_endpoints", {})
        mean_nadir = endpoints.get("mean_gsh_nadir_mM")
        if mean_nadir is not None:
            checked["mean_gsh_nadir_mM"] = mean_nadir

        pct_crisis = endpoints.get("pct_below_crisis_gsh")
        if pct_crisis is not None:
            checked["pct_below_crisis_gsh"] = pct_crisis

        claims_text = " ".join([
            response.executive_summary,
            response.tail_risk_analysis,
            response.g6pd_interaction_analysis,
            response.lysis_risk_evaluation,
        ]).lower()
        for pattern, explanation in FORBIDDEN_HALLUCINATIONS:
            if re.search(pattern, claims_text):
                flags.append(f"Forbidden biological claim detected ({pattern}): {explanation}")
            elif re.search(r"\bclinical\s+safety\s+certified\b", all_text):
                flags.append("In silico simulation outputs cannot certify clinical safety.")

        has_boundary_words = any(kw in all_text for kw in MANDATORY_DISCLAIMER_KEYWORDS)
        if not has_boundary_words:
            flags.append("Mandatory model boundary keywords missing from cohort report.")

        has_unverified = context.get("has_unverified_compounds", False)
        unverified_present = (
            "unverified" in all_text or "preliminary candidate" in all_text
        ) if has_unverified else True

        if has_unverified and not unverified_present:
            flags.append("Cohort scenario contains unverified compounds, but warning is missing.")

        passed = len(flags) == 0

        return GroundingEvaluation(
            passed=passed,
            checked_metrics=checked,
            disclaimers_present=has_boundary_words,
            unverified_compound_warning_present=unverified_present,
            flags=flags,
        )
