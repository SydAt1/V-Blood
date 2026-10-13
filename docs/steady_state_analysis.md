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

---

## 3. Solver Implementation

The solver is implemented in [`src/vblood/simulation/steady_state.py`](file:///Users/sydatsin/Blood%20Med/src/vblood/simulation/steady_state.py).

### Key Features
1. **Closed-form + Root Hybrid:** Combines exact analytical derivation with 1D root-finding (`brentq` for NADPH) and multi-dimensional cross-verification (`scipy.optimize.root`).
2. **Eigenvalue Stability Check:** Evaluates numerical Jacobian $J = \frac{\partial f}{\partial x}$ and computes eigenvalues $\lambda_i$. Confirms local asymptotic stability ($\max \text{Re}(\lambda_i) < 0$).
3. **Positivity Constraints:** Strictly rejects negative concentrations. Never silently clips negative values.
4. **Plausibility Diagnostics:** Automatically audits equilibrium against L2 human RBC physiological targets and produces structured diagnostics.
5. **Caching:** Deterministic SHA-256 fingerprint of parameters ensures $O(1)$ lookups for repeated runs.

---

## 4. Simulation Workflow Integration

In [`src/vblood/simulation/engine.py`](file:///Users/sydatsin/Blood%20Med/src/vblood/simulation/engine.py):
- `SimulationRequest()` defaults to equilibrium initialization (`use_steady_state_ic = None` and `initial_conditions = None`).
- If `initial_conditions` is provided, it **overrides** the default equilibrium.
- When equilibrium initialization is used, `SimulationResult.steady_state_summary` stores solver provenance and residuals, and `SimulationWarning(code="STEADY_STATE_UNPHYSIOLOGICAL")` is emitted to maintain transparency.
