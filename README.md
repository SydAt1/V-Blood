# V-Blood

**V-Blood** is a research-oriented platform for mechanistic simulation of biological processes in human blood, with uncertainty quantification, machine-learning integration, and LLM-based scientific interpretation.

> ⚠️ **Research software — pre-alpha.** V-Blood is a hypothesis-generation and model-development tool. It does **not** replace laboratory experiments, clinical trials, or human testing.

---

## Current status: Milestone 4 Complete (v0.4.0)

Milestone 4 introduces the chemical exposure and scenario simulation layer:
- **Task 1: Mechanism preset library (`src/vblood/scenarios/mechanisms.py`):** Typed Pydantic specifications for 5 major toxicological mechanism classes (direct oxidant, GSH conjugator, redox cycler, G6PD/GR enzyme inhibitor, NADPH pool drain) with default-off hooks.
- **Task 2: Curated compound library (`data/processed/compounds.json` & `src/vblood/scenarios/compounds.py`):** Curated database of oxidants, conjugators, and redox cyclers with SMILES/InChIKey validation, SHA-256 integrity verification, and evidence tier grading (`CURATED`, `ESTIMATED`, `UNVERIFIED`).
- **Task 3: Scenario simulation engine (`src/vblood/scenarios/engine.py`):** Multi-compound exposure simulation with configurable profiles (`BOLUS`, `INFUSION`, `REPEATED_PULSES`), G6PD $\alpha$ vulnerability tuning, and dense early transient sampling.
- **Task 4: High-performance cohort simulation (`src/vblood/scenarios/population.py`):** Vectorized RK4 batch simulator executing 1000 cells in under 2 seconds across biological parameter priors, outputting crisis percentages and percentile trajectories.
- **Task 5: Frontend visual-state contract (`src/vblood/reporting/visual_state.py`):** Animation frame schema categorizing biochemical health (`healthy`, `stressed`, `severely_stressed`, `lysis_risk`) derived strictly from modeled variables.
- **Task 6: FastAPI scenario endpoints (`src/vblood/api/`):** REST and Server-Sent Event streaming endpoints (`/compounds`, `/scenarios`, `/scenarios/population`, `/scenarios/{id}/visual`, `/scenarios/{id}/stream`).

---

## Quick start

### Requirements

- Python 3.11+ (tested on Python 3.13)
- uv or pip

### Installation

```bash
git clone <repo-url>
cd v-blood
pip install -e ".[dev]"
```

### Running Simulations & Analysis

1. **Run the baseline demonstration script:**
   ```bash
   python scripts/run_demo.py
   ```

2. **Run local sensitivity analysis:**
   ```bash
   python scripts/run_sensitivity_analysis.py
   ```
   Outputs are saved to `simulation_outputs/sensitivity_tornado.png`, `sensitivity_analysis.csv`, and `sensitivity_analysis.json`.

3. **Run experimental data ingestion pipeline:**
   ```bash
   python scripts/ingest_data.py
   ```
   Processed records written to `data/processed/experimental_records.json`.

4. **Run G6PD deficiency scenario comparison:**
   ```bash
   python scripts/compare_g6pd_deficiency.py
   ```
   Comparison saved to `simulation_outputs/g6pd_deficiency_comparison.csv`.

5. **Start the FastAPI backend:**
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   Interactive OpenAPI documentation available at `http://127.0.0.1:8000/docs`.

### Run tests

```bash
pytest
```
*Currently 148 automated tests passing across unit, scientific, and API test suites.*

---

## Project layout

```
v-blood/
├── docs/                    # Scientific and architectural documentation
├── data/                    # Raw and processed experimental data
├── models/                  # Model registry and versioned artefacts
├── src/vblood/              # Core Python package
│   ├── config.py            # Application configuration
│   ├── schemas/             # Pydantic data models
│   ├── chemistry/           # Chemical identity and descriptor utilities
│   ├── biology/             # Mechanistic biological models
│   │   └── rbc/             # Red blood cell sub-models
│   ├── simulation/          # ODE integration engine
│   ├── parameter_estimation/ # Parameter fitting utilities (planned)
│   ├── machine_learning/    # ML models (planned)
│   ├── uncertainty/         # UQ and applicability domain (planned)
│   ├── validation/          # Scientific validation utilities
│   ├── reporting/           # Structured output and LLM interface contract
│   ├── provenance/          # Experiment and model versioning
│   └── api/                 # FastAPI endpoints
├── tests/                   # Automated tests
├── notebooks/               # Exploratory and demonstration notebooks
└── scripts/                 # Standalone executable scripts
```

---

## Scientific principles

Every implemented reaction has a documented rationale, unit, and parameter provenance. All simulation outputs are clearly distinguished from experimental observations. See [docs/assumptions_and_limitations.md](docs/assumptions_and_limitations.md) for all current limitations.

---

## Licence

MIT
