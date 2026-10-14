"""
API integration tests for Milestone 4 compounds and scenario endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from vblood.api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


class TestCompoundsAPI:
    """Tests for /compounds endpoints."""

    def test_list_compounds_returns_curated_list(self, client):
        resp = client.get("/compounds")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 6
        ids = [item["compound_id"] for item in data]
        assert "cmp_menadione" in ids
        assert "cmp_cdnb" in ids

    def test_get_compound_by_id_success(self, client):
        resp = client.get("/compounds/cmp_menadione")
        assert resp.status_code == 200
        data = resp.json()
        assert data["compound_id"] == "cmp_menadione"
        assert data["mechanism_type"] == "REDOX_CYCLER"
        assert data["evidence_level"] == "CURATED"

    def test_get_compound_not_found(self, client):
        resp = client.get("/compounds/cmp_nonexistent")
        assert resp.status_code == 404


class TestScenarioAPI:
    """Tests for /scenarios and /scenarios/population endpoints."""

    def test_run_scenario_success(self, client):
        payload = {
            "compounds": [{"compound_id": "cmp_menadione", "dose_mM": 0.02}],
            "exposure_profile": "BOLUS",
            "duration_s": 300.0,
            "g6pd_alpha": 1.0,
            "model_version": "rbc-g6pd-gsh-v2",
        }
        resp = client.post("/scenarios", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert "run_id" in data
        assert "derived_metrics" in data
        assert "gsh_nadir_mM" in data["derived_metrics"]
        assert "RESEARCH USE ONLY" in data["research_disclaimer"]

        run_id = data["run_id"]

        # Test visual frames retrieval
        vis_resp = client.get(f"/scenarios/{run_id}/visual")
        assert vis_resp.status_code == 200
        vis_data = vis_resp.json()
        assert vis_data["total_frames"] > 0
        assert "cell_state" in vis_data["frames"][0]
        assert not vis_data["frames"][0]["morphology_simulated"]

        # Test SSE streaming
        stream_resp = client.get(f"/scenarios/{run_id}/stream")
        assert stream_resp.status_code == 200
        assert "text/event-stream" in stream_resp.headers["content-type"]
        assert "event: frame" in stream_resp.text

    def test_scenario_dose_limit_enforced(self, client):
        payload = {
            "compounds": [{"compound_id": "cmp_menadione", "dose_mM": 25.0}],  # > 20 mM limit
            "duration_s": 300.0,
        }
        resp = client.post("/scenarios", json=payload)
        assert resp.status_code == 422
        assert "exceeds maximum" in resp.json()["detail"]

    def test_population_scenario_success(self, client):
        payload = {
            "scenario_request": {
                "compounds": [{"compound_id": "cmp_h2o2", "dose_mM": 0.05}],
                "duration_s": 300.0,
            },
            "n_cells": 100,
            "random_seed": 42,
        }
        resp = client.post("/scenarios/population", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["n_cells"] == 100
        assert data["execution_time_s"] < 5.0
        assert "pct_cells_below_mild_gsh" in data
        assert "percentile_bands" in data
        assert "gsh_p50" in data["percentile_bands"]
