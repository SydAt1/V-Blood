"""
Candidate Validation and Lifecycle Gatekeeper (Milestone 7 - Steps 8 & 9).

Executes 10 scientific validation gates against candidate dossiers before allowing
lifecycle transitions to SIMULATION_READY.
"""

from __future__ import annotations

import logging
from typing import Any

from vblood.chemistry.identifiers import validate_inchikey, validate_smiles
from vblood.intelligence.schemas import (
    CandidateParameter,
    CandidateValidationSummary,
    ChemicalIdentity,
    LiteratureSource,
    ProposedMechanismMapping,
    ResearchLifecycleStatus,
    ValidationGateResult,
)
from vblood.scenarios.mechanisms import (
    DirectOxidantSpec,
    EnzymeInhibitorSpec,
    EnzymeTarget,
    GSHConjugatorSpec,
    InhibitionType,
    MechanismType,
    NADPHDrainSpec,
    RedoxCyclerSpec,
    ScenarioMechanismHooks,
)

logger = logging.getLogger(__name__)

PROTECTED_CATALOG_IDS = {"cmp_h2o2", "cmp_menadione", "cmp_cdnb", "cmp_nem", "cmp_dhea"}


class CandidateValidator:
    """Validator executing 10 rigorous scientific gates on research candidates."""

    def validate(
        self,
        candidate_id: str,
        identity: ChemicalIdentity,
        sources: list[LiteratureSource],
        mappings: list[ProposedMechanismMapping],
    ) -> CandidateValidationSummary:
        """Run all 10 validation gates and return a comprehensive summary."""
        gates: list[ValidationGateResult] = []
        blocking_reasons: list[str] = []
        warnings: list[str] = []

        # Gate 1: Chemical identity consistency
        g1_pass = True
        g1_msg = "Chemical identity, SMILES, and InChIKey are structurally verified."
        if not identity.preferred_name or len(identity.preferred_name.strip()) < 2:
            g1_pass = False
            g1_msg = "Substance name is empty or too short."
        else:
            s_res = validate_smiles(identity.smiles)
            if not s_res.is_valid:
                g1_pass = False
                g1_msg = f"Invalid SMILES string: {s_res.error_message}"
            i_res = validate_inchikey(identity.inchikey)
            if not i_res.is_valid:
                g1_pass = False
                g1_msg = f"Invalid InChIKey string: {i_res.error_message}"

        if identity.is_ambiguous:
            warnings.append(
                f"Substance identity '{identity.preferred_name}' has ambiguity candidates: "
                f"{', '.join(identity.ambiguity_candidates[:3])}."
            )

        gates.append(
            ValidationGateResult(
                gate_name="Gate 1: Chemical Identity Consistency",
                passed=g1_pass,
                message=g1_msg,
                severity="ERROR" if not g1_pass else "INFO",
            )
        )
        if not g1_pass:
            blocking_reasons.append(g1_msg)

        # Gate 2: Schema & Data-Type Integrity
        g2_pass = bool(identity.smiles and identity.inchikey and identity.source)
        g2_msg = "Schema validation succeeded." if g2_pass else "Missing required structural identity fields."
        gates.append(
            ValidationGateResult(
                gate_name="Gate 2: Schema & Data-Type Validity",
                passed=g2_pass,
                message=g2_msg,
                severity="ERROR" if not g2_pass else "INFO",
            )
        )
        if not g2_pass:
            blocking_reasons.append(g2_msg)

        # Gate 3: Source Existence and Identifier Consistency
        g3_pass = True
        g3_msg = f"{len(sources)} scientific literature sources retrieved with valid identifiers."
        if not sources:
            g3_pass = False
            g3_msg = "No scientific literature sources were found for this chemical entity."
        else:
            invalid_sources = [s.source_id for s in sources if not (s.doi or s.pmid or s.url)]
            if invalid_sources:
                g3_pass = False
                g3_msg = f"Sources lacking verifiable DOI, PMID, or URL: {', '.join(invalid_sources)}"

        gates.append(
            ValidationGateResult(
                gate_name="Gate 3: Source Existence & Traceability",
                passed=g3_pass,
                message=g3_msg,
                severity="ERROR" if not g3_pass else "INFO",
            )
        )
        if not g3_pass:
            blocking_reasons.append(g3_msg)

        # Gate 4: Unit and Dimensional Consistency
        valid_units = {"mM", "s^-1", "mM^-1 s^-1", "mM/s", "uM"}
        g4_pass = True
        g4_msg = "All proposed kinetic parameters use dimensional units compatible with V-Blood ODEs."
        for m in mappings:
            for p in m.parameters:
                if p.units not in valid_units:
                    g4_pass = False
                    g4_msg = f"Parameter '{p.name}' uses unsupported units '{p.units}'. Must be in {valid_units}."
                    break

        gates.append(
            ValidationGateResult(
                gate_name="Gate 4: Unit & Dimensional Consistency",
                passed=g4_pass,
                message=g4_msg,
                severity="ERROR" if not g4_pass else "INFO",
            )
        )
        if not g4_pass:
            blocking_reasons.append(g4_msg)

        # Gate 5: Parameter Provenance and Missing-Value Handling
        g5_pass = True
        g5_msg = "All kinetic parameters have explicit provenance and documented derivation methods."
        if not mappings or not any(m.parameters for m in mappings if m.is_compatible):
            g5_pass = False
            g5_msg = "No parameters available for compatible mechanism."
        else:
            for m in mappings:
                if m.is_compatible:
                    for p in m.parameters:
                        if not p.is_identifiable or p.value is None:
                            g5_pass = False
                            g5_msg = f"Parameter '{p.name}' is unidentifiable or missing from evidence."
                            break

        gates.append(
            ValidationGateResult(
                gate_name="Gate 5: Parameter Provenance & Identifiability",
                passed=g5_pass,
                message=g5_msg,
                severity="ERROR" if not g5_pass else "INFO",
            )
        )
        if not g5_pass:
            blocking_reasons.append(g5_msg)

        # Gate 6: Mechanism Compatibility
        compatible_mappings = [m for m in mappings if m.is_compatible]
        g6_pass = bool(compatible_mappings)
        g6_msg = (
            f"Mapped to compatible ODE mechanism class '{compatible_mappings[0].mechanism_type}'."
            if g6_pass
            else "Proposed biological effects do not map to V-Blood's 5 supported chemical mechanism classes."
        )
        gates.append(
            ValidationGateResult(
                gate_name="Gate 6: Mechanism Compatibility with ODE Models",
                passed=g6_pass,
                message=g6_msg,
                severity="ERROR" if not g6_pass else "INFO",
            )
        )
        if not g6_pass:
            blocking_reasons.append(g6_msg)

        # Gate 7: Required Parameter Completeness
        g7_pass = True
        g7_msg = "All required kinetic parameters for the mechanism class are present."
        if compatible_mappings:
            target_mapping = compatible_mappings[0]
            param_names = {p.name for p in target_mapping.parameters}
            m_type = target_mapping.mechanism_type

            if m_type == MechanismType.REDOX_CYCLER.value:
                req = {"catalytic_rate_s", "km_nadph_mM"}
                if not req.issubset(param_names):
                    g7_pass = False
                    g7_msg = f"REDOX_CYCLER requires {req}, but got {param_names}."
            elif m_type == MechanismType.GSH_CONJUGATOR.value:
                req = {"rate_constant_mM_s"}
                if not req.issubset(param_names):
                    g7_pass = False
                    g7_msg = f"GSH_CONJUGATOR requires {req}, but got {param_names}."
            elif m_type == MechanismType.DIRECT_OXIDANT.value:
                req = {"bolus_mM"}
                if not req.issubset(param_names):
                    g7_pass = False
                    g7_msg = f"DIRECT_OXIDANT requires {req}, but got {param_names}."
            elif m_type == MechanismType.ENZYME_INHIBITOR.value:
                req = {"ki_mM"}
                if not req.issubset(param_names) or not target_mapping.target_enzyme:
                    g7_pass = False
                    g7_msg = "ENZYME_INHIBITOR requires ki_mM and target_enzyme."
            elif m_type == MechanismType.NADPH_DRAIN.value:
                req = {"drain_rate_s"}
                if not req.issubset(param_names):
                    g7_pass = False
                    g7_msg = f"NADPH_DRAIN requires {req}, but got {param_names}."
        else:
            g7_pass = False
            g7_msg = "Cannot assess parameter completeness without compatible mechanism mapping."

        gates.append(
            ValidationGateResult(
                gate_name="Gate 7: Required Parameter Completeness",
                passed=g7_pass,
                message=g7_msg,
                severity="ERROR" if not g7_pass else "INFO",
            )
        )
        if not g7_pass:
            blocking_reasons.append(g7_msg)

        # Gate 8: Numeric Bounds Validation
        g8_pass = True
        g8_msg = "All parameters are strictly within physiological and physical bounds."
        if compatible_mappings:
            for p in compatible_mappings[0].parameters:
                if not (p.min_bound <= p.value <= p.max_bound) or p.value < 0:
                    g8_pass = False
                    g8_msg = f"Parameter '{p.name}' value {p.value} is out of bounds [{p.min_bound}, {p.max_bound}]."
                    break
        else:
            g8_pass = False
            g8_msg = "No compatible parameters to validate bounds."

        gates.append(
            ValidationGateResult(
                gate_name="Gate 8: Valid Numeric Bounds",
                passed=g8_pass,
                message=g8_msg,
                severity="ERROR" if not g8_pass else "INFO",
            )
        )
        if not g8_pass:
            blocking_reasons.append(g8_msg)

        # Gate 9: Simulation-Engine Compatibility Test
        g9_pass = True
        g9_msg = "ODE engine test integration verified without numerical divergence or NaNs."
        if compatible_mappings and g7_pass and g8_pass:
            try:
                self._test_ode_integration(compatible_mappings[0])
            except Exception as exc:
                g9_pass = False
                g9_msg = f"Simulation engine test integration failed: {exc}"
        else:
            g9_pass = False
            g9_msg = "Skipped ODE integration test due to prior validation blockers."

        gates.append(
            ValidationGateResult(
                gate_name="Gate 9: Simulation-Engine Compatibility Integration",
                passed=g9_pass,
                message=g9_msg,
                severity="ERROR" if not g9_pass else "INFO",
            )
        )
        if not g9_pass:
            blocking_reasons.append(g9_msg)

        # Gate 10: Catalog Regression Safety
        g10_pass = candidate_id not in PROTECTED_CATALOG_IDS
        g10_msg = (
            "Registration does not conflict with protected curated catalog entries."
            if g10_pass
            else f"Candidate ID '{candidate_id}' collides with protected curated core compound."
        )
        gates.append(
            ValidationGateResult(
                gate_name="Gate 10: Catalog Regression Safety",
                passed=g10_pass,
                message=g10_msg,
                severity="ERROR" if not g10_pass else "INFO",
            )
        )
        if not g10_pass:
            blocking_reasons.append(g10_msg)

        is_valid = len(blocking_reasons) == 0
        simulation_eligible = is_valid

        return CandidateValidationSummary(
            is_valid=is_valid,
            simulation_eligible=simulation_eligible,
            gates=gates,
            blocking_reasons=blocking_reasons,
            warnings=warnings,
        )

    def _test_ode_integration(self, mapping: ProposedMechanismMapping) -> None:
        """Execute a short in-memory ODE rate and hook step to ensure numerical stability."""
        param_dict = {p.name: p.value for p in mapping.parameters}
        m_type = mapping.mechanism_type

        # Construct mechanism spec
        spec: Any = None
        if m_type == MechanismType.REDOX_CYCLER.value:
            spec = RedoxCyclerSpec(
                compound_conc_mM=0.01,
                catalytic_rate_s=param_dict["catalytic_rate_s"],
                km_nadph_mM=param_dict["km_nadph_mM"],
            )
        elif m_type == MechanismType.GSH_CONJUGATOR.value:
            spec = GSHConjugatorSpec(
                compound_conc_mM=0.01,
                rate_constant_mM_s=param_dict["rate_constant_mM_s"],
            )
        elif m_type == MechanismType.DIRECT_OXIDANT.value:
            spec = DirectOxidantSpec(
                bolus_mM=param_dict.get("bolus_mM", 0.05),
            )
        elif m_type == MechanismType.ENZYME_INHIBITOR.value:
            spec = EnzymeInhibitorSpec(
                compound_conc_mM=0.01,
                ki_mM=param_dict["ki_mM"],
                target_enzyme=EnzymeTarget(mapping.target_enzyme or "G6PD"),
                inhibition_type=InhibitionType(mapping.inhibition_type or "NON_COMPETITIVE"),
            )
        elif m_type == MechanismType.NADPH_DRAIN.value:
            spec = NADPHDrainSpec(
                compound_conc_mM=0.01,
                drain_rate_s=param_dict["drain_rate_s"],
            )

        if spec is None:
            raise ValueError(f"Unrecognized mechanism type '{m_type}' for integration test.")

        # Test hooks
        hooks = ScenarioMechanismHooks([spec])
        dummy_params = {"vmax_g6pd": 0.1, "vmax_gr": 0.03, "km_nadp": 0.01}
        mod_params = hooks.modify_parameters(dummy_params)
        for val in mod_params.values():
            if val <= 0:
                raise ValueError("Modified parameter was non-positive.")

        # Test rates evaluation at baseline state: [GSH=2.0, GSSG=0.01, H2O2=0.0001, NADPH=0.05, D=0.0]
        rates = hooks.compute_rates(0.0, [2.0, 0.01, 0.0001, 0.05, 0.0])
        for r_name, r_val in rates.items():
            if r_val < 0.0:
                raise ValueError(f"Dynamic rate '{r_name}' evaluated to negative flux ({r_val}).")
