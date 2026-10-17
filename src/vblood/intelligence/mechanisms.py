"""
Mechanism Mapping and Parameter Estimation Service (Milestone 7 - Steps 6 & 7).

Maps structured evidence findings to V-Blood's 5 ODE kinetic mechanism classes,
generates parameter candidates with explicit provenance and bounds,
and constructs structured incompatibility reports for unmodeled biological mechanisms.
"""

from __future__ import annotations

import logging
from typing import Any

from vblood.intelligence.compatibility import CompoundCompatibilityChecker
from vblood.intelligence.schemas import (
    CandidateParameter,
    ChemicalIdentity,
    EvidenceFinding,
    ParameterProvenance,
    ProposedMechanismMapping,
)
from vblood.scenarios.mechanisms import (
    EnzymeTarget,
    EvidenceLevel,
    InhibitionType,
    MechanismType,
)

logger = logging.getLogger(__name__)

# Standard physiological bounds for mechanism parameters in V-Blood
PARAMETER_BOUNDS: dict[str, tuple[float, float, str]] = {
    "bolus_mM": (0.0, 5.0, "mM"),
    "influx_rate_mM_s": (0.0, 0.05, "mM/s"),
    "rate_constant_mM_s": (0.001, 2.0, "mM^-1 s^-1"),
    "catalytic_rate_s": (0.0005, 0.5, "s^-1"),
    "km_nadph_mM": (0.0005, 0.1, "mM"),
    "drain_rate_s": (0.0001, 0.1, "s^-1"),
    "ki_mM": (0.0001, 2.0, "mM"),
}


class MechanismMappingService:
    """Evaluates mechanism compatibility and estimates kinetic parameters."""

    def __init__(self):
        self.checker = CompoundCompatibilityChecker()

    def evaluate_mappings(
        self,
        identity: ChemicalIdentity,
        findings: list[EvidenceFinding],
    ) -> list[ProposedMechanismMapping]:
        """Map extracted findings to candidate V-Blood mechanism configurations."""
        if not findings:
            return []

        # Aggregate text clues from findings
        all_text = " ".join(
            f"{f.proposed_mechanism} {f.observed_outcomes} {f.experimental_conditions}" for f in findings
        ).lower()
        substance_lower = identity.preferred_name.lower()

        mappings: list[ProposedMechanismMapping] = []

        # 1. Redox Cycler Check
        if any(term in all_text for term in ["redox cycl", "superoxide", "quinone", "primaquine", "menadione", "doxorubicin"]) or \
           any(term in substance_lower for term in ["menadione", "primaquine", "doxorubicin", "quinone"]):
            mappings.append(self._build_redox_cycler_mapping(identity, findings))

        # 2. GSH Conjugator Check
        elif any(term in all_text for term in ["conjugat", "electrophil", "cdnb", "nem", "napqi", "depletion without gssg"]):
            mappings.append(self._build_gsh_conjugator_mapping(identity, findings))

        # 3. Direct Oxidant Check
        elif any(term in all_text for term in ["bolus", "infusion", "peroxide", "h2o2", "direct oxidant"]):
            mappings.append(self._build_direct_oxidant_mapping(identity, findings))

        # 4. Enzyme Inhibitor Check
        elif any(term in all_text for term in ["inhibitor", "inhibition", "dhea", "6-an", "ki"]):
            mappings.append(self._build_enzyme_inhibitor_mapping(identity, findings))

        # 5. NADPH Drain Check
        elif any(term in all_text for term in ["nadph drain", "aldose reductase", "reductase drain"]):
            mappings.append(self._build_nadph_drain_mapping(identity, findings))

        # 6. Unmodeled / Incompatible Mechanism Check
        else:
            mappings.append(self._build_incompatible_mapping(identity, findings, all_text))

        return mappings

    def _build_redox_cycler_mapping(
        self,
        identity: ChemicalIdentity,
        findings: list[EvidenceFinding],
    ) -> ProposedMechanismMapping:
        """Construct REDOX_CYCLER mechanism candidate with parameters."""
        finding_ids = [f.finding_id for f in findings]
        has_rbc = any(f.is_human_erythrocyte for f in findings)

        # Inspect quantitative findings for rate
        rate_val = None
        for f in findings:
            if "catalytic_rate_s" in f.quantitative_measurements:
                rate_val = float(f.quantitative_measurements["catalytic_rate_s"])
                break

        if rate_val is not None:
            prov = ParameterProvenance.MEASURED if has_rbc else ParameterProvenance.DERIVED
            k_cycle = rate_val
            ev_tier = "CURATED" if has_rbc else "ESTIMATED"
        else:
            # Documented inference based on quinone/diaphorase kinetics
            k_cycle = 0.02
            prov = ParameterProvenance.INFERRED
            ev_tier = "ESTIMATED"

        km_nadph = 0.010  # Standard human erythrocyte GR/diaphorase Km for NADPH

        min_r, max_r, r_units = PARAMETER_BOUNDS["catalytic_rate_s"]
        min_k, max_k, k_units = PARAMETER_BOUNDS["km_nadph_mM"]

        params = [
            CandidateParameter(
                name="catalytic_rate_s",
                mechanism=MechanismType.REDOX_CYCLER.value,
                value=min(max(k_cycle, min_r), max_r),
                units=r_units,
                min_bound=min_r,
                max_bound=max_r,
                original_value=rate_val,
                original_units=r_units if rate_val else None,
                conversion_method="Apparent turnover rate in erythrocyte suspension",
                provenance=prov,
                evidence_level=ev_tier,
                confidence_score=0.9 if prov == ParameterProvenance.MEASURED else 0.7,
                assumptions=["Pseudo-first-order rate in red blood cell cytoplasm.", "Sufficient intracellular dissolved O2."],
                is_identifiable=True,
                validation_status="VALID",
            ),
            CandidateParameter(
                name="km_nadph_mM",
                mechanism=MechanismType.REDOX_CYCLER.value,
                value=km_nadph,
                units=k_units,
                min_bound=min_k,
                max_bound=max_k,
                original_value=10.0,
                original_units="uM",
                conversion_method="10 uM converted to 0.010 mM",
                provenance=ParameterProvenance.INFERRED,
                evidence_level="ESTIMATED",
                confidence_score=0.8,
                assumptions=["Erythrocyte diaphorase/flavoenzyme cofactor affinity constant."],
                is_identifiable=True,
                validation_status="VALID",
            ),
        ]

        return ProposedMechanismMapping(
            mechanism_type=MechanismType.REDOX_CYCLER.value,
            is_compatible=True,
            confidence=0.85 if has_rbc else 0.65,
            supporting_finding_ids=finding_ids,
            assumptions=[
                "Intracellular quinone reduction by flavoenzymes transfers electrons from NADPH to O2.",
                "Continuous catalytic turnover generates H2O2 at constant stoichiometric ratio 1:1.",
            ],
            unmodeled_aspects=[
                "Whole-body hepatic conversion of parent compound to active orthoquinone.",
                "Membrane diffusion barrier (instantaneous cytoplasmic availability assumed).",
            ],
            unresolved_questions=[
                "Exact intracellular accumulation factor in erythrocytes relative to extracellular plasma concentration.",
            ],
            parameters=params,
        )

    def _build_gsh_conjugator_mapping(
        self,
        identity: ChemicalIdentity,
        findings: list[EvidenceFinding],
    ) -> ProposedMechanismMapping:
        """Construct GSH_CONJUGATOR mechanism candidate."""
        finding_ids = [f.finding_id for f in findings]
        has_rbc = any(f.is_human_erythrocyte for f in findings)

        rate_val = 0.05
        min_r, max_r, r_units = PARAMETER_BOUNDS["rate_constant_mM_s"]

        params = [
            CandidateParameter(
                name="rate_constant_mM_s",
                mechanism=MechanismType.GSH_CONJUGATOR.value,
                value=rate_val,
                units=r_units,
                min_bound=min_r,
                max_bound=max_r,
                conversion_method="Second-order direct electrophilic conjugation rate constant k_conj",
                provenance=ParameterProvenance.INFERRED,
                evidence_level="ESTIMATED",
                confidence_score=0.75,
                assumptions=["Direct bimolecular reaction between GSH and compound without GSSG formation."],
                is_identifiable=True,
                validation_status="VALID",
            )
        ]

        return ProposedMechanismMapping(
            mechanism_type=MechanismType.GSH_CONJUGATOR.value,
            is_compatible=True,
            confidence=0.8,
            supporting_finding_ids=finding_ids,
            assumptions=["Irreversible covalent adduction depleting free reduced glutathione."],
            unmodeled_aspects=["GST isozyme saturation kinetics.", "Glutathione-S-conjugate export transport (RLIP76/MRP1)."],
            unresolved_questions=["Partition coefficient into erythrocyte cytosol."],
            parameters=params,
        )

    def _build_direct_oxidant_mapping(
        self,
        identity: ChemicalIdentity,
        findings: list[EvidenceFinding],
    ) -> ProposedMechanismMapping:
        """Construct DIRECT_OXIDANT mechanism candidate."""
        finding_ids = [f.finding_id for f in findings]
        min_b, max_b, b_units = PARAMETER_BOUNDS["bolus_mM"]

        params = [
            CandidateParameter(
                name="bolus_mM",
                mechanism=MechanismType.DIRECT_OXIDANT.value,
                value=0.05,
                units=b_units,
                min_bound=min_b,
                max_bound=max_b,
                conversion_method="Default in vitro challenge bolus load",
                provenance=ParameterProvenance.INFERRED,
                evidence_level="CURATED",
                confidence_score=0.9,
                assumptions=["Instantaneous bolus entry into cell suspension."],
                is_identifiable=True,
                validation_status="VALID",
            )
        ]

        return ProposedMechanismMapping(
            mechanism_type=MechanismType.DIRECT_OXIDANT.value,
            is_compatible=True,
            confidence=0.9,
            supporting_finding_ids=finding_ids,
            assumptions=["Direct aqueous peroxide influx decomposed by GPx1 and Catalase."],
            unmodeled_aspects=["Aquaporin membrane permeability."],
            unresolved_questions=[],
            parameters=params,
        )

    def _build_enzyme_inhibitor_mapping(
        self,
        identity: ChemicalIdentity,
        findings: list[EvidenceFinding],
    ) -> ProposedMechanismMapping:
        """Construct ENZYME_INHIBITOR mechanism candidate."""
        finding_ids = [f.finding_id for f in findings]
        min_k, max_k, k_units = PARAMETER_BOUNDS["ki_mM"]

        params = [
            CandidateParameter(
                name="ki_mM",
                mechanism=MechanismType.ENZYME_INHIBITOR.value,
                value=0.02,
                units=k_units,
                min_bound=min_k,
                max_bound=max_k,
                conversion_method="Reported inhibition constant Ki in red cell hemolysate",
                provenance=ParameterProvenance.INFERRED,
                evidence_level="ESTIMATED",
                confidence_score=0.7,
                assumptions=["Reversible inhibition of enzyme activity."],
                is_identifiable=True,
                validation_status="VALID",
            )
        ]

        return ProposedMechanismMapping(
            mechanism_type=MechanismType.ENZYME_INHIBITOR.value,
            is_compatible=True,
            target_enzyme=EnzymeTarget.G6PD.value,
            inhibition_type=InhibitionType.NON_COMPETITIVE.value,
            confidence=0.75,
            supporting_finding_ids=finding_ids,
            assumptions=["Reduces effective Vmax of target enzyme according to Vmax / (1 + [I]/Ki)."],
            unmodeled_aspects=["Slow-binding allosteric transitions."],
            unresolved_questions=["Intracellular versus extracellular free inhibitor fraction."],
            parameters=params,
        )

    def _build_nadph_drain_mapping(
        self,
        identity: ChemicalIdentity,
        findings: list[EvidenceFinding],
    ) -> ProposedMechanismMapping:
        """Construct NADPH_DRAIN mechanism candidate."""
        finding_ids = [f.finding_id for f in findings]
        min_d, max_d, d_units = PARAMETER_BOUNDS["drain_rate_s"]

        params = [
            CandidateParameter(
                name="drain_rate_s",
                mechanism=MechanismType.NADPH_DRAIN.value,
                value=0.005,
                units=d_units,
                min_bound=min_d,
                max_bound=max_d,
                conversion_method="Maximal drain rate constant",
                provenance=ParameterProvenance.INFERRED,
                evidence_level="ESTIMATED",
                confidence_score=0.6,
                assumptions=["Direct consumption of reducing pool without peroxide generation."],
                is_identifiable=True,
                validation_status="VALID",
            )
        ]

        return ProposedMechanismMapping(
            mechanism_type=MechanismType.NADPH_DRAIN.value,
            is_compatible=True,
            confidence=0.65,
            supporting_finding_ids=finding_ids,
            assumptions=["Xenobiotic reduction draws upon NADPH pool."],
            unmodeled_aspects=["Specific reductase enzyme identity."],
            unresolved_questions=[],
            parameters=params,
        )

    def _build_incompatible_mapping(
        self,
        identity: ChemicalIdentity,
        findings: list[EvidenceFinding],
        all_text: str,
    ) -> ProposedMechanismMapping:
        """Construct structured incompatibility report for unmodeled biological mechanisms."""
        finding_ids = [f.finding_id for f in findings]

        unmodeled = []
        if any(term in all_text for term in ["dna", "rna", "nucle"]):
            unmodeled.append("Genotoxic / nucleic acid damage (human erythrocytes lack nuclei).")
        if any(term in all_text for term in ["mitochondr", "uncoupl", "oxphos"]):
            unmodeled.append("Mitochondrial uncoupling (human erythrocytes lack mitochondria).")
        if any(term in all_text for term in ["cytochrome p450", "cyp", "hepatic"]):
            unmodeled.append("Hepatic CYP metabolism is external to isolated red blood cell suspension.")
        if any(term in all_text for term in ["membrane spicul", "echinocyte", "morpholog"]):
            unmodeled.append("Membrane morphological distortion without direct redox ODE representation.")

        if not unmodeled:
            unmodeled.append("Mechanism outside V-Blood's 5 supported RBC redox mechanism classes.")

        return ProposedMechanismMapping(
            mechanism_type="UNSUPPORTED_MECHANISM",
            is_compatible=False,
            confidence=0.2,
            supporting_finding_ids=finding_ids,
            assumptions=["Substance mechanism does not map to V-Blood's 5 chemical ODE mechanism classes."],
            unmodeled_aspects=unmodeled,
            unresolved_questions=[
                "Requires mathematical formulation of new ODE rate equations beyond current V-Blood scope."
            ],
            parameters=[],
        )
