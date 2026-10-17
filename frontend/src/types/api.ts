/**
 * TypeScript representations of V-Blood Pydantic schemas.
 * Derived directly from src/vblood/api/schemas.py, src/vblood/scenarios/, and src/vblood/schemas/.
 * DO NOT invent fields or alter units.
 */

export type EvidenceLevel = 'CURATED' | 'ESTIMATED' | 'UNVERIFIED';

export type MechanismType =
  | 'DIRECT_OXIDANT'
  | 'GSH_CONJUGATOR'
  | 'REDOX_CYCLER'
  | 'ENZYME_INHIBITOR'
  | 'NADPH_DRAIN';

export type ExposureProfile = 'BOLUS' | 'INFUSION' | 'REPEATED_PULSES';

export type CellVisualState =
  | 'healthy'
  | 'stressed'
  | 'severely_stressed'
  | 'lysis_risk';

export interface CompoundResponse {
  compound_id: string;
  name: string;
  smiles: string;
  inchikey: string;
  mechanism_type: MechanismType | string;
  default_parameters: Record<string, any>;
  parameter_ranges: Record<string, [number, number]>;
  exposure_units: string;
  evidence_level: EvidenceLevel;
  is_unverified: boolean;
  provenance: string;
  confidence_score: number;
}

export interface CompoundExposure {
  compound_id: string;
  dose_mM: number;
  parameter_overrides?: Record<string, number>;
}

export interface ScenarioRequest {
  compounds: CompoundExposure[];
  exposure_profile: ExposureProfile;
  duration_s: number;
  g6pd_alpha: number;
  model_version: 'rbc-g6pd-gsh-v2' | 'rbc-gsh-redox-v1' | string;
  pulse_period_s?: number;
  pulse_duration_s?: number;
  infusion_rate_mM_s?: number;
}

export interface TrajectoryPoint {
  t_s: number;
  gsh_mM: number;
  gssg_mM: number;
  h2o2_mM: number;
  nadph_mM: number;
  damage: number;
  hemolysis_pct: number;
  gsh_gssg_ratio: number;
}

export interface ScenarioDerivedMetrics {
  gsh_nadir_mM: number;
  gssg_peak_mM: number;
  time_to_90pct_recovery_s: number | null;
  net_total_glutathione_loss_pct: number;
  damage_onset_time_s: number | null;
}

export interface ScenarioRunResponse {
  run_id: string;
  scenario_request: ScenarioRequest;
  derived_metrics: ScenarioDerivedMetrics;
  has_unverified_compounds: boolean;
  unverified_compounds: string[];
  compound_summaries: Array<{
    compound_id: string;
    name: string;
    mechanism: string;
    evidence_level: EvidenceLevel;
    is_unverified: boolean;
    provenance: string;
  }>;
  interaction_assumptions: string[];
  trajectory_length: number;
  research_disclaimer: string;
  trajectory?: TrajectoryPoint[];
}

export interface PopulationRequest {
  scenario_request: ScenarioRequest;
  n_cells: number;
  random_seed?: number;
  gsh_mild_threshold_mM?: number;
  gsh_crisis_threshold_mM?: number;
  hemolysis_proxy_threshold_pct?: number;
}

export interface PopulationPercentileBands {
  time_points_s: number[];
  gsh_p5: number[];
  gsh_p25: number[];
  gsh_p50: number[];
  gsh_p75: number[];
  gsh_p95: number[];
  nadph_p5: number[];
  nadph_p25: number[];
  nadph_p50: number[];
  nadph_p75: number[];
  nadph_p95: number[];
  damage_p5: number[];
  damage_p25: number[];
  damage_p50: number[];
  damage_p75: number[];
  damage_p95: number[];
}

export interface PopulationResult {
  n_cells: number;
  execution_time_ms: number;
  percentile_bands: PopulationPercentileBands;
  pct_cells_gsh_depleted: number;
  pct_cells_lysis_risk: number;
  n_depleted_cells: number;
  n_lysis_risk_cells: number;
  heterogeneity_parameters_sampled: string[];
  research_disclaimer: string;
}

export interface VisualFrame {
  t_s: number;
  normalized_gsh: number;
  normalized_nadph: number;
  damage: number;
  hemolysis_pct: number;
  cell_state: CellVisualState;
  state_classification_type: 'MODEL_DERIVED' | 'ILLUSTRATIVE';
  morphology_simulated: boolean;
}

export interface VisualTrajectoryResponse {
  run_id: string;
  total_frames: number;
  playback_duration_s: number;
  frames: VisualFrame[];
  model_notes: string;
}

export interface ModelDetailResponse {
  model_id: string;
  name: string;
  version: string;
  description: string;
  supported_scenarios: string[];
  state_variables: string[];
  state_variable_units: string[];
  compartment: string;
  parameter_count: number;
  evidence_status_summary: Record<string, number>;
  literature_sources: string[];
}

export interface HealthResponse {
  status: string;
  application_version: string;
  model_registry_status: string;
  registered_models_count: number;
  scientific_validation_status: string;
}

export interface StoredRunRecord {
  id: string;
  timestamp: string;
  title: string;
  type: 'single' | 'population';
  compoundNames: string[];
  modelVersion: string;
  g6pdAlpha: number;
  hasUnverified: boolean;
  result?: ScenarioRunResponse;
  populationResult?: PopulationResult;
}

// =========================================================================
// Milestone 6: Scientific Interpretation Interfaces
// =========================================================================

export interface GroundingEvaluation {
  passed: boolean;
  checked_metrics: Record<string, any>;
  disclaimers_present: boolean;
  unverified_compound_warning_present: boolean;
  flags: string[];
}

export interface PlaygroundInterpretationRequest {
  scenario_request: ScenarioRequest;
  scenario_result: any;
  control_result?: any;
  provider_preference?: 'auto' | 'deterministic' | 'llm';
  force_refresh?: boolean;
}

export interface PlaygroundInterpretationResponse {
  executive_summary: string;
  nadir_analysis: string;
  pathway_flux_breakdown: string;
  control_comparison: string;
  uncertainty_and_limitations: string;
  suggested_experiments: string[];
  provider_used: string;
  fallback_applied: boolean;
  fallback_reason?: string | null;
  grounding?: GroundingEvaluation | null;
  generated_at_utc: string;
}

export interface CohortInterpretationRequest {
  population_request: PopulationRequest;
  population_result: any;
  provider_preference?: 'auto' | 'deterministic' | 'llm';
  force_refresh?: boolean;
}

export interface CohortInterpretationResponse {
  executive_summary: string;
  tail_risk_analysis: string;
  g6pd_interaction_analysis: string;
  lysis_risk_evaluation: string;
  uncertainty_and_limitations: string;
  suggested_experiments: string[];
  provider_used: string;
  fallback_applied: boolean;
  fallback_reason?: string | null;
  grounding?: GroundingEvaluation | null;
  generated_at_utc: string;
}

export interface InterpretationStatusResponse {
  providers_available: string[];
  default_provider: string;
  llm_configured: boolean;
  llm_model?: string | null;
  guardrails_active: boolean;
  unmodeled_physics_declared: string[];
}

/* ------------------------------------------------------------------ */
/* Milestone 7: Compound Research-to-Library Schemas                  */
/* ------------------------------------------------------------------ */

export type ResearchLifecycleStatus =
  | 'NEEDS_RESEARCH'
  | 'RESEARCHED'
  | 'CANDIDATE'
  | 'SIMULATION_READY'
  | 'REJECTED';

export type ParameterProvenance =
  | 'MEASURED'
  | 'DERIVED'
  | 'INFERRED'
  | 'SYNTHETIC'
  | 'MISSING';

export type ChemicalEntityType =
  | 'SMALL_MOLECULE'
  | 'ELEMENT'
  | 'ION'
  | 'SALT'
  | 'METABOLITE'
  | 'FORMULATION'
  | 'UNKNOWN';

export type LiteratureSourceType =
  | 'PUBMED'
  | 'EUROPE_PMC'
  | 'CROSSREF'
  | 'PUBCHEM'
  | 'MANUAL';

export type ResearchPipelineStage =
  | 'INITIALIZED'
  | 'RESOLVING_IDENTITY'
  | 'RETRIEVING_LITERATURE'
  | 'EXTRACTING_EVIDENCE'
  | 'GRADING_EVIDENCE'
  | 'ASSESSING_COMPATIBILITY'
  | 'ESTIMATING_PARAMETERS'
  | 'VALIDATING_CANDIDATE'
  | 'PERSISTING_DOSSIER'
  | 'COMPLETED'
  | 'FAILED';

export interface ChemicalIdentity {
  preferred_name: string;
  common_names: string[];
  molecular_formula?: string | null;
  smiles: string;
  inchikey: string;
  inchi?: string | null;
  pubchem_cid?: number | null;
  entity_type: ChemicalEntityType;
  charge: number;
  molecular_weight?: number | null;
  source: string;
  retrieved_at: string;
  is_ambiguous: boolean;
  ambiguity_candidates: string[];
}

export interface LiteratureSource {
  source_id: string;
  title: string;
  authors: string[];
  journal: string;
  year?: number | null;
  doi?: string | null;
  pmid?: string | null;
  pmcid?: string | null;
  url: string;
  abstract: string;
  source_type: LiteratureSourceType;
  full_text_available: boolean;
  erythrocyte_relevant: boolean;
  retrieval_timestamp: string;
}

export interface EvidenceFinding {
  finding_id: string;
  source_id: string;
  biological_system: string;
  species: string;
  is_human_erythrocyte: boolean;
  experimental_conditions: string;
  concentration?: number | null;
  concentration_unit?: string | null;
  exposure_duration_s?: number | null;
  observed_outcomes: string;
  proposed_mechanism: string;
  quantitative_measurements: Record<string, any>;
  uncertainty_notes: string;
  controls_and_limitations: string;
  supports_proposed_effect: boolean;
  exact_quote: string;
  finding_evidence_level: string;
  grade_rationale: string;
}

export interface CandidateParameter {
  name: string;
  mechanism: string;
  value: number;
  units: string;
  min_bound: number;
  max_bound: number;
  original_value?: number | null;
  original_units?: string | null;
  conversion_method: string;
  provenance: ParameterProvenance;
  evidence_level: string;
  confidence_score: number;
  assumptions: string[];
  is_identifiable: boolean;
  validation_status: string;
}

export interface ProposedMechanismMapping {
  mechanism_type: string;
  is_compatible: boolean;
  target_enzyme?: string | null;
  inhibition_type?: string | null;
  confidence: number;
  supporting_finding_ids: string[];
  assumptions: string[];
  unmodeled_aspects: string[];
  unresolved_questions: string[];
  parameters: CandidateParameter[];
}

export interface ValidationGateResult {
  gate_name: string;
  passed: boolean;
  message: string;
  severity: string;
}

export interface CandidateValidationSummary {
  is_valid: boolean;
  simulation_eligible: boolean;
  gates: ValidationGateResult[];
  blocking_reasons: string[];
  warnings: string[];
}

export interface AuditLogEntry {
  timestamp: string;
  action: string;
  actor: string;
  previous_status?: ResearchLifecycleStatus | null;
  new_status: ResearchLifecycleStatus;
  notes: string;
}

export interface ResearchDossier {
  candidate_id: string;
  query_name: string;
  research_objective: string;
  target_scope: string;
  status: ResearchLifecycleStatus;
  chemical_identity: ChemicalIdentity;
  sources: LiteratureSource[];
  findings: EvidenceFinding[];
  mechanism_mappings: ProposedMechanismMapping[];
  validation_summary: CandidateValidationSummary;
  limitations: string[];
  unresolved_questions: string[];
  audit_history: AuditLogEntry[];
  created_at: string;
  updated_at: string;
  pipeline_version: string;
  llm_provider_metadata: Record<string, any>;
  prompt_version: string;
  revision: number;
}

export interface ResearchJobStatus {
  job_id: string;
  query_name: string;
  stage: ResearchPipelineStage;
  progress_pct: number;
  message: string;
  error?: string | null;
  candidate_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ResearchSubmissionRequest {
  substance_name: string;
  research_objective?: string | null;
  force_refresh?: boolean;
}
