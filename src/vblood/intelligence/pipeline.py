"""
Compound Research Orchestration Pipeline (Milestone 7 - Step 1).

Coordinates identity resolution, literature retrieval, evidence extraction, grading,
mechanism compatibility checks, parameter estimation, 10-gate validation, and dossier persistence.
"""

from __future__ import annotations

import asyncio
import datetime
import logging
import re
import uuid
from typing import Any

from vblood.intelligence.extraction import EvidenceExtractionService
from vblood.intelligence.grading import EvidenceGradingService
from vblood.intelligence.identity import ChemicalIdentityResolver
from vblood.intelligence.mechanisms import MechanismMappingService
from vblood.intelligence.repository import ResearchRepository, get_research_repository
from vblood.intelligence.retrieval import LiteratureRetrievalService
from vblood.intelligence.schemas import (
    AuditLogEntry,
    ResearchDossier,
    ResearchJobStatus,
    ResearchLifecycleStatus,
    ResearchPipelineStage,
)
from vblood.intelligence.validator import CandidateValidator

logger = logging.getLogger(__name__)


def _generate_candidate_id(name: str) -> str:
    """Generate normalized stable candidate identifier (e.g. rcand_primaquine)."""
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", name.lower()).strip("_")
    return f"rcand_{clean}"


class CompoundResearchOrchestrator:
    """Orchestrates end-to-end LLM-assisted research-to-library pipeline."""

    def __init__(
        self,
        repository: ResearchRepository | None = None,
        identity_resolver: ChemicalIdentityResolver | None = None,
        retrieval_service: LiteratureRetrievalService | None = None,
        extraction_service: EvidenceExtractionService | None = None,
        grading_service: EvidenceGradingService | None = None,
        mapping_service: MechanismMappingService | None = None,
        validator: CandidateValidator | None = None,
    ):
        self.repository = repository or get_research_repository()
        self.identity_resolver = identity_resolver or ChemicalIdentityResolver()
        self.retrieval_service = retrieval_service or LiteratureRetrievalService()
        self.grading_service = grading_service or EvidenceGradingService()
        self.extraction_service = extraction_service or EvidenceExtractionService(grading_service=self.grading_service)
        self.mapping_service = mapping_service or MechanismMappingService()
        self.validator = validator or CandidateValidator()

        # Job registry for async tasks
        self._jobs: dict[str, ResearchJobStatus] = {}

    def get_job(self, job_id: str) -> ResearchJobStatus | None:
        """Retrieve current status of a background research job."""
        return self._jobs.get(job_id)

    def submit_job(
        self,
        substance_name: str,
        research_objective: str | None = None,
        force_refresh: bool = False,
    ) -> str:
        """Submit a background research job and return the job_id."""
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        job_status = ResearchJobStatus(
            job_id=job_id,
            query_name=substance_name,
            stage=ResearchPipelineStage.INITIALIZED,
            progress_pct=5,
            message=f"Research job queued for '{substance_name}'.",
            error=None,
            candidate_id=None,
            created_at=now_iso,
            updated_at=now_iso,
        )
        self._jobs[job_id] = job_status

        # Spawn background task safely across async and sync thread environments
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._run_job_async(job_id, substance_name, research_objective, force_refresh))
        except RuntimeError:
            import threading
            def _runner():
                asyncio.run(self._run_job_async(job_id, substance_name, research_objective, force_refresh))
            t = threading.Thread(target=_runner, daemon=True)
            t.start()

        return job_id

    async def _run_job_async(
        self,
        job_id: str,
        substance_name: str,
        research_objective: str | None,
        force_refresh: bool,
    ) -> None:
        """Execute the research job asynchronously, updating stage status."""
        try:
            self._update_job(
                job_id,
                stage=ResearchPipelineStage.RESOLVING_IDENTITY,
                progress_pct=15,
                message=f"Resolving chemical identity and structure for '{substance_name}'...",
            )

            dossier = self.run_pipeline(
                substance_name=substance_name,
                research_objective=research_objective,
                force_refresh=force_refresh,
                job_id=job_id,
            )

            self._update_job(
                job_id,
                stage=ResearchPipelineStage.COMPLETED,
                progress_pct=100,
                message=f"Research dossier created for '{dossier.chemical_identity.preferred_name}' ({dossier.status.value}).",
                candidate_id=dossier.candidate_id,
            )
        except Exception as exc:
            logger.error("Research job %s failed: %s", job_id, exc, exc_info=True)
            self._update_job(
                job_id,
                stage=ResearchPipelineStage.FAILED,
                progress_pct=100,
                message=f"Research failed: {exc}",
                error=str(exc),
            )

    def _update_job(
        self,
        job_id: str,
        stage: ResearchPipelineStage,
        progress_pct: int,
        message: str,
        error: str | None = None,
        candidate_id: str | None = None,
    ) -> None:
        """Update job status record in memory."""
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        current = self._jobs.get(job_id)
        cid = candidate_id or (current.candidate_id if current else None)
        created = current.created_at if current else now_iso

        self._jobs[job_id] = ResearchJobStatus(
            job_id=job_id,
            query_name=current.query_name if current else "substance",
            stage=stage,
            progress_pct=progress_pct,
            message=message,
            error=error,
            candidate_id=cid,
            created_at=created,
            updated_at=now_iso,
        )

    def run_pipeline(
        self,
        substance_name: str,
        research_objective: str | None = None,
        force_refresh: bool = False,
        job_id: str | None = None,
    ) -> ResearchDossier:
        """Run the end-to-end research workflow synchronously."""
        substance_clean = substance_name.strip()
        if not substance_clean:
            raise ValueError("Substance name cannot be empty.")

        # Check existing records first unless force_refresh
        if not force_refresh:
            existing = self.repository.find_by_query_name(substance_clean)
            if existing:
                return existing

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Step 2: Chemical Identity Resolution
        if job_id:
            self._update_job(job_id, ResearchPipelineStage.RESOLVING_IDENTITY, 20, f"Resolving identity for '{substance_clean}'...")
        identity = self.identity_resolver.resolve(substance_clean)

        # Check by InChIKey to avoid duplicate entries with different names
        if not force_refresh:
            existing_by_inchi = self.repository.find_by_inchikey(identity.inchikey)
            if existing_by_inchi:
                return existing_by_inchi

        candidate_id = _generate_candidate_id(identity.preferred_name)

        # Step 3: Scientific Literature Retrieval
        if job_id:
            self._update_job(job_id, ResearchPipelineStage.RETRIEVING_LITERATURE, 40, f"Searching literature for '{identity.preferred_name}'...")
        sources = self.retrieval_service.retrieve(identity, objective=research_objective)

        # Step 4: Evidence Extraction
        if job_id:
            self._update_job(job_id, ResearchPipelineStage.EXTRACTING_EVIDENCE, 60, f"Extracting structured findings from {len(sources)} sources...")
        findings = self.extraction_service.extract(identity, sources)

        # Step 5: Evidence Grading
        if job_id:
            self._update_job(job_id, ResearchPipelineStage.GRADING_EVIDENCE, 70, "Grading evidence tiers and erythrocyte directness...")
        # (Grading has been applied per finding, compound tier is evaluated)
        compound_eval = self.grading_service.grade_compound(findings, len(sources))

        # Step 6 & 7: Mechanism Mapping & Parameter Estimation
        if job_id:
            self._update_job(job_id, ResearchPipelineStage.ASSESSING_COMPATIBILITY, 80, "Evaluating ODE mechanism compatibility and parameters...")
        mappings = self.mapping_service.evaluate_mappings(identity, findings)

        # Step 8 & 9: Candidate Validation Gates
        if job_id:
            self._update_job(job_id, ResearchPipelineStage.VALIDATING_CANDIDATE, 90, "Executing 10-gate scientific validation checklist...")
        val_summary = self.validator.validate(candidate_id, identity, sources, mappings)

        # Determine initial lifecycle status
        if not sources or not findings:
            init_status = ResearchLifecycleStatus.NEEDS_RESEARCH
        elif not any(m.is_compatible for m in mappings):
            init_status = ResearchLifecycleStatus.RESEARCHED
        elif val_summary.simulation_eligible:
            init_status = ResearchLifecycleStatus.CANDIDATE
        else:
            init_status = ResearchLifecycleStatus.RESEARCHED

        # Prepare audit history
        audit_entry = AuditLogEntry(
            timestamp=now_iso,
            action="CREATED",
            actor="research_orchestrator",
            previous_status=None,
            new_status=init_status,
            notes=(
                f"Initial research completed for '{identity.preferred_name}'. "
                f"Retrieved {len(sources)} sources, extracted {len(findings)} findings. "
                f"Evidence tier: {compound_eval.evidence_level.value}."
            ),
        )

        # Limitations & Unresolved Questions
        limitations = [
            "In vitro single-cell/suspension model: no whole-body pharmacokinetics, hepatic metabolism, or renal clearance.",
            "Erythrocytes lack nucleus and mitochondria; all dynamics reflect PPP, glutathione redox cycle, and GPx/GR turnover.",
        ]
        unresolved = []
        if identity.is_ambiguous:
            unresolved.append(f"Substance name was ambiguous; resolved to '{identity.preferred_name}'.")
        for m in mappings:
            limitations.extend(m.unmodeled_aspects)
            unresolved.extend(m.unresolved_questions)

        dossier = ResearchDossier(
            candidate_id=candidate_id,
            query_name=substance_clean,
            research_objective=research_objective or "Investigate oxidative stress and redox dynamics in human erythrocytes.",
            target_scope="Human Erythrocyte Redox Biology (V-Blood ODE Engine)",
            status=init_status,
            chemical_identity=identity,
            sources=sources,
            findings=findings,
            mechanism_mappings=mappings,
            validation_summary=val_summary,
            limitations=list(dict.fromkeys(limitations)),
            unresolved_questions=list(dict.fromkeys(unresolved)),
            audit_history=[audit_entry],
            created_at=now_iso,
            updated_at=now_iso,
            pipeline_version="1.0.0",
            llm_provider_metadata={"provider": "V-Blood Intelligence", "model": "gemini-2.5-flash / deterministic"},
            prompt_version="v1.0",
            revision=1,
        )

        # Step 10: Persist Dossier
        if job_id:
            self._update_job(job_id, ResearchPipelineStage.PERSISTING_DOSSIER, 95, "Persisting research dossier...")
        self.repository.save_dossier(dossier)

        return dossier


# Global orchestrator singleton
_GLOBAL_ORCHESTRATOR: CompoundResearchOrchestrator | None = None


def get_research_orchestrator() -> CompoundResearchOrchestrator:
    """Retrieve or initialize the global CompoundResearchOrchestrator singleton."""
    global _GLOBAL_ORCHESTRATOR
    if _GLOBAL_ORCHESTRATOR is None:
        _GLOBAL_ORCHESTRATOR = CompoundResearchOrchestrator()
    return _GLOBAL_ORCHESTRATOR
