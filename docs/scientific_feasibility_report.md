# Scientific Feasibility Report — V-Blood Milestone 1

**Prepared:** 2026-10-13  
**Author:** V-Blood development team (AI-assisted)  
**Status:** Working document

---

## 1. Objective

Determine whether a red blood cell (RBC) oxidative-stress ODE model is a scientifically defensible starting point for V-Blood Milestone 1, and identify the most suitable published model or evidence base to use.

---

## 2. Literature and model survey

### 2.1 Published ODE models reviewed

| Model / Paper | Scope | Parameters | Validation | Suitable? |
|---|---|---|---|---|
| **Mulquiney & Kuchel (1999)** Biochem. J. 342:567 | Glycolysis, 2,3-BPG, adenine nucleotides; GSH treated as simplified | Full enzyme kinetics for glycolysis; partial for glutathione | Steady-state comparison | Partially — requires GSH sub-model extension |
| **Nakayama et al. (2005)** — E-Cell implementation | Added H₂O₂ challenge and GSH/GSSG dynamics to Kuchel framework | Glutathione cycle kinetics added | G6PD-deficiency GSH/GSSG ratio recovery | Suitable as reference |
| **Oshino & Chance (1977)** Arch. Biochem. Biophys. | H₂O₂ metabolism; catalase and GPx competition | Catalase Km, GPx rate | H₂O₂ clearance experiments | Useful for H₂O₂ parameterisation |
| **Gaetani et al. (1994)** Blood 87:1595 | Catalase vs GPx in H₂O₂ disposal | Measured H₂O₂ clearance rates | Experimental validation | Useful for NADPH supply scaling |
| **BioModels MODEL2410170001** (RBC-GEM) | Genome-scale metabolic reconstruction | Flux-balance; not kinetic ODEs | Constraint-based, not dynamic | Not directly usable for ODE integration |
| **BioModels MODEL1106080000** (iAB-RBC-283) | Proteomically derived stoichiometric model | Constraint-based | Flux-balance analysis | Not directly usable for ODE integration |

### 2.2 Assessment of existing models

The BioModels genome-scale models use flux-balance analysis (FBA) rather than kinetic ODEs with explicit Michaelis-Menten or mass-action kinetics. They cannot be directly integrated as initial value problems. They are useful for pathway topology reference but not for time-domain simulation.

The Nakayama et al. / Kuchel framework is the most directly relevant published kinetic ODE model. The core glutathione sub-model (GPx + GR + GSSG export) is well-parameterised and has been used in published peer-reviewed simulations. We adopt this conceptual structure for Milestone 1, with the simplification of modelling NADPH as a regulated source flux rather than implementing the full PPP.

### 2.3 Parameter availability

Kinetic parameters for the glutathione redox cycle in human erythrocytes are available in the primary enzymology literature:

- **GPx1** (glutathione peroxidase 1): operates via ping-pong bi-bi kinetics. The apparent bimolecular rate constant k_cat/Km has been measured as ~5×10⁷ M⁻¹ s⁻¹ for H₂O₂ (Flohé 1979; Ursini 1995). Because physiological [H₂O₂] ≪ Km(H₂O₂), the effective rate is approximately first-order in H₂O₂ and first-order in GSH, giving a bimolecular approximation that is valid in the physiological range.

- **GR** (glutathione reductase): Km(GSSG) ≈ 0.055–0.065 mM; Km(NADPH) ≈ 0.004–0.009 mM (Worthington & Rosemeyer 1974). These values are well-established.

- **GSSG export**: modelled as first-order in [GSSG]; rate constant estimated from Kondo et al. 1987, with acknowledged uncertainty.

- **NADPH supply**: the PPP regenerates NADPH; its flux is tightly regulated by NADPH product inhibition of G6PD. This is simplified in Milestone 1 as a Michaelis-type source flux term that increases when NADPH is consumed and saturates at the maximum measured PPP capacity.

### 2.4 Experimental datasets reviewed

| Dataset | Endpoint | Chemical | Availability | License | Usable? |
|---|---|---|---|---|---|
| Gaetani et al. 1994 (Blood) | H₂O₂ clearance kinetics | Endogenous H₂O₂ | Published figures; not raw data | Not openly licensed | Reference only |
| Giustarini et al. 2013 (Nat. Protoc.) | GSH/GSSG normal ranges | — | Published table | Reference | Reference values |
| Nakayama 2005 simulation data | GSH/GSSG recovery trajectories | H₂O₂ pulse | Simulation output only | Reference | Cross-validation target |
| OpenTox, ToxCast | Haemolysis assay endpoints | Multiple chemicals | Publicly available | Open | Planned for Milestone 2 |

No raw time-series kinetic dataset has been ingested in Milestone 1. The model is parameterised from literature constants, not fitted to a training set.

---

## 3. Feasibility conclusion

### 3.1 Is the RBC oxidative-stress model feasible?

**Yes, with caveats.**

The core glutathione redox cycle (GPx + GR + GSSG export) is well-characterised and parameterisable from the literature. A minimal ODE model tracking GSH, GSSG, H₂O₂, and NADPH is scientifically defensible for qualitative illustration of oxidative-stress dynamics.

### 3.2 Is haemolysis a feasible endpoint for Milestone 1?

**Partially feasible as a mechanistic proxy only.**

Haemolysis is the downstream consequence of membrane damage. Modelling it accurately requires either:
- Experimental kinetic data linking intracellular GSH depletion to measured haemolysis (not yet ingested), or
- A validated membrane-damage sub-model (out of scope for Milestone 1).

Milestone 1 therefore implements a **cumulative oxidative damage index** (`D`) as a proxy. This index is computed from unresolved oxidative load (elevated H₂O₂ × time). A Hill-type sigmoidal function maps `D` to an estimated haemolysis percentage. This mapping contains **synthetic parameters** (see `assumptions_and_limitations.md`) and must not be interpreted as a calibrated prediction.

### 3.3 Recommended scope

Proceed with the following for Milestone 1:

1. A 4-variable ODE system: GSH, GSSG, H₂O₂, NADPH.
2. Three enzyme rate expressions: GPx1 (bimolecular), GR (bi-substrate Michaelis-Menten), GSSG export (first-order).
3. Two source terms: GSH synthesis (constant), NADPH supply (regulated source term).
4. One damage variable `D` (proxy only, synthetic parameters clearly labelled).
5. Literature-sourced parameters with full provenance documentation.
6. No chemical-specific predictions.

---

## 4. Gaps and next steps

| Gap | Priority | Plan |
|---|---|---|
| No ingested experimental time-series for validation | High | Milestone 2: ingest Nakayama simulation data and/or HCT haemolysis assay data |
| NADPH modelled as simplified regulated supply | Medium | Milestone 2: add G6PD-catalysed PPP sub-model |
| Haemolysis endpoint uses synthetic parameters | High | Milestone 2: calibrate against experimental dose-response curves |
| No chemical-specific predictions | Medium | Milestone 5: ML chemical-response prediction layer |
| GPx1 bimolecular approximation may break at high [H₂O₂] | Medium | Milestone 2: implement full ping-pong kinetics |
| Catalase pathway not included | Low | Optional: add competition between catalase and GPx for H₂O₂ |

---

## 5. References

1. Mulquiney, P.J. & Kuchel, P.W. (1999). Biochemical Journal 342:567-580.
2. Nakayama, Y. et al. (2005). Dynamic simulation of red blood cell metabolism. Biosystems 83(2-3):91-101.
3. Flohé, L. (1979). Ciba Found. Symp. 65:95-122.
4. Ursini, F. et al. (1995). Methods in Enzymology 252:38-53.
5. Worthington, D.J. & Rosemeyer, M.A. (1974). European Journal of Biochemistry 48:167-177.
6. Gaetani, G.F. et al. (1994). Blood 87(4):1595-1601.
7. Kondo, T. et al. (1987). Biochemistry 26(24):7729-7734.
8. Antunes, F. & Cadenas, E. (2000). FEBS Letters 475(2):121-126.
9. Giustarini, D. et al. (2013). Nature Protocols 8:1660-1669.
