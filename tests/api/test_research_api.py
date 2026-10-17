"""
API Integration Tests for Milestone 7 Research Endpoints.

Verifies:
- POST /research/jobs and GET /research/jobs/{job_id}
- GET /research/candidates and GET /research/candidates/{id}
- POST /research/candidates/{id}/validate
- POST /research/candidates/{id}/approve
- Dynamic catalog availability on GET /compounds
- POST /scenarios simulation execution with approved compound
- POST /scenarios rejection with HTTP 422 for unapproved candidates
"""

from __future__ import annotations

import time
import pytest
from fastapi.testclient import TestClient

from vblood.api.app import app
from vblood.intelligence.pipeline import get_research_orchestrator
from vblood.intelligence.repository import get_research_repository


@pytest.fixture
def client():
    return TestClient(app)


class TestResearchAPI:
    def test_submit_and_poll_research_job(self, client):
        payload = {
            "substance_name": "Primaquine",
            "research_objective": "Investigate redox cycling kinetics in human G6PD erythrocytes",
            "force_refresh": True,
        }
        res = client.post("/research/jobs", json=payload)
        assert res.status_code == 202
        data = res.json()
        assert "job_id" in data
        job_id = data["job_id"]

        # Poll for completion (background async task)
        completed = False
        for _ in range(30):
            job_res = client.get(f"/research/jobs/{job_id}")
            assert job_res.status_code == 200
            jdata = job_res.json()
            if jdata["stage"] in ("COMPLETED", "FAILED"):
                completed = True
                assert jdata["stage"] == "COMPLETED"
                assert jdata["candidate_id"] == "rcand_primaquine"
                break
            time.sleep(0.1)

        assert completed is True

    def test_list_and_get_candidates(self, client):
        # Ensure candidate exists
        orchestrator = get_research_orchestrator()
        orchestrator.run_pipeline("Menadione", force_refresh=True)

        list_res = client.get("/research/candidates")
        assert list_res.status_code == 200
        candidates = list_res.json()
        assert len(candidates) >= 1

        cid = "rcand_menadione"
        detail_res = client.get(f"/research/candidates/{cid}")
        assert detail_res.status_code == 200
        dossier = detail_res.json()
        assert dossier["candidate_id"] == cid
        assert dossier["chemical_identity"]["preferred_name"] == "Menadione"
        assert len(dossier["sources"]) >= 1
        assert len(dossier["findings"]) >= 1
        assert len(dossier["validation_summary"]["gates"]) == 10

    def test_approve_candidate_and_simulate_scenario(self, client):
        orchestrator = get_research_orchestrator()
        dossier = orchestrator.run_pipeline("Primaquine", force_refresh=True)
        cid = dossier.candidate_id

        # Verify not yet simulation ready in candidate status
        if dossier.status.value != "SIMULATION_READY":
            # Attempt scenario before approval -> must fail with 422
            unapproved_scenario = {
                "model_version": "rbc-g6pd-gsh-v2",
                "duration_s": 3600.0,
                "g6pd_alpha": 1.0,
                "compounds": [
                    {
                        "compound_id": cid,
                        "dose_mM": 0.02,
                        "start_time_s": 0.0,
                        "waveform": "BOLUS",
                    }
                ],
            }
            scen_fail = client.post("/scenarios", json=unapproved_scenario)
            assert scen_fail.status_code == 422
            assert "not approved for active simulation" in scen_fail.json()["detail"]

        # Approve candidate
        approve_res = client.post(f"/research/candidates/{cid}/approve", params={"actor": "lead_researcher"})
        assert approve_res.status_code == 200
        app_data = approve_res.json()
        assert app_data["status"] == "SIMULATION_READY"

        # Check GET /compounds now lists newly registered compound
        compounds_res = client.get("/compounds")
        assert compounds_res.status_code == 200
        all_compounds = compounds_res.json()
        found = next((c for c in all_compounds if c["compound_id"] == cid), None)
        assert found is not None
        assert found["name"] == "Primaquine"

        # Now simulate scenario with newly approved compound -> must succeed with 200
        scen_success = client.post(
            "/scenarios",
            json={
                "model_version": "rbc-g6pd-gsh-v2",
                "duration_s": 1800.0,
                "g6pd_alpha": 1.0,
                "compounds": [
                    {
                        "compound_id": cid,
                        "dose_mM": 0.02,
                        "start_time_s": 0.0,
                        "waveform": "BOLUS",
                    }
                ],
            },
        )
        assert scen_success.status_code == 200
        scen_data = scen_success.json()
        assert scen_data["trajectory_length"] > 0
        assert scen_data["derived_metrics"]["gsh_nadir_mM"] < 2.5

    def test_revalidate_and_reject_candidate(self, client):
        orchestrator = get_research_orchestrator()
        dossier = orchestrator.run_pipeline("Menadione", force_refresh=True)
        cid = dossier.candidate_id

        val_res = client.post(f"/research/candidates/{cid}/validate")
        assert val_res.status_code == 200
        val_data = val_res.json()
        assert len(val_data["validation_summary"]["gates"]) == 10

        rej_res = client.post(f"/research/candidates/{cid}/reject", params={"notes": "Out of biological scope"})
        assert rej_res.status_code == 200
        rej_data = rej_res.json()
        assert rej_data["status"] == "REJECTED"
