"""
Compound Library and Loader (Milestone 4 - Task 2).

Provides schema validation, SMILES/InChIKey integrity checks, and SHA-256
file verification for curated compounds in data/processed/compounds.json.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from vblood.chemistry.identifiers import validate_inchikey, validate_smiles
from vblood.scenarios.mechanisms import EvidenceLevel, MechanismType


class CompoundEntry(BaseModel):
    """Curated chemical entry in the V-Blood compound library."""

    model_config = ConfigDict(frozen=True)

    compound_id: str = Field(description="Unique identifier (e.g. cmp_menadione).")
    name: str = Field(description="Common or scientific compound name.")
    smiles: str = Field(description="SMILES chemical structure representation.")
    inchikey: str = Field(description="Standard IUPAC InChIKey.")
    mechanism_type: MechanismType = Field(description="Primary mechanism class.")
    default_parameters: dict[str, Any] = Field(description="Default kinetic parameter values.")
    parameter_ranges: dict[str, list[float]] = Field(
        default_factory=dict,
        description="Plausible range [min, max] per parameter.",
    )
    exposure_units: str = Field(default="mM", description="Dose/exposure concentration units.")
    evidence_level: EvidenceLevel = Field(default=EvidenceLevel.CURATED)
    provenance: str = Field(description="Literature reference or source study.")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)

    @field_validator("inchikey")
    @classmethod
    def check_inchikey(cls, v: str) -> str:
        res = validate_inchikey(v)
        if not res.is_valid:
            raise ValueError(f"Invalid InChIKey: {res.error_message}")
        return res.canonical or v

    @field_validator("smiles")
    @classmethod
    def check_smiles(cls, v: str) -> str:
        res = validate_smiles(v)
        if not res.is_valid:
            raise ValueError(f"Invalid SMILES string: {res.error_message}")
        return res.canonical or v

    @property
    def is_unverified(self) -> bool:
        """True if the compound is flagged as unverified for validation exclusion."""
        return self.evidence_level == EvidenceLevel.UNVERIFIED


class CompoundLibrary:
    """In-memory registry and verified loader for compounds."""

    def __init__(self, data_path: Path | str | None = None):
        if data_path is None:
            # Default to data/processed/compounds.json relative to repo root
            repo_root = Path(__file__).resolve().parent.parent.parent.parent
            self.data_path = repo_root / "data" / "processed" / "compounds.json"
        else:
            self.data_path = Path(data_path)

        self._compounds: dict[str, CompoundEntry] = {}
        self._sha256_hash: str = ""
        self.load()

    def load(self) -> None:
        """Load, validate, and compute SHA-256 digest of compounds.json."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Compound library file not found at {self.data_path}")

        raw_bytes = self.data_path.read_bytes()
        self._sha256_hash = hashlib.sha256(raw_bytes).hexdigest()

        data = json.loads(raw_bytes.decode("utf-8"))
        if not isinstance(data, list):
            raise ValueError("compounds.json must contain a top-level list of compound objects.")

        entries: dict[str, CompoundEntry] = {}
        for item in data:
            entry = CompoundEntry(**item)
            if entry.compound_id in entries:
                raise ValueError(f"Duplicate compound_id detected: {entry.compound_id}")
            entries[entry.compound_id] = entry

        self._compounds = entries

    @property
    def sha256_hash(self) -> str:
        """SHA-256 fingerprint of the underlying compounds.json file."""
        return self._sha256_hash

    def get(self, compound_id: str) -> CompoundEntry | None:
        """Retrieve a compound by its unique compound_id."""
        return self._compounds.get(compound_id)

    def get_or_raise(self, compound_id: str) -> CompoundEntry:
        """Retrieve a compound by compound_id or raise ValueError."""
        entry = self.get(compound_id)
        if entry is None:
            raise ValueError(
                f"Unknown compound_id '{compound_id}'. Available: {list(self._compounds.keys())}"
            )
        return entry

    def list_all(self) -> list[CompoundEntry]:
        """Return all registered compounds in the library."""
        return list(self._compounds.values())

    def filter_by_mechanism(self, mechanism_type: MechanismType) -> list[CompoundEntry]:
        """Filter compounds by mechanism class."""
        return [c for c in self._compounds.values() if c.mechanism_type == mechanism_type]


# Singleton default compound library
_GLOBAL_LIBRARY: CompoundLibrary | None = None


def get_compound_library() -> CompoundLibrary:
    """Retrieve or initialize the global CompoundLibrary singleton."""
    global _GLOBAL_LIBRARY
    if _GLOBAL_LIBRARY is None:
        _GLOBAL_LIBRARY = CompoundLibrary()
    return _GLOBAL_LIBRARY
