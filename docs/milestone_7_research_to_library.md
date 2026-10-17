# Milestone 7 Implementation Plan: LLM Compound Intelligence and Research-to-Library Pipeline

## 1. Executive Summary

Milestone 7 introduces an end-to-end, LLM-assisted research-to-library pipeline for the V-Blood platform. It enables researchers to submit unsupported chemical entities, resolve their identity through authoritative databases (e.g. PubChem), retrieve scientific literature (PubMed, Europe PMC, Crossref), extract structured findings, evaluate evidence tiers, assess compatibility against V-Blood's 5 ODE kinetic mechanism classes, generate parameter candidates with explicit provenance, validate them against 10 strict scientific gates, manage their lifecycle (`RESEARCHED`, `NEEDS_RESEARCH`, `CANDIDATE`, `SIMULATION_READY`, `REJECTED`), and persist approved compounds into the simulation catalog.

### Core Principle
**Automate literature research and candidate registration, but never confuse a plausible LLM-generated definition with a scientifically validated simulation model.**

---

## 2. Existing Baseline & Audit Findings

- **Backend tests:** 191 / 191 passing (`uv run pytest`).
- **Frontend tests:** 19 / 19 passing (`npm run test`).
- **Existing mechanisms (`src/vblood/scenarios/mechanisms.py`):**
  1. `DIRECT_OXIDANT` (H2O2-like bolus / infusion)
  2. `GSH_CONJUGATOR` (Electrophilic depletion of GSH)
  3. `REDOX_CYCLER` (NADPH-dependent catalytic generation of H2O2)
  4. `ENZYME_INHIBITOR` (Competitive or non-competitive G6PD / GR inhibition)
  5. `NADPH_DRAIN` (Direct enzymatic NADPH pool consumption)
- **Existing intelligence module (`src/vblood/intelligence/`):**
  - `CompoundCompatibilityChecker`: checks mechanism compatibility against supported models (`rbc-gsh-redox-v1`, `rbc-g6pd-gsh-v2`).
  - `evaluate_evidence_tier`: classifies evidence into `CURATED`, `ESTIMATED`, and `UNVERIFIED`.
- **Existing LLM provider (`src/vblood/interpretation/providers/llm_client.py`):**
  - ExternalLLMProvider with Gemini / OpenAI / Anthropic / local endpoints, native Gemini REST support, JSON parsing, and fallback.

---

## 3. Architecture & New Components

### A. Data Schemas (`src/vblood/intelligence/schemas.py`)
- `ResearchLifecycleStatus`: `NEEDS_RESEARCH`, `RESEARCHED`, `CANDIDATE`, `SIMULATION_READY`, `REJECTED`
- `ParameterProvenance`: `MEASURED`, `DERIVED`, `INFERRED`, `SYNTHETIC`, `MISSING`
- `ChemicalIdentity`: preferred name, synonyms, molecular formula, SMILES, InChIKey, InChI, PubChem CID, charge, entity type.
- `LiteratureSource`: source_id, title, authors, journal, year, DOI, PMID, URL, abstract, erythrocyte_relevant.
- `EvidenceFinding`: finding_id, source_id, biological_system, species, human_erythrocyte_relevance, experimental_conditions, concentration, units, duration, observed_outcomes, proposed_mechanism, exact_quote, evidence_grade, rationale.
- `CandidateParameter`: name, mechanism, value, units, min_bound, max_bound, original_value, original_units, conversion_method, provenance, evidence_level, confidence_score.
- `ProposedMechanismMapping`: mechanism_type, is_compatible, target_enzyme, inhibition_type, confidence, assumptions, unresolved_questions, parameters.
- `ValidationGateResult` & `CandidateValidationSummary`: 10-gate check results.
- `ResearchDossier`: comprehensive research record containing all the above, timestamps, audit history, revision numbers.
- `ResearchJobStatus`: asynchronous job progress tracking.

### B. Core Intelligence Services (`src/vblood/intelligence/`)
1. `identity.py` (`ChemicalIdentityResolver`):
   - Queries PubChem PUG REST API for structure, formula, InChIKey, synonyms, and CID.
   - Disambiguation and synonym normalization.
   - Offline / mock cache for reproducible, deterministic testing.
   - Syntactic and RDKit validation via `vblood.chemistry.identifiers`.
2. `retrieval.py` (`LiteratureRetrievalService`):
   - Multi-source search (Europe PMC, PubMed, Crossref, PubChem).
   - Erythrocyte-prioritized query builder.
   - Deduplication by DOI, PMID, and normalized title.
   - Prompt-injection sanitization for untrusted retrieved literature.
   - Offline deterministic fixtures for CI reliability.
3. `extraction.py` (`EvidenceExtractionService`):
   - Extracts structured findings and experimental conditions using LLM or deterministic rule-based extractor.
   - Grounding validation against source text quotes.
4. `grading.py` (`EvidenceGradingService`):
   - Separate finding-level and compound-level grading.
   - Explicit scoring rubrics for human erythrocyte directness.
5. `mechanisms.py` (`MechanismMappingService`):
   - Maps extracted findings to the 5 V-Blood kinetic mechanism classes.
   - Assigns parameter provenance (`MEASURED`, `DERIVED`, `INFERRED`, `SYNTHETIC`, `MISSING`).
   - Identifies unmodeled pathways and outputs structured incompatibility reports.
6. `validator.py` (`CandidateValidator`):
   - Enforces the 10 scientific validation gates:
     1. Identity consistency & canonical SMILES/InChIKey.
     2. Schema & data-type integrity.
     3. Source existence & DOI/PMID traceability.
     4. Unit & dimensional consistency.
     5. Parameter provenance & missing-value handling.
     6. Mechanism compatibility with ODE engine.
     7. Required parameter completeness.
     8. Numeric bounds validation.
     9. Simulation-engine test integration.
     10. Catalog regression safety.
7. `repository.py` (`ResearchRepository`):
   - Persistent candidate store (`data/processed/research_candidates.json`) with audit trail.
   - Idempotent registration with duplicate detection by InChIKey.
   - Dynamic integration with `CompoundLibrary`: approved `SIMULATION_READY` compounds are dynamically made available to the scenario engine, while ineligible compounds remain research-only records.
8. `pipeline.py` (`CompoundResearchOrchestrator`):
   - Coordinates end-to-end research workflow and manages async jobs.

---

## 4. API Endpoints (`src/vblood/api/app.py`)

- `POST /research/jobs` — Initiate substance research job (returns `job_id`).
- `GET /research/jobs/{job_id}` — Check status and stage progress.
- `GET /research/candidates` — List all research candidates and dossiers.
- `GET /research/candidates/{candidate_id}` — Get full dossier.
- `POST /research/candidates/{candidate_id}/validate` — Re-run 10 validation gates.
- `POST /research/candidates/{candidate_id}/approve` — Approve eligible candidate for simulation.
- `POST /research/candidates/{candidate_id}/reject` — Reject candidate.
- `POST /research/candidates/{candidate_id}/refresh` — Refresh literature and research.

---

## 5. Frontend Workstation Integration (`frontend/src/`)

- Add `Module 06: Compound Intelligence` to the primary navigation rail.
- Research Entry: Substance input, optional research objective, scope indicators.
- Pipeline Telemetry: Real-time progress tracker through all 7 research stages.
- Research Dossier Plate:
  - Chemical identity & formula viewer.
  - Literature source registry with direct DOI/PMID external links.
  - Structured findings ledger with evidence grades and quotes.
  - Mechanism compatibility badge & unmodeled physics disclaimer.
  - Kinetic parameters ledger with provenance tags.
  - 10-Gate validation checklist.
  - Lifecycle transition actions (Approve, Revalidate, Reject, Load in Playground).
- Catalog & Playground Integration:
  - Curated vs Researched compound filters.
  - Immediate selection of approved compounds in scenario builder.

---

## 6. Testing Strategy

- **Unit tests:** Identity resolution, retrieval deduplication, extraction schema validation, evidence grading, mechanism mapping, parameter bounds, 10 validation gates, audit logging, prompt-injection defense.
- **Integration tests:** End-to-end research job execution to persisted candidate, candidate approval to catalog availability, ineligible candidate rejection in simulation engine.
- **Frontend tests:** Component rendering, research form submission, dossier inspection, candidate approval, and scenario loading.
- **Regression assurance:** 100% pass on all 191 backend and 19 frontend baseline tests.
