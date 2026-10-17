# V-Blood

**V-Blood** is a research-oriented computational biology platform for the mechanistic simulation of biochemical processes in human blood, featuring uncertainty quantification, population-scale Monte Carlo analysis, and LLM-powered scientific interpretation grounded in physical equations.

> ⚠️ **Research software - pre-alpha.** V-Blood is a hypothesis-generation and model-development tool. It does **not** replace laboratory experiments, clinical assays, or human testing.

---

## Current Status: Milestone 7 Complete (v0.7.0)

Milestone 7 introduces the **LLM Compound Intelligence and Research-to-Library Pipeline**, an end-to-end autonomous research workstation that investigates novel chemical substances, extracts structured biological evidence, maps them to V-Blood's mechanistic ODE kinetic classes, validates candidates through 10 scientific gates, and dynamically registers approved compounds into the simulation catalog.

### Key Milestone 7 Capabilities

1. **Chemical Identity Resolution (`ChemicalIdentityResolver`):**
   - Authoritative chemical identity retrieval via PubChem PUG REST API (preferred names, synonyms, canonical SMILES, InChIKey, CID, entity classifications).
   - InChIKey checksum and canonical SMILES validation with RDKit and fallback regex.

2. **Literature Retrieval & Prompt-Injection Defense (`LiteratureRetrievalService`):**
   - Multi-source search across Europe PMC and PubMed with erythrocyte-specific keyword prioritization.
   - Cross-source deduplication by DOI, PMID, and title distance.
   - Robust prompt-injection sanitization (`sanitize_retrieved_text`) stripping instructional override attacks from untrusted external abstracts.

3. **Evidence Extraction & Dual-Tier Grading (`EvidenceExtractionService`, `EvidenceGradingService`):**
   - Structured extraction of biological systems, experimental concentrations, exposure durations, observed redox outcomes, and exact grounding quotes.
   - Resilient LLM client with deterministic fallback for 100% CI reproducibility without network reliance.
   - Finding-level and compound-level grading (`CURATED`, `ESTIMATED`, `UNVERIFIED`) evaluating human erythrocyte directness.

4. **Mechanism Mapping & Provenance Tracking (`MechanismMappingService`):**
   - Translates findings into V-Blood's 5 kinetic ODE mechanism classes (`DIRECT_OXIDANT`, `GSH_CONJUGATOR`, `REDOX_CYCLER`, `ENZYME_INHIBITOR`, `NADPH_DRAIN`).
   - Rejects or structures warnings for unmodeled pathways (e.g. DNA alkylation, mitochondrial collapse, whole-body ADME).
   - Assigns explicit parameter provenance (`MEASURED`, `DERIVED`, `INFERRED`, `SYNTHETIC`, `MISSING`).

5. **10-Gate Scientific Validation Engine (`CandidateValidator`):**
   - Strict candidate evaluation across 10 verification gates: Identity Consistency, Schema Integrity, Traceability, Dimensional Consistency, Parameter Provenance, Mechanism Compatibility, Parameter Completeness, Numeric Bounds, Numerical ODE Integration Trial, and Catalog Non-Regression.

6. **Dynamic Library Registration & Lifecycle Persistence (`ResearchRepository`):**
   - State-machine lifecycle: `NEEDS_RESEARCH` → `RESEARCHED` → `CANDIDATE` → `SIMULATION_READY` or `REJECTED`.
   - Immutable revision audit log stored in `data/processed/research_candidates.json`.
   - Dynamic injection into `CompoundLibrary` upon approval; unapproved candidates are blocked from simulation scenarios with HTTP 422.

7. **Field Station Research Workstation (Module 06 Frontend):**
   - React 19 + TypeScript workstation (`CompoundResearchWorkspace`) designed with the signature Field Station editorial aesthetic.
   - Substance intake bench, real-time stage progress tracker, collapsible deep-inspection plates, and editorial approval/rejection actions.

---

## Retrospective: Milestones 1–6

- **Milestone 6 - LLM-Powered Scientific Interpretation:** Dual-provider interpretation architecture (deterministic biochemical engine + external LLM client), $\pm 1\%$ numerical grounding guardrails, zero-latency caching, and bespoke Field Station editorial interpretation plates.
- **Milestone 5 - Blood Playground Frontend Workstation:** Interactive React 19 + Vite interface featuring the Single-Cell Scenario Builder, Population Cohort Visualizer (100–5,000 cells), animated SVG erythrocyte dynamics playback, and session history export.
- **Milestone 4 - Chemical Exposure Scenarios & Compound Library:** Multi-compound mixtures, curated library (`CURATED`, `ESTIMATED`, `UNVERIFIED`), exposure delivery profiles (`BOLUS`, `INFUSION`, `REPEATED_PULSES`), and dense early-time sampling.
- **Milestone 3 - Production FastAPI Platform:** Decoupled REST service with model registry, steady-state initial condition computation, and simulation store.
- **Milestone 2 - Extended Biology & Scientific Validation:** Model `rbc-g6pd-gsh-v2` with G6PD deficiency factor $\alpha \in [0.0, 1.0]$, NADPH cofactor cycling, and validation against published human red blood cell datasets.
- **Milestone 1 - Baseline Mechanistic Simulation Core:** ODE systems biology integration (`scipy.integrate.solve_ivp`), Radau/BDF stiff solvers, baseline model `rbc-gsh-redox-v1`, mass conservation checks, and parameter sensitivity auditing.

*For detailed historical journals and technical designs, see [docs/milestone_journal_and_m6_plan.md](docs/milestone_journal_and_m6_plan.md) and [docs/milestone_7_research_to_library.md](docs/milestone_7_research_to_library.md).*

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

- **Backend Python Suite (212 tests):**
  ```bash
  uv run pytest
  ```
  *(Includes 21 tests dedicated to chemical identity resolution, literature retrieval, evidence extraction, mechanism mapping, candidate validation gates, repository persistence, and research REST endpoints).*

- **Frontend Vitest Suite (22 tests):**
  ```bash
  cd frontend
  npm test
  ```
  *(Includes unit tests for compound research workflow, stage progress bars, dossier inspection, and candidate approval).*

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
