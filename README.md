# V-Blood

**V-Blood** is a research-oriented platform for mechanistic simulation of biological processes in human blood, with uncertainty quantification, machine-learning integration, and LLM-based scientific interpretation.

> ⚠️ **Research software — pre-alpha.** V-Blood is a hypothesis-generation and model-development tool. It does **not** replace laboratory experiments, clinical trials, or human testing.

---

## Current status: Milestone 5 Complete (v0.5.0)

Milestone 5 introduces the **Blood Playground Frontend**: an interactive, production-quality research workstation built with React 19, TypeScript, Vite, and Tailwind CSS.
- **Task 1: Chemical Compound Catalog:** Searchable and filterable chemical catalog with real-time evidence grading (`CURATED`, `ESTIMATED`, `UNVERIFIED`) and literature provenance.
- **Task 2: Single-Cell Scenario Builder & Visualizer:** Configure chemical mixtures, exposure waveforms (`BOLUS`, `INFUSION`, `REPEATED_PULSES`), G6PD $\alpha$ enzymatic activity, parallel baseline control comparisons, and interactive multi-channel time-series charts.
- **Task 3: Heterogeneous Population Cohort Simulator:** Vectorized cohort runs (100 to 5,000 cells) executed in ~1.2s, displaying $p_5 \dots p_{95}$ percentile bands, median trajectories, and model-defined crisis fractions.
- **Task 4: Erythrocyte Dynamics Playback:** Scalable SVG biconcave disc animation with normalized biochemical health states, scrubbing controls, and real-time Server-Sent Events (SSE) streaming.
- **Task 5: Session Run History & Data Export:** Complete local session auditing with CSV and JSON exports for simulation trajectories and provenance.
- **Task 6: Model & Scientific Boundaries:** Transparent documentation of biological scope (no ATP/glycolysis, no unmodeled physical membrane morphology).

---

## Quick start

### Frontend Research Workstation
```bash
# Terminal 1: Start FastAPI Backend
.\.venv\Scripts\python.exe -m uvicorn vblood.api.app:app --reload --host 127.0.0.1 --port 8000

# Terminal 2: Start Vite Frontend
cd frontend
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser to access the Blood Playground workstation.
Interactive OpenAPI/Swagger docs are available at `http://127.0.0.1:8000/docs`.

### Running Automated Test Suites
- **Backend (Python):** `pytest` (176 tests passing across unit, scientific, and API suites)
- **Frontend (TypeScript):** `cd frontend && npm test` (15 tests passing across component and API suites)


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
*Currently 176 automated tests passing across unit, scientific, and API test suites.*

For a comprehensive history of Milestones 1 through 5 and the architecture for Milestone 6, see [docs/milestone_journal_and_m6_plan.md](docs/milestone_journal_and_m6_plan.md).

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
