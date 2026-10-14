# Assumptions and Limitations — V-Blood Milestone 1

This document catalogues every scientific assumption and limitation in the current implementation. It is updated whenever a new assumption is introduced.

---

## CRITICAL DISCLAIMER

V-Blood is a research simulation platform. All outputs are **model predictions**, not experimental measurements. The presence of a simulation result does not imply:

- That the modelled effect has been experimentally observed.
- That the model parameters are calibrated to the specific condition being simulated.
- That the model generalises to all chemicals, concentrations, or physiological states.

---

## Model-level assumptions

| ID | Assumption | Biological component | Impact | Alternative |
|---|---|---|---|---|
| A-01 | The RBC cytosol is treated as a well-mixed single compartment. | All | No spatial gradients; may miss membrane-localised effects | Spatial PDE model (out of scope) |
| A-02 | Temperature is fixed at 37 °C. Model parameters are not adjusted for other temperatures. | All | Parameters from multiple sources may have been measured at different temperatures | Q₁₀ corrections (planned) |
| A-03 | pH is fixed at 7.2 (normal RBC cytosolic pH). | All | No pH dynamics | Dynamic pH model (out of scope) |
| A-04 | H₂O₂ is used as a generic oxidant challenge. No chemical-specific oxidant pathways are modelled. | Oxidant | Cannot predict chemical-specific effects | ML layer + chemical-specific kinetics (Milestone 5) |
| A-05 | NADPH supply is modelled as a simple regulated source term, not full G6PD/PPP kinetics. | NADPH | May not capture G6PD deficiency correctly | Full PPP sub-model (Milestone 2) |
| A-06 | GSH synthesis is modelled as a zero-order constant rate. In reality it is regulated. | GSH | May overestimate synthesis under severe depletion | Regulated synthesis model |
| A-07 | GPx1 ping-pong kinetics are approximated using an effective bimolecular rate constant. | GPx1 | Slightly different saturation behaviour than the true ping-pong mechanism | Full ping-pong equations |
| A-08 | The cumulative damage index `D` is a mechanistic proxy. It is not directly measurable. | Damage | No experimental calibration of D | Link to haemoglobin release data (Milestone 2) |
| A-09 | GSSG export is modelled as first-order in [GSSG]. The transporter is saturable at high [GSSG]; saturation is not modelled. | GSSG export | May underestimate protection at high oxidant load | Michaelis-Menten transport model |
| A-10 | Endogenous H₂O₂ production from haemoglobin autoxidation is modelled as a small constant baseline flux. | H₂O₂ | Does not respond to haemoglobin concentration changes | Haemoglobin sub-model |
| A-11 | Chemical exposure scenarios simulate an in vitro isolated erythrocyte suspension with no systemic PK/ADME clearance. | Scenario Engine | In vivo drug clearance and metabolite kinetics are not captured | Full PBPK coupling (planned) |
| A-12 | Multi-compound combinations assume independent rate flux additivity and no direct extracellular chemical-chemical adduct formation. | Scenario Engine | May miss synergistic chemical reactions in the suspension medium | Adduct kinetic sub-models |
| A-13 | Visual-state health categories are strictly biochemical; physical erythrocyte morphology (echinocytes, crenation) is explicitly unmodeled. | Reporting | Does not predict membrane shape changes or mechanical fragility | Biomechanical membrane model |
| A-14 | Glycolytic intermediates (ATP, 2,3-BPG, NADH) are unmodeled; scenarios cannot predict ATP-dependent deformability loss. | Metabolism | Misses ATP-dependent active transport collapse | Glycolysis sub-model |
| A-15 | Compounds with UNVERIFIED evidence status are exploratory synthetic entries excluded from validation pass/fail scoring. | Compounds | Prevents synthetic parameters from distorting validation benchmarks | Strict validation filtering |

## Parameter-level assumptions

| ID | Parameter | Assumed value | Units | Evidence status | Source |
|---|---|---|---|---|---|
| P-01 | GSH initial concentration | 2.5 | mM (intracellular water) | Literature | Sies 1999; Anderson 1998 |
| P-02 | GSSG initial concentration | 0.025 | mM | Literature | Giustarini et al. 2013 |
| P-03 | H₂O₂ initial (endogenous SS) | 0.001 | mM | Literature-estimated | Antunes & Cadenas 2000 |
| P-04 | NADPH initial concentration | 0.030 | mM | Literature-estimated | Gaetani et al. 1994 |
| P-05 | GPx effective rate constant k_gpx | 5.0×10⁷ | M⁻¹ s⁻¹ → converted to mM⁻¹ s⁻¹ | Literature; uncertain | Flohé 1979; Ursini et al. 1995 |
| P-06 | GR Vmax | 2.4×10⁻³ | mM s⁻¹ | Literature-estimated | Worthington & Rosemeyer 1974 |
| P-07 | GR Km_GSSG | 0.060 | mM | Literature | Worthington & Rosemeyer 1974 |
| P-08 | GR Km_NADPH | 0.006 | mM | Literature | Worthington & Rosemeyer 1974 |
| P-09 | NADPH supply Vmax (PPP surrogate) | 3.0×10⁻³ | mM s⁻¹ | Estimated | Gaetani et al. 1994 |
| P-10 | NADPH supply Km (NADPH feedback) | 0.015 | mM | Estimated | Gaetani et al. 1994; model calibration |
| P-11 | GSH synthesis rate k_synth | 5.0×10⁻⁶ | mM s⁻¹ | Literature-estimated | Griffith 1980 |
| P-12 | GSSG export rate k_export | 2.0×10⁻² | s⁻¹ (first-order) | Literature-estimated | Kondo et al. 1987 |
| P-13 | H₂O₂ endogenous production rate k_prod | 1.0×10⁻⁶ | mM s⁻¹ | Estimated | Antunes & Cadenas 2000 |
| P-14 | H₂O₂ passive removal k_rem | 1.0×10⁻³ | s⁻¹ | Estimated | Assigned to achieve physiological SS |
| P-15 | Damage accumulation rate k_damage | 1.0×10⁻⁴ | mM⁻¹ s⁻¹ | **SYNTHETIC** — no experimental calibration | V-Blood model assumption |
| P-16 | Damage repair rate k_repair | 5.0×10⁻⁶ | s⁻¹ | **SYNTHETIC** — no experimental calibration | V-Blood model assumption |

> Parameters marked **SYNTHETIC** are placeholders used to complete the software architecture. They must not be used to make biological predictions until they are replaced with experimentally derived or validated values.

## Data limitations

- No experimental time-series dataset has been ingested in Milestone 1.
- Model parameters are literature-derived from multiple independent studies with different experimental conditions; they have not been fitted to a single consistent dataset.
- The model has not been validated against independent experimental haemolysis time courses.

## What the model cannot do (Milestone 1)

- Predict the effect of any specific chemical compound.
- Predict haemolysis probability with quantified uncertainty.
- Distinguish between genetic variants (e.g., G6PD deficiency).
- Model whole-blood or plasma effects.
- Account for donor-to-donor variability.

## References

1. Sies, H. (1999). Glutathione and its role in cellular functions. Free Radical Biology and Medicine, 27(9-10), 916-921.
2. Anderson, M.E. (1998). Glutathione: an overview of biosynthesis and modulation. Chem-Biol Interactions, 111, 1-14.
3. Giustarini, D. et al. (2013). Analysis of GSH and GSSG after derivatization with N-ethylmaleimide. Nature Protocols, 8, 1660-1669.
4. Antunes, F. & Cadenas, E. (2000). Estimation of H₂O₂ gradients across biomembranes. FEBS Letters, 475(2), 121-126.
5. Flohé, L. (1979). Glutathione peroxidase: fact and fiction. Ciba Found. Symp., 65, 95-122.
6. Ursini, F. et al. (1995). The selenoenzyme phospholipid hydroperoxide glutathione peroxidase. Methods in Enzymology, 252, 38-53.
7. Worthington, D.J. & Rosemeyer, M.A. (1974). Human glutathione reductase: purification of the crystalline enzyme from erythrocytes. European Journal of Biochemistry, 48(1), 167-177.
8. Gaetani, G.F. et al. (1994). Predominant role of catalase in the disposal of hydrogen peroxide within human erythrocytes. Blood, 87(4), 1595-1601.
9. Griffith, O.W. (1980). Determination of glutathione and glutathione disulfide using glutathione reductase and 2-vinylpyridine. Analytical Biochemistry, 106(1), 207-212.
10. Kondo, T. et al. (1987). Amino acid sequence of the heavy subunit of human erythrocyte glutathione S-transferase: relationship to cationic glutathione S-transferase. Biochemistry, 26(24), 7729-7734.
11. Mulquiney, P.J. & Kuchel, P.W. (1999). Model of 2,3-bisphosphoglycerate metabolism in the human erythrocyte based on detailed enzyme kinetic equations. Biochemical Journal, 342, 567-580.
