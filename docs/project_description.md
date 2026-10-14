# V-Blood: Detailed Project Description

> *This document provides an exhaustive reference for the V-Blood platform. The root-level copy is maintained at [PROJECT_DESCRIPTION.md](file:///c:/new%20project/V-Blood/PROJECT_DESCRIPTION.md).*

---

## 1. Executive Summary & Vision

**V-Blood** is a modular, research-oriented computational biology platform designed for the mechanistic simulation of biochemical processes in human blood. The platform combines:
- **Systems biology Ordinary Differential Equation (ODE) modeling** of intracellular metabolic and antioxidant pathways.
- **Uncertainty quantification (UQ)** and local sensitivity analysis.
- **Hierarchical scientific validation** against curated human physiological reference data.
- **A decoupled FastAPI REST backend** for headless integration with laboratory data pipelines, web dashboards, and in silico toxicology workflows.
- **Future foundations** for machine-learning response prediction (chemical structure to biological response) and LLM-based scientific explanation.

The primary objective of V-Blood is to support **mechanistic hypothesis generation** regarding how physiological stressors, genetic variants (such as G6PD deficiency), and xenobiotic/chemical exposures impact human erythrocyte survival and redox balance.

---

## 2. Scope: What V-Blood Is and What It Is Not

### What V-Blood Is:
- A computational simulation environment simulating non-linear metabolic fluxes, cofactor recycling, and oxidative stress responses.
- A tool for running in silico comparative experiments (e.g., normal vs. G6PD-deficient red blood cells under varying oxidant loads).
- A platform implementing rigorous mathematical validation, mass conservation checks, and stability auditing.

### What V-Blood Is NOT:
- **Not a medical or clinical decision support tool**: Outputs must never be used for medical diagnosis, patient care, or clinical triage.
- **Not a safety/toxicity certification platform**: It does not replace in vitro assays, animal studies, or regulatory toxicology pipelines.
- **Not an empirical measurement**: All model outputs are synthetic trajectories derived from mathematical hypotheses and must be verified experimentally.

---

## 3. Biological Focus: Human Erythrocyte Redox Homeostasis

### Why Red Blood Cells (Erythrocytes)?
Human erythrocytes are enucleated and lack mitochondria, ribosomes, and endoplasmic reticulum. Consequently:
1. They cannot synthesize new proteins or respond transcriptionally to stress.
2. They cannot rely on mitochondrial oxidative phosphorylation for ATP or mitochondrial antioxidant defenses.
3. Their survival depends almost entirely on **glycolysis** (for ATP and NADH) and the **pentose phosphate pathway (PPP)** to generate NADPH.
4. NADPH is the obligatory reducing equivalent required by glutathione reductase to regenerate reduced glutathione (GSH), the cell's frontline defense against reactive oxygen species (ROS).

This relative biochemical simplicity makes erythrocytes an ideal, tractable system for high-fidelity mechanistic ODE modeling with extensive published kinetic literature.

---

## 4. Mathematical Models & Reaction Networks

V-Blood currently features two versioned models within its biological model registry:

### A. Baseline Model: `rbc-gsh-redox-v1`
Tracks five primary state variables in the erythrocyte cytosol:
- $[GSH]$: Reduced glutathione ($1.5–3.0\text{ mM}$ physiological range).
- $[GSSG]$: Oxidized glutathione disulfide ($0.010–0.040\text{ mM}$ physiological range).
- $[H_2O_2]$: Cytosolic hydrogen peroxide ($0.0001–0.010\text{ mM}$ steady-state range).
- $[NADPH]$: Reduced nicotinamide adenine dinucleotide phosphate ($0.010–0.050\text{ mM}$).
- $D$: Cumulative oxidative damage index (dimensionless, $[0.0, 1.0]$), acting as a mechanistic proxy for downstream hemolysis.

#### Core Differential Equations:
$$\frac{d[GSH]}{dt} = 2 v_{\text{GR}} - 2 v_{\text{GPx}} + v_{\text{synth}}$$

$$\frac{d[GSSG]}{dt} = v_{\text{GPx}} - v_{\text{GR}} - v_{\text{export}}$$

$$\frac{d[H_2O_2]}{dt} = v_{\text{prod}} - v_{\text{GPx}} + \text{H}_2\text{O}_2^{\text{bolus}}(t) - v_{\text{rem}}$$

$$\frac{d[NADPH]}{dt} = v_{\text{PPP}} - v_{\text{GR}}$$

$$\frac{dD}{dt} = k_{\text{damage}} \cdot [H_2O_2] \cdot \max\left(0, 1 - \frac{[GSH]}{[GSH]_0}\right) - k_{\text{repair}} \cdot D \cdot (1 - D)$$

#### Implemented Reactions:
1. **$v_{\text{GPx}}$ (Glutathione Peroxidase, GPx1)**: Bimolecular approximation $v_{\text{GPx}} = k_{\text{gpx}} [H_2O_2] [GSH]$ ($k_{\text{gpx}} = 5.0 \times 10^4\text{ mM}^{-1}\text{s}^{-1}$).
2. **$v_{\text{GR}}$ (Glutathione Reductase)**: Bi-substrate Michaelis-Menten kinetics:
   $$v_{\text{GR}} = \frac{V_{\max,\text{GR}} [GSSG] [NADPH]}{(K_{m,\text{GSSG}} + [GSSG])(K_{m,\text{NADPH}} + [NADPH])}$$
3. **$v_{\text{export}}$ (GSSG Export)**: First-order active export via MRP1 transporter: $v_{\text{export}} = k_{\text{export}} [GSSG]$.
4. **$v_{\text{synth}}$ (GSH De Novo Synthesis)**: Basal replenishment flux.
5. **$v_{\text{PPP}}$ (Simplified Pentose Phosphate Flux)**: Michaelis-type negative-feedback product inhibition by NADPH.
6. **$v_{\text{prod}}$ / $v_{\text{rem}}$**: Endogenous basal generation (hemoglobin autoxidation) and background clearance.

---

### B. Advanced Model: `rbc-g6pd-gsh-v2`
Incorporates an evidence-grounded, bi-substrate G6PD kinetic rate law, replacing the empirical PPP surrogate.

#### Rate Equation:
$$v_{\text{G6PD}} = \alpha \cdot \frac{V_{\max,\text{G6PD}} \cdot [G6P] \cdot [NADP^+]}{K_{m,\text{G6P}} K_{m,\text{NADP}^+} \left(1 + \frac{[NADPH]}{K_{i,\text{NADPH}}}\right) + K_{m,\text{NADP}^+} [G6P] + K_{m,\text{G6P}} [NADP^+] + [G6P] [NADP^+]}$$

#### Key Biophysical Properties:
- **Pyridine Nucleotide Pool Conservation**: Total cofactors are conserved:
  $$[NADP^+] = \max\left(0, [NADP]_{\text{tot}} - [NADPH]\right), \quad [NADP]_{\text{tot}} = 0.040\text{ mM}$$
- **Competitive Inhibition**: Potent product inhibition by NADPH ($K_{i,\text{NADPH}} = 0.012\text{ mM}$) vs. substrate $NADP^+$ ($K_{m,\text{NADP}^+} = 0.008\text{ mM}$).
- **In Silico Genetic Deficiencies ($\alpha$)**:
  - $\alpha = 1.0$: Normal physiological G6PD activity.
  - $\alpha = 0.5$: Moderate deficiency (heterozygous or intermediate kinetic variants).
  - $\alpha = 0.1$: Severe deficiency (mimicking WHO Class II variants like G6PD Mediterranean).
  - $\alpha = 0.0$: Total lack of enzymatic activity.

---

## 5. System Architecture & Component Design

The platform enforces strict unidirectional dependencies. Core biological equations remain completely decoupled from solvers, APIs, or database frameworks.

```
┌────────────────────────────────────────────────────────┐
│           FastAPI Web Service (src/vblood/api)         │
│          REST Endpoints: /health, /models, /simulations │
└───────────────────────────┬────────────────────────────┘
                            │ Calls engine
┌───────────────────────────▼────────────────────────────┐
│      Simulation Engine (src/vblood/simulation)         │
│       • solve_ivp (RK45 adaptive ODE integration)      │
│       • SteadyStateSolver (Root finding & stability)   │
└───────────────────────────┬────────────────────────────┘
                            │ Evaluates
┌───────────────────────────▼────────────────────────────┐
│       Biological Models (src/vblood/biology)           │
│       • BiologicalModel abstract base class            │
│       • Model registry (_MODEL_REGISTRY)               │
│       • Parameters, RHS functions, analytical Jacobians│
└────────────────────────────────────────────────────────┘
Supporting Systems:
├── schemas/               Strict Pydantic contracts (SimulationRequest, SimulationResult)
├── uncertainty/           Finite-difference local sensitivity & tornado plot generation
├── validation/            L0–L5 hierarchical validation and L2 physiological checks
├── data/                  Experimental data ingestion with SHA-256 integrity verification
├── chemistry/             RDKit descriptor generation & chemical identification utilities
└── reporting/             Typed input/output contracts for LLM scientific explanations
```

---

## 6. Hierarchical Validation Framework

To ensure scientific credibility, V-Blood uses a 6-tier validation hierarchy:

| Level | Name | Purpose | Implementation Status |
|---|---|---|---|
| **L0** | Software Correctness | Unit tests verifying rate laws, Pydantic bounds, solver event termination, and numerical handling. | Complete (Unit test suite) |
| **L1** | Qualitative Directionality | Integration tests verifying expected biological trends (e.g., $H_2O_2$ bolus decreases GSH, increases GSSG, elevates GR flux). | Complete (Scientific test suite) |
| **L2** | Steady-State Validity | Compares resting unperturbed simulation equilibria against curated human physiological reference ranges. | Complete (`L2Validator`, `l2_reference_ranges.json`) |
| **L3** | Dynamic Time-Series | Validates clearance trajectories against published wet-lab time courses (e.g., Gaetani 1994, Nakayama 2005). | Planned (Milestone 3) |
| **L4** | External Held-Out Data | Evaluates model predictions against unseen experimental challenges. | Planned (Milestone 3+) |
| **L5** | Cross-Model Benchmarking | Compares fluxes with genome-scale metabolic models (RBC-GEM, iAB-RBC-283). | Planned (Milestone 3+) |

---

## 7. Current Milestone Deliverables (Milestones 1 & 2 Completed)

1. **ODE Numerical Integration Engine**: Robust `solve_ivp` adaptive RK45 runner with automatic mass-balance tracking, trajectory interpolation, and error bounds.
2. **Steady-State & Stability Auditing**: `SteadyStateSolver` utilizing non-linear root solving (`scipy.optimize.root`) and computing the analytical/numerical Jacobian eigenvalue spectrum to confirm asymptotic Lyapunov stability ($\operatorname{Re}(\lambda_i) < 0$).
3. **L2 Reference Range Validator**: Automated checks against healthy erythrocyte baselines ($[GSH] \in [1.5, 3.0]\text{ mM}$, $GSH/GSSG > 30$, $[NADPH] \in [0.01, 0.05]\text{ mM}$).
4. **Local Sensitivity Analysis**: Finite-difference perturbation engine computing normalized sensitivity coefficients ($S_{i,j} = \frac{\partial \ln Y_i}{\partial \ln P_j}$) for endpoints like GSH nadir and recovery time, outputting JSON summaries and visual tornado plots.
5. **Experimental Data Ingestion Pipeline**: Ingestion script parsing raw laboratory CSVs into verified Pydantic `ExperimentalRecord` schemas with automated concentration unit conversions (e.g., $\mu\text{mol/g Hb} \rightarrow \text{mM}$) and immutable SHA-256 source hashing.
6. **Bi-Substrate G6PD Kinetic Model**: Implementation of `rbc-g6pd-gsh-v2` with pyridine nucleotide pool conservation and deficiency profiling.
7. **FastAPI REST API**: Asynchronous service providing interactive OpenAPI documentation (`/docs`), simulation dispatch, and run query endpoints.

---

## 8. Quick Start & Execution Guide

### Prerequisites
- Python 3.11+
- Virtual environment with dependencies installed:
  ```bash
  pip install -e ".[dev]"
  ```

### Executing Key Scripts
- **Run the baseline simulation demo:**
  ```bash
  python scripts/run_demo.py
  ```
  *Produces trajectory CSVs for baseline, 0.05 mM, and 0.2 mM $H_2O_2$ boluses in `simulation_outputs/`.*

- **Compare G6PD deficiency scenarios:**
  ```bash
  python scripts/compare_g6pd_deficiency.py
  ```
  *Simulates challenges across $\alpha \in \{1.0, 0.5, 0.1, 0.0\}$ and records recovery deficits.*

- **Execute local parameter sensitivity analysis:**
  ```bash
  python scripts/run_sensitivity_analysis.py
  ```
  *Generates `simulation_outputs/sensitivity_tornado.png` and sensitivity metrics.*

- **Ingest and validate experimental records:**
  ```bash
  python scripts/ingest_data.py
  ```
  *Produces `data/processed/experimental_records.json` with SHA-256 provenance.*

- **Start the FastAPI backend:**
  ```bash
  uvicorn main:app --reload --port 8000
  ```
  *Access API documentation at `http://127.0.0.1:8000/docs`.*

- **Run all automated test suites:**
  ```bash
  pytest
  ```
  *(148 automated tests covering unit, scientific, numerical, and API functionality).*

---

## 9. Assumptions, Caveats & Known Limitations

- **Isolated Cytosolic Approximation**: The cell is modeled as a well-mixed, single-compartment aqueous volume without spatial gradients or membrane diffusion barriers.
- **Unmodeled Metabolic Sectors**: Glycolytic intermediates (ATP, 2,3-BPG, lactate), catalase sub-pathways, membrane lipid peroxidation cascades, and eryptotic signaling are not yet modeled in Milestone 2.
- **Constant Enzyme Abundance**: Total concentrations of GPx, GR, and G6PD are treated as constant over the simulation timeframe (valid for erythrocyte lifespans of ~120 days under acute hours-scale challenges).
- **Damage Index ($D$) is a Synthetic Proxy**: The cumulative oxidative damage parameter ($D$) is a heuristic mathematical surrogate connecting severe GSH depletion to hemolytic risk; it is not yet directly fitted to mechanical cell fragility assays.

---

## 10. Repository Directory Map

```
v-blood/
├── docs/                                # Technical & scientific specifications
│   ├── project_overview.md              # High-level architecture and scope
│   ├── model_specification.md           # Equations, rate laws, and parameter provenance
│   ├── steady_state_analysis.md         # Steady-state solver and stability math
│   ├── validation_plan.md               # L0–L5 validation requirements
│   └── assumptions_and_limitations.md   # Explicit boundary catalogue
├── data/
│   ├── raw/                             # Immutable source datasets
│   └── processed/                       # Curated ranges and ingested experimental records
├── models/                              # Versioned model registry definitions
├── simulation_outputs/                  # Exported trajectory CSVs and analysis plots
├── src/vblood/                          # Core Python library
│   ├── biology/                         # ODE RHS equations, parameters, and models
│   ├── simulation/                      # Numerical solvers (solve_ivp, steady-state)
│   ├── uncertainty/                     # Local parameter sensitivity and UQ
│   ├── validation/                      # Automated physiological validators
│   ├── schemas/                         # Pydantic data schemas
│   ├── api/                             # FastAPI application and routers
│   ├── chemistry/                       # Chemical identity and descriptor tools
│   └── reporting/                       # Typed interface contracts for LLM modules
├── scripts/                             # Executable command-line workflows
├── tests/                               # Comprehensive test suite (Unit, Scientific, API)
├── main.py                              # Entry point for ASGI server
└── pyproject.toml                       # Package build configuration & dependencies
```
