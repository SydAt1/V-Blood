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
