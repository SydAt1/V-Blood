"""
Unit tests for the Scientific Interpretation Engine (Milestone 6).
"""

from __future__ import annotations

import asyncio
import pytest

from vblood.intelligence.compatibility import (
    CompoundCompatibilityChecker,
    evaluate_evidence_tier,
)
from vblood.interpretation.context import (
    build_cohort_context,
    build_playground_context,
)
from vblood.interpretation.guardrails import GroundingGuardrail
from vblood.interpretation.providers.deterministic import DeterministicBiochemicalProvider
from vblood.interpretation.schemas import (
    CohortInterpretationRequest,
    PlaygroundInterpretationRequest,
    PlaygroundInterpretationResponse,
)
from vblood.interpretation.service import InterpretationService
from vblood.scenarios.compounds import get_compound_library
from vblood.scenarios.engine import (
    CompoundExposure,
    ExposureProfile,
    ScenarioRequest,
    run_scenario,
)
from vblood.scenarios.mechanisms import EvidenceLevel, MechanismType
from vblood.scenarios.population import PopulationRequest, simulate_population


@pytest.fixture
def sample_playground_result():
    """Execute a fast, standard single-cell scenario for testing."""
    req = ScenarioRequest(
        model_version="rbc-g6pd-gsh-v2",
        g6pd_alpha=0.5,
        duration_s=300.0,
        exposure_profile=ExposureProfile.BOLUS,
        compounds=[
            CompoundExposure(compound_id="cmp_menadione", dose_mM=0.03),
        ],
    )
    result = run_scenario(req)
    return req, result


@pytest.fixture
def sample_cohort_result():
    """Execute a fast population cohort scenario for testing."""
    req = PopulationRequest(
        scenario_request=ScenarioRequest(
            model_version="rbc-g6pd-gsh-v2",
            g6pd_alpha=0.5,
            duration_s=300.0,
            exposure_profile=ExposureProfile.BOLUS,
            compounds=[
                CompoundExposure(compound_id="cmp_menadione", dose_mM=0.02),
            ],
        ),
        n_cells=20,
        random_seed=42,
    )
    result = simulate_population(req)
    return req, result


class TestInterpretationContext:
    def test_build_playground_context_endpoints(self, sample_playground_result):
        req, result = sample_playground_result
        ctx = build_playground_context(req, result)

        assert "endpoints" in ctx
        assert ctx["model_version"] == "rbc-g6pd-gsh-v2"
        assert ctx["g6pd_alpha"] == 0.5
        assert ctx["endpoints"]["gsh_min_mM"] <= 2.5
        assert ctx["endpoints"]["gsh_depleted_pct"] > 0.0
        assert len(ctx["compounds"]) == 1
        assert ctx["compounds"][0]["id"] == "cmp_menadione"
        assert len(ctx["unmodeled_physics"]) >= 3

    def test_build_cohort_context_endpoints(self, sample_cohort_result):
        req, result = sample_cohort_result
        ctx = build_cohort_context(req, result)

        assert ctx["n_cells"] == 20
        assert "distribution_endpoints" in ctx
        assert ctx["distribution_endpoints"]["median_gsh_nadir_mM"] > 0.0
        assert "p5_nadir_mM" in ctx["distribution_endpoints"]
        assert len(ctx["unmodeled_physics"]) >= 3


class TestDeterministicBiochemicalProvider:
    def test_interpret_playground_success(self, sample_playground_result):
        req, result = sample_playground_result
        ctx = build_playground_context(req, result)

        provider = DeterministicBiochemicalProvider()
        resp = asyncio.run(provider.interpret_playground(ctx))

        assert resp.provider_used == "deterministic-biochemical-v1"
        assert len(resp.executive_summary) > 50
        assert len(resp.nadir_analysis) > 50
        assert len(resp.pathway_flux_breakdown) > 50
        assert len(resp.uncertainty_and_limitations) > 50
        assert len(resp.suggested_experiments) >= 2
        assert resp.grounding.passed is True
        assert resp.grounding.disclaimers_present is True

    def test_interpret_cohort_success(self, sample_cohort_result):
        req, result = sample_cohort_result
        ctx = build_cohort_context(req, result)

        provider = DeterministicBiochemicalProvider()
        resp = asyncio.run(provider.interpret_cohort(ctx))

        assert resp.provider_used == "deterministic-biochemical-v1"
        assert "N = 20" in resp.executive_summary
        assert len(resp.tail_risk_analysis) > 30
        assert len(resp.g6pd_interaction_analysis) > 30
        assert len(resp.lysis_risk_evaluation) > 30
        assert resp.grounding.passed is True


class TestGroundingGuardrail:
    def test_guardrail_detects_forbidden_claims(self, sample_playground_result):
        req, result = sample_playground_result
        ctx = build_playground_context(req, result)

        guardrail = GroundingGuardrail()
        hallucinated_resp = PlaygroundInterpretationResponse(
            executive_summary="Simulation demonstrated clear mitochondrial ROS generation in the matrix.",
            nadir_analysis="The nadir was 1.20 mM.",
            pathway_flux_breakdown="Normal pathway.",
            control_comparison="No control.",
            uncertainty_and_limitations="In vitro model surrogate.",
            suggested_experiments=[],
            provider_used="mock",
        )
        evaluation = guardrail.verify_playground(hallucinated_resp, ctx)
        assert evaluation.passed is False
        assert any("mitochondri" in flag.lower() for flag in evaluation.flags)

    def test_unverified_compound_warning_enforced(self):
        ctx = {
            "endpoints": {"gsh_min_mM": 1.2},
            "has_unverified_compounds": True,
            "unverified_compounds": ["cmp_xenobiotic_x101"],
            "compounds": [],
        }
        guardrail = GroundingGuardrail()
        resp_without_warning = PlaygroundInterpretationResponse(
            executive_summary="All results normal in vitro suspension.",
            nadir_analysis="Nadir 1.2 mM.",
            pathway_flux_breakdown="Pathway normal.",
            control_comparison="None.",
            uncertainty_and_limitations="Standard in vitro ADME limitations.",
            suggested_experiments=[],
            provider_used="mock",
        )
        eval_result = guardrail.verify_playground(resp_without_warning, ctx)
        assert eval_result.unverified_compound_warning_present is False
        assert eval_result.passed is False


class TestInterpretationService:
    def test_service_deterministic_dispatch(self, sample_playground_result):
        req, result = sample_playground_result
        service = InterpretationService()

        play_req = PlaygroundInterpretationRequest(
            scenario_request=req,
            scenario_result=result,
            provider_preference="deterministic",
        )
        resp = asyncio.run(service.interpret_playground(play_req))
        assert resp.provider_used == "deterministic-biochemical-v1"
        assert resp.fallback_applied is False
        assert resp.grounding.passed is True

    def test_service_auto_fallback_when_llm_missing(self, sample_playground_result):
        req, result = sample_playground_result
        service = InterpretationService()

        # In test environment with no API key, preference 'auto' should use deterministic
        play_req = PlaygroundInterpretationRequest(
            scenario_request=req,
            scenario_result=result,
            provider_preference="auto",
        )
        resp = asyncio.run(service.interpret_playground(play_req))
        assert "deterministic" in resp.provider_used

    def test_service_status(self):
        service = InterpretationService()
        status = service.get_status()
        assert "deterministic" in status.providers_available
        assert status.guardrails_active is True
        assert len(status.unmodeled_physics_declared) >= 3


class TestIntelligenceCompatibility:
    def test_check_supported_mechanisms(self):
        checker = CompoundCompatibilityChecker()
        res = checker.check_mechanism(MechanismType.DIRECT_OXIDANT)
        assert res.is_compatible is True
        assert "rbc-g6pd-gsh-v2" in res.supported_models

    def test_check_unknown_mechanism(self):
        checker = CompoundCompatibilityChecker()
        res = checker.check_mechanism("UNKNOWN_MAGIC_MECHANISM")
        assert res.is_compatible is False

    def test_evidence_tier_evaluation(self):
        # With valid citation & erythrocyte validation -> CURATED
        cur = evaluate_evidence_tier("Blood 84:2018", {}, is_human_erythrocyte_validated=True)
        assert cur.evidence_level == EvidenceLevel.CURATED

        # With citation but not erythrocyte-validated -> ESTIMATED
        est = evaluate_evidence_tier("In Vitro Tox 1999", {}, is_human_erythrocyte_validated=False)
        assert est.evidence_level == EvidenceLevel.ESTIMATED

        # Without citation -> UNVERIFIED
        unv = evaluate_evidence_tier(None, {})
        assert unv.evidence_level == EvidenceLevel.UNVERIFIED
