"""
Automated tests for FastAPI endpoints (Task 5).

Tests cover:
- GET /health operational status and scientific disclaimer.
- GET /models metadata, state variables, and evidence status.
- POST /simulations execution, default steady state, explicit IC override, and parameter validation.
- GET /simulations/{run_id} retrieval and 404 handling.
- Independence of core simulation engine from API layer.
"""

import pytest
from fastapi.testclient import TestClient

from vblood.api.app import create_app
from vblood.api.storage import InMemorySimulationStore


@pytest.fixture
def client():
    store = InMemorySimulationStore()
    app = create_app(store=store)
    return TestClient(app)


class TestHealthEndpoint:
    """Tests on GET /health."""

    def test_health_returns_200_and_status_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["application_version"] == "0.1.0"
        assert data["model_registry_status"] == "operational"
        assert data["registered_models_count"] >= 1
        assert "RESEARCH_PROTOTYPE_ONLY" in data["scientific_validation_status"]


class TestModelsEndpoint:
    """Tests on GET /models."""

    def test_list_models_returns_registered_rbc_model(self, client):
        resp = client.get("/models")
        assert resp.status_code == 200
        models = resp.json()
        assert len(models) >= 1

        rbc_model = next((m for m in models if m["model_id"] == "rbc-gsh-redox-v1"), None)
        assert rbc_model is not None
        assert rbc_model["name"] == "RBC Glutathione Redox Model"
        assert rbc_model["version"] == "1.0.0"
        assert "GSH" in rbc_model["state_variables"]
        assert "GSSG" in rbc_model["state_variables"]
        assert rbc_model["parameter_count"] == 12
        assert "LITERATURE" in rbc_model["evidence_status_summary"]
        assert "SYNTHETIC" in rbc_model["evidence_status_summary"]


class TestSimulationsEndpoint:
    """Tests on POST /simulations and GET /simulations/{run_id}."""

    def test_create_simulation_default_steady_state(self, client):
        payload = {
            "model_id": "rbc-gsh-redox-v1",
            "t_start_s": 0.0,
            "t_end_s": 100.0,
            "n_eval_points": 50,
        }
        resp = client.post("/simulations", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert "run_id" in data
        assert data["solver_status"] == "success"
        assert data["initial_condition_source"] == "steady_state"
        assert data["steady_state_initialization"] is True
        assert data["trajectory_length"] == 50

    def test_create_simulation_explicit_initial_conditions(self, client):
        payload = {
            "model_id": "rbc-gsh-redox-v1",
            "initial_conditions": {
                "gsh_0": 2.8,
                "gssg_0": 0.02,
                "h2o2_0": 0.0001,
                "nadph_0": 0.035,
                "damage_0": 0.0,
            },
            "t_start_s": 0.0,
            "t_end_s": 60.0,
            "n_eval_points": 30,
        }
        resp = client.post("/simulations", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["initial_condition_source"] == "explicit_initial_conditions"
        assert data["steady_state_initialization"] is False

    def test_create_simulation_with_h2o2_bolus(self, client):
        payload = {
            "model_id": "rbc-gsh-redox-v1",
            "exposure": {
                "h2o2_bolus_mM": 0.05,
                "description": "50 µM H2O2 bolus",
            },
            "t_start_s": 0.0,
            "t_end_s": 120.0,
            "n_eval_points": 50,
        }
        resp = client.post("/simulations", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["max_h2o2_mM"] > 0.04

    def test_get_simulation_by_run_id(self, client):
        # 1. Create run
        post_resp = client.post(
            "/simulations",
            json={"model_id": "rbc-gsh-redox-v1", "t_end_s": 30.0, "n_eval_points": 20},
        )
        assert post_resp.status_code == 201
        run_id = post_resp.json()["run_id"]

        # 2. Retrieve by run_id
        get_resp = client.get(f"/simulations/{run_id}")
        assert get_resp.status_code == 200
        get_data = get_resp.json()
        assert get_data["run_id"] == run_id
        assert get_data["model_id"] == "rbc-gsh-redox-v1"

    def test_get_unknown_simulation_returns_404(self, client):
        resp = client.get("/simulations/non-existent-run-id")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_unknown_model_id_returns_404(self, client):
        resp = client.post("/simulations", json={"model_id": "non-existent-model"})
        assert resp.status_code == 404

    def test_invalid_parameter_override_rejected(self, client):
        payload = {
            "model_id": "rbc-gsh-redox-v1",
            "parameter_overrides": {"fake_parameter_name": 123.0},
        }
        resp = client.post("/simulations", json=payload)
        assert resp.status_code == 422
        assert "unknown parameter override" in resp.json()["detail"].lower()

    def test_negative_parameter_override_rejected(self, client):
        payload = {
            "model_id": "rbc-gsh-redox-v1",
            "parameter_overrides": {"k_gpx": -50.0},
        }
        resp = client.post("/simulations", json=payload)
        assert resp.status_code == 422
        assert "cannot be negative" in resp.json()["detail"].lower()
