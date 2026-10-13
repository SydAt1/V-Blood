"""
FastAPI application for V-Blood Mechanistic Simulation Platform (Task 5).

Exposes the simulation engine and model registry via REST endpoints.
Keeps biological equations strictly inside the core simulation modules.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from vblood.api.schemas import (
    HealthResponse,
    ModelDetailResponse,
    SimulationCreateRequest,
    SimulationDetailResponse,
)
from vblood.api.storage import InMemorySimulationStore, SimulationStore
from vblood.biology.rbc.parameters import DEFAULT_PARAMETERS
from vblood.schemas.simulation import (
    SimulationRequest,
    SimulationResult,
    SolverStatus,
)
from vblood.simulation.engine import _MODEL_REGISTRY, run_simulation


def create_app(store: SimulationStore | None = None) -> FastAPI:
    """Application factory for the V-Blood API."""
    app = FastAPI(
        title="V-Blood Mechanistic Simulation API",
        version="0.1.0",
        description=(
            "REST API for running mechanistic blood simulations and inspecting biological models. "
            "WARNING: For research simulation only — NOT for clinical, diagnostic, or regulatory use."
        ),
    )

    simulation_store = store or InMemorySimulationStore()

    @app.exception_handler(ValueError)
    async def value_error_handler(request, exc: ValueError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc)},
        )

    @app.get(
        "/health",
        response_model=HealthResponse,
        summary="Service health and readiness check",
    )
    def get_health() -> HealthResponse:
        """Return application readiness status and model registry availability.

        NOTE: An 'ok' status indicates software availability, NOT that biological
        models have achieved clinical or experimental validation.
        """
        return HealthResponse(
            status="ok",
            application_version="0.1.0",
            model_registry_status="operational",
            registered_models_count=len(_MODEL_REGISTRY),
            scientific_validation_status=(
                "RESEARCH_PROTOTYPE_ONLY: Model outputs are mechanistic hypotheses and not clinically validated."
            ),
        )

    @app.get(
        "/models",
        response_model=list[ModelDetailResponse],
        summary="List all registered biological models and their metadata",
    )
    def list_models() -> list[ModelDetailResponse]:
        """Return all registered biological models with parameter provenance and evidence grading."""
        results: list[ModelDetailResponse] = []
        for model_id, model in _MODEL_REGISTRY.items():
            meta = model.metadata
            all_params = DEFAULT_PARAMETERS.all_parameters()

            # Summarize parameter evidence status
            evidence_counts: dict[str, int] = {}
            for p in all_params.values():
                st = p.evidence_status.value
                evidence_counts[st] = evidence_counts.get(st, 0) + 1

            results.append(
                ModelDetailResponse(
                    model_id=meta.model_id,
                    name=meta.name,
                    version=meta.version,
                    description=meta.description,
                    supported_scenarios=[
                        "Resting erythrocyte baseline (no challenge)",
                        "Generic oxidative challenge (H2O2 bolus)",
                        "Equilibrium steady-state analysis",
                    ],
                    state_variables=list(meta.state_variable_names),
                    state_variable_units=list(meta.state_variable_units),
                    compartment=meta.compartment,
                    parameter_count=len(all_params),
                    evidence_status_summary=evidence_counts,
                    literature_sources=list(meta.literature_sources),
                )
            )
        return results

    @app.post(
        "/simulations",
        response_model=SimulationDetailResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Execute a biological simulation run",
    )
    def create_simulation(req_body: SimulationCreateRequest) -> SimulationDetailResponse:
        """Launch a simulation run synchronously and store the resulting trajectory.

        - Uses computed steady-state equilibrium as default initial condition when initial_conditions is omitted.
        - Supports explicit initial condition overrides.
        - Validates parameter bounds and rejects unsupported overrides.
        - Returns HTTP 422 if the ODE solver fails.
        """
        if req_body.model_id not in _MODEL_REGISTRY:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unknown model_id '{req_body.model_id}'. Available: {list(_MODEL_REGISTRY.keys())}.",
            )

        # Validate parameter overrides if supplied
        if req_body.parameter_overrides:
            valid_keys = set(DEFAULT_PARAMETERS.all_parameters().keys())
            for k, v in req_body.parameter_overrides.items():
                if k not in valid_keys:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Unknown parameter override '{k}'. Supported: {sorted(list(valid_keys))}.",
                    )
                if v < 0.0:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Parameter '{k}' cannot be negative, got {v}.",
                    )

        # Build simulation request
        sim_req = SimulationRequest(
            model_id=req_body.model_id,
            initial_conditions=req_body.initial_conditions,
            exposure=req_body.exposure,
            t_start_s=req_body.t_start_s,
            t_end_s=req_body.t_end_s,
            n_eval_points=req_body.n_eval_points,
            solver=req_body.solver,
            use_steady_state_ic=req_body.use_steady_state_ic,
            run_label=req_body.run_label,
        )

        sim_result = run_simulation(sim_req)

        # If solver failed, do not present as valid scientific result
        if sim_result.solver_status != SolverStatus.SUCCESS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Numerical ODE solver failed: {sim_result.solver_message}",
            )

        # Persist result in development store
        simulation_store.save(sim_result)

        ic_source = "steady_state" if sim_result.steady_state_initialization else "explicit_initial_conditions"

        return SimulationDetailResponse(
            run_id=sim_result.run_id,
            model_id=sim_result.model_id,
            model_version=sim_result.model_version,
            parameter_set="default_v1",
            scenario_description=sim_req.exposure.description or "Default scenario",
            initial_condition_source=ic_source,
            solver_status=sim_result.solver_status.value,
            solver_message=sim_result.solver_message,
            solver_time_s=sim_result.solver_time_s,
            n_evaluations=sim_result.n_function_evaluations,
            final_gsh_mM=sim_result.final_gsh_mM,
            final_gssg_mM=sim_result.final_gssg_mM,
            min_gsh_mM=sim_result.min_gsh_mM,
            max_h2o2_mM=sim_result.max_h2o2_mM,
            final_damage=sim_result.final_damage,
            final_hemolysis_pct=sim_result.final_hemolysis_pct,
            warnings_count=len(sim_result.warnings),
            warnings=[w.model_dump() for w in sim_result.warnings],
            steady_state_initialization=sim_result.steady_state_initialization,
            provenance=sim_result.provenance,
            trajectory_length=len(sim_result.trajectory),
        )

    @app.get(
        "/simulations/{run_id}",
        response_model=SimulationDetailResponse,
        summary="Retrieve simulation run by run_id",
    )
    def get_simulation(run_id: str) -> SimulationDetailResponse:
        """Retrieve stored simulation endpoints and metadata for a previous run.

        Returns HTTP 404 if run_id is not found in the storage repository.
        """
        res = simulation_store.get(run_id)
        if res is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Simulation run '{run_id}' not found. In-memory storage does not persist across server restarts.",
            )

        ic_source = "steady_state" if res.steady_state_initialization else "explicit_initial_conditions"

        return SimulationDetailResponse(
            run_id=res.run_id,
            model_id=res.model_id,
            model_version=res.model_version,
            parameter_set="default_v1",
            scenario_description=res.request.exposure.description or "Default scenario",
            initial_condition_source=ic_source,
            solver_status=res.solver_status.value,
            solver_message=res.solver_message,
            solver_time_s=res.solver_time_s,
            n_evaluations=res.n_function_evaluations,
            final_gsh_mM=res.final_gsh_mM,
            final_gssg_mM=res.final_gssg_mM,
            min_gsh_mM=res.min_gsh_mM,
            max_h2o2_mM=res.max_h2o2_mM,
            final_damage=res.final_damage,
            final_hemolysis_pct=res.final_hemolysis_pct,
            warnings_count=len(res.warnings),
            warnings=[w.model_dump() for w in res.warnings],
            steady_state_initialization=res.steady_state_initialization,
            provenance=res.provenance,
            trajectory_length=len(res.trajectory),
        )

    return app
