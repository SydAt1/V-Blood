# V-Blood

**V-Blood** is a research-oriented computational biology platform for the mechanistic simulation of biochemical processes in human blood, featuring uncertainty quantification, population-scale Monte Carlo analysis, and LLM-powered scientific interpretation grounded in physical equations.

> ⚠️ **Research software - pre-alpha.** V-Blood is a hypothesis-generation and model-development tool. It does **not** replace laboratory experiments, clinical assays, or human testing.

---

## Current Status: Milestone 6 Complete (v0.6.0)

Milestone 6 introduces **LLM-Powered Scientific Interpretation** coupled with a distinctive **Scientific Editorial Interface**, bridging raw mathematical ODE trajectories with evidence-grounded biochemical memoranda.

### Key Milestone 6 Capabilities

1. **Dual-Provider Interpretation Architecture:**
   - **Deterministic Biochemical Engine (`deterministic-biochemical-v1`):** High-speed rule-based interpreter executing in $<10\text{ ms}$ with zero network calls and zero cost, applying expert haematology rules to $[GSH]_{\min}$, $t_{90\%}$ kinetics, and vehicle control deltas.
   - **External LLM Client Adapter:** Seamless connection to commercial and local model endpoints. Automatically prioritizes **Google Gemini** (`gemini-2.5-flash`, `gemini-1.5-flash`, `gemini-1.5-pro`) via Google's official OpenAI-compatible endpoint with automatic fallback to native REST (`generateContent`), while also supporting OpenAI (`gpt-4o`, `gpt-4o-mini`), Anthropic (`claude-3-5-sonnet`), and local endpoints (Ollama, vLLM, LM Studio).

2. **Automated Grounding Guardrails & Biological Boundaries:**
   - **$\pm 1\%$ Numerical Assertion Verification:** Every cited nadir, depletion percentage, and recovery timescale in the interpretation is cross-checked against actual solver metrics.
   - **Mandatory Research Disclaimers:** Rejects or flags unhedged clinical claims.
   - **Biological Constraint Auditing:** Explicitly detects and prohibits claims violating erythrocyte physiology (e.g. no mitochondria, no nuclear transcription/protein synthesis, no in vivo ADME or renal/hepatic clearance in isolated cell suspensions).
   - **Unverified Compound Warnings:** Enforces explicit caveats whenever experimental xenobiotics lack human erythrocyte literature provenance.

3. **Zero-Latency ID-Indexed Caching:**
   - **Dual-Tier Cache (In-Memory + Disk):** Generated memoranda are indexed by `run_id` (or context hash) and provider mode, persisted to disk under `simulation_outputs/interpretations/`.
   - **Instantaneous Mode Switching (0 ms):** Toggling between **Rule Engine**, **Auto**, and **Live LLM** restores previous responses instantaneously without wiping the UI plate, waiting on network roundtrips, or re-billing API tokens.

4. **Bespoke Scientific Editorial Plate (`InterpretationPlate`):**
   - Designed with a "Computational Biology Field Station" aesthetic (warm parchment tones, archival typography, grounding badges).
   - Structured sections: Executive Summary, Nadir & Kinetics Analysis, Pathway Flux Breakdown, Vehicle Control Deltas, Population Tail Risk ($p_5$ vulnerable subgroup), Lysis Risk Evaluation, Declared Unmodeled Physics, and Suggested Follow-Up Experiments.

5. **REST API Extensions:**
   - `GET /interpret/status`: Telemetry endpoint reporting provider readiness, active model, and declared biological boundaries.
   - `POST /interpret/playground`: Synthesizes single-cell exposure memoranda.
   - `POST /interpret/cohort`: Synthesizes population-scale cohort vulnerability memoranda.

---

## Retrospective: Milestones 1–5

- **Milestone 1 - Baseline Mechanistic Simulation Core:** ODE systems biology integration (`scipy.integrate.solve_ivp`), Radau/BDF stiff solvers, baseline model `rbc-gsh-redox-v1`, mass conservation checks, and parameter sensitivity auditing.
- **Milestone 2 - Extended Biology & Scientific Validation:** Model `rbc-g6pd-gsh-v2` with G6PD deficiency factor $\alpha \in [0.0, 1.0]$, NADPH cofactor cycling, and validation against published human red blood cell datasets.
- **Milestone 3 - Production FastAPI Platform:** Decoupled REST service with model registry, steady-state initial condition computation, and simulation store.
- **Milestone 4 - Chemical Exposure Scenarios & Compound Library:** Multi-compound mixtures, curated library (`CURATED`, `ESTIMATED`, `UNVERIFIED`), exposure delivery profiles (`BOLUS`, `INFUSION`, `REPEATED_PULSES`), and dense early-time sampling.
- **Milestone 5 - Blood Playground Frontend Workstation:** Interactive React 19 + Vite interface featuring the Single-Cell Scenario Builder, Population Cohort Visualizer (100–5,000 cells), animated SVG erythrocyte dynamics playback, and session history export.

*For detailed historical journals and technical designs, see [docs/milestone_journal_and_m6_plan.md](docs/milestone_journal_and_m6_plan.md).*

---

## Quick Start

### 1. Environment Configuration

Copy the template to `.env` in the root directory:
```bash
cp .env.example .env
```

To enable live LLM interpretations, add your **Google Gemini** API key (recommended) or OpenAI key:
```ini
# .env
GEMINI_API_KEY=AIzaSy...
LLM_MODEL=gemini-2.5-flash
```
*(If no API key is set, V-Blood automatically uses the built-in deterministic biochemical rule engine).*

### 2. Start the Backend Server

```bash
# Using uv (recommended)
uv run main.py

# Or using standard python
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
Interactive OpenAPI/Swagger documentation is available at **`http://127.0.0.1:8000/docs`**.

### 3. Start the Frontend Workstation

```bash
cd frontend
npm install
npm run dev
```
Open **`http://localhost:5173`** to access the Blood Playground workstation.

---

## Running Automated Test Suites

Both backend and frontend suites are maintained with 100% passing tests:

- **Backend Python Suite (191 tests):**
  ```bash
  uv run pytest
  ```
  *(Includes 15 tests dedicated to context extraction, guardrail enforcement, deterministic dispatch, and interpretation REST endpoints).*

- **Frontend Vitest Suite (19 tests):**
  ```bash
  cd frontend
  npm test
  ```
  *(Includes unit tests for interpretation plate rendering, mode switching, caching, and guardrail badge states).*

---

## Project Layout

```
v-blood/
├── docs/                             # Scientific documentation, journals, and logs
│   ├── milestone_journal_and_m6_plan.md # Comprehensive Milestone 1–6 journal & architecture
│   └── research_log.md              # Research and implementation timeline
├── data/                             # Raw and processed physiological fixtures
├── models/                           # Versioned model registry definitions
├── simulation_outputs/               # Generated simulation runs and cached memoranda
│   └── interpretations/              # Persistent disk cache of generated memoranda
├── src/vblood/                       # Core computational biology package
│   ├── config.py                     # Environment and secrets configuration
│   ├── schemas/                      # Core Pydantic domain models
│   ├── biology/rbc/                  # Mechanistic kinetic rate laws (GPx, GR, G6PD, Cat)
│   ├── simulation/                   # Stiff ODE numerical solver engine
│   ├── scenarios/                    # Chemical library, kinetic hooks, and cohort generator
│   ├── intelligence/                 # Mechanism compatibility & evidence tier checking
│   ├── interpretation/               # Milestone 6 interpretation engine
│   │   ├── schemas.py                # Interpretation requests, responses, and grounding types
│   │   ├── context.py                # Structured biochemical endpoint extraction
│   │   ├── guardrails.py             # Numerical assertion verifier & biological claim filters
│   │   ├── service.py                # Dual-tier cache and provider dispatch coordinator
│   │   └── providers/
│   │       ├── base.py               # Abstract provider interface
│   │       ├── deterministic.py      # Rule-based expert biochemical engine
│   │       └── llm_client.py         # Google Gemini, OpenAI & Anthropic client adapter
│   └── api/                          # FastAPI REST application and endpoints
├── frontend/                         # Vite + React 19 + TypeScript workstation
│   ├── src/components/               # Editorial UI components (InterpretationPlate, Charts)
│   ├── src/features/                 # Single-cell playground and cohort features
│   └── src/api/                      # Typed REST client with dev proxy
├── tests/                            # Automated test suite
│   ├── unit/test_interpretation.py   # Guardrail, context, and provider tests
│   └── api/test_interpretation_api.py# REST endpoint verification
└── scripts/                          # Standalone computational biology scripts
```

---

## Scientific Principles & Limitations

Every biological rate equation implemented in V-Blood originates from published kinetic literature with explicit parameter provenance.

- **Scope:** Simulates intracellular redox dynamics in isolated human erythrocytes under in vitro conditions.
- **Unmodeled Physics:**
  - No in vivo whole-body pharmacokinetics (ADME), renal clearance, or hepatic metabolism.
  - No glycolysis, ATP/energy charge, or active membrane ion pumps.
  - No physical membrane deformability, shear stresses, or echinocytic morphological changes.
  - Damage index ($D$) and lysis percentage are synthetic mathematical indicators, not clinical diagnostic assays.

See [docs/assumptions_and_limitations.md](docs/assumptions_and_limitations.md) for full documentation of physical boundaries.

---

## License

MIT
