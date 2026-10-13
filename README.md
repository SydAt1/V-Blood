# V-Blood

**V-Blood** is a research-oriented platform for mechanistic simulation of biological processes in human blood, with uncertainty quantification, machine-learning integration, and LLM-based scientific interpretation.

> ⚠️ **Research software — pre-alpha.** V-Blood is a hypothesis-generation and model-development tool. It does **not** replace laboratory experiments, clinical trials, or human testing.

---

## Current status: Milestone 2 Complete

Milestone 2 extends the platform with:
- **Task 1: Steady-state analysis:** Robust algebraic/numerical solver (`SteadyStateSolver`), stability auditing, and explanation of model equilibrium vs. resting physiological drift.
- **Task 2: L2 reference data validation:** Curated reference ranges from human erythrocytes (`data/processed/l2_reference_ranges.json`) and automated validation engine (`L2Validator`).
- **Task 3: Local sensitivity analysis:** Finite-difference parameter sensitivity analyzer for GSH depletion metrics, generating reports and tornado plots (`src/vblood/uncertainty/sensitivity.py`).
- **Task 4: Experimental data ingestion:** Pydantic `ExperimentalRecord` schema, unit conversion module, and immutable SHA-256 verified ingestion pipeline (`scripts/ingest_data.py`).
- **Task 5: FastAPI backend:** Decoupled REST API (`/health`, `/models`, `/simulations`, `/simulations/{run_id}`) without contaminating core biological models (`src/vblood/api/`).
- **Task 6: G6PD kinetic sub-model:** Bi-substrate kinetic rate law with competitive NADPH product inhibition and total pyridine nucleotide pool conservation (`rbc-g6pd-gsh-v2`), supporting in silico deficiency scenarios.

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
