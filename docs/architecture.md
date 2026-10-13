# Architecture — V-Blood

## System overview

V-Blood separates six distinct concerns, each in its own Python sub-package. No layer has import dependencies on layers above it.

```
┌─────────────────────────────────────────────────────┐
│              Frontend (React / TypeScript)            │   ← Milestone 7
│           Interactive research dashboard              │
└────────────────────────┬────────────────────────────┘
                         │ HTTP (JSON)
┌────────────────────────▼────────────────────────────┐
│              API Layer  (FastAPI)                     │   ← Milestone 4
│          /simulations, /models, /reports              │
└────────────────────────┬────────────────────────────┘
                         │ Python function call
┌────────────────────────▼────────────────────────────┐
│           Simulation Engine  (src/vblood/simulation) │   ← Milestone 1 ✓
│        solve_ivp wrapper + result formatting          │
└────────────────────────┬────────────────────────────┘
                         │ calls
┌────────────────────────▼────────────────────────────┐
│         Biological Model  (src/vblood/biology)       │   ← Milestone 1 ✓
│      rhs(), initial_state(), validate_params()        │
└─────────────────────────────────────────────────────┘

Supporting modules (independent of above stack):
 ├── src/vblood/schemas/         Pydantic input/output contracts
 ├── src/vblood/chemistry/       Chemical identity, RDKit descriptors
 ├── src/vblood/machine_learning/ ML predictions (Milestone 5)
 ├── src/vblood/uncertainty/     UQ and applicability domain (Milestone 5)
 ├── src/vblood/parameter_estimation/ Fitting from time-series (Milestone 3)
 ├── src/vblood/validation/      Scientific validation utilities
 ├── src/vblood/reporting/       LLM interface contract (Milestone 6)
 └── src/vblood/provenance/      Run versioning and metadata
```

## Dependency rules

| From | May import | May NOT import |
|---|---|---|
| biology/ | schemas/, numpy | simulation/, api/, ml/ |
| simulation/ | biology/, schemas/ | api/, ml/ |
| api/ | simulation/, schemas/ | biology/ directly |
| reporting/ | schemas/ only | simulation/ (receives structured data) |
| ml/ | schemas/, chemistry/ | biology/ equations directly |

## Key design decisions

### 1. Engine independence
The mechanistic engine (`simulation.engine.run_simulation`) is a plain Python function. It does not require a running server, database connection, or external API. This makes it:
- Directly testable with pytest
- Callable from notebooks and scripts
- Independent of infrastructure changes

### 2. Pydantic for all contracts
All data crossing module boundaries is validated with Pydantic models. This catches unit errors, negative concentrations, and time-span inversions before the ODE solver is invoked.

### 3. BiologicalModel abstract base
New biological models (platelet, coagulation, etc.) implement `BiologicalModel.rhs()` and `BiologicalModel.initial_state()`. The simulation engine and API are model-agnostic; they operate on any registered model by ID.

### 4. Model registry
`simulation/engine.py` maintains a `_MODEL_REGISTRY` dict mapping model IDs to model instances. Adding a new model requires only:
1. Implementing `BiologicalModel` in `biology/<system>/`
2. Registering the instance in `_MODEL_REGISTRY`

### 5. Provenance by default
Every `SimulationResult` contains a `provenance` dict recording model version, parameter set version, solver settings, and run ID. This is sufficient for reproducing any result from the result object alone.

### 6. LLM interface is a data contract, not a live call
The `reporting/llm_interface.py` defines `LLMReportInput` and `LLMReportOutput` schemas. The LLM module receives a fully structured object, not raw text or simulation logs. This prevents hallucinated numerical values.

## File map

```
src/vblood/
├── __init__.py          Package version
├── config.py            Environment-based configuration
├── schemas/
│   ├── __init__.py
│   └── simulation.py    SimulationRequest, SimulationResult, TrajectoryPoint
├── biology/
│   ├── __init__.py
│   ├── base.py          BiologicalModel ABC, ModelMetadata
│   └── rbc/
│       ├── __init__.py
│       ├── parameters.py  RBCGSHParameters (Parameter dataclass + provenance)
│       └── gsh_redox_model.py  RBCGSHRedoxModel (ODE RHS + constraints)
├── simulation/
│   ├── __init__.py
│   └── engine.py        run_simulation(), list_registered_models()
├── reporting/
│   └── llm_interface.py LLMReportInput / LLMReportOutput (interface only)
└── [future modules...]
```
