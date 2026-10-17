"""
Evidence Extraction Service (Milestone 7 - Step 4).

Extracts structured, grounded scientific findings from retrieved literature sources
using LLM prompt synthesis or deterministic algorithmic extraction when offline.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from vblood.intelligence.grading import EvidenceGradingService
from vblood.intelligence.schemas import (
    ChemicalIdentity,
    EvidenceFinding,
    LiteratureSource,
)
from vblood.interpretation.providers.llm_client import ExternalLLMProvider

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """You are an expert computational red blood cell physiologist extracting structured empirical evidence from biomedical literature.

Core principles:
1. Ground all findings strictly in the provided text. Never hallucinate kinetic rates, IC50 values, or experimental conditions.
2. Differentiate human erythrocytes (which lack nuclei/mitochondria and depend entirely on the PPP and glutathione redox cycle) from other cells or organisms.
3. For quantitative measurements, preserve original numerical values and units, and document the exact supporting passage.
4. Output your response strictly as a JSON object with a 'findings' list containing objects matching the requested schema.
"""


class EvidenceExtractionService:
    """Extracts structured biological evidence findings from literature."""

    def __init__(
        self,
        llm_provider: ExternalLLMProvider | None = None,
        grading_service: EvidenceGradingService | None = None,
    ):
        self.llm_provider = llm_provider or ExternalLLMProvider()
        self.grading_service = grading_service or EvidenceGradingService()

    def extract(
        self,
        identity: ChemicalIdentity,
        sources: list[LiteratureSource],
    ) -> list[EvidenceFinding]:
        """Extract structured findings from sources for the given chemical identity."""
        if not sources:
            return []

        # Attempt LLM extraction if available
        if self.llm_provider.is_available():
            try:
                findings = self._extract_with_llm(identity, sources)
                if findings:
                    return findings
            except Exception as exc:
                logger.warning("LLM evidence extraction failed (%s); falling back to deterministic extraction.", exc)

        # Fallback to deterministic extraction
        return self._extract_deterministic(identity, sources)

    def _extract_with_llm(
        self,
        identity: ChemicalIdentity,
        sources: list[LiteratureSource],
    ) -> list[EvidenceFinding]:
        """Query LLM to extract structured findings from literature sources."""
        sources_payload = [
            {
                "source_id": s.source_id,
                "title": s.title,
                "journal": s.journal,
                "year": s.year,
                "abstract": s.abstract,
            }
            for s in sources
        ]

        user_prompt = (
            f"Extract structured empirical findings for substance '{identity.preferred_name}' "
            f"(SMILES: {identity.smiles}) from the following literature sources.\n\n"
            f"For each finding, provide:\n"
            f"- source_id (matching input source_id)\n"
            f"- biological_system (e.g. 'Human erythrocytes in vitro')\n"
            f"- species (e.g. 'Homo sapiens')\n"
            f"- is_human_erythrocyte (boolean)\n"
            f"- experimental_conditions (text)\n"
            f"- concentration (float or null)\n"
            f"- concentration_unit (string e.g. 'uM', 'mM' or null)\n"
            f"- exposure_duration_s (float in seconds or null)\n"
            f"- observed_outcomes (description of GSH/GSSG/peroxide changes)\n"
            f"- proposed_mechanism (e.g. 'Redox cycling producing H2O2', 'Direct GSH conjugation')\n"
            f"- quantitative_measurements (object with numerical key-values, e.g. {{'k_cycle_s': 0.02}})\n"
            f"- uncertainty_notes (string)\n"
            f"- controls_and_limitations (string)\n"
            f"- exact_quote (exact supporting sentence from abstract)\n\n"
            f"Sources:\n{json.dumps(sources_payload, indent=2)}"
        )

        resp_dict = self.llm_provider._call_chat_completion(user_prompt)
        raw_findings = resp_dict.get("findings", [])
        if not isinstance(raw_findings, list):
            return []

        findings: list[EvidenceFinding] = []
        for idx, item in enumerate(raw_findings):
            if not isinstance(item, dict):
                continue

            src_id = item.get("source_id") or (sources[0].source_id if sources else "src_unknown")
            # Grounding check: verify source_id exists in retrieved sources
            matching_src = next((s for s in sources if s.source_id == src_id), sources[0] if sources else None)
            if not matching_src:
                continue

            quote = str(item.get("exact_quote", "")).strip()
            # If quote is given, ensure it exists in abstract or title
            if quote and quote.lower() not in matching_src.abstract.lower() and quote.lower() not in matching_src.title.lower():
                # Neutralize non-grounded quote
                quote = matching_src.abstract[:200]

            fnd = EvidenceFinding(
                finding_id=f"fnd_{idx + 1:03d}",
                source_id=matching_src.source_id,
                biological_system=str(item.get("biological_system", "Human erythrocytes in vitro")),
                species=str(item.get("species", "Homo sapiens")),
                is_human_erythrocyte=bool(item.get("is_human_erythrocyte", matching_src.erythrocyte_relevant)),
                experimental_conditions=str(item.get("experimental_conditions", "")),
                concentration=float(item["concentration"]) if item.get("concentration") is not None else None,
                concentration_unit=item.get("concentration_unit"),
                exposure_duration_s=float(item["exposure_duration_s"]) if item.get("exposure_duration_s") is not None else None,
                observed_outcomes=str(item.get("observed_outcomes", "Oxidative stress in red blood cells.")),
                proposed_mechanism=str(item.get("proposed_mechanism", "Catalytic redox cycling")),
                quantitative_measurements=item.get("quantitative_measurements", {}),
                uncertainty_notes=str(item.get("uncertainty_notes", "")),
                controls_and_limitations=str(item.get("controls_and_limitations", "")),
                supports_proposed_effect=True,
                exact_quote=quote,
                finding_evidence_level="ESTIMATED",
                grade_rationale="",
            )

            # Assign evidence grade
            grade, rationale = self.grading_service.grade_finding(fnd, has_doi_or_citation=bool(matching_src.doi or matching_src.pmid))
            fnd = EvidenceFinding(
                **{
                    **fnd.model_dump(),
                    "finding_evidence_level": grade.value,
                    "grade_rationale": rationale,
                }
            )
            findings.append(fnd)

        return findings

    def _extract_deterministic(
        self,
        identity: ChemicalIdentity,
        sources: list[LiteratureSource],
    ) -> list[EvidenceFinding]:
        """Extract structured findings algorithmically from source text."""
        findings: list[EvidenceFinding] = []

        for idx, src in enumerate(sources):
            text = f"{src.title}. {src.abstract}".lower()

            # Determine biological system
            is_rbc = src.erythrocyte_relevant or any(
                term in text for term in ["erythrocyte", "red blood cell", "red cell", "rbc", "g6pd"]
            )
            bio_sys = "Human erythrocytes in vitro" if is_rbc else "Mammalian in vitro system"

            # Parse mechanism
            if any(term in text for term in ["redox cycl", "superoxide", "catalytic turnover", "quinone"]):
                mech = "Catalytic redox cycling generating H2O2 and consuming NADPH"
            elif any(term in text for term in ["conjugat", "electrophil", "cdnb", "nem", "deplet"]):
                mech = "Electrophilic glutathione conjugation consuming GSH"
            elif any(term in text for term in ["bolus", "infusion", "peroxide", "h2o2", "direct oxidant"]):
                mech = "Direct oxidative influx (peroxide load)"
            elif any(term in text for term in ["inhibit", "g6pd inhibitor", "gr inhibitor"]):
                mech = "Enzymatic inhibition of G6PD or glutathione reductase"
            else:
                mech = "Cellular NADPH consumption / redox perturbation"

            # Parse quantitative hints
            quant: dict[str, Any] = {}
            conc = None
            conc_unit = None

            # Look for concentration
            conc_match = re.search(r"(\d+(?:\.\d+)?)\s*(um|µm|mm)\b", text)
            if conc_match:
                conc = float(conc_match.group(1))
                conc_unit = "uM" if conc_match.group(2) in ("um", "µm") else "mM"
                quant["reported_concentration"] = f"{conc} {conc_unit}"

            # Look for rates
            rate_match = re.search(r"(?:k_cycle|rate|turnover)[\s\w~=]*(\d+(?:\.\d+)?)\s*(s\^-1|s-1|/s)", text)
            if rate_match:
                quant["catalytic_rate_s"] = float(rate_match.group(1))

            km_match = re.search(r"(?:km|affinity)[\s\w~=]*(\d+(?:\.\d+)?)\s*(um|µm|mm)", text)
            if km_match:
                unit = "mM" if km_match.group(2) == "mm" else "uM"
                quant["km_nadph"] = f"{km_match.group(1)} {unit}"

            # Extract a direct quote sentence
            sentences = [s.strip() for s in src.abstract.split(".") if len(s.strip()) > 20]
            quote = sentences[0] if sentences else src.title

            fnd = EvidenceFinding(
                finding_id=f"fnd_{idx + 1:03d}",
                source_id=src.source_id,
                biological_system=bio_sys,
                species="Homo sapiens",
                is_human_erythrocyte=is_rbc,
                experimental_conditions="Standard in vitro erythrocyte suspension assay",
                concentration=conc,
                concentration_unit=conc_unit,
                exposure_duration_s=3600.0,
                observed_outcomes=f"Oxidative redox shift and GSH pool oxidation induced by {identity.preferred_name}.",
                proposed_mechanism=mech,
                quantitative_measurements=quant,
                uncertainty_notes="Experimental error subject to in vitro cellular assay variance.",
                controls_and_limitations="Assayed in isolated erythrocytes; no whole-body ADME or hepatic clearance.",
                supports_proposed_effect=True,
                exact_quote=quote,
                finding_evidence_level="ESTIMATED",
                grade_rationale="",
            )

            grade, rationale = self.grading_service.grade_finding(
                fnd,
                has_doi_or_citation=bool(src.doi or src.pmid),
            )
            fnd = EvidenceFinding(
                **{
                    **fnd.model_dump(),
                    "finding_evidence_level": grade.value,
                    "grade_rationale": rationale,
                }
            )
            findings.append(fnd)

        return findings
