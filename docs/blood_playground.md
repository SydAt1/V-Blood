# V-Blood Blood Playground Frontend Specification (Milestone 5)

## 1. Overview

**Blood Playground** is the interactive research workstation for the **V-Blood** mechanistic red blood cell simulation platform. It bridges in silico ordinary differential equation (ODE) models and chemical mechanism libraries to an accessible, responsive research interface without compromising scientific integrity.

### Core Philosophy
1. **Source of Truth:** The FastAPI backend is the authoritative source of biological truth; biochemical equations are never re-implemented or estimated in JavaScript/TypeScript.
2. **Scientific Honesty:** Evidence levels (`CURATED`, `ESTIMATED`, `UNVERIFIED`) and model boundaries (no glycolysis/ATP, no membrane morphology) are prominently surfaced rather than hidden in disclaimers.
3. **No Unmodeled Morphology:** Cytosolic redox states (GSH, NADPH, D) are visually rendered, but the platform explicitly warns that physical membrane deformations (echinocytosis, crenation, swelling) are not simulated.

---

## 2. Technology Stack & Architecture

- **Core Framework:** React 19, TypeScript 5.8+, Vite 8
- **Styling:** Tailwind CSS v4, dark scientific research theme
- **Icons:** Lucide React
- **Testing:** Vitest, React Testing Library, jsdom
- **Data Transport:** Typed `fetch` client with SSE (`EventSource`) support for real-time visual streaming.

### Directory Structure

```text
frontend/src/
├── api/
│   └── client.ts             # Typed fetch client, error handling, SSE visual stream subscriber
├── types/
│   └── api.ts                # TypeScript interfaces matching backend Pydantic schemas exactly
├── components/
│   ├── Header.tsx            # Navigation, backend connectivity status, permanent research notice
│   ├── EvidenceBadge.tsx     # CURATED (emerald), ESTIMATED (amber), UNVERIFIED (rose) badges
│   ├── StressBadge.tsx       # healthy, stressed, severely_stressed, lysis_risk badges
│   ├── AlertBox.tsx          # Scientific limitation and boundary callouts
│   └── TimeSeriesChart.tsx   # Interactive SVG chart with channel toggles and hover crosshairs
├── features/
│   ├── compounds/
│   │   ├── CompoundCatalog.tsx   # Searchable, filterable chemical library
│   │   └── CompoundModal.tsx     # In-depth SMILES, InChIKey, bounds, and literature citations
│   ├── scenarios/
│   │   ├── ScenarioBuilder.tsx   # Multi-compound exposure, waveform, G6PD alpha, control compare
│   │   └── ScenarioResults.tsx   # Recovery metrics, time-series plots, JSON/CSV exports
│   ├── population/
│   │   ├── PopulationBuilder.tsx # Cohort size N (10..5000), G6PD alpha, seed
│   │   ├── PopulationPercentileChart.tsx # Shaded intervals (p5-p95, p25-p75, median p50)
│   │   └── PopulationResults.tsx # Depleted fraction, lysis risk proxy, runtime reporting
│   ├── visualization/
│   │   └── ErythrocyteViewer.tsx # SVG biconcave disc, timeline slider, speed controls, SSE stream
│   ├── runs/
│   │   └── SessionRunHistory.tsx # Local session log, run reload, export
│   └── models/
│       └── ModelInfoView.tsx     # Registered model metadata, parameters, unmodeled physics
├── pages/
│   └── PlaygroundPage.tsx        # Orchestrates scenario execution and visual animation
├── App.tsx                       # Root application layout and tab state
└── test/                         # Unit & component test suites (15 tests passing)
```

---

## 3. Configuration & Running Locally

### Prerequisites
- Node.js >= 18 (Tested on v20.19.4)
- Python 3.11+ virtual environment with V-Blood backend installed

### Environment Configuration
The frontend reads the backend URL from `VITE_API_BASE_URL`.
- **Default (Development):** In `vite.config.ts`, Vite automatically proxies `/compounds`, `/scenarios`, `/models`, and `/health` to `http://127.0.0.1:8000`.
- **Custom Backend URL:** Set `VITE_API_BASE_URL=http://your-server:8000` in a `.env.local` file inside `frontend/`.

### Development Server
```bash
# Terminal 1: Backend
.\.venv\Scripts\python.exe -m uvicorn vblood.api.app:app --reload --host 127.0.0.1 --port 8000

# Terminal 2: Frontend
cd frontend
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser.

### Running Tests
```bash
cd frontend
npm test
```

### Production Build & Type Checking
```bash
cd frontend
npm run build
```

---

## 4. Key Functional Features

### A. Chemical Compound Catalog
- Browse all curated compounds from `data/processed/compounds.json`.
- Filter by mechanism (`DIRECT_OXIDANT`, `GSH_CONJUGATOR`, `REDOX_CYCLER`, `ENZYME_INHIBITOR`, `NADPH_DRAIN`).
- Filter by evidence level (`CURATED`, `ESTIMATED`, `UNVERIFIED`).
- Inspect complete parameter bounds and literature citations.
- **Unverified Compound Handling:** Compounds such as `Xenobiotic X-101` carry prominent red warning badges and are flagged in all subsequent simulation runs.

### B. Single-Cell Simulation Playground
- Build single or multi-compound mixtures with explicit doses (0.001 to 20.0 mM).
- Select exposure profile (`BOLUS`, `INFUSION`, `REPEATED_PULSES`).
- Set G6PD enzyme activity multiplier ($\alpha \in [0.01, 1.00]$).
- Optional parallel execution of an untreated baseline control.
- Primary result plots for $[\text{GSH}]$, $[\text{GSSG}]$, $[\text{NADPH}]$, $[H_2O_2]$, and Damage proxy $D$.
- Displays derived metrics: GSH nadir, peak GSSG, 90% recovery time, net total glutathione loss %, and damage onset time.
- Direct export to JSON and CSV.

### C. Vectorized Population Cohort Playground
- Simulate up to $N = 5,000$ heterogeneous red blood cells sampled across biological priors.
- Fast execution (~1.2 seconds for 1,000 cells) reported in real-time.
- Visualizes percentile envelopes ($p_5 \dots p_{95}$) and median trajectory ($p_{50}$).
- Computes cohort crisis fractions: $\%$ cells with $[\text{GSH}] < 1.0\,\text{mM}$ and $\%$ cells with damage proxy $D > 0.30$.
- Explains that damage proxy thresholds are model-defined stress indicators, not clinical hemolysis assays.

### D. Erythrocyte Visualization & Frame Playback
- Scalable SVG biconcave erythrocyte disc silhouette with central pallor.
- Cytosolic color transitions mapped to normalized biochemical health:
  - `healthy` ($\text{GSH} \ge 1.5\,\text{mM}, D < 0.05$)
  - `stressed` ($\text{GSH} \in [0.8, 1.5)\,\text{mM}, D \in [0.05, 0.20)$)
  - `severely_stressed` ($\text{GSH} \in [0.25, 0.8)\,\text{mM}, D \in [0.20, 0.50)$)
  - `lysis_risk` ($\text{GSH} < 0.25\,\text{mM}$ or $D \ge 0.50$)
- Timeline scrubbing slider, play/pause controls, and 1x/2x/5x/10x playback speed.
- Real-time Server-Sent Events (SSE) streaming endpoint integration (`/scenarios/{run_id}/stream`).
- Explicit warning: Physical membrane deformation (crenation, spiculation) is unmodeled.

### E. Session Run History
- Logs all single-cell and cohort simulations during the current browser session.
- One-click reloading of historical runs back into the interactive viewer.
- Full provenance auditing (model ID, compound IDs, G6PD alpha, seed).

---

## 5. Verification & Test Results

- **Frontend Vitest Suite:** 15 / 15 tests passing (100% pass rate).
- **TypeScript & Vite Build:** 0 type errors, clean production bundle in 444ms.
- **Backend API Suite:** 16 / 16 pytest tests passing.
- **Backend Scientific Suite:** All biological and mass-conservation tests continue to pass.
