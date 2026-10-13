# Validation Plan — V-Blood

## Purpose

This document describes how each model component will be validated, and what constitutes an acceptable validation result. It is updated as experimental data is ingested.

---

## Current status (Milestone 1)

**No experimental validation has been performed.** The model parameters are literature-derived from multiple independent studies. No parameter fitting to a single consistent dataset has been done.

The model currently produces qualitatively plausible behaviour (tested in `tests/scientific/test_rbc_simulation.py`), but quantitative accuracy cannot be assessed until experimental data is ingested.

---

## Validation hierarchy

| Level | Description | Status |
|---|---|---|
| L0 — Software correctness | Unit tests on equations, schemas, solver | ✓ Implemented (55 tests) |
| L1 — Qualitative behaviour | Integration tests for direction-of-change | ✓ Implemented (23 tests) |
| L2 — Steady-state validation | Compare model SS to published RBC measurements | ✓ Implemented (src/vblood/validation/l2_validator.py) |
| L3 — Dynamic validation | Compare trajectories to published time-series | Planned (Milestone 2) |
| L4 — External validation | Predict held-out experimental outcomes | Planned (Milestone 3+) |
| L5 — Cross-model comparison | Compare predictions to RBC-GEM / iAB-RBC-283 flux predictions | Planned (Milestone 3+) |

---

## L2: Steady-state targets

When experimental data is ingested, the model should produce steady-state values within the following ranges for a resting, unstressed normal human erythrocyte:

| Variable | Target range | Source |
|---|---|---|
| [GSH] | 1.5–3.0 mM | Sies 1999; Anderson 1998 |
| [GSSG] | 0.010–0.040 mM | Giustarini et al. 2013 |
| GSH/GSSG ratio | > 30 | Giustarini et al. 2013 |
| [H2O2] | 0.00001–0.001 mM (10–1000 nM) | Antunes & Cadenas 2000 |
| [NADPH] | 0.010–0.050 mM | Gaetani et al. 1994 |

---

## L3: Dynamic validation targets

Target datasets for trajectory validation (to be ingested in Milestone 2):

1. **H2O2 clearance kinetics** (Gaetani et al. 1994, Blood 87:1595): H2O2 clearance rates in normal RBC vs G6PD-deficient RBC. Can be used to validate GPx + GR dynamics.

2. **GSH/GSSG recovery after H2O2 pulse** (Nakayama et al. 2005, Biosystems 83:91): Simulated GSH/GSSG ratio recovery trajectory after a defined H2O2 bolus. Published simulation data available for cross-model comparison.

3. **AAPH-induced haemolysis time courses** (multiple published papers): Chemical-specific haemolysis kinetics. Cannot be used until the chemical-exposure module is implemented (Milestone 5).

---

## Validation failure criteria

A model fails L2 validation if:
- Predicted SS [GSH] is outside [0.5, 5.0] mM.
- Predicted GSH/GSSG ratio is < 5.
- Predicted [H2O2] is outside [1e-5, 0.01] mM.

A model fails L3 validation if:
- The direction of change after H2O2 bolus is wrong for GSH, GSSG, or NADPH.
- The time to 50% GSH recovery differs from Nakayama et al. by more than 10×.

---

## Parameter calibration approach (Milestone 3)

When time-series data is available:

1. Identify the most sensitive parameters using local sensitivity analysis.
2. Constrain parameter ranges using uncertainty bounds from `parameters.py`.
3. Use `scipy.optimize.minimize` or a Bayesian sampler for fitting.
4. Hold out at least 20% of experiments as a test set.
5. Report calibrated parameter values with 95% confidence intervals.
6. Never claim the calibrated model generalises to unseen chemicals without a proper held-out evaluation.
