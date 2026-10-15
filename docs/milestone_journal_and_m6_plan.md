# V-Blood: Milestone Journal (1–5) & Milestone 6 Implementation Plan

**Platform:** V-Blood — Mechanistic Simulation Platform for Human Blood Biology  
**Author:** Computational Biology & Systems Architecture Team  
**Date:** October 2026  
**Status:** Milestones 1–5 Complete (v0.5.0) | Milestone 6 Architecture & Plan Approved  
**Current Baseline Verification:** 176 / 176 Backend Tests Passing | 15 / 15 Frontend Tests Passing  

---

## Table of Contents

1. [Executive Summary & System Philosophy](#1-executive-summary--system-philosophy)
2. [Chronological Progress: Milestones 1 Through 5](#2-chronological-progress-milestones-1-through-5)
   - [Milestone 1: Core Mechanistic Biological Engine](#milestone-1-core-mechanistic-biological-engine)
   - [Milestone 2: Mathematical Rigor, L2 Validation & Decoupled REST Service](#milestone-2-mathematical-rigor-l2-validation--decoupled-rest-service)
   - [Milestone 3: Dynamic Validation, Sensitivity Benchmarks & Experimental Alignment](#milestone-3-dynamic-validation-sensitivity-benchmarks--experimental-alignment)
   - [Milestone 4: Chemical Exposure & Scenario Simulation Engine](#milestone-4-chemical-exposure--scenario-simulation-engine)
   - [Milestone 5: Blood Playground Frontend & Field Station Editorial Redesign](#milestone-5-blood-playground-frontend--field-station-editorial-redesign)
3. [Current Repository State & Authoritative Baseline](#3-current-repository-state--authoritative-baseline)
4. [Milestone 6: LLM-Powered Scientific Interpretation](#4-milestone-6-llm-powered-scientific-interpretation)
   - [Primary Objectives](#primary-objectives)
   - [Scientific Guardrails & Grounding Protocol](#scientific-guardrails--grounding-protocol)
   - [Dual-Provider Architecture (Deterministic Rule Engine & Live LLM Adapter)](#dual-provider-architecture)
   - [Forward-Looking Compound Intelligence Interfaces](#forward-looking-compound-intelligence-interfaces)
   - [Backend REST API Specifications](#backend-rest-api-specifications)
   - [Frontend Editorial UI Integration](#frontend-editorial-ui-integration)
   - [Step-by-Step Implementation Roadmap](#step-by-step-implementation-roadmap)
   - [Verification & Acceptance Criteria](#verification--acceptance-criteria)
5. [Appendix: Scientific Boundaries & Unmodeled Physics](#5-appendix-scientific-boundaries--unmodeled-physics)

---

## 1. Executive Summary & System Philosophy

**V-Blood** is an in silico research workstation dedicated to the mechanistic modeling of human erythrocyte biochemistry under chemical exposures, oxidative stressors, and genetic enzymatic deficiencies (notably Glucose-6-Phosphate Dehydrogenase [G6PD] deficiency).

Human red blood cells (RBCs) lack nuclei, mitochondria, and ribosomes; they cannot synthesize new enzymes in response to acute challenges. Their antioxidant capacity depends almost entirely on the continuous coupling of the **hexose monophosphate shunt (pentose phosphate pathway / PPP)**, which supplies NADPH, and the **glutathione redox cycle**, which reduces toxic peroxides.

```
                  Hexose Monophosphate Shunt (G6PD, 6PGD)
                                │
                              NADPH
                                │
                                ▼
GSSG + 2 H⁺ ─────────── Glutathione Reductase (GR) ───────────► 2 GSH
    ▲                                                             │
    │                                                             ▼
    └─────────── Glutathione Peroxidase (GPx1) ────────────── H₂O₂ ──► 2 H₂O
```

### Core Axioms
1. **Biological Source of Truth:** Mathematical models formulated as Ordinary Differential Equations (ODEs) represent explicit mechanistic hypotheses. All parameter values are tied to published literature or explicitly tagged as `SYNTHETIC`.
2. **Strict Decoupling:** The numerical simulation engine runs as pure, zero-dependency Python code. It does not require web servers, databases, or language models to execute.
3. **Scientific Humility & Transparency:** Model outputs are explicitly identified as *synthetic simulation trajectories*, not experimental measurements or clinical facts. Unmodeled physics (ADME, whole-body pharmacokinetics, membrane morphological spiculation) are surfaced prominently.

---

## 2. Chronological Progress: Milestones 1 Through 5

### Milestone 1: Core Mechanistic Biological Engine
*Target: Establish a reproducible, mathematically rigorous ODE model of erythrocyte glutathione turnover.*

- **Model Specification (`rbc-gsh-redox-v1`):**
  A 5-variable kinetic ODE system tracking:
  - $[\text{GSH}]$: Reduced glutathione (physiological baseline: $1.5\text{--}3.0\text{ mM}$)
  - $[\text{GSSG}]$: Glutathione disulfide (physiological baseline: $0.01\text{--}0.04\text{ mM}$)
  - $[\text{H}_2\text{O}_2]$: Intracellular peroxide (resting baseline: $10\text{--}100\text{ nM}$)
  - $[\text{NADPH}]$: Reducing equivalent cofactor (physiological baseline: $0.01\text{--}0.05\text{ mM}$)
  - $D$: Cumulative oxidative damage index (dimensionless $[0, 1]$, synthetic proxy for membrane stress)
- **Kinetic Formulations:**
  - Bimolecular approximation for Glutathione Peroxidase ($v_{\text{GPx}} = k_{\text{gpx}} [\text{H}_2\text{O}_2] [\text{GSH}]$) based on Flohé (1979) intracellular adaptations.
  - Bi-substrate Michaelis-Menten rate law for Glutathione Reductase ($v_{\text{GR}}$) with parameters derived from Worthington & Rosemeyer (1974).
  - First-order export of oxidized GSSG ($v_{\text{export}} = k_{\text{export}} [\text{GSSG}]$) via MRP1.
- **Engine Infrastructure:**
  - Abstract base class `BiologicalModel` enforcing typed parameter dictionaries, state variable schemas, and analytical right-hand-side evaluations.
  - Integration with SciPy's `solve_ivp` using adaptive Dormand-Prince (RK45) with mass-balance audits and conservation tracking.
- **Verification Baseline:**
  - 55 unit tests + 23 scientific integration tests (78 total) passing 100%.

---

### Milestone 2: Mathematical Rigor, L2 Validation & Decoupled REST Service
*Target: Resolve numerical drift, establish analytical steady-state solvers, ingest literature baselines, and expose headless API endpoints.*

- **Task 1: Steady-State Equilibrium & Drift Root Cause Analysis:**
  - Discovered that unperturbed baseline simulations drifted over hours due to glutathione pool mass-balance constraints:
    $$[\text{GSSG}]^* = \frac{k_{\text{synth}}}{2 \cdot k_{\text{export}}} \approx 1.25 \times 10^{-4}\text{ mM}$$
  - Implemented `SteadyStateSolver` combining analytical equilibrium derivation, non-linear optimization (`scipy.optimize.root`), and Jacobian eigenvalue analysis to prove asymptotic Lyapunov stability ($\operatorname{Re}(\lambda_i) < 0$).
- **Task 2: L2 Physiological Reference Range Ingestion:**
  - Ingested curated human clinical and biochemical reference intervals from Sies (1999), Anderson (1998), Gaetani (1994), and Antunes & Cadenas (2000) into `data/processed/l2_reference_ranges.json`.
  - Built `L2Validator` to mathematically evaluate whether steady-state resting equilibria conform to known human physiological bounds.
- **Task 3: Local Sensitivity Analysis (UQ):**
  - Built finite-difference sensitivity module computing normalized sensitivity coefficients ($S_{i,j} = \frac{\partial \ln Y_i}{\partial \ln P_j}$) for critical endpoints: minimum $[\text{GSH}]$, maximum $[\text{H}_2\text{O}_2]$, and $50\%$ recovery time.
  - Generated automated sensitivity tornado charts (`simulation_outputs/sensitivity_tornado.png`) proving that $k_{\text{gpx}}$, $v_{\max,\text{gr}}$, and $k_{\text{export}}$ dominate acute oxidative response.
- **Task 4: Immutable Data Ingestion Pipeline:**
  - Created Pydantic schema `ExperimentalRecord` with complete provenance (DOI, chemical identifiers, assay conditions, confidence tiers).
  - Built automated unit conversion engine ($\mu\text{M} \to \text{mM}$, $\text{nM} \to \text{mM}$) and immutable SHA-256 integrity verification.
- **Task 5: Decoupled FastAPI Web Service:**
  - Exposed REST endpoints (`GET /health`, `GET /models`, `POST /simulations`, `GET /simulations/{run_id}`) without contaminating core biological models with web dependencies.
- **Task 6: Bi-Substrate G6PD Kinetic Model (`rbc-g6pd-gsh-v2`):**
  - Replaced empirical PPP surrogate with a mechanistic bi-substrate rate law incorporating product inhibition by NADPH and pyridine nucleotide pool conservation:
    $$[\text{NADP}^+] = \max(0, [\text{NADP}]_{\text{tot}} - [\text{NADPH}])$$
  - Enabled genetic deficiency profiling via enzymatic scaling factor $\alpha \in [0.0, 1.0]$.
- **Test Suite Status:** Suite expanded from 78 to 148 passing tests.

---

### Milestone 3: Dynamic Validation, Sensitivity Benchmarks & Experimental Alignment
*Target: Calibrate dynamic responses against published in vitro time-courses and benchmark non-linear perturbation responses.*

- **Dynamic Time-Series Matching (L3 Validation):**
  - Benchmarked simulated $[\text{GSH}]$ depletion and clearance kinetics against Gaetani et al. (1994) in vitro challenge datasets.
  - Verified dynamic clearance trajectories under bolus peroxide doses ranging from $0.05\text{ mM}$ to $0.50\text{ mM}$.
- **Uncertainty & Kinetic Bounds:**
  - Established formal distinction between epistemic uncertainty (imprecisely measured enzyme kinetic rates) and biological variance (cell-to-cell enzyme capacity across human populations).
  - Calibrated bounds on synthetic damage rate constants ($k_{\text{damage}}$, $k_{\text{repair}}$) to prevent numerical instability under extreme oxidant loads.

---

### Milestone 4: Chemical Exposure & Scenario Simulation Engine
*Target: Bridge chemical toxicological libraries to mechanistic ODE models and enable heterogeneous population cohort simulations.*

- **Five Mechanistic Kinetic Classes (`src/vblood/scenarios/mechanisms.py`):**
  1. **Direct Oxidant:** Continuous infusion or bolus injection of $\text{H}_2\text{O}_2$.
  2. **GSH Conjugator:** Electrophilic depletion of $[\text{GSH}]$ without disulfide ($[\text{GSSG}]$) formation (e.g. CDNB, NEM, Acetaminophen-NAPQI proxy).
  3. **Redox Cycler:** Catalytic oxidation consuming $[\text{NADPH}]$ to generate $[\text{H}_2\text{O}_2]$ (e.g. Menadione, Doxorubicin, Primaquine-metabolite proxies).
  4. **Enzyme Inhibitor:** Competitive or non-competitive inhibition of G6PD or GR (e.g. DHEA, 6-AN).
  5. **NADPH Drain:** Direct non-redox xenobiotic consumption of reducing equivalents.
- **Curated Compound Catalog & Evidence Grading:**
  - Built `data/processed/compounds.json` with three-tier evidence badges:
    - `CURATED`: High-confidence literature parameters (e.g. $\text{H}_2\text{O}_2$, Menadione, CDNB, NEM).
    - `ESTIMATED`: Extrapolated from analogous quinone or in vitro cellular models (e.g. Primaquine 5,6-orthoquinone).
    - `UNVERIFIED`: Synthetic placeholder or exploratory xenobiotic (e.g. Xenobiotic X-101). Scenarios involving unverified compounds are automatically flagged and excluded from formal validation scoring.
- **Exposure Waveform Generator:**
  - Supported multiple delivery kinetics: instantaneous `BOLUS`, zero-order continuous `INFUSION`, and periodic `REPEATED_PULSES`.
- **Vectorized Monte Carlo Population Simulator (`src/vblood/scenarios/population.py`):**
  - Executes heterogeneous virtual cohorts ($N = 100 \dots 5000$ cells) with log-normal biological parameter variance ($\text{CV} \approx 15\text{--}25\%$) across $V_{\max,\text{GR}}$, $k_{\text{gpx}}$, and basal G6PD activity.
  - Optimized with NumPy vectorization: 1,000 cells simulated in $\approx 1.2\text{ seconds}$.
  - Computes time-resolved percentile bands ($p_5, p_{25}, p_{50}, p_{75}, p_{95}$) and subpopulation crisis fractions.
- **Biochemical Visual-State Classifier:**
  - Trajectories categorized into four physiological states: `healthy`, `stressed`, `severely_stressed`, and `lysis_risk` (proxy for membrane collapse).

---

### Milestone 5: Blood Playground Frontend & Field Station Editorial Redesign
*Target: Deliver a production-quality, responsive research workstation and elevate its visual language to a bespoke scientific instrument.*

- **Interactive Research Workstation (React 19 + TypeScript + Vite):**
  - **Module 1: Chemical Compound Catalog:** Searchable monograph ledger with SMILES, InChIKey, kinetic mechanisms, and evidence badges.
  - **Module 2: Formulation Bench (Scenario Builder):** Multi-compound mixture exposures, waveform configuration, G6PD $\alpha$ slider, and parallel unperturbed vehicle control comparisons.
  - **Module 3: Heterogeneous Population Cohort Simulator:** Parameterized cohort runs with interactive shaded percentile envelopes ($p_5 \dots p_{95}$) and crisis statistics.
  - **Module 4: Erythrocyte Dynamics Playback:** Dynamic SVG biconcave disc visualizer with normalized biochemical stress coloring, timeline scrubbing, and Server-Sent Events (SSE) streaming.
  - **Module 5: Session Run History & Model Dossiers:** Local session audit logbook with full JSON and CSV trajectory export capabilities.
- **Editorial Redesign — The "Computational Biology Field Station":**
  - *Palette:* Warm mineral/parchment surfaces (`#F5F2EB`, `#EBE7DD`, `#FFFFFF`) with crisp carbon boundaries (`#DDD7CD`, `#2D2A26`) and deep biological accents (arterial red `#9E2A2B`, deep copper `#B3541E`, spruce `#2D5A4C`).
  - *Typography:* Newsreader serif for titles, section headers, and hero metrics ($[GSH]_{\min}$ nadir); Plus Jakarta Sans for UI controls and forms; JetBrains Mono for telemetry, parameters, and mathematical symbols.
  - *Cartography & Charts:* Calibrated SVG time-series charts with crisp grid lines, distinct dash arrays, and hover crosshair readouts.
- **Verification Baseline:**
  - 176 backend unit, scientific, and API tests passing.
  - 15 frontend component and API tests passing.
  - Clean production build with 0 TypeScript warnings.

---

## 3. Current Repository State & Authoritative Baseline

| Subsystem | Location | Current Capabilities | Status |
|---|---|---|---|
| **Biological Models** | `src/vblood/biology/` | `rbc-gsh-redox-v1`, `rbc-g6pd-gsh-v2` with G6PD bi-substrate kinetics | Verified (L0, L1, L2) |
| **Solvers & Stability** | `src/vblood/simulation/` | Adaptive RK45 integrator, analytical SteadyStateSolver, Jacobian audit | Verified (100% stable) |
| **Scenario Engine** | `src/vblood/scenarios/` | 5 mechanism classes, 3 exposure waveforms, Monte Carlo population cohort ($N \le 5000$) | Verified |
| **REST API** | `src/vblood/api/` | `/health`, `/models`, `/simulations`, `/compounds`, `/scenarios`, `/scenarios/population` | Verified (FastAPI) |
| **Frontend UI** | `frontend/src/` | 5-module Field Station workstation (Catalog, Scenario, Population, Viewer, History) | Verified (React 19) |
| **Interpretation Interface** | `src/vblood/reporting/` | Initial typed contracts (`LLMReportInput`, `LLMReportOutput`) | Contract Stub |

```
Current Test Suite Metrics:
├── Python Backend: 176 passed in ~45s (0 failures, 0 warnings)
└── Frontend:       15 passed in ~3s (0 failures, 0 TypeScript errors)
```

---

## 4. Milestone 6: LLM-Powered Scientific Interpretation

### Primary Objectives

Milestone 6 transforms raw numerical trajectories and population distributions into **context-rich, biologically rigorous scientific memoranda**.

1. **Playground Single-Cell Interpretation:** Generate structured explanations of dynamic single-cell redox trajectories, linking minimum $[GSH]$ nadirs, $[H_2O_2]$ peaks, recovery times ($t_{90\%}$), and cumulative damage ($D$) to underlying kinetic reactions.
2. **Cohort Population Interpretation:** Generate epidemiological and pharmacological synthesis of heterogeneous cohort simulations, analyzing subpopulation vulnerability across the $p_5 \dots p_{95}$ envelope and quantifying hemolytic crisis risk under genetic deficiencies.
3. **Strict Scientific Grounding & Hallucination Prevention:** Enforce mathematical and factual consistency. Every numerical statement must tie to verified simulation endpoints; all unverified xenobiotics and unmodeled biology must be transparently declared.
4. **Dual-Provider Architecture:** Guarantee **100% offline reproducibility and CI test reliability** via an algorithmic deterministic biochemical engine, while supporting live LLMs (OpenAI, Anthropic, or local endpoints) when API credentials are provided.
5. **Field Station Editorial UX:** Integrate interpretation memoranda directly into the redesigned scientific interface as elegant archival report plates.

---

### Scientific Guardrails & Grounding Protocol

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Simulation Result (Playground or Cohort)             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   Structured Context Builder                           │
│  - Extracts exact numerical endpoints (min GSH, max H2O2, t90, p5-p95) │
│  - Gathers compound evidence tiers (CURATED, ESTIMATED, UNVERIFIED)    │
│  - Appends model assumptions and unmodeled physics catalogue          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   Interpretation Engine Execution                      │
│     [Deterministic Biochemical Engine]  OR  [External LLM Adapter]     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   Grounding & Verification Guardrails                  │
│  1. Numerical Consistency Check (values within ±1% of simulation)      │
│  2. Directional Integrity (e.g. GSH cannot increase during oxidant peak)│
│  3. Compulsory Unmodeled Physics Disclaimer Injection                  │
│  4. Compulsory Unverified Compound Warning Injection                   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   Verified Scientific Memorandum                       │
└────────────────────────────────────────────────────────────────────────┘
```

#### Mandatory Safeguards
- **Zero Hallucination Tolerance on Metrics:** Any claim regarding minimum $[GSH]$, time to recovery, or population crisis percentage is cross-checked against the raw simulation output. If a discrepancy exceeds $1\%$, the guardrail flags or corrects the claim.
- **Evidence Grading Warnings:** If any exposure includes an `UNVERIFIED` chemical (e.g., Xenobiotic X-101), the report must explicitly state: *"This scenario incorporates unverified chemical parameters lacking experimental erythrocyte validation. Results are exploratory hypotheses only."*
- **Unmodeled Physics Declaration:** Every report must conclude with standard model boundary reminders: *no in vivo pharmacokinetics (ADME), no ATP/glycolysis, and damage index $D$ is a mathematical surrogate, not an in vitro osmotic fragility measurement.*

---

### Dual-Provider Architecture

To guarantee that the software functions in air-gapped laboratory computers, CI runners, and environments without commercial API keys, Milestone 6 implements a dual-provider strategy:

```
                          ┌───────────────────────────┐
                          │   InterpretationManager   │
                          └─────────────┬─────────────┘
                                        │
                 ┌──────────────────────┴──────────────────────┐
                 ▼                                             ▼
  ┌─────────────────────────────┐               ┌─────────────────────────────┐
  │ DeterministicBiochemical    │               │ ExternalLLMProvider         │
  │ Provider (Default / CI)     │               │ (OpenAI / Anthropic)        │
  ├─────────────────────────────┤               ├─────────────────────────────┤
  │ • Algorithmic rule engine   │               │ • High-capability synthesis │
  │ • Zero external network     │               │ • Context-window grounded   │
  │ • 100% deterministic tests  │               │ • Graceful fallback on fail │
  │ • Full biochemical depth    │               │ • Strictly validated by     │
  │ • Instant execution (<10ms) │               │   local guardrails          │
  └─────────────────────────────┘               └─────────────────────────────┘
```

#### 1. Deterministic Biochemical Provider (`DeterministicBiochemicalProvider`)
An expert rule-based interpretation system that:
- Categorizes redox dynamics using biological threshold heuristics ($[GSH]_{\min} < 0.25\text{ mM}$ indicates severe oxidative exhaustion).
- Diagnoses the kinetic bottlenecks (e.g., G6PD capacity limitation vs. GPx saturation vs. NADPH depletion).
- Synthesizes cohort vulnerability and tail-risk comparisons between control and challenged populations.
- Operates instantly with zero latency, zero API costs, and 100% reproducible test assertions.

#### 2. External LLM Provider (`ExternalLLMProvider`)
An adapter utilizing modern foundational models:
- Formulates a system prompt embedded with the V-Blood domain ontology, physical boundaries, and raw simulation telemetry.
- Enforces JSON structured outputs adhering to Pydantic schemas.
- Routes through the `GroundingGuardrail` before surfacing to users. If the external API fails, times out, or returns invalid schemas, the manager falls back to the deterministic provider without interrupting the user.

---

### Forward-Looking Compound Intelligence Interfaces

To support future milestones (such as proposed compound evaluation and registration) without destabilizing the current verified compound library:
- **Zero Invasive Writes:** Milestone 6 will **not** modify `data/processed/compounds.json` at runtime or autonomously inject untested compounds into biological equations.
- **Clean Extensibility Interfaces:** A dedicated package `src/vblood/intelligence/` will define:
  - `CompoundCompatibilityChecker`: Reusable protocols for testing whether a chemical mechanism class is supported by the active ODE models.
  - `EvidenceGradingProtocol`: Formal rules for grading chemical literature into `CURATED`, `ESTIMATED`, and `UNVERIFIED`.

---

### Backend REST API Specifications

Milestone 6 introduces three endpoints under the `/interpret` route namespace:

#### 1. `POST /interpret/playground`
Generates a structured scientific report for a single-cell playground simulation run.
- **Request Body:**
  ```json
  {
    "run_id": "sim_20261015_001",
    "scenario": { ... },
    "result": { ... },
    "control_result": { ... },
    "provider_preference": "auto"
  }
  ```
- **Response Schema (`SingleRunInterpretationResponse`):**
  - `executive_summary`: High-level plain-language biological outcome.
  - `nadir_analysis`: Detailed breakdown of $[GSH]$ nadir, $[H_2O_2]$ peak, and recovery trajectory.
  - `mechanistic_pathway_breakdown`: Specific enzymatic analysis (flux through GPx, GR, G6PD).
  - `control_comparison`: Differential impact compared to unperturbed control.
  - `model_uncertainty_and_limitations`: Documented caveats and synthetic parameters.
  - `suggested_experiments`: Actionable wet-lab assays to test the generated hypothesis (e.g. spectrophotometric GSH recycling assay, catalase inhibition test).
  - `provider_used`: `"deterministic"` or `"llm:<model_name>"`.
  - `guardrail_status`: Validation status of numerical claims.

#### 2. `POST /interpret/cohort`
Generates a cohort synthesis report for a heterogeneous population simulation.
- **Request Body:**
  ```json
  {
    "cohort_result": { ... },
    "scenario": { ... },
    "provider_preference": "auto"
  }
  ```
- **Response Schema (`CohortInterpretationResponse`):**
  - `executive_summary`: Population-level vulnerability overview.
  - `variance_and_tail_risk`: Analysis of the $p_5 \dots p_{95}$ envelope and susceptible outliers.
  - `g6pd_deficiency_interaction`: Interaction between chemical stress and genetic enzyme variant.
  - `lysis_risk_assessment`: Breakdown of the predicted crisis fraction.
  - `limitations_disclaimer`: Unmodeled whole-body pharmacokinetics notice.

#### 3. `GET /interpret/status`
Returns the status of available interpretation providers, active LLM API keys (masked), and guardrail configuration.

---

### Frontend Editorial UI Integration

In keeping with the "Computational Biology Field Station" visual language, interpretation reports will be rendered as **archival scientific memoranda**:

1. **Playground Results Integration (`ScenarioResults.tsx`):**
   - Appended below the hero metrics and SVG time-series chart.
   - Designed as an editorial memo card with warm ivory background, Newsreader serif headers, and structured analytical blocks:
     - *Executive Finding*
     - *Enzyme Flux & Kinetic Bottlenecks*
     - *Differential Control Delta*
     - *Experimental Follow-up Suggestions*
   - Badges indicating whether the interpretation was derived via the Deterministic Engine or Live LLM.
2. **Cohort Analysis Integration (`PopulationResults.tsx`):**
   - Appended alongside the population distribution metrics and percentile charts.
   - Displays subpopulation vulnerability breakdowns and Monte Carlo tail-risk synthesis.
3. **Interactive Re-Interpretation & Loading States:**
   - Dedicated "Generate Scientific Interpretation" action button with elegant typographic loading states.
   - Transparent display of guardrail verification status.

---

### Step-by-Step Implementation Roadmap

```
Phase 1: Architecture & Schemas (Backend)
├── Create src/vblood/interpretation/schemas.py (Pydantic contracts)
├── Create src/vblood/interpretation/context.py (Prompt & context assembler)
└── Create src/vblood/interpretation/guardrails.py (Numerical grounding validator)

Phase 2: Provider Engines (Backend)
├── Create src/vblood/interpretation/providers/base.py (Abstract interface)
├── Create src/vblood/interpretation/providers/deterministic.py (Rule-based engine)
├── Create src/vblood/interpretation/providers/llm_client.py (OpenAI / Anthropic adapter)
├── Create src/vblood/interpretation/service.py (Orchestrator & fallback manager)
└── Create src/vblood/intelligence/compatibility.py (Forward-looking compound interfaces)

Phase 3: REST API Endpoints (Backend)
├── Expose POST /interpret/playground in src/vblood/api/app.py
├── Expose POST /interpret/cohort in src/vblood/api/app.py
├── Expose GET /interpret/status in src/vblood/api/app.py
└── Write unit & integration tests (tests/unit/test_interpretation.py, tests/api/test_interpret_api.py)

Phase 4: Frontend Client & Component Integration
├── Extend frontend/src/types/api.ts with interpretation contracts
├── Add API client methods in frontend/src/api/client.ts
├── Build InterpretationPlate.tsx component in frontend/src/components/
├── Integrate into ScenarioResults.tsx (Playground single-cell view)
├── Integrate into PopulationResults.tsx (Cohort population view)
└── Add frontend Vitest tests in frontend/src/test/interpretation.test.tsx

Phase 5: Full System Verification & Review
├── Run full backend pytest suite (176 existing + new tests)
├── Run frontend vitest suite and npm run build
└── Capture visual verification of interpretation plates in browser
```

---

### Verification & Acceptance Criteria

1. **Numerical Faithfulness:**
   - Evaluated $[GSH]_{\min}$, peak $[H_2O_2]$, and recovery times in generated text must match simulation output values within a $1\%$ tolerance window.
   - Zero hallucinated chemical entities or unmodeled pathways (e.g. no claims regarding ATP or DNA repair).
2. **Deterministic Baseline Coverage:**
   - All backend interpretation tests pass without requiring any network connectivity or environment API keys.
3. **Graceful Degradation:**
   - When an invalid or expired API key is provided, the service logs a clear warning and seamlessly falls back to the deterministic provider without throwing a 500 error.
4. **Editorial Visual Consistency:**
   - The UI components adhere strictly to the "Computational Biology Field Station" design system (Newsreader serif, warm parchment card `#FFFFFF`/`#F5F2EB`, border `#DDD7CD`, JetBrains Mono metadata).
5. **Zero Regression:**
   - All 176 pre-existing backend tests and 15 frontend tests continue to pass without modification to core biological ODE equations.

---

## 5. Appendix: Scientific Boundaries & Unmodeled Physics

To maintain scientific integrity across all user touchpoints and automated interpretations, the following boundaries remain permanent constraints of the V-Blood platform:

1. **In Vitro Suspension Boundary:** V-Blood simulates isolated, washed erythrocytes suspended in an aqueous medium. It does not model whole-body pharmacokinetics (ADME), hepatic cytochrome P450 metabolism, plasma protein binding, or renal clearance.
2. **Metabolic Scope Boundary:** The present models (`rbc-gsh-redox-v1`, `rbc-g6pd-gsh-v2`) simulate the hexose monophosphate shunt and glutathione redox cycle. They do **not** simulate Embden-Meyerhof glycolysis, 2,3-diphosphoglycerate (2,3-BPG) synthesis, or ATP-dependent ion transport pumps.
3. **Membrane Morphology Boundary:** The platform renders dynamic erythrocyte discs for visual engagement, but physical cellular deformations (echinocytic spiculation, stomatocytosis, spherocytic swelling) are **not** simulated physically.
4. **Damage Index Heuristic ($D$):** The cumulative damage metric $D$ and corresponding "lysis risk" are synthetic mathematical proxies for cellular exhaustion; they are not direct readouts of mechanical osmotic fragility or clinical intravascular hemolysis.
