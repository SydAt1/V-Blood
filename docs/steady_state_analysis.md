# Steady-State Analysis & Equilibrium Solver — V-Blood

**Module:** `src/vblood/simulation/steady_state.py`  
**Milestone:** 2 (Task 1)  
**Status:** Verified & Integrated  

---

## 1. Mathematical Formulation

For the 5-variable RBC oxidative-stress ODE system:
$$\frac{dx}{dt} = f(x, p)$$
with state vector:
$$x = \begin{bmatrix} [\text{GSH}] \\ [\text{GSSG}] \\ [\text{H}_2\text{O}_2] \\ [\text{NADPH}] \\ D \end{bmatrix} \in \mathbb{R}_{\ge 0}^5$$

The steady-state condition is defined as:
$$f(x^*, p) = 0 \quad \text{subject to } x^* \ge 0, \quad 0 \le D^* \le 1$$

Numerically, convergence requires the residual norm to satisfy:
$$\|f(x^*, p)\|_\infty = \max_i |f_i(x^*, p)| \le \text{tol}$$
where $\text{tol} = 10^{-8}\text{ mM s}^{-1}$ by default.

---

## 2. Investigation of Model Drift in Milestone 1

### Observed Phenomenon
Simulations initialized at default physiological concentrations:
$$[\text{GSH}]_0 = 2.5\text{ mM}, \quad [\text{GSSG}]_0 = 0.025\text{ mM}, \quad [\text{H}_2\text{O}_2]_0 = 0.0001\text{ mM}, \quad [\text{NADPH}]_0 = 0.030\text{ mM}$$
exhibited rapid drift in the $\text{GSH}/\text{GSSG}$ ratio from the initial 100:1 to > 10,000:1.

### Root Cause Analysis

1. **Glutathione Pool Mass Balance Constraint:**
   The total glutathione equivalent pool is $G_{\text{tot}} = [\text{GSH}] + 2[\text{GSSG}]$.
   Summing the differential equations for GSH and GSSG:
   $$\frac{d([\text{GSH}] + 2[\text{GSSG}])}{dt} = k_{\text{synth}} - 2 k_{\text{export}} [\text{GSSG}]$$
   At any true steady state, $\frac{d G_{\text{tot}}}{dt} = 0$, which strictly enforces:
   $$[\text{GSSG}]^* = \frac{k_{\text{synth}}}{2 k_{\text{export}}}$$
   With parameters $k_{\text{synth}} = 5 \times 10^{-6}\text{ mM s}^{-1}$ and $k_{\text{export}} = 0.02\text{ s}^{-1}$:
   $$[\text{GSSG}]^* = \frac{5 \times 10^{-6}}{2 \times 0.02} = 1.25 \times 10^{-4}\text{ mM} = 0.125\ \mu\text{M}$$
   Because $k_{\text{export}} = 0.02\text{ s}^{-1}$ (half-life $\approx 35\text{ s}$) is ~200-fold faster than de novo synthesis, active export drains GSSG until $[\text{GSSG}]^*$ drops from $0.025\text{ mM}$ down to $0.000125\text{ mM}$.

2. **NADPH Flux Imbalance:**
   In the 5-variable model, the **sole consumer of NADPH** is glutathione reductase (GR):
   $$r_{\text{GR}} = V_{\max,\text{GR}} \frac{[\text{GSSG}]}{K_{m,\text{GSSG}} + [\text{GSSG}]} \frac{[\text{NADPH}]}{K_{m,\text{NADPH}} + [\text{NADPH}]}$$
   At $[\text{GSSG}]^* = 1.25 \times 10^{-4}\text{ mM}$, GR is heavily substrate-limited ($K_{m,\text{GSSG}} = 0.060\text{ mM}$), capping the maximum possible GR turnover to:
   $$r_{\text{GR}} \le 2.4 \times 10^{-3} \times \frac{0.000125}{0.060125} \approx 4.99 \times 10^{-6}\text{ mM s}^{-1}$$
   Meanwhile, the pentose phosphate pathway (PPP) produces NADPH at $V_{\max,\text{PPP}} = 3 \times 10^{-3}\text{ mM s}^{-1}$ ($600\times$ higher).
   To satisfy $\frac{d[\text{NADPH}]}{dt} = r_{\text{PPP}} - r_{\text{GR}} = 0$, product inhibition must suppress PPP by $99.8\%$:
   $$r_{\text{PPP}} = V_{\max,\text{PPP}} \frac{K_m}{K_m + [\text{NADPH}]} = r_{\text{GR}}^* \implies [\text{NADPH}]^* \approx 9.01\text{ mM}$$
   This is well above the physiological resting level ($0.010\text{–}0.050\text{ mM}$).

3. **GSH Depletion at Steady State:**
   GPx flux satisfies $r_{\text{GPx}}^* = r_{\text{GR}}^* + r_{\text{export}}^* \approx 7.49 \times 10^{-6}\text{ mM s}^{-1}$.
   Endogenous $\text{H}_2\text{O}_2$ production is $k_{\text{h2o2\_prod}} = 1.5 \times 10^{-5}\text{ mM s}^{-1}$.
   The remaining peroxide must be cleared passively:
   $$[\text{H}_2\text{O}_2]^* = \frac{k_{\text{h2o2\_prod}} - r_{\text{GPx}}^*}{k_{\text{h2o2\_rem}}} = \frac{1.5 \times 10^{-5} - 7.49 \times 10^{-6}}{0.1} \approx 7.51 \times 10^{-5}\text{ mM}$$
   Finally, $r_{\text{GPx}} = k_{\text{gpx}} [\text{GSH}]^* [\text{H}_2\text{O}_2]^*$ forces:
   $$[\text{GSH}]^* = \frac{7.49 \times 10^{-6}}{50 \times 7.51 \times 10^{-5}} \approx 1.99 \times 10^{-3}\text{ mM} = 1.99\ \mu\text{M}$$

### Scientific Conclusion
The Milestone 1 model equations possess a **single, unique, mathematically stable equilibrium**:
- $[\text{GSH}]^* = 1.99\ \mu\text{M}$
- $[\text{GSSG}]^* = 0.125\ \mu\text{M}$
- $[\text{H}_2\text{O}_2]^* = 75.1\text{ nM}$
- $[\text{NADPH}]^* = 9.01\text{ mM}$
- $D^* = 0.0015$

However, this mathematical fixed point is **unphysiological** because:
1. $k_{\text{export}} = 0.02\text{ s}^{-1}$ represents high-stress export rather than basal resting export.
2. The model lacks other physiological NADPH sinks (e.g. thioredoxin reductase, lipid peroxidation reduction, catalase maintenance).
3. The model lacks feedback regulation on de novo GSH synthesis.

### 2.4 Numerical Audit of the 2-Hour Baseline Transient ($t = 7200\text{ s}$)

When `rbc-gsh-redox-v1` is integrated dynamically over 2 hours starting from standard resting physiological conditions:
$$[\text{GSH}]_0 = 2.5\text{ mM}, \quad [\text{GSSG}]_0 = 0.025\text{ mM}, \quad [\text{H}_2\text{O}_2]_0 = 0.0001\text{ mM}, \quad [\text{NADPH}]_0 = 0.030\text{ mM}$$

the trajectory reveals significant drift without achieving physiological rest:

| Observable | $t = 0\text{ s}$ (Initial) | $t = 7200\text{ s}$ (2 h) | L2 Reference Range | Mechanism / Root Cause |
|---|---|---|---|---|
| $[\text{NADPH}]$ | $0.030\text{ mM}$ | **$0.7432\text{ mM}$** (rising) | $0.010–0.050\text{ mM}$ | No pyridine nucleotide conservation ($[NADP^+] + [NADPH] = \text{const}$) in v1. At $t=7200\text{ s}$, $v_{\text{PPP}} \approx 5.96 \times 10^{-5}\text{ mM s}^{-1}$ exceeds $v_{\text{GR}} \approx 9.96 \times 10^{-6}\text{ mM s}^{-1}$, driving continuous accumulation toward asymptotic $9.01\text{ mM}$. |
| $[\text{GSSG}]$ | $0.025\text{ mM}$ | **$2.518 \times 10^{-4}\text{ mM}$** | $0.010–0.040\text{ mM}$ | Overestimated active export ($k_{\text{export}} = 0.02\text{ s}^{-1}$) drains GSSG 100-fold below normal physiological levels. |
| $[\text{GSH}]/[\text{GSSG}]$ | $100$ | **$9,896$ ($\approx 10^4$)** | $30–250$ | Artificially elevated by the collapse of $[\text{GSSG}]$. |
| $[\text{H}_2\text{O}_2]$ | $1.0 \times 10^{-4}\text{ mM}$ | **$1.203 \times 10^{-7}\text{ mM}$** | $1.0 \times 10^{-4}–1.0 \times 10^{-2}\text{ mM}$ | Bimolecular GPx clearance ($k_{\text{eff}} = k_{\text{rem}} + k_{\text{gpx}}[\text{GSH}] \approx 125.1\text{ s}^{-1}$) clears peroxide down to $k_{\text{prod}} / 125.1 \approx 0.12\text{ nM}$, conflicting with the documented reference interval. |
| Total Glutathione ($G_{\text{tot}}$) | $2.550\text{ mM}$ | **$2.4926\text{ mM}$** | $1.5–3.0\text{ mM}$ | **Net loss of $2.25\%$ ($0.0574\text{ mM}$)** over 2 h because $2 v_{\text{export}} > v_{\text{synth}}$ ($1.007 \times 10^{-5}\text{ mM s}^{-1} > 5.0 \times 10^{-6}\text{ mM s}^{-1}$). |

### 2.5 Solver & Validator Audit: Why Was This Missed in Standard Runs?

1. **`SteadyStateSolver` Behaviour:**
   - The steady-state solver **correctly detected** the asymptotic unphysiological fixed point ($[\text{NADPH}]^* = 9.01\text{ mM}$, $[\text{GSH}]^* = 1.99\ \mu\text{M}$) and flagged `is_physiologically_plausible = False`.
   - When `use_steady_state_ic = True`, `engine.py` emits `SimulationWarning(code="STEADY_STATE_UNPHYSIOLOGICAL")`.
   - **Gap:** In user scripts and demonstration workflows (e.g. `scripts/run_demo.py`), simulations are initialized with user-provided `RBCGSHInitialConditions()`, setting `use_ss = False`. In this path, `SteadyStateSolver` is **never executed**.

2. **`L2Validator` Behaviour:**
   - `L2Validator` was designed as an offline validation tool for testing fixed states (unit tests in `tests/scientific/test_l2_validation.py`).
   - It was **not integrated into `engine.py`'s simulation post-processing pipeline**.
   - Consequently, long-duration transient runs can drift far out of L2 reference bounds without raising warnings or failing validation checks.

### 2.6 Verification of Model `rbc-g6pd-gsh-v2`

Model `rbc-g6pd-gsh-v2` introduces total pyridine nucleotide pool conservation:
$$[\text{NADP}^+] = \max\left(0, [\text{NADP}]_{\text{tot}} - [\text{NADPH}]\right), \quad [\text{NADP}]_{\text{tot}} = 0.040\text{ mM}$$
and bi-substrate competitive G6PD rate kinetics.

- **Pool Conservation Verification:**
  When simulated over a 2-hour unperturbed baseline run ($t = 7200\text{ s}$), $[\text{NADPH}]$ peaks at **$0.03995\text{ mM}$** and asymptotically approaches $[\text{NADP}]_{\text{tot}} = 0.040\text{ mM}$.
- As $[\text{NADPH}] \to 0.040\text{ mM}$, $[\text{NADP}^+] \to 0\text{ mM}$, causing G6PD velocity $v_{\text{G6PD}} \to 0\text{ mM s}^{-1}$.
- This mathematically and computationally guarantees that $[\text{NADPH}]$ **cannot exceed $0.040\text{ mM}$**, resolving the runaway NADPH behavior observed in `rbc-gsh-redox-v1`.

### 2.7 Proposed Fixes and Regression Testing Plan

1. **Model Parameter Calibration & Export Tuning (Milestone 3 / Task 5):**
   - Re-evaluate $k_{\text{export}}$: Replace high-stress export constant ($0.02\text{ s}^{-1}$) with basal transport rate or saturable Michaelis-Menten kinetics ($v_{\text{export}} = V_{\max,\text{export}} [\text{GSSG}] / (K_{m,\text{export}} + [\text{GSSG}])$).
   - Reconcile $H_2O_2$ reference expectations ($10^{-5}\text{–}10^{-3}\text{ mM}$) with effective GPx and autoxidation kinetics.
2. **Online L2 Drift Auditing in `SimulationEngine`:**
   - Add optional end-of-run L2 health checking in `SimulationResult` that flags when baseline simulations drift outside physiological bounds.
3. **Regression Tests:**
   - Test 1: Verify 2-hour baseline run of `rbc-g6pd-gsh-v2` enforces $[\text{NADPH}] \le [\text{NADP}]_{\text{tot}} = 0.040\text{ mM}$.
   - Test 2: Verify total glutathione rate of change $|\frac{dG_{\text{tot}}}{dt}| \le \epsilon$ at physiological steady state.
   - Test 3: Automated regression test asserting `L2Validator` flags unphysiological states if drift exceeds tolerance thresholds.

---

## 3. Solver Implementation

The solver is implemented in [`src/vblood/simulation/steady_state.py`](file:///c:/new%20project/V-Blood/src/vblood/simulation/steady_state.py).

### Key Features
1. **Closed-form + Root Hybrid:** Combines exact analytical derivation with 1D root-finding (`brentq` for NADPH) and multi-dimensional cross-verification (`scipy.optimize.root`).
2. **Eigenvalue Stability Check:** Evaluates numerical Jacobian $J = \frac{\partial f}{\partial x}$ and computes eigenvalues $\lambda_i$. Confirms local asymptotic stability ($\max \text{Re}(\lambda_i) < 0$).
3. **Positivity Constraints:** Strictly rejects negative concentrations. Never silently clips negative values.
4. **Plausibility Diagnostics:** Automatically audits equilibrium against L2 human RBC physiological targets and produces structured diagnostics.
5. **Caching:** Deterministic SHA-256 fingerprint of parameters ensures $O(1)$ lookups for repeated runs.

---

## 4. Simulation Workflow Integration

In [`src/vblood/simulation/engine.py`](file:///c:/new%20project/V-Blood/src/vblood/simulation/engine.py):
- `SimulationRequest()` defaults to equilibrium initialization (`use_steady_state_ic = None` and `initial_conditions = None`).
- If `initial_conditions` is provided, it **overrides** the default equilibrium.
- When equilibrium initialization is used, `SimulationResult.steady_state_summary` stores solver provenance and residuals, and `SimulationWarning(code="STEADY_STATE_UNPHYSIOLOGICAL")` is emitted to maintain transparency.

