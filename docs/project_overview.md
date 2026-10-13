# Project Overview — V-Blood

## Vision

V-Blood is a research-oriented virtual experimental platform that combines mechanistic biological simulation, machine learning, uncertainty quantification, and LLM-based scientific explanation to support hypothesis generation around chemical effects on blood biology.

A researcher using V-Blood will eventually be able to:

1. Configure a chemical exposure scenario.
2. Simulate the response of selected blood components over time.
3. Inspect biological changes and compare scenarios.
4. Evaluate prediction uncertainty and model applicability.
5. Ask an AI assistant to explain what happened, with traceable reasoning.

## What V-Blood is not (critical)

- V-Blood does **not** replace laboratory experiments, animal studies, or clinical trials.
- V-Blood does **not** certify safety or toxicity for any chemical.
- V-Blood outputs are **simulation results**, not experimental observations.
- V-Blood should not be used to make regulatory, medical, or clinical decisions.

## Long-term architecture

The platform is designed around six principal layers:

| Layer | Description |
|---|---|
| Mechanistic engine | ODE-based biological reaction networks |
| ML layer | Chemical-response prediction, parameter estimation, surrogates |
| Uncertainty | Epistemic and aleatoric UQ, applicability-domain scoring |
| LLM assistant | Evidence-grounded explanation of simulation outputs |
| API | FastAPI endpoints exposing the engine and results |
| Frontend | Interactive React dashboard (planned) |

Each layer has stable, tested interfaces. The mechanistic engine runs independently of all other layers.

## Development philosophy

- Scientific correctness and reproducibility are primary engineering requirements.
- Every equation, parameter, and assumption is explicitly documented.
- No biological constants are invented or silently estimated without documentation.
- Outputs are never hardcoded to match expected-looking plots.
- All limitations and unsupported capabilities are catalogued.
- Tests are run and results are reported; passing tests do not guarantee biological correctness.

## Milestone roadmap

| Milestone | Scope | Status |
|---|---|---|
| 1 | RBC glutathione redox ODE engine + tests + demo | In Progress |
| 2 | Data ingestion schema + experimental evidence register | Planned |
| 3 | Parameter estimation from time-series data | Planned |
| 4 | FastAPI backend + simulation endpoints | Planned |
| 5 | ML chemical-response prediction baseline | Planned |
| 6 | LLM reporting module | Planned |
| 7 | React frontend dashboard | Planned |
