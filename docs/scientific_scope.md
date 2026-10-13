# Scientific Scope — V-Blood Milestone 1

## Biological system

**Human red blood cells (erythrocytes) under oxidative stress**

Human erythrocytes are enucleate cells that lack mitochondria. Their antioxidant capacity depends almost entirely on the glutathione redox system, powered by NADPH generated through the pentose phosphate pathway (PPP). This makes them a well-studied, relatively tractable system for mechanistic ODE modelling.

## Motivation for selecting RBC oxidative stress

- Well-characterised biochemistry with decades of published kinetic data.
- Established published ODE models available for reference (Mulquiney & Kuchel 1999; Nakayama et al. 2005; Oshino & Chance 1977; Gaetani et al. 1994).
- Experimentally measurable endpoints (GSH, GSSG, haemolysis) with available reference datasets.
- Chemical-induced haemolysis is a toxicologically relevant and clinically observable endpoint.
- RBC-GEM (BioModels: MODEL2410170001) and iAB-RBC-283 (MODEL1106080000) exist for cross-validation.

## Milestone 1 biological scope

### Included in scope

| Component | Role |
|---|---|
| Reduced glutathione (GSH) | Primary intracellular antioxidant |
| Oxidised glutathione (GSSG) | Product of GSH oxidation by GPx |
| Hydrogen peroxide (H₂O₂) | Model oxidant / external challenge |
| NADPH (simplified) | Cofactor for glutathione reductase; modelled as regulated steady-state supply |
| Glutathione peroxidase (GPx1) | Catalyses H₂O₂ + 2 GSH → GSSG + 2 H₂O |
| Glutathione reductase (GR) | Catalyses GSSG + NADPH → 2 GSH + NADP⁺ |
| GSSG export | Active transport of GSSG out of the cell |
| GSH baseline synthesis | Net de novo synthesis, simplified first-order |
| Cumulative oxidative damage index (D) | Integrated measure of unresolved oxidative burden |

### Explicitly excluded from scope

- Glycolytic pathway intermediates (ATP, ADP, 2,3-BPG, lactate).
- Full PPP mechanistic detail (G6PD kinetics modelled as regulated flux, not individual steps).
- Superoxide dismutase and catalase sub-pathways (H₂O₂ is the model input oxidant).
- Membrane lipid peroxidation chain reactions (planned Milestone 2).
- Haemoglobin autoxidation kinetics (modelled as a constant endogenous H₂O₂ source rate).
- Platelet biology, coagulation, immune responses, whole-body physiology.
- Intracellular pH dynamics.
- Calcium signalling.
- Eryptosis pathways.

## State variables

| Symbol | Full name | Units | Compartment | Normal range |
|---|---|---|---|---|
| `GSH` | Reduced glutathione | mM (intracellular water) | RBC cytosol | 1.5–3.0 mM |
| `GSSG` | Oxidised glutathione | mM (intracellular water) | RBC cytosol | 0.01–0.04 mM |
| `H2O2` | Hydrogen peroxide | mM (intracellular water) | RBC cytosol | ~0.001–0.01 mM at steady state |
| `NADPH` | Reduced NADPH (simplified) | mM (intracellular water) | RBC cytosol | 0.01–0.05 mM |
| `D` | Cumulative oxidative damage index | dimensionless, [0, 1] | Abstract | 0 (healthy) |

## Measurable downstream endpoint

**Percentage haemolysis** — computed from the cumulative damage index `D` via a Hill-type sigmoidal function. This is a modelled proxy, not a direct simulation of membrane physics.

## Evidence status per component

| Component | Evidence status | Key source |
|---|---|---|
| GSH baseline concentration | Well-established | Sies 1999; Anderson 1998 |
| GSSG baseline concentration | Well-established | Giustarini et al. 2013 |
| H₂O₂ steady-state range | Established | Antunes & Cadenas 2000 |
| GPx1 kinetics (ping-pong) | Established; Km uncertain | Flohé 1979; Ursini et al. 1995 |
| GR kinetics (Michaelis-Menten) | Established | Worthington & Rosemeyer 1974 |
| NADPH simplified supply | Simplified assumption; documented | Gaetani et al. 1994 |
| GSH synthesis rate | Estimated from turnover data | Griffith 1980 |
| GSSG export rate | Literature-estimated; high uncertainty | Kondo et al. 1987 |
| Damage index formulation | Mechanistic proxy; not validated independently | V-Blood model assumption |
| Haemolysis endpoint | Qualitative connection only in Milestone 1 | Documented assumption |

## Out-of-scope chemicals

No chemical-specific predictions are made in Milestone 1. The `H₂O₂` input is used as a generic oxidant challenge. Chemical-specific predictions require the ML layer (Milestone 5).
