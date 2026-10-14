"""
FastAPI application for V-Blood Mechanistic Simulation Platform (Task 5).

Exposes the simulation engine and model registry via REST endpoints.
Keeps biological equations strictly inside the core simulation modules.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse


from vblood.api.schemas import (
    CompoundResponse,
    HealthResponse,
    ModelDetailResponse,
    ScenarioRunResponse,
    SimulationCreateRequest,
    SimulationDetailResponse,
)
from vblood.api.storage import InMemorySimulationStore, SimulationStore
from vblood.biology.rbc.parameters import DEFAULT_PARAMETERS
from vblood.reporting.visual_state import (
    VisualTrajectoryResponse,
    trajectory_to_visual_frames,
)
from vblood.scenarios.compounds import get_compound_library
from vblood.scenarios.engine import ScenarioRequest, run_scenario
from vblood.scenarios.population import (
    PopulationRequest,
    PopulationResult,
    simulate_population,
)
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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    simulation_store = store or InMemorySimulationStore()

    @app.exception_handler(ValueError)
    async def value_error_handler(request, exc: ValueError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
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
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail=f"Unknown parameter override '{k}'. Supported: {sorted(list(valid_keys))}.",
                    )
                if v < 0.0:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
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
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
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
        "/simulations",
        response_model=list[SimulationDetailResponse],
        summary="List recent simulation runs from store",
    )
    def list_simulations(limit: int = 50) -> list[SimulationDetailResponse]:
        """List recently stored simulation runs."""
        stored = simulation_store.list_all(limit=limit)
        results = []
        for res in stored:
            ic_source = "steady_state" if res.steady_state_initialization else "explicit_initial_conditions"
            results.append(
                SimulationDetailResponse(
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
            )
        return results

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

    # ------------------------------------------------------------------ #
    # Milestone 4: Compounds & Scenarios Endpoints
    # ------------------------------------------------------------------ #

    @app.get(
        "/compounds",
        response_model=list[CompoundResponse],
        summary="List all curated compounds in the library",
    )
    def list_compounds() -> list[CompoundResponse]:
        """Return all curated compounds with metadata, mechanism, and evidence status."""
        lib = get_compound_library()
        return [
            CompoundResponse(
                compound_id=c.compound_id,
                name=c.name,
                smiles=c.smiles,
                inchikey=c.inchikey,
                mechanism_type=c.mechanism_type.value,
                default_parameters=c.default_parameters,
                parameter_ranges=c.parameter_ranges,
                exposure_units=c.exposure_units,
                evidence_level=c.evidence_level.value,
                is_unverified=c.is_unverified,
                provenance=c.provenance,
                confidence_score=c.confidence_score,
            )
            for c in lib.list_all()
        ]

    @app.get(
        "/compounds/{compound_id}",
        response_model=CompoundResponse,
        summary="Retrieve detailed compound metadata by ID",
    )
    def get_compound(compound_id: str) -> CompoundResponse:
        """Return compound entry by ID, or 404 if not found."""
        lib = get_compound_library()
        c = lib.get(compound_id)
        if c is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Compound '{compound_id}' not found in library.",
            )
        return CompoundResponse(
            compound_id=c.compound_id,
            name=c.name,
            smiles=c.smiles,
            inchikey=c.inchikey,
            mechanism_type=c.mechanism_type.value,
            default_parameters=c.default_parameters,
            parameter_ranges=c.parameter_ranges,
            exposure_units=c.exposure_units,
            evidence_level=c.evidence_level.value,
            is_unverified=c.is_unverified,
            provenance=c.provenance,
            confidence_score=c.confidence_score,
        )

    @app.post(
        "/scenarios",
        response_model=ScenarioRunResponse,
        summary="Execute a chemical exposure scenario (single cell)",
    )
    def create_scenario(req: ScenarioRequest) -> ScenarioRunResponse:
        """Simulate single-cell redox dynamics under one or more chemical exposures."""
        for c in req.compounds:
            if c.dose_mM > 20.0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"Dose {c.dose_mM} mM exceeds maximum allowable limit of 20.0 mM.",
                )
        if req.duration_s > 86400.0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Duration {req.duration_s} s exceeds 24 h limit (86400 s).",
            )

        result = run_scenario(req)
        simulation_store.save_scenario(result)
        simulation_store.save(result.simulation_result)

        return ScenarioRunResponse(
            run_id=result.simulation_result.run_id,
            scenario_request=req.model_dump(),
            derived_metrics=result.derived_metrics.model_dump(),
            has_unverified_compounds=result.has_unverified_compounds,
            unverified_compounds=result.unverified_compounds,
            compound_summaries=result.compound_summaries,
            interaction_assumptions=result.interaction_assumptions,
            trajectory_length=len(result.simulation_result.trajectory),
            research_disclaimer=result.research_disclaimer,
            trajectory=[p.model_dump() for p in result.simulation_result.trajectory],
        )

    @app.get(
        "/scenarios/{run_id}",
        response_model=ScenarioRunResponse,
        summary="Retrieve detailed scenario run by run_id",
    )
    def get_scenario(run_id: str) -> ScenarioRunResponse:
        """Retrieve stored chemical scenario run by run_id."""
        scen = simulation_store.get_scenario(run_id)
        if scen is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scenario run '{run_id}' not found.",
            )
        return ScenarioRunResponse(
            run_id=scen.simulation_result.run_id,
            scenario_request=scen.scenario_request.model_dump(),
            derived_metrics=scen.derived_metrics.model_dump(),
            has_unverified_compounds=scen.has_unverified_compounds,
            unverified_compounds=scen.unverified_compounds,
            compound_summaries=scen.compound_summaries,
            interaction_assumptions=scen.interaction_assumptions,
            trajectory_length=len(scen.simulation_result.trajectory),
            research_disclaimer=scen.research_disclaimer,
            trajectory=[p.model_dump() for p in scen.simulation_result.trajectory],
        )

    @app.post(
        "/scenarios/population",
        response_model=PopulationResult,
        summary="Simulate a cohort of cells (N cells) under chemical exposure",
    )
    def create_population_scenario(req: PopulationRequest) -> PopulationResult:
        """Simulate cohort variability across N cells sampled from biological priors."""
        if req.n_cells > 5000:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Cohort size n_cells={req.n_cells} exceeds limit of 5000.",
            )
        return simulate_population(req)

    @app.get(
        "/scenarios/{run_id}/visual",
        response_model=VisualTrajectoryResponse,
        summary="Retrieve visual-state frames for frontend animation playback",
    )
    def get_visual_scenario(run_id: str, max_frames: int = 300) -> VisualTrajectoryResponse:
        """Retrieve downsampled visual frames classified by biochemical cell health."""
        scen = simulation_store.get_scenario(run_id)
        if scen is None:
            sim = simulation_store.get(run_id)
            if sim is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Simulation run '{run_id}' not found.",
                )
            traj = sim.trajectory
            dur = sim.request.t_end_s - sim.request.t_start_s
        else:
            traj = scen.simulation_result.trajectory
            dur = scen.scenario_request.duration_s

        frames = trajectory_to_visual_frames(traj, max_frames=max_frames)
        return VisualTrajectoryResponse(
            run_id=run_id,
            total_frames=len(frames),
            playback_duration_s=dur,
            frames=frames,
        )

    @app.get(
        "/scenarios/{run_id}/stream",
        summary="Server-Sent Events (SSE) stream of visual animation frames",
    )
    def stream_visual_scenario(run_id: str, max_frames: int = 200) -> StreamingResponse:
        """Stream visual frames as Server-Sent Events for real-time frontend playback."""
        scen = simulation_store.get_scenario(run_id)
        sim = simulation_store.get(run_id) if scen is None else scen.simulation_result
        if sim is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Simulation run '{run_id}' not found.",
            )

        frames = trajectory_to_visual_frames(sim.trajectory, max_frames=max_frames)

        def event_generator():
            import json as json_mod

            for idx, frame in enumerate(frames):
                payload = json_mod.dumps(frame.model_dump())
                yield f"id: {idx}\nevent: frame\ndata: {payload}\n\n"
            yield "event: complete\ndata: {}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    return app


app = create_app()