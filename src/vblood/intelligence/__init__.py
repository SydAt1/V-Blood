"""
Intelligence, Compatibility, and Research-to-Library Pipeline (Milestones 6 & 7).

Provides foundation interfaces for chemical mechanism compatibility,
evidence grading, identity resolution, literature retrieval, parameter provenance,
candidate validation, and end-to-end research orchestration.
"""

from __future__ import annotations

from vblood.intelligence.compatibility import (
    ChemicalCompatibilityAssessment,
    CompoundCompatibilityChecker,
    EvidenceTierEvaluation,
    evaluate_evidence_tier,
)
from vblood.intelligence.extraction import EvidenceExtractionService
from vblood.intelligence.grading import EvidenceGradingService
from vblood.intelligence.identity import ChemicalIdentityResolver
from vblood.intelligence.mechanisms import MechanismMappingService
from vblood.intelligence.pipeline import (
    CompoundResearchOrchestrator,
    get_research_orchestrator,
)
from vblood.intelligence.repository import (
    ResearchRepository,
    get_research_repository,
)
from vblood.intelligence.retrieval import (
    LiteratureRetrievalService,
    sanitize_retrieved_text,
)
from vblood.intelligence.schemas import (
    AuditLogEntry,
    CandidateParameter,
    CandidateValidationSummary,
    ChemicalEntityType,
    ChemicalIdentity,
    EvidenceFinding,
    LiteratureSource,
    LiteratureSourceType,
    ParameterProvenance,
    ProposedMechanismMapping,
    ResearchDossier,
    ResearchJobStatus,
    ResearchLifecycleStatus,
    ResearchPipelineStage,
    ResearchSubmissionRequest,
    ValidationGateResult,
)
from vblood.intelligence.validator import CandidateValidator

__all__ = [
    "AuditLogEntry",
    "CandidateParameter",
    "CandidateValidationSummary",
    "CandidateValidator",
    "ChemicalCompatibilityAssessment",
    "ChemicalEntityType",
    "ChemicalIdentity",
    "ChemicalIdentityResolver",
    "CompoundCompatibilityChecker",
    "CompoundResearchOrchestrator",
    "EvidenceExtractionService",
    "EvidenceFinding",
    "EvidenceGradingService",
    "EvidenceTierEvaluation",
    "LiteratureRetrievalService",
    "LiteratureSource",
    "LiteratureSourceType",
    "MechanismMappingService",
    "ParameterProvenance",
    "ProposedMechanismMapping",
    "ResearchDossier",
    "ResearchJobStatus",
    "ResearchLifecycleStatus",
    "ResearchPipelineStage",
    "ResearchRepository",
    "ResearchSubmissionRequest",
    "ValidationGateResult",
    "evaluate_evidence_tier",
    "get_research_orchestrator",
    "get_research_repository",
    "sanitize_retrieved_text",
]
