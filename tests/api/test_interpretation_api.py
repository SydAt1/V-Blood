"""
API integration tests for Milestone 6 interpretation endpoints.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from vblood.api.app import create_app
from vblood.scenarios.engine import (
    CompoundExposure,
    ExposureProfile,
    ScenarioRequest,
    run_scenario,
)
from vblood.scenarios.population import PopulationRequest, simulate_population


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


class TestInterpretationAPI:
    def test_get_interpret_status(self, client):
        resp = client.get("/interpret/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "providers_available" in data
        assert "deterministic" in data["providers_available"]
        assert data["guardrails_active"] is True
        assert len(data["unmodeled_physics_declared"]) >= 3

    def test_interpret_playground_endpoint(self, client):
        req = ScenarioRequest(
            model_version="rbc-g6pd-gsh-v2",
            g6pd_alpha=0.6,
            duration_s=300.0,
            exposure_profile=ExposureProfile.BOLUS,
            compounds=[
                CompoundExposure(compound_id="cmp_menadione", dose_mM=0.03),
            ],
        )
        sim_res = run_scenario(req)

        payload = {
            "scenario_request": req.model_dump(),
            "scenario_result": sim_res.model_dump(),
            "provider_preference": "deterministic",
        }

        resp = client.post("/interpret/playground", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "executive_summary" in data
        assert "nadir_analysis" in data
        assert "pathway_flux_breakdown" in data
        assert "uncertainty_and_limitations" in data
        assert data["provider_used"] == "deterministic-biochemical-v1"
        assert data["grounding"]["passed"] is True

    def test_interpret_cohort_endpoint(self, client):
        req = PopulationRequest(
            scenario_request=ScenarioRequest(
                model_version="rbc-g6pd-gsh-v2",
                g6pd_alpha=0.5,
                duration_s=300.0,
                compounds=[
                    CompoundExposure(compound_id="cmp_menadione", dose_mM=0.02),
                ],
            ),
            n_cells=20,
            random_seed=42,
        )
        pop_res = simulate_population(req)

        payload = {
            "population_request": req.model_dump(),
            "population_result": pop_res.model_dump(),
            "provider_preference": "deterministic",
        }

        resp = client.post("/interpret/cohort", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "executive_summary" in data
        assert "tail_risk_analysis" in data
        assert "g6pd_interaction_analysis" in data
        assert "lysis_risk_evaluation" in data
        assert data["provider_used"] == "deterministic-biochemical-v1"
        assert data["grounding"]["passed"] is True
