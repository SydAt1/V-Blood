"""
Schemas for LLM Compound Intelligence and Research-to-Library Pipeline (Milestone 7).

Defines typed Pydantic models for chemical identity resolution, literature sources,
structured evidence findings, mechanism compatibility, parameter provenance,
candidate validation gates, and versioned research dossiers.
"""

from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ResearchLifecycleStatus(str, Enum):
    """Lifecycle state of a chemical research record."""

    NEEDS_RESEARCH = "NEEDS_RESEARCH"        # Insufficient or conflicting evidence
    RESEARCHED = "RESEARCHED"                # Identity resolution & literature review complete
    CANDIDATE = "CANDIDATE"                  # Structured candidate created, pending validation/approval
    SIMULATION_READY = "SIMULATION_READY"    # Approved and verified for active ODE scenario simulation
    REJECTED = "REJECTED"                    # Failed validation or rejected during scientific review


class ParameterProvenance(str, Enum):
    """Provenance and derivation category for kinetic parameters."""

    MEASURED = "MEASURED"                    # Directly reported in human erythrocyte or relevant experiment
    DERIVED = "DERIVED"                      # Calculated from reported experimental data using documented method
    INFERRED = "INFERRED"                    # Estimated indirectly from related chemical analogies or cell lines
    SYNTHETIC = "SYNTHETIC"                  # Exploratory estimate not experimentally established
    MISSING = "MISSING"                      # Insufficient information to propose a defensible value


class ChemicalEntityType(str, Enum):
    """Classification of chemical entity type to prevent interchangeable misidentifications."""

    SMALL_MOLECULE = "SMALL_MOLECULE"
    ELEMENT = "ELEMENT"
    ION = "ION"
    SALT = "SALT"
    METABOLITE = "METABOLITE"
    FORMULATION = "FORMULATION"
    UNKNOWN = "UNKNOWN"


class LiteratureSourceType(str, Enum):
    """Authoritative source database for retrieved evidence."""

    PUBMED = "PUBMED"
    EUROPE_PMC = "EUROPE_PMC"
    CROSSREF = "CROSSREF"
    PUBCHEM = "PUBCHEM"
    MANUAL = "MANUAL"


class ResearchPipelineStage(str, Enum):
    """Discrete sequential stages of the research orchestration pipeline."""

    INITIALIZED = "INITIALIZED"
    RESOLVING_IDENTITY = "RESOLVING_IDENTITY"
    RETRIEVING_LITERATURE = "RETRIEVING_LITERATURE"
    EXTRACTING_EVIDENCE = "EXTRACTING_EVIDENCE"
    GRADING_EVIDENCE = "GRADING_EVIDENCE"
    ASSESSING_COMPATIBILITY = "ASSESSING_COMPATIBILITY"
    ESTIMATING_PARAMETERS = "ESTIMATING_PARAMETERS"
    VALIDATING_CANDIDATE = "VALIDATING_CANDIDATE"
    PERSISTING_DOSSIER = "PERSISTING_DOSSIER"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# --------------------------------------------------------------------------- #
# Chemical Identity
# --------------------------------------------------------------------------- #


class ChemicalIdentity(BaseModel):
    """Resolved chemical identity with traceable authoritative identifiers."""

    model_config = ConfigDict(frozen=True)

    preferred_name: str = Field(description="Canonical IUPAC or authoritative name.")
    common_names: list[str] = Field(default_factory=list, description="Common names and synonyms.")
    molecular_formula: str | None = Field(default=None, description="Hill system molecular formula.")
    smiles: str = Field(description="Canonical SMILES structure representation.")
    inchikey: str = Field(description="Standard 27-character IUPAC InChIKey.")
    inchi: str | None = Field(default=None, description="Full IUPAC InChI string.")
    pubchem_cid: int | None = Field(default=None, description="PubChem Compound Identification Number.")
    entity_type: ChemicalEntityType = Field(
        default=ChemicalEntityType.SMALL_MOLECULE,
        description="Distinguishes element, ion, salt, metabolite, or small molecule.",
    )
    charge: int = Field(default=0, description="Formal molecular or ionic charge.")
    molecular_weight: float | None = Field(default=None, description="Molecular mass in g/mol.")
    source: str = Field(default="PubChem", description="Source repository of resolved identity.")
    retrieved_at: str = Field(description="ISO-8601 timestamp of identity resolution.")
    is_ambiguous: bool = Field(default=False, description="True if query resolved to multiple candidates.")
    ambiguity_candidates: list[str] = Field(
        default_factory=list,
        description="Alternative entities if query was ambiguous.",
    )


# --------------------------------------------------------------------------- #
# Literature Sources & Structured Findings
# --------------------------------------------------------------------------- #


class LiteratureSource(BaseModel):
    """Normalized, deduplicated scientific publication or database record."""

    model_config = ConfigDict(frozen=True)

    source_id: str = Field(description="Unique internal source identifier (e.g. src_pmid_12345).")
    title: str = Field(description="Article title.")
    authors: list[str] = Field(default_factory=list, description="Author list.")
    journal: str = Field(default="", description="Journal name.")
    year: int | None = Field(default=None, description="Publication year.")
    doi: str | None = Field(default=None, description="Digital Object Identifier.")
    pmid: str | None = Field(default=None, description="PubMed ID.")
    pmcid: str | None = Field(default=None, description="PubMed Central ID.")
    url: str = Field(description="Permanent or canonical external link.")
    abstract: str = Field(default="", description="Source abstract text.")
    source_type: LiteratureSourceType = Field(default=LiteratureSourceType.PUBMED)
    full_text_available: bool = Field(default=False, description="True if open access full text was accessed.")
    erythrocyte_relevant: bool = Field(
        default=False,
        description="True if human red blood cells or erythrocytes are investigated.",
    )
    retrieval_timestamp: str = Field(description="ISO-8601 timestamp of retrieval.")


class EvidenceFinding(BaseModel):
    """Structured, graded factual finding extracted from a literature source."""

    model_config = ConfigDict(frozen=True)

    finding_id: str = Field(description="Unique finding identifier (e.g. fnd_001).")
    source_id: str = Field(description="Reference to LiteratureSource.source_id.")
    biological_system: str = Field(
        description="Biological test system (e.g., Human erythrocytes in vitro, intact blood, rat hepatocytes).",
    )
    species: str = Field(default="Homo sapiens", description="Experimental organism/species.")
    is_human_erythrocyte: bool = Field(
        default=False,
        description="Directness flag: True if human red blood cells were directly assayed.",
    )
    experimental_conditions: str = Field(
        default="",
        description="Buffer, temperature, hematocrit, pre-incubation, or assay details.",
    )
    concentration: float | None = Field(default=None, description="Reported compound concentration.")
    concentration_unit: str | None = Field(default=None, description="Reported concentration units (e.g., uM, mM).")
    exposure_duration_s: float | None = Field(default=None, description="Exposure duration in seconds.")
    observed_outcomes: str = Field(
        description="Observed biological outcome (e.g., GSH depletion, GSSG increase, methemoglobin, lysis).",
    )
    proposed_mechanism: str = Field(
        description="Mechanistic pathway proposed by study (e.g., catalytic redox cycling, GSH conjugation).",
    )
    quantitative_measurements: dict[str, Any] = Field(
        default_factory=dict,
        description="Specific numerical endpoints, rate constants, or percentages.",
    )
    uncertainty_notes: str = Field(
        default="",
        description="Reported experimental error, variance, standard deviation, or limitations.",
    )
    controls_and_limitations: str = Field(
        default="",
        description="Relevant experimental controls or noted confounding factors.",
    )
    supports_proposed_effect: bool = Field(
        default=True,
        description="True if finding supports redox activity; False if contradictory/negative.",
    )
    exact_quote: str = Field(
        default="",
        description="Direct supporting passage from source text for grounding validation.",
    )
    finding_evidence_level: str = Field(
        default="ESTIMATED",
        description="Tier assigned to this specific finding (CURATED, ESTIMATED, UNVERIFIED).",
    )
    grade_rationale: str = Field(
        default="",
        description="Scientific justification for finding grade based on directness and rigor.",
    )


# --------------------------------------------------------------------------- #
# Kinetic Parameters & Proposed Mechanisms
# --------------------------------------------------------------------------- #


class CandidateParameter(BaseModel):
    """Parameter value proposed for simulation scenario integration."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(description="Parameter variable name matching V-Blood mechanism schemas.")
    mechanism: str = Field(description="Mechanism class this parameter belongs to.")
    value: float = Field(description="Numeric value in standardized simulation units.")
    units: str = Field(description="Standardized simulation units (e.g. mM, s^-1, mM^-1 s^-1).")
    min_bound: float = Field(description="Allowable minimum physiological/physical bound.")
    max_bound: float = Field(description="Allowable maximum physiological/physical bound.")
    original_value: float | None = Field(default=None, description="Raw value reported in source literature.")
    original_units: str | None = Field(default=None, description="Raw units reported in source literature.")
    conversion_method: str = Field(
        default="Direct conversion",
        description="Explicit derivation formula or unit conversion path.",
    )
    provenance: ParameterProvenance = Field(
        default=ParameterProvenance.INFERRED,
        description="Provenance category: MEASURED, DERIVED, INFERRED, SYNTHETIC, MISSING.",
    )
    evidence_level: str = Field(
        default="ESTIMATED",
        description="Evidence tier (CURATED, ESTIMATED, UNVERIFIED).",
    )
    confidence_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence score in [0.0, 1.0].",
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="Biochemical assumptions underlying this parameter value.",
    )
    is_identifiable: bool = Field(
        default=True,
        description="True if value is identifiable from retrieved evidence; False if missing/unconstrained.",
    )
    validation_status: str = Field(
        default="PENDING",
        description="Validation outcome for this specific parameter (VALID, OUT_OF_BOUNDS, MISSING).",
    )


class ProposedMechanismMapping(BaseModel):
    """Mapping of biological evidence to an existing V-Blood ODE mechanism class."""

    model_config = ConfigDict(frozen=True)

    mechanism_type: str = Field(description="Mapped class: DIRECT_OXIDANT, GSH_CONJUGATOR, REDOX_CYCLER, etc.")
    is_compatible: bool = Field(description="True if mathematically supported by current V-Blood ODE engine.")
    target_enzyme: str | None = Field(default=None, description="For ENZYME_INHIBITOR: G6PD or GR.")
    inhibition_type: str | None = Field(
        default=None,
        description="For ENZYME_INHIBITOR: COMPETITIVE or NON_COMPETITIVE.",
    )
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Overall mapping confidence.")
    supporting_finding_ids: list[str] = Field(
        default_factory=list,
        description="Finding IDs providing direct or indirect evidence for this mechanism.",
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="Simplifications made to fit the ODE formulation.",
    )
    unmodeled_aspects: list[str] = Field(
        default_factory=list,
        description="Biological aspects of the drug not represented in the ODE engine.",
    )
    unresolved_questions: list[str] = Field(
        default_factory=list,
        description="Scientific uncertainties remaining from literature.",
    )
    parameters: list[CandidateParameter] = Field(
        default_factory=list,
        description="Proposed parameter set for this mechanism.",
    )


# --------------------------------------------------------------------------- #
# Validation Gates & Audit Records
# --------------------------------------------------------------------------- #


class ValidationGateResult(BaseModel):
    """Result of a single deterministic validation gate check."""

    model_config = ConfigDict(frozen=True)

    gate_name: str = Field(description="Short identifier for validation gate.")
    passed: bool = Field(description="True if candidate satisfies gate criteria.")
    message: str = Field(description="Detailed scientific reason or failure explanation.")
    severity: str = Field(default="ERROR", description="Severity: ERROR (blocks approval), WARNING, INFO.")


class CandidateValidationSummary(BaseModel):
    """Consolidated 10-gate validation assessment for candidate lifecycle."""

    model_config = ConfigDict(frozen=True)

    is_valid: bool = Field(description="True if all blocking gates passed without errors.")
    simulation_eligible: bool = Field(
        description="True if candidate meets all scientific requirements for ODE simulation.",
    )
    gates: list[ValidationGateResult] = Field(default_factory=list, description="All individual gate results.")
    blocking_reasons: list[str] = Field(
        default_factory=list,
        description="List of blocking errors preventing SIMULATION_READY status.",
    )
    warnings: list[str] = Field(default_factory=list, description="Non-blocking scientific caveats or warnings.")


class AuditLogEntry(BaseModel):
    """Immutable audit entry tracking research modifications and lifecycle transitions."""

    model_config = ConfigDict(frozen=True)

    timestamp: str = Field(description="ISO-8601 timestamp of audit event.")
    action: str = Field(description="Action name (e.g. CREATED, VALIDATED, APPROVED, REJECTED, REFRESHED).")
    actor: str = Field(default="system", description="User or automated agent performing action.")
    previous_status: ResearchLifecycleStatus | None = Field(default=None)
    new_status: ResearchLifecycleStatus = Field(description="Status resulting from action.")
    notes: str = Field(default="", description="Context or justification for transition.")


# --------------------------------------------------------------------------- #
# Research Dossier & Candidate Revision
# --------------------------------------------------------------------------- #


class ResearchDossier(BaseModel):
    """Complete versioned research dossier for an interrogated chemical substance."""

    model_config = ConfigDict(frozen=True)

    candidate_id: str = Field(description="Stable internal identifier (e.g. rcand_primaquine).")
    query_name: str = Field(description="Original user-submitted substance name.")
    research_objective: str = Field(
        default="Investigate oxidative stress and redox dynamics in human erythrocytes.",
        description="Declared objective of the research inquiry.",
    )
    target_scope: str = Field(
        default="Human Erythrocyte Redox Biology (V-Blood ODE Engine)",
        description="Scope boundary for research findings.",
    )
    status: ResearchLifecycleStatus = Field(
        default=ResearchLifecycleStatus.RESEARCHED,
        description="Current lifecycle status.",
    )
    chemical_identity: ChemicalIdentity = Field(description="Resolved authoritative chemical identity.")
    sources: list[LiteratureSource] = Field(default_factory=list, description="Retrieved literature sources.")
    findings: list[EvidenceFinding] = Field(default_factory=list, description="Extracted structured findings.")
    mechanism_mappings: list[ProposedMechanismMapping] = Field(
        default_factory=list,
        description="Evaluated mechanism mappings.",
    )
    validation_summary: CandidateValidationSummary = Field(
        description="Consolidated 10-gate validation assessment.",
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Explicitly identified biological, chemical, or model limitations.",
    )
    unresolved_questions: list[str] = Field(
        default_factory=list,
        description="Scientific questions not answered by available literature.",
    )
    audit_history: list[AuditLogEntry] = Field(
        default_factory=list,
        description="Immutable revision and lifecycle history.",
    )
    created_at: str = Field(description="ISO-8601 creation timestamp.")
    updated_at: str = Field(description="ISO-8601 last update timestamp.")
    pipeline_version: str = Field(default="1.0.0", description="Version of research pipeline engine.")
    llm_provider_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata on LLM provider and model used during extraction.",
    )
    prompt_version: str = Field(default="v1.0", description="Prompt and extraction schema version.")
    revision: int = Field(default=1, description="Candidate revision counter.")


class ResearchJobStatus(BaseModel):
    """Real-time progress reporting for asynchronous compound research jobs."""

    model_config = ConfigDict(frozen=True)

    job_id: str = Field(description="Unique job execution identifier.")
    query_name: str = Field(description="Requested chemical name.")
    stage: ResearchPipelineStage = Field(default=ResearchPipelineStage.INITIALIZED)
    progress_pct: int = Field(default=0, ge=0, le=100, description="Overall completion percentage [0-100].")
    message: str = Field(default="Initializing research job...", description="Human-readable stage message.")
    error: str | None = Field(default=None, description="Error message if failed.")
    candidate_id: str | None = Field(default=None, description="Resulting candidate ID once generated.")
    created_at: str = Field(description="ISO-8601 job creation timestamp.")
    updated_at: str = Field(description="ISO-8601 last status update timestamp.")


class ResearchSubmissionRequest(BaseModel):
    """User request payload to submit a substance for automated research."""

    model_config = ConfigDict(frozen=True)

    substance_name: str = Field(min_length=1, description="Name or identifier of chemical entity to research.")
    research_objective: str | None = Field(
        default=None,
        description="Optional specific biological objective or context.",
    )
    force_refresh: bool = Field(
        default=False,
        description="If True, bypass existing research record and re-query literature.",
    )
