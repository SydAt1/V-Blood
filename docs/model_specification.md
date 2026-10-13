# Mathematical Model Specification — RBC Glutathione Redox ODE Model

**Model ID:** `rbc-gsh-redox-v1`  
**Version:** 1.0.0  
**Date:** 2026-10-13  
**Status:** Implemented in Milestone 1

---

## 1. Compartments

| ID | Name | Description |
|---|---|---|
| `cyto` | RBC cytosol | Intracellular aqueous volume of a single human erythrocyte; modelled as well-mixed |

All concentrations are in mM of intracellular water unless otherwise stated.

---

## 2. State variables

| Symbol | Name | Units | Compartment | Physiological range |
|---|---|---|---|---|
| `GSH` | Reduced glutathione | mM | cyto | 1.5–3.0 |
| `GSSG` | Oxidised glutathione | mM | cyto | 0.010–0.040 |
| `H2O2` | Hydrogen peroxide | mM | cyto | 0.0001–0.010 |
| `NADPH` | Reduced nicotinamide adenine dinucleotide phosphate | mM | cyto | 0.010–0.050 |
| `D` | Cumulative oxidative damage index | dimensionless | abstract | 0.0–1.0 |

---

## 3. Input parameters (scenario-specific)

| Symbol | Name | Units | Description |
|---|---|---|---|
| `H2O2_dose` | Exogenous H₂O₂ bolus | mM | Added to H₂O₂ at t=0 |
| `t_span` | Simulation interval | s | [t_start, t_end] |

---

## 4. Reactions and rate expressions

### R1 — Glutathione peroxidase (GPx1) reaction

**Reaction:** H₂O₂ + 2 GSH → GSSG + 2 H₂O

**Mechanism:** The true mechanism is ping-pong bi-bi. At physiological [H₂O₂] ≪ Km(H₂O₂) and [GSH] within its working range, the rate is well-approximated by:

$$v_{\text{GPx}} = k_{\text{gpx}} \cdot [\text{H}_2\text{O}_2] \cdot [\text{GSH}]$$

where $k_{\text{gpx}}$ is an effective bimolecular rate constant.

**Rationale:** This bimolecular approximation is used in multiple published RBC models (Nakayama 2005; similar to Oshino & Chance 1977). It is valid when [H₂O₂] ≪ Km,H₂O₂ ≈ 0.1–1.0 mM, which holds at physiological and moderate challenge concentrations. The approximation breaks down at high [H₂O₂] > 0.5 mM; a warning is raised in that regime.

**Parameter:**
- $k_{\text{gpx}}$ = 5.0×10⁷ M⁻¹ s⁻¹ = 5.0×10⁴ mM⁻¹ s⁻¹ (note: unit conversion to mM basis)
  - Source: Flohé (1979); Ursini et al. (1995)
  - Conditions: 37 °C, pH 7.0–7.4, purified human erythrocyte GPx1
  - Uncertainty: ±50% (ping-pong mechanism makes apparent k₂ dependent on assay conditions)

### R2 — Glutathione reductase (GR) reaction

**Reaction:** GSSG + NADPH + H⁺ → 2 GSH + NADP⁺

**Mechanism:** Ordered bi-bi or ping-pong; approximated by bi-substrate Michaelis-Menten:

$$v_{\text{GR}} = \frac{V_{\max,\text{GR}} \cdot [\text{GSSG}] \cdot [\text{NADPH}]}{(K_{m,\text{GSSG}} + [\text{GSSG}]) \cdot (K_{m,\text{NADPH}} + [\text{NADPH}])}$$

**Rationale:** Standard bi-substrate saturation kinetics are well-established for GR. The random Bi-Bi formulation is equivalent to the simpler product of saturation terms used here under the assumption of independent binding, which is a common modelling approximation.

**Parameters:**
- $V_{\max,\text{GR}}$ = 2.4×10⁻³ mM s⁻¹
  - Source: estimated from Worthington & Rosemeyer (1974); normalised to estimated intracellular enzyme concentration
  - Uncertainty: factor of 2 (depends on assumed intracellular volume and enzyme amount)
- $K_{m,\text{GSSG}}$ = 0.060 mM
  - Source: Worthington & Rosemeyer (1974), Table 2
  - Conditions: 37 °C, pH 6.9, purified human erythrocyte GR
- $K_{m,\text{NADPH}}$ = 0.006 mM
  - Source: Worthington & Rosemeyer (1974), Table 2
  - Conditions: same as above

### R3 — GSSG export

**Reaction:** GSSG_cyto → GSSG_extracellular

**Mechanism:** Active transport by MRP1/ABCC1; modelled as first-order in [GSSG] (unsaturated regime):

$$v_{\text{export}} = k_{\text{export}} \cdot [\text{GSSG}]$$

**Rationale:** The exporter is saturable at very high GSSG, but under normal and moderate-stress conditions operates below Km. First-order is an appropriate simplification.

**Parameter:**
- $k_{\text{export}}$ = 2.0×10⁻² s⁻¹
  - Source: Estimated from Kondo et al. (1987)
  - Uncertainty: high; ±factor of 3

### R4 — GSH de novo synthesis

**Reaction:** Precursors → GSH

**Mechanism:** Net zero-order (constant) synthesis rate. In reality it is regulated by γ-glutamylcysteine synthetase and cysteine availability, but these are not modelled.

$$v_{\text{synth}} = k_{\text{synth}}$$

**Parameter:**
- $k_{\text{synth}}$ = 5.0×10⁻⁶ mM s⁻¹
  - Source: Estimated from Griffith (1980); GSH half-life in RBC ~4 days → turnover rate
  - Uncertainty: ±50%

### R5 — NADPH supply (PPP surrogate)

**Mechanism:** The PPP produces NADPH via G6PD, regulated by NADPH product inhibition. Modelled as a Michaelis-type source:

$$v_{\text{PPP}} = \frac{V_{\max,\text{PPP}} \cdot K_{m,\text{NADPH,PPP}}}{K_{m,\text{NADPH,PPP}} + [\text{NADPH}]}$$

This decreases as [NADPH] rises (product inhibition / saturation model). When NADPH is depleted, the flux approaches Vmax.

**Rationale:** This is a simplified surrogate for the full G6PD regulatory module. It captures the key qualitative behaviour: PPP flux is low at rest (NADPH near baseline), increases when NADPH is consumed by GR during oxidative stress.

**Parameters:**
- $V_{\max,\text{PPP}}$ = 3.0×10⁻³ mM s⁻¹
  - Source: Estimated from Gaetani et al. (1994); ceiling PPP flux in normal RBC
  - Uncertainty: ±factor of 2
- $K_{m,\text{NADPH,PPP}}$ = 0.015 mM
  - Source: Estimated; consistent with NADPH/NADP⁺ product inhibition of G6PD Km(NADPH) ~10–16 µM (Gaetani 1994)
  - Uncertainty: ±50%

### R6 — H₂O₂ endogenous production

**Reaction:** Haemoglobin autoxidation and other sources → H₂O₂

$$v_{\text{prod}} = k_{\text{prod}}$$

**Parameter:**
- $k_{\text{prod}}$ = 1.0×10⁻⁶ mM s⁻¹
  - Source: Estimated from Antunes & Cadenas (2000); steady-state H₂O₂ production in resting RBC
  - Uncertainty: ±factor of 5

### R7 — H₂O₂ passive removal

**Reaction:** H₂O₂ → H₂O (non-enzymatic removal, membrane permeation, catalase contribution under moderate stress)

$$v_{\text{rem}} = k_{\text{rem}} \cdot [\text{H}_2\text{O}_2]$$

**Parameter:**
- $k_{\text{rem}}$ = 1.0×10⁻³ s⁻¹
  - Source: **Assigned** to achieve physiological steady-state H₂O₂ ≈ 0.001 mM in combination with R6 and R1; **not directly literature-sourced**
  - Uncertainty: high

### R8 — Damage accumulation

**Mechanism:** Damage accumulates in proportion to excess H₂O₂ (above physiological steady-state) when GSH is low:

$$\frac{dD}{dt} = k_{\text{damage}} \cdot [\text{H}_2\text{O}_2] \cdot \max(0, 1 - \text{GSH/GSH}_0) - k_{\text{repair}} \cdot D \cdot (1 - D)$$

D is capped at [0, 1].

**Parameter:**
- $k_{\text{damage}}$ = 1.0×10⁻⁴ mM⁻¹ s⁻¹ — **SYNTHETIC**
- $k_{\text{repair}}$ = 5.0×10⁻⁶ s⁻¹ — **SYNTHETIC**

> These parameters have no experimental basis. They produce qualitatively plausible dynamics and are used solely to test the software architecture.

---

## 5. Differential equations

Let $g = [\text{GSH}]$, $s = [\text{GSSG}]$, $h = [\text{H}_2\text{O}_2]$, $n = [\text{NADPH}]$, $d = D$.

$$\frac{dg}{dt} = 2 v_{\text{GR}} - 2 v_{\text{GPx}} + v_{\text{synth}}$$

$$\frac{ds}{dt} = v_{\text{GPx}} - v_{\text{GR}} - v_{\text{export}}$$

$$\frac{dh}{dt} = v_{\text{prod}} - v_{\text{GPx}} + \text{H}_2\text{O}_2^{\text{bolus}}(t) - v_{\text{rem}}$$

$$\frac{dn}{dt} = v_{\text{PPP}} - v_{\text{GR}}$$

$$\frac{dd}{dt} = k_{\text{damage}} \cdot h \cdot \max(0, 1 - g/g_0) - k_{\text{repair}} \cdot d \cdot (1 - d), \quad d \in [0, 1]$$

---

## 6. Initial conditions (physiological baseline)

| Variable | Value | Units | Evidence |
|---|---|---|---|
| GSH₀ | 2.5 | mM | Literature (see P-01) |
| GSSG₀ | 0.025 | mM | Literature (see P-02) |
| H₂O₂₀ | 0.001 | mM | Literature-estimated (see P-03) |
| NADPH₀ | 0.030 | mM | Literature-estimated (see P-04) |
| D₀ | 0.0 | — | Model definition |

---

## 7. Expected qualitative behaviour

In a zero-bolus (baseline) simulation:
- GSH, GSSG, H₂O₂, NADPH should all approach a stable non-trivial steady state.
- The GSH/GSSG ratio should be >> 1 (healthy RBC redox state).
- D should remain near zero.

Following an H₂O₂ bolus:
- H₂O₂ rises transiently and is consumed by GPx.
- GSH decreases; GSSG increases.
- GR activity increases, driven by elevated GSSG and PPP-supplied NADPH.
- NADPH is transiently depleted then recovers as PPP upregulates.
- GSH recovers toward baseline if the bolus is moderate.
- At large bolus, GSH depletes substantially, D rises.
- If GSH recovers, D should stabilise; if not, D approaches 1.

---

## 8. Constraints

- All concentrations must remain ≥ 0.
- D must remain in [0, 1].
- GSH depletion below ~10% of baseline (< 0.25 mM) indicates severe oxidative crisis.
- The bimolecular GPx approximation issues a warning when [H₂O₂] > 0.5 mM.

---

## 9. Conservation properties

The system does not have a strict glutathione conservation law because synthesis, degradation, and export occur. However:

$$2 \frac{d[\text{GSSG}]}{dt} + \frac{d[\text{GSH}]}{dt} \approx 2 v_{\text{synth}} - 2 v_{\text{export}}$$

This can be used as a partial consistency check. See scientific tests.

---

## 10. Solver configuration

- Integrator: `scipy.integrate.solve_ivp` with `method='RK45'` (adaptive step size)
- Relative tolerance: 1e-8
- Absolute tolerance: 1e-10
- Maximum number of steps: 50000
- Event detection: GSH < 0 (failure), H₂O₂ < 0 (failure)
- Dense output: requested for interpolation

---

## 11. G6PD Kinetic Sub-Model — Version 2.0.0 (`rbc-g6pd-gsh-v2`)

Implemented in Milestone 2 (Task 6), `rbc-g6pd-gsh-v2` replaces the simplified PPP surrogate reaction (R5) with an evidence-grounded, bi-substrate G6PD kinetic rate law incorporating competitive product inhibition by NADPH and pyridine nucleotide pool conservation.

### Rate Equation (Option A)

$$v_{\text{G6PD}} = \alpha \cdot \frac{V_{\max,\text{G6PD}} \cdot [\text{G6P}] \cdot [\text{NADP}^+]}{K_{m,\text{G6P}} K_{m,\text{NADP}^+} \left(1 + \frac{[\text{NADPH}]}{K_{i,\text{NADPH}}}\right) + K_{m,\text{NADP}^+} [\text{G6P}] + K_{m,\text{G6P}} [\text{NADP}^+] + [\text{G6P}] [\text{NADP}^+]}$$

where total pyridine nucleotide pool conservation dictates:
$$[\text{NADP}^+] = \max\left(0, [\text{NADP}]_{\text{tot}} - [\text{NADPH}]\right)$$

### Parameter Provenance

| Parameter | Value | Units | Source | Evidence Status | Notes |
|---|---|---|---|---|---|
| $V_{\max,\text{G6PD}}$ | 0.008 | mM s⁻¹ (8 µM/s) | Gaetani et al. (1994) Blood 84:2018; Kirkman & Gaetani (1986) JBC 261:4033 | LITERATURE | Intracellular enzyme velocity in adult human erythrocytes |
| $K_{m,\text{G6P}}$ | 0.040 | mM (40 µM) | Yoshida (1973) Science 179:532; Mulquiney & Kuchel (1999) | LITERATURE | Substrate affinity for G6P |
| $K_{m,\text{NADP}^+}$ | 0.008 | mM (8 µM) | Yoshida (1973); Kirkman et al. (1986) | LITERATURE | Cofactor affinity for NADP+ |
| $K_{i,\text{NADPH}}$ | 0.012 | mM (12 µM) | Kirkman & Gaetani (1986); Gaetani et al. (1989) | LITERATURE | Competitive inhibition constant against NADP+ |
| $[\text{NADP}]_{\text{tot}}$ | 0.040 | mM (40 µM) | Gaetani et al. (1994); Kirkman et al. (1986) | LITERATURE | Conserved intracellular pool: [NADP+] + [NADPH] |
| $[\text{G6P}]_{\text{ss}}$ | 0.040 | mM (40 µM) | Minakami et al. (1965) BBRC 19:422; Mulquiney & Kuchel (1999) | LITERATURE | Steady-state erythrocyte glycolysis intermediate |
| $\alpha$ | 1.0 | dimensionless | Model definition | ESTIMATED | Relative enzyme activity multiplier (1.0 = normal, 0.1 = severe deficiency) |

### G6PD Deficiency Scenarios

The activity multiplier $\alpha \in [0.0, 1.0]$ scales maximal enzyme activity $V_{\max,\text{G6PD}}$:
- **$\alpha = 1.0$ (Normal):** Resting NADPH is buffered near $[\text{NADP}]_{\text{tot}} \approx 0.040\text{ mM}$. Under 0.05 mM H₂O₂ challenge, NADPH drops transiently to 0.0339 mM and rapidly recovers.
- **$\alpha = 0.5$ (Moderate reduction):** Mimics heterozygous or moderate kinetic variant; minimum NADPH drops to 0.0294 mM.
- **$\alpha = 0.1$ (Severe reduction):** Mimics severe WHO Class II (e.g. Mediterranean variant) residual activity; minimum NADPH drops to 0.0146 mM, showing impaired glutathione reductase recycling capacity.
- **$\alpha = 0.0$ (Complete deficiency):** NADPH drops to zero; GSH recovery is blocked.

*Cautionary Note:* $\alpha$ is a continuous mathematical scaling multiplier and must not be conflated with specific clinical genotypes or diagnostic forecasts without independent clinical calibration.

