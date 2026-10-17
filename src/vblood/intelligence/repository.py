"""
Research Candidate Repository and Library Persistence (Milestone 7 - Step 10).

Persists research dossiers and candidates, enforces idempotent duplicate detection,
maintains immutable audit logs and versioning, and synchronizes approved SIMULATION_READY
compounds into the active CompoundLibrary.
"""

from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path
from typing import Any

from vblood.intelligence.schemas import (
    AuditLogEntry,
    CandidateValidationSummary,
    ResearchDossier,
    ResearchLifecycleStatus,
)
from vblood.intelligence.validator import CandidateValidator
from vblood.scenarios.compounds import CompoundEntry, get_compound_library
from vblood.scenarios.mechanisms import EvidenceLevel, MechanismType

logger = logging.getLogger(__name__)


def _dossier_to_compound_entry(dossier: ResearchDossier) -> CompoundEntry:
    """Convert an approved SIMULATION_READY ResearchDossier into a CompoundEntry for simulation."""
    identity = dossier.chemical_identity
    compatible_mappings = [m for m in dossier.mechanism_mappings if m.is_compatible]
    if not compatible_mappings:
        raise ValueError(f"Dossier '{dossier.candidate_id}' has no compatible mechanism mappings.")

    target_mapping = compatible_mappings[0]
    mech_type = MechanismType(target_mapping.mechanism_type)

    # Build default parameters and ranges
    defaults: dict[str, Any] = {}
    ranges: dict[str, list[float]] = {}
    for p in target_mapping.parameters:
        defaults[p.name] = p.value
        ranges[p.name] = [p.min_bound, p.max_bound]

    # Handle enzyme inhibitor specific fields
    if mech_type == MechanismType.ENZYME_INHIBITOR:
        if target_mapping.target_enzyme:
            defaults["target_enzyme"] = target_mapping.target_enzyme
        if target_mapping.inhibition_type:
            defaults["inhibition_type"] = target_mapping.inhibition_type

    # Determine evidence level
    has_curated = any(p.evidence_level == "CURATED" for p in target_mapping.parameters)
    has_estimated = any(p.evidence_level == "ESTIMATED" for p in target_mapping.parameters)
    if has_curated:
        ev_level = EvidenceLevel.CURATED
        conf = 0.95
    elif has_estimated:
        ev_level = EvidenceLevel.ESTIMATED
        conf = 0.75
    else:
        ev_level = EvidenceLevel.UNVERIFIED
        conf = 0.3

    prov_str = f"Milestone 7 LLM Intelligence Dossier ({dossier.candidate_id}). "
    if dossier.sources:
        s0 = dossier.sources[0]
        prov_str += f"Primary source: {s0.title} ({s0.journal or s0.source_type.value}, {s0.year or 'n.d.'})"

    return CompoundEntry(
        compound_id=dossier.candidate_id,
        name=identity.preferred_name,
        smiles=identity.smiles,
        inchikey=identity.inchikey,
        mechanism_type=mech_type,
        default_parameters=defaults,
        parameter_ranges=ranges,
        exposure_units="mM",
        evidence_level=ev_level,
        provenance=prov_str,
        confidence_score=conf,
    )


class ResearchRepository:
    """Persistent storage repository for research dossiers and candidate registration."""

    def __init__(self, storage_path: Path | str | None = None):
        if storage_path is None:
            repo_root = Path(__file__).resolve().parent.parent.parent.parent
            self.storage_path = repo_root / "data" / "processed" / "research_candidates.json"
        else:
            self.storage_path = Path(storage_path)

        self._dossiers: dict[str, ResearchDossier] = {}
        self._inchikey_index: dict[str, str] = {}
        self._name_index: dict[str, str] = {}
        self.validator = CandidateValidator()
        self.load()

    def load(self) -> None:
        """Load stored dossiers from disk if available and sync approved ones to catalog."""
        if not self.storage_path.exists():
            return

        try:
            raw_text = self.storage_path.read_text(encoding="utf-8")
            if not raw_text.strip():
                return
            data = json.loads(raw_text)
            if not isinstance(data, list):
                return

            for item in data:
                try:
                    dossier = ResearchDossier(**item)
                    self._dossiers[dossier.candidate_id] = dossier
                    self._inchikey_index[dossier.chemical_identity.inchikey] = dossier.candidate_id
                    self._name_index[dossier.query_name.lower().strip()] = dossier.candidate_id

                    # If already SIMULATION_READY, sync to compound library
                    if dossier.status == ResearchLifecycleStatus.SIMULATION_READY:
                        try:
                            c_entry = _dossier_to_compound_entry(dossier)
                            get_compound_library().register_compound(c_entry)
                        except Exception as sync_exc:
                            logger.warning("Failed to sync approved dossier %s to library: %s", dossier.candidate_id, sync_exc)
                except Exception as parse_exc:
                    logger.warning("Error parsing stored candidate dossier: %s", parse_exc)
        except Exception as exc:
            logger.warning("Failed to load research repository from %s: %s", self.storage_path, exc)

    def save_all(self) -> None:
        """Persist all dossiers atomically to JSON on disk."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        serialized = [d.model_dump() for d in self._dossiers.values()]
        temp_path = self.storage_path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(serialized, indent=2), encoding="utf-8")
        temp_path.replace(self.storage_path)

    def get(self, candidate_id: str) -> ResearchDossier | None:
        """Retrieve dossier by candidate_id."""
        return self._dossiers.get(candidate_id)

    def find_by_inchikey(self, inchikey: str) -> ResearchDossier | None:
        """Retrieve dossier by InChIKey."""
        cid = self._inchikey_index.get(inchikey.strip().upper())
        return self._dossiers.get(cid) if cid else None

    def find_by_query_name(self, name: str) -> ResearchDossier | None:
        """Retrieve dossier by query name."""
        cid = self._name_index.get(name.lower().strip())
        return self._dossiers.get(cid) if cid else None

    def list_all(
        self,
        status_filter: ResearchLifecycleStatus | None = None,
    ) -> list[ResearchDossier]:
        """List all research dossiers, optionally filtered by lifecycle status."""
        if status_filter is None:
            return list(self._dossiers.values())
        return [d for d in self._dossiers.values() if d.status == status_filter]

    def save_dossier(self, dossier: ResearchDossier) -> None:
        """Store or update a research dossier."""
        self._dossiers[dossier.candidate_id] = dossier
        self._inchikey_index[dossier.chemical_identity.inchikey] = dossier.candidate_id
        self._name_index[dossier.query_name.lower().strip()] = dossier.candidate_id

        # If SIMULATION_READY, register into active CompoundLibrary
        if dossier.status == ResearchLifecycleStatus.SIMULATION_READY:
            try:
                c_entry = _dossier_to_compound_entry(dossier)
                get_compound_library().register_compound(c_entry)
            except Exception as exc:
                logger.warning("Could not register simulation candidate %s: %s", dossier.candidate_id, exc)

        self.save_all()

    def approve_candidate(
        self,
        candidate_id: str,
        actor: str = "researcher",
        notes: str = "",
    ) -> ResearchDossier:
        """Approve an eligible candidate to SIMULATION_READY status and register into compound catalog."""
        dossier = self.get(candidate_id)
        if dossier is None:
            raise ValueError(f"Research candidate '{candidate_id}' not found.")

        # Revalidate before approval
        val_summary = self.validator.validate(
            dossier.candidate_id,
            dossier.chemical_identity,
            dossier.sources,
            dossier.mechanism_mappings,
        )

        if not val_summary.simulation_eligible:
            blockers = "; ".join(val_summary.blocking_reasons)
            raise ValueError(
                f"Candidate '{candidate_id}' cannot be approved for simulation due to validation blockers: {blockers}"
            )

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        audit_entry = AuditLogEntry(
            timestamp=now_iso,
            action="APPROVED",
            actor=actor,
            previous_status=dossier.status,
            new_status=ResearchLifecycleStatus.SIMULATION_READY,
            notes=notes or "Candidate passed all 10 validation gates and was approved for active simulation.",
        )

        updated = ResearchDossier(
            **{
                **dossier.model_dump(),
                "status": ResearchLifecycleStatus.SIMULATION_READY,
                "validation_summary": val_summary.model_dump(),
                "audit_history": [audit_entry.model_dump(), *[a.model_dump() for a in dossier.audit_history]],
                "updated_at": now_iso,
                "revision": dossier.revision + 1,
            }
        )

        # Register into CompoundLibrary
        c_entry = _dossier_to_compound_entry(updated)
        get_compound_library().register_compound(c_entry)

        self.save_dossier(updated)
        return updated

    def reject_candidate(
        self,
        candidate_id: str,
        actor: str = "researcher",
        notes: str = "",
    ) -> ResearchDossier:
        """Mark a candidate as REJECTED during scientific review."""
        dossier = self.get(candidate_id)
        if dossier is None:
            raise ValueError(f"Research candidate '{candidate_id}' not found.")

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        audit_entry = AuditLogEntry(
            timestamp=now_iso,
            action="REJECTED",
            actor=actor,
            previous_status=dossier.status,
            new_status=ResearchLifecycleStatus.REJECTED,
            notes=notes or "Candidate rejected during scientific review.",
        )

        updated = ResearchDossier(
            **{
                **dossier.model_dump(),
                "status": ResearchLifecycleStatus.REJECTED,
                "audit_history": [audit_entry.model_dump(), *[a.model_dump() for a in dossier.audit_history]],
                "updated_at": now_iso,
                "revision": dossier.revision + 1,
            }
        )
        self.save_dossier(updated)
        return updated

    def revalidate_candidate(self, candidate_id: str) -> ResearchDossier:
        """Re-run the 10 validation gates and update validation summary."""
        dossier = self.get(candidate_id)
        if dossier is None:
            raise ValueError(f"Research candidate '{candidate_id}' not found.")

        val_summary = self.validator.validate(
            dossier.candidate_id,
            dossier.chemical_identity,
            dossier.sources,
            dossier.mechanism_mappings,
        )

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        audit_entry = AuditLogEntry(
            timestamp=now_iso,
            action="VALIDATED",
            actor="system",
            previous_status=dossier.status,
            new_status=dossier.status,
            notes="Re-executed 10-gate validation checklist.",
        )

        new_status = dossier.status
        # If was simulation ready but no longer eligible, downgrade to CANDIDATE
        if dossier.status == ResearchLifecycleStatus.SIMULATION_READY and not val_summary.simulation_eligible:
            new_status = ResearchLifecycleStatus.CANDIDATE

        updated = ResearchDossier(
            **{
                **dossier.model_dump(),
                "status": new_status,
                "validation_summary": val_summary.model_dump(),
                "audit_history": [audit_entry.model_dump(), *[a.model_dump() for a in dossier.audit_history]],
                "updated_at": now_iso,
                "revision": dossier.revision + 1,
            }
        )
        self.save_dossier(updated)
        return updated


# Global repository singleton
_GLOBAL_REPOSITORY: ResearchRepository | None = None


def get_research_repository() -> ResearchRepository:
    """Retrieve or initialize the global ResearchRepository singleton."""
    global _GLOBAL_REPOSITORY
    if _GLOBAL_REPOSITORY is None:
        _GLOBAL_REPOSITORY = ResearchRepository()
    return _GLOBAL_REPOSITORY
