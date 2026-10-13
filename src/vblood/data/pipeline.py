"""
Traceable Data Ingestion Pipeline for Experimental Observations (Task 4).

Reads raw CSV and JSON files from data/raw/, validates against ExperimentalRecord,
performs explicit unit conversions, detects duplicates, preserves raw file immutability,
and writes structured records to data/processed/.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from vblood.data.unit_conversion import convert_measurement
from vblood.schemas.experimental_record import EndpointType, ExperimentalRecord


class IngestionSummary(BaseModel):
    """Summary metrics and audit trail for an ingestion run."""

    model_config = ConfigDict(frozen=True)

    input_file: str
    total_records: int
    accepted_records: int
    rejected_records: int
    warnings_count: int
    rejection_reasons: list[str] = Field(default_factory=list)
    conversions_performed: list[str] = Field(default_factory=list)
    potential_duplicates: list[str] = Field(default_factory=list)
    provenance_completeness_pct: float


class DataIngestionPipeline:
    """Staged pipeline for ingesting, validating, and normalizing experimental data."""

    def __init__(self, raw_dir: Path | str = "data/raw", processed_dir: Path | str = "data/processed"):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def ingest_file(self, file_path: Path | str) -> tuple[list[ExperimentalRecord], IngestionSummary]:
        """Ingest and validate a single raw CSV or JSON file.

        Args:
            file_path: Path to input CSV or JSON file.

        Returns:
            Tuple of (list of validated ExperimentalRecord objects, IngestionSummary).
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Input data file does not exist: {path}")

        # Compute SHA-256 before read to guarantee immutability
        initial_hash = self._compute_file_hash(path)

        suffix = path.suffix.lower()
        if suffix == ".json":
            raw_entries = self._read_json(path)
        elif suffix == ".csv":
            raw_entries = self._read_csv(path)
        else:
            raise ValueError(f"Unsupported file format '{suffix}'. Supported: .json, .csv")

        # Verify immutability after read
        post_hash = self._compute_file_hash(path)
        if initial_hash != post_hash:
            raise RuntimeError(f"CRITICAL: Raw data file {path} was modified during ingestion!")

        accepted: list[ExperimentalRecord] = []
        rejections: list[str] = []
        conversions: list[str] = []
        duplicates: list[str] = []
        seen_keys: set[tuple[Any, ...]] = set()
        provenance_scores: list[float] = []

        for idx, entry in enumerate(raw_entries, start=1):
            entry_id = entry.get("record_id", f"entry_{idx}")
            try:
                # 1. Clean empty strings to None for optional fields
                cleaned_entry = self._clean_entry(entry)

                # 2. Check for potential duplicate before Pydantic parsing
                dup_key = (
                    cleaned_entry.get("study_id"),
                    cleaned_entry.get("chemical_name"),
                    cleaned_entry.get("endpoint"),
                    cleaned_entry.get("exposure_concentration"),
                    cleaned_entry.get("exposure_duration_s"),
                    cleaned_entry.get("original_value"),
                )
                if dup_key in seen_keys:
                    duplicates.append(f"Record {entry_id}: duplicate observation key {dup_key}")
                seen_keys.add(dup_key)

                # 3. Perform explicit unit conversion if needed
                orig_val = float(cleaned_entry["original_value"])
                orig_unit = str(cleaned_entry["original_unit"])
                ep_str = str(cleaned_entry["endpoint"])

                norm_val, norm_unit = convert_measurement(orig_val, orig_unit, ep_str)
                cleaned_entry["normalized_value"] = norm_val
                cleaned_entry["normalized_unit"] = norm_unit

                if orig_unit.lower() != norm_unit.lower():
                    conversions.append(
                        f"Record {entry_id} ({ep_str}): {orig_val} {orig_unit} -> {norm_val:.6e} {norm_unit}"
                    )

                # 4. Parse into immutable Pydantic schema
                rec = ExperimentalRecord.model_validate(cleaned_entry)
                accepted.append(rec)

                # 5. Measure provenance completeness
                prov_score = self._calculate_provenance_score(rec)
                provenance_scores.append(prov_score)

            except Exception as e:
                rejections.append(f"Record {entry_id} REJECTED: {e}")

        total_count = len(raw_entries)
        accepted_count = len(accepted)
        rejected_count = len(rejections)
        warnings_count = len(duplicates)
        avg_prov = (sum(provenance_scores) / len(provenance_scores)) if provenance_scores else 0.0

        summary = IngestionSummary(
            input_file=str(path),
            total_records=total_count,
            accepted_records=accepted_count,
            rejected_records=rejected_count,
            warnings_count=warnings_count,
            rejection_reasons=rejections,
            conversions_performed=conversions,
            potential_duplicates=duplicates,
            provenance_completeness_pct=round(avg_prov * 100.0, 1),
        )

        return accepted, summary

    def save_processed_records(
        self,
        records: list[ExperimentalRecord],
        output_basename: str = "experimental_records",
    ) -> Path:
        """Write accepted records to data/processed/ as JSON."""
        out_json = self.processed_dir / f"{output_basename}.json"
        data_to_write = [r.model_dump() for r in records]
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(data_to_write, f, indent=2)
        return out_json

    @staticmethod
    def _clean_entry(entry: dict[str, Any]) -> dict[str, Any]:
        """Convert empty strings to None and parse numbers where necessary."""
        cleaned = {}
        for k, v in entry.items():
            if isinstance(v, str) and v.strip() == "":
                cleaned[k] = None
            elif k in ("publication_year", "pubchem_cid", "replicate_count") and v is not None:
                try:
                    cleaned[k] = int(v)
                except (ValueError, TypeError):
                    cleaned[k] = v
            elif k in (
                "original_value", "exposure_concentration", "exposure_duration_s",
                "temperature_celsius", "ph", "uncertainty_value", "control_baseline_value"
            ) and v is not None:
                try:
                    cleaned[k] = float(v)
                except (ValueError, TypeError):
                    cleaned[k] = v
            else:
                cleaned[k] = v
        return cleaned

    @staticmethod
    def _calculate_provenance_score(rec: ExperimentalRecord) -> float:
        """Score provenance completeness out of 1.0."""
        fields_to_check = [
            rec.publication_title,
            rec.authors,
            rec.doi_or_url,
            rec.chemical_name,
            rec.sample_type,
            rec.assay_method,
            rec.uncertainty_value,
            rec.replicate_count,
        ]
        present = sum(1 for f in fields_to_check if f is not None and str(f).strip() != "")
        return present / len(fields_to_check)

    @staticmethod
    def _compute_file_hash(path: Path) -> str:
        """Compute SHA-256 file hash to guarantee immutability."""
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def _read_json(path: Path) -> list[dict[str, Any]]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "records" in data:
                return data["records"]
            raise ValueError(f"JSON in {path} must be a list of records or contain a 'records' key.")

    @staticmethod
    def _read_csv(path: Path) -> list[dict[str, Any]]:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [dict(row) for row in reader]
