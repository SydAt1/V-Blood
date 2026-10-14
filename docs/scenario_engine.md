# Chemical Exposure & Scenario Simulation Engine — V-Blood

**Module:** `src/vblood/scenarios/`  
**Milestone:** 4  
**Status:** Implemented & Verified  

---

## 1. Overview & Objective

The Scenario Engine acts as the bridge between chemical library definitions, toxicological mechanism classes, and the underlying mechanistic ODE models (`rbc-gsh-redox-v1` and `rbc-g6pd-gsh-v2`).

It provides the computational backend for the interactive "Blood Playground" web dashboard (Milestone 5), allowing researchers to:
1. Expose in silico erythrocytes to curated compounds or custom chemical exposures.
2. Select temporal delivery profiles (`BOLUS`, `INFUSION`, `REPEATED_PULSES`).
3. Model genetic vulnerability by scaling pentose phosphate capacity ($\alpha \in [0, 1]$).
4. Run vectorized cohort simulations ($N = 1000$ cells) with biological parameter variance.
5. Stream standardized visual-state frames classified by biochemical cell health.

---

## 2. Kinetic Mechanism Classes

Each chemical compound is assigned to one or more mechanistic presets in [`src/vblood/scenarios/mechanisms.py`](file:///c:/new%20project/V-Blood/src/vblood/scenarios/mechanisms.py):

| Mechanism Class | Kinetic Rate Law | Biological Meaning | Literature Reference |
|---|---|---|---|
| **Direct Oxidant** | $v_{\text{influx}}(t) = k_{\text{influx}}$ (infusion) or $[H_2O_2]_0 += \text{Dose}$ (bolus) | Direct peroxide exposure | Gaetani et al. (1994) Blood 84:2018 |
| **GSH Conjugator** | $v_{\text{conj}} = k_{\text{conj}} \cdot [C] \cdot [\text{GSH}]$ | Electrophilic depletion of GSH without GSSG formation | Habig et al. (1974) JBC 249:7130 |
| **Redox Cycler** | $v_{\text{cycle}} = k_{\text{cycle}} \cdot [C] \cdot \frac{[\text{NADPH}]}{K_m + [\text{NADPH}]}$ | Catalytic cycle consuming NADPH and generating $H_2O_2$ | Winterbourn (1979) Biochem J 182:87 |
| **Enzyme Inhibitor** | Comp: $K_m^{\text{app}} = K_m(1 + [I]/K_i)$<br>Non-comp: $V_{\max}^{\text{app}} = V_{\max} / (1 + [I]/K_i)$ | Competitive or non-competitive inhibition of G6PD or GR | Marks & Banks (1960) PNAS 46:447 |
| **NADPH Drain** | $v_{\text{drain}} = k_{\text{drain}} \cdot [C] \cdot \frac{[\text{NADPH}]}{K_m + [\text{NADPH}]}$ | Xenobiotic reduction or non-redox cofactor consumption | Gaetani et al. (1989) |

---

## 3. Explicit Model Boundaries: What Mechanisms Do NOT Capture

To maintain scientific integrity and prevent misinterpretation:

1. **No Pharmacokinetics (ADME):** The scenario engine models an in vitro suspension of isolated red blood cells. It does **not** simulate hepatic metabolism, renal clearance, protein binding, or whole-body pharmacokinetics.
2. **No Physical Membrane Morphology:** The visual state contract categorizes biochemical health based on $[GSH]$, $[NADPH]$, and $D$. It does **not** simulate physical erythrocyte shape changes (e.g. echinocyte spiculation, stomatocytosis, or spherocytosis).
3. **No Glycolytic Energy Metabolism:** ATP, 2,3-BPG, and NADH pools are not simulated. Scenarios cannot predict ATP depletion-mediated loss of membrane deformability.
4. **No Direct Adduct Chemistry:** Multi-compound simulations assume independent flux additivity and do not simulate chemical-chemical cross-reactions in the extracellular medium.

---

## 4. Compound Library & Evidence Grading

Compounds in [`data/processed/compounds.json`](file:///c:/new%20project/V-Blood/data/processed/compounds.json) are graded into three evidence levels:
- `CURATED`: Parameters directly supported by peer-reviewed erythrocyte kinetics (e.g., $H_2O_2$, Menadione, CDNB, NEM, DHEA).
- `ESTIMATED`: Extrapolated from analogous quinone or in vitro cellular models (e.g., Primaquine 5,6-orthoquinone).
- `UNVERIFIED`: Synthetic placeholder or preliminary candidate (e.g., Xenobiotic X-101).

> [!WARNING]
> **Automatic Validation Exclusion:** Any scenario involving an `UNVERIFIED` compound is automatically tagged with `has_unverified_compounds: true` and excluded from quantitative validation scoring.

---

## 5. Visual-State Contract & Frontend Readiness

The endpoint `GET /scenarios/{run_id}/visual` converts trajectories into animation frames with strict biochemical boundaries:

| Status Label | Criteria | Physiological Meaning |
|---|---|---|
| `healthy` | $[GSH] \ge 1.50\text{ mM}$ and $D < 0.05$ | Full antioxidant reserve and intact redox buffer. |
| `stressed` | $0.80 \le [GSH] < 1.50\text{ mM}$ or $0.05 \le D < 0.20$ | Glutathione oxidation exceeds normal basal turnover. |
| `severely_stressed` | $0.25 \le [GSH] < 0.80\text{ mM}$ or $0.20 \le D < 0.50$ | Severe redox exhaustion; NADPH synthesis near ceiling. |
| `lysis_risk` | $[GSH] < 0.25\text{ mM}$ (oxidative crisis) or $D \ge 0.50$ | Critical loss of antioxidant defense; cell vulnerable to hemolysis. |
