# Research Log — V-Blood

This log records scientific decisions, model changes, and evidence reviews in chronological order.

---

## 2026-10-13 — Milestone 1 inception

### Scientific feasibility investigation

**Objective:** Determine whether an RBC oxidative-stress ODE model is a defensible starting point for V-Blood Milestone 1.

**Models surveyed:**
- Mulquiney & Kuchel (1999) — Comprehensive RBC glycolysis model with partial glutathione treatment. Useful reference; GSH sub-model requires extension.
- Nakayama et al. (2005) — E-Cell implementation adding H2O2 challenge and GSH/GSSG dynamics. Most directly relevant published kinetic ODE model.
- BioModels MODEL2410170001 (RBC-GEM) — Genome-scale FBA model. Not suitable for ODE integration.
- BioModels MODEL1106080000 (iAB-RBC-283) — Constraint-based stoichiometric model. Not suitable for ODE integration.

**Decision:** Implement a 5-variable ODE model (GSH, GSSG, H2O2, NADPH, D) inspired by the Nakayama/Kuchel framework. Use literature-derived kinetic parameters. Do not copy equations without independent verification.

**Key parameter decisions:**
- `k_gpx = 50 mM⁻¹ s⁻¹`: Based on Flohé 1979 catalogue value (5×10⁷ M⁻¹s⁻¹), reduced to reflect effective intracellular rate (macromolecular crowding, enzyme concentration per cell water volume). High uncertainty (×5).
- `vmax_gr = 2.4×10⁻³ mM s⁻¹`: From Worthington & Rosemeyer 1974 (direct measurement), normalised to intracellular volume.
- `k_gpx` unit conversion note: The in vitro rate constant (M⁻¹s⁻¹) cannot be directly applied in a whole-cell ODE model in mM units without accounting for the actual intracellular enzyme concentration per unit cell volume. This is an acknowledged limitation.

**H2O2 physiology note:**
- Corrected initial H2O2 from 1 µM to 0.1 µM (0.0001 mM) following literature review.
- Sources: Antunes & Cadenas (2000); Winterbourn & Metodiewa (1999) — intracellular H2O2 in resting erythrocytes is ~10–100 nM.

**Damage index:**
- Parameters k_damage and k_repair are explicitly labelled SYNTHETIC. They have no experimental calibration.
- The Hill-type haemolysis function uses these SYNTHETIC parameters. It is a software placeholder only.

### Software implementation

**Architecture:** 
- BiologicalModel ABC → RBCGSHRedoxModel → simulation engine → Pydantic schemas → API (planned)
- Engine callable without any infrastructure (db, API, LLM)

**Tests written:** 55 unit tests + 23 scientific integration tests = 78 tests total.

**Test results (2026-10-13):**
- Unit tests: 55/55 PASSED (0.27s)
- Scientific tests: 23/23 PASSED (59.56s)
- Full suite: 78/78 PASSED

### Open scientific questions

1. What is the effective intracellular k_gpx per unit cell water? Requires measurement of GPx1 enzyme content per cell plus in-cell activity data.
2. Is the simplified NADPH source term (PPP surrogate) appropriate for G6PD-deficiency studies?
3. Can the damage index be linked to any experimental assay (e.g., MDA, LDH release)?
4. What experimental haemolysis time-course dataset should be used for L3 validation?

### Next planned steps

1. Ingest published RBC GSH/GSSG measurements for L2 steady-state validation. (Done in Task 2)
2. Add sensitivity analysis module (local + global).
3. Implement G6PD/PPP sub-model as a separate biology module.
4. Begin data architecture for experimental records.

---

## 2026-10-13 — Milestone 2: Tasks 1 & 2 Execution

### Task 1: Steady-State Solver and Drift Investigation
- **Drift Root Cause Identified & Mathematically Proven:**
  - Glutathione pool mass balance strictly enforces $[GSSG]^* = k_{\text{synth}} / (2 k_{\text{export}}) = 1.25 \times 10^{-4}$ mM ($0.125\ \mu$M), which is $\sim 200\times$ lower than resting physiological levels ($0.010\text{--}0.040$ mM).
  - GR substrate saturation is limited by this minute $[GSSG]^*$, capping GR turnover to $\sim 4.99 \times 10^{-6}$ mM/s.
  - PPP product inhibition forces $[NADPH]^*$ to accumulate to $9.01$ mM to balance the tiny GR sink.
  - GPx turnover is limited by mass balance, forcing $[GSH]^*$ down to $1.99\ \mu$M and $[H_2O_2]^*$ to $75.1$ nM.
- **Implementation:** Created reusable `SteadyStateSolver` in `src/vblood/simulation/steady_state.py` with analytical derivation, numerical root-finding, Jacobian eigenvalue stability checks, and automatic plausibility auditing.
- **Workflow Integration:** Simulations default to equilibrium initialization unless explicit initial conditions are provided.

### Task 2: Ingest L2 Validation Data
- **Reference Ingestion:** Created `src/vblood/validation/reference_data.py` and `data/processed/l2_reference_ranges.json` with curated literature values (Sies 1999, Anderson 1998, Giustarini 2013, Antunes & Cadenas 2000, Gaetani 1994).
- **Validation Engine:** Created `src/vblood/validation/l2_validator.py` with `L2Validator` and `validate_l2()` assessing state variables against strict ranges and failure criteria.
- **Test Suite:** Added 28 new tests (106 tests total across unit and scientific suites). All 106 tests pass.

---

## 2026-10-13 — Milestone 2: Tasks 3–6 Execution

### Task 3: Local Sensitivity Analysis
- **Module:** Created `src/vblood/uncertainty/sensitivity.py` implementing finite-difference local sensitivity analysis around the physiological steady-state baseline.
- **Metrics Supported:** Maximum fractional GSH depletion ($D_{\max}$), minimum GSH concentration, fractional depletion at arbitrary time $t$, and 50% recovery time.
- **Robustness & Provenance:** Handled zero baseline outputs, relative vs absolute perturbations, verified baseline restoration without modifying parameters in-place, and tracked parameter evidence tiers.
- **Visualization:** Produced ranked tornado plot `simulation_outputs/sensitivity_tornado.png` and tabular outputs in JSON/CSV. Top sensitive parameters under 0.05 mM H2O2 challenge: $k_{\text{gpx}}$, $v_{\max,\text{gr}}$, $k_{\text{rem}}$, $k_{\text{synth}}$, $k_{\text{export}}$.

### Task 4: ExperimentalRecord Schema and Immutable Ingestion Pipeline
- **Pydantic Schema:** Created `src/vblood/schemas/experimental_record.py` containing complete metadata (Record ID, study DOI, sample compartment, chemical CID/InChIKey, experimental conditions, assay method, uncertainty).
- **Unit Conversion:** Implemented `src/vblood/data/unit_conversion.py` supporting deterministic conversions ($\mu\text{M} \to \text{mM}$, $\text{nM} \to \text{mM}$, $\text{fraction} \to \%$) without inferring missing data.
- **Pipeline:** Implemented `src/vblood/data/pipeline.py` enforcing SHA-256 pre/post immutability verification, duplicate detection, and structured summary reporting. Ingested published literature observations and synthetic challenge fixtures into `data/processed/`.

### Task 5: FastAPI Backend
- **Service Architecture:** Implemented `src/vblood/api/app.py` and `storage.py` with endpoints:
  - `GET /health`: Service health and version status.
  - `GET /models`: Model registry metadata and state variable schemas.
  - `POST /simulations`: Synchronous execution with schema validation, parameter bounds checking, and steady-state default initial conditions.
  - `GET /simulations/{run_id}`: Trajectory retrieval with structured 404 handling.
- **Clean Decoupling:** Standalone Python simulation engine remains 100% independent of FastAPI and ASGI server.

### Task 6: G6PD Kinetic Sub-Model (`rbc-g6pd-gsh-v2`)
- **Biological Rationale:** Replaced the uncoupled simplified PPP surrogate with an evidence-grounded bi-substrate rate law (Option A):
  $$v_{\text{G6PD}} = \alpha \cdot \frac{V_{\max,\text{G6PD}} \cdot [\text{G6P}] \cdot [\text{NADP}^+]}{K_{m,\text{G6P}} K_{m,\text{NADP}^+} (1 + [\text{NADPH}]/K_{i,\text{NADPH}}) + \dots}$$
- **Pool Conservation:** Coupled with total pyridine nucleotide conservation $[\text{NADP}^+] = \max(0, [\text{NADP}]_{\text{tot}} - [\text{NADPH}])$.
- **Deficiency Scenarios:** Simulated across $\alpha \in \{1.0, 0.5, 0.1, 0.0\}$. Under 0.05 mM H2O2 bolus, severe reduction ($\alpha=0.1$) causes minimum [NADPH] to plunge from 0.0339 mM down to 0.0146 mM, demonstrating impaired glutathione regeneration capacity.
- **Regression Assurance:** Milestone 1 baseline model (`rbc-gsh-redox-v1`) preserved identically without side effects.
---

## 2026-10-14 — Milestone 3: Dynamic Validation, Sensitivity Benchmarks & Experimental Alignment
- **Dynamic In Vitro Validation (L3):** Benchmarked $[GSH]$ clearance trajectories against Gaetani et al. (1994) in vitro challenge datasets ($0.05\text{--}0.50$ mM $H_2O_2$ boluses).
- **Epistemic vs Aleatoric Separation:** Formalized parameter variance bounds for Monte Carlo cohort sampling.
- **Damage Index Bounds:** Calibrated synthetic rate constants ($k_{\text{damage}}$, $k_{\text{repair}}$) to prevent numerical divergence under severe oxidant loads.

---

## 2026-10-15 — Milestone 4: Chemical Exposure & Scenario Simulation Engine
- **Mechanism Classes:** Implemented 5 kinetic mechanism classes in `src/vblood/scenarios/mechanisms.py` (Direct Oxidant, GSH Conjugator, Redox Cycler, Enzyme Inhibitor, NADPH Drain).
- **Compound Catalog & Evidence Grading:** Curated chemical entries in `data/processed/compounds.json` with three-tier evidence badges (`CURATED`, `ESTIMATED`, `UNVERIFIED`). Automatic validation exclusion flag for unverified xenobiotics.
- **Waveform Delivery:** Supported `BOLUS`, `INFUSION`, and `REPEATED_PULSES` temporal exposure profiles.
- **Vectorized Monte Carlo Population Simulator:** Implemented in `src/vblood/scenarios/population.py` simulating $N = 100 \dots 5000$ cells with log-normal parameter variance in ~1.2s. Output percentile envelopes ($p_5 \dots p_{95}$) and subpopulation crisis fractions.
- **Visual State Classifier:** Implemented 4 biochemical cell states (`healthy`, `stressed`, `severely_stressed`, `lysis_risk`).

---

## 2026-10-15 — Milestone 5: Blood Playground Frontend & Field Station Editorial Redesign
- **Interactive Workstation (React 19 + TypeScript + Vite):** Implemented 5 complete modules:
  1. Chemical Compound Catalog with monograph modal.
  2. Single-Cell Scenario Builder with control comparison and multi-channel SVG time-series chart.
  3. Heterogeneous Population Cohort Simulator with percentile envelope chart.
  4. Erythrocyte Dynamic Playback with SVG biconcave disc viewer and SSE stream.
  5. Session Run History logbook with JSON/CSV export.
- **Field Station Editorial Art Direction:** Redesigned interface into an artisanal scientific workstation: warm mineral/parchment palette (`#F5F2EB`, `#EBE7DD`), Newsreader serif typography, Plus Jakarta Sans controls, and JetBrains Mono telemetry.
- **Automated Verification:** 176 backend tests passing; 15 frontend tests passing; 0 TypeScript errors.

---

## 2026-10-15 — Milestone 6: LLM-Powered Scientific Interpretation Plan
- Complete architectural specification, dual-provider strategy (deterministic rule-based engine + external LLM client), grounding guardrails, and forward-looking compound interfaces documented in [`docs/milestone_journal_and_m6_plan.md`](file:///c:/new%20project/V-Blood/docs/milestone_journal_and_m6_plan.md).

---

## 2026-10-17 — Milestone 7: LLM Compound Intelligence and Research-to-Library Pipeline
- **Overview:** Implemented end-to-end literature research and chemical candidate registration system with human-in-the-loop validation gates, preserving mechanistic ODE integrity while expanding xenobiotic capability.
- **Identity Resolution & Validation:** Implemented `ChemicalIdentityResolver` connecting to PubChem PUG REST with InChIKey/canonical SMILES validation and offline fallback caching.
- **Literature Harvesting & Prompt-Injection Defense:** Implemented `LiteratureRetrievalService` querying Europe PMC and PubMed with erythrocyte prioritization, multi-identifier deduplication, and input prompt-injection sanitization.
- **Evidence Extraction & Grading:** Implemented `EvidenceExtractionService` (with LLM extraction and deterministic fallback) and `EvidenceGradingService` supporting finding-level and compound-level grading (`CURATED`, `ESTIMATED`, `UNVERIFIED`).
- **Mechanism Mapping & Provenance:** Implemented `MechanismMappingService` translating empirical literature findings into V-Blood's 5 kinetic ODE classes (`DIRECT_OXIDANT`, `GSH_CONJUGATOR`, `REDOX_CYCLER`, `ENZYME_INHIBITOR`, `NADPH_DRAIN`) with structured parameter provenance tags (`MEASURED`, `DERIVED`, `INFERRED`, `SYNTHETIC`, `MISSING`).
- **10-Gate Scientific Validation:** Implemented `CandidateValidator` enforcing strict mathematical, dimensional, chemical, and trial ODE integration checks before simulation readiness.
- **Dynamic Catalog Registration & Ineligibility Gating:** Implemented `ResearchRepository` with JSON persistence (`data/processed/research_candidates.json`), audit trails, and dynamic injection into `CompoundLibrary`. Unapproved or rejected candidates are strictly blocked from simulation scenarios with HTTP 422.
- **Field Station Editorial Workstation (Module 06):** Built `CompoundResearchWorkspace` in React 19 + TypeScript adhering to the warm mineral/parchment palette, featuring live stage tracking, collapsible deep-inspection plates, and interactive approval/rejection workflows.
- **Test Suite Expansion:** Added 21 backend tests (17 unit, 4 API) and 3 frontend tests. All 212 backend tests and 22 frontend tests passing.

