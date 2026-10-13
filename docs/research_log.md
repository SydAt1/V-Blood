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
