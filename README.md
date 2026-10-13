# V-Blood

**V-Blood** is a research-oriented platform for mechanistic simulation of biological processes in human blood, with uncertainty quantification, machine-learning integration, and LLM-based scientific interpretation.

> ⚠️ **Research software — pre-alpha.** V-Blood is a hypothesis-generation and model-development tool. It does **not** replace laboratory experiments, clinical trials, or human testing.

---

## Current status: Milestone 1

Milestone 1 implements the minimal scientifically defensible mechanistic simulation of red blood cell (RBC) oxidative stress using a well-parameterised glutathione redox ODE model.

See [docs/project_overview.md](docs/project_overview.md) for the full vision and [docs/scientific_scope.md](docs/scientific_scope.md) for the biological scope.

---

## Quick start

### Requirements

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

```bash
# Clone and enter the repository
git clone <repo-url>
cd v-blood

# Install with uv (creates a virtual environment automatically)
uv sync --all-extras

# Or with pip
pip install -e ".[dev]"
```

### Run the demo

```bash
python scripts/run_demo.py
```

### Run tests

```bash
pytest tests/ -v
```

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
