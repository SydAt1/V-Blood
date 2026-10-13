"""
Unit tests for ExperimentalRecord schema and data ingestion pipeline (Task 4).

Tests cover:
- Schema validation, required fields, and null safety.
- Physical measurement bounds (negative concentration rejection).
- Unit conversion functions.
- Duplicate detection.
- Pipeline execution with valid, malformed, and invalid records.
- Raw data immutability enforcement.
- Strict separation of SYNTHETIC fixtures from EXPERIMENTAL datasets.
"""

import json
from pathlib import Path

import pytest

from vblood.data.pipeline import DataIngestionPipeline
from vblood.data.unit_conversion import convert_measurement
from vblood.schemas.experimental_record import (
    EndpointType,
    EvidenceStatus,
    ExperimentalRecord,
    SampleType,
)


class TestExperimentalRecordSchema:
    """Tests on the ExperimentalRecord Pydantic model."""

    def test_valid_record_creation(self):
        rec = ExperimentalRecord(
            record_id="REC-TEST-01",
            study_id="STUDY-TEST-01",
            publication_title="Test Study on Erythrocytes",
            authors="Test Authors",
            publication_year=2024,
            doi_or_url="https://doi.org/10.1234/test",
            evidence_status=EvidenceStatus.EXPERIMENTAL,
            chemical_name="Hydrogen peroxide",
            sample_type=SampleType.ISOLATED_RBCS,
            endpoint=EndpointType.GSH,
            original_value=2.5,
            original_unit="mM",
        )
        assert rec.record_id == "REC-TEST-01"
        assert rec.original_value == 2.5
        assert rec.exposure_concentration is None  # Optional field remains None
        assert rec.assay_method is None

    def test_missing_required_field_raises_error(self):
        with pytest.raises(Exception):
            ExperimentalRecord(
                record_id="REC-TEST-INCOMPLETE",
                # missing publication_title, authors, etc.
                original_value=2.5,
                original_unit="mM",
            )

    def test_negative_measurement_rejected(self):
        with pytest.raises(ValueError):
            ExperimentalRecord(
                record_id="REC-NEG-01",
                study_id="STUDY-TEST-01",
                publication_title="Negative Test",
                authors="Test Authors",
                publication_year=2024,
                doi_or_url="https://doi.org/10.1234/test",
                evidence_status=EvidenceStatus.EXPERIMENTAL,
                chemical_name="H2O2",
                sample_type=SampleType.ISOLATED_RBCS,
                endpoint=EndpointType.GSH,
                original_value=-1.5,  # Physically invalid!
                original_unit="mM",
            )

    def test_excessive_hemolysis_rejected(self):
        with pytest.raises(ValueError):
            ExperimentalRecord(
                record_id="REC-HEMO-TOO-HIGH",
                study_id="STUDY-TEST-01",
                publication_title="Hemolysis Test",
                authors="Test Authors",
                publication_year=2024,
                doi_or_url="https://doi.org/10.1234/test",
                evidence_status=EvidenceStatus.EXPERIMENTAL,
                chemical_name="AAPH",
                sample_type=SampleType.ISOLATED_RBCS,
                endpoint=EndpointType.HEMOLYSIS,
                original_value=150.0,  # Cannot exceed 100%
                original_unit="%",
            )


class TestUnitConversionUtilities:
    """Tests on convert_measurement."""

    def test_micromolar_to_millimolar(self):
        val, unit = convert_measurement(50.0, "µM", "H2O2")
        assert val == 0.050
        assert unit == "mM"

    def test_nanomolar_to_millimolar(self):
        val, unit = convert_measurement(100.0, "nM", "H2O2")
        assert abs(val - 0.0001) < 1e-9
        assert unit == "mM"

    def test_fraction_to_percent_hemolysis(self):
        val, unit = convert_measurement(0.25, "fraction", "HEMOLYSIS")
        assert val == 25.0
        assert unit == "%"

    def test_unsupported_unit_raises_error(self):
        with pytest.raises(ValueError):
            convert_measurement(10.0, "furlongs_per_fortnight", "GSH")


class TestIngestionPipeline:
    """Integration tests on DataIngestionPipeline."""

    @pytest.fixture
    def pipeline(self, tmp_path):
        return DataIngestionPipeline(
            raw_dir=tmp_path / "raw",
            processed_dir=tmp_path / "processed",
        )

    def test_ingest_valid_published_json(self, pipeline, tmp_path):
        raw_file = Path("data/raw/published_rbc_observations.json")
        records, summary = pipeline.ingest_file(raw_file)

        assert summary.total_records == 3
        assert summary.accepted_records == 3
        assert summary.rejected_records == 0
        assert len(summary.conversions_performed) == 2  # µM -> mM
        assert all(r.evidence_status == EvidenceStatus.EXPERIMENTAL for r in records)

    def test_synthetic_records_strictly_flagged(self, pipeline):
        synth_file = Path("data/raw/synthetic_challenge_fixtures.json")
        records, summary = pipeline.ingest_file(synth_file)

        assert summary.total_records == 1
        assert summary.accepted_records == 1
        assert records[0].evidence_status == EvidenceStatus.SYNTHETIC

    def test_raw_file_immutability(self, pipeline, tmp_path):
        """Verifies that the raw file on disk is unchanged after pipeline execution."""
        test_file = tmp_path / "raw" / "test_raw.json"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps([{
            "record_id": "REC-IMMUTABLE-01",
            "study_id": "STUDY-IMMUTABLE",
            "publication_title": "Immutability Test",
            "authors": "Author",
            "publication_year": 2024,
            "doi_or_url": "https://doi.org/10.1234/immut",
            "evidence_status": "EXPERIMENTAL",
            "chemical_name": "H2O2",
            "sample_type": "ISOLATED_RBCS",
            "endpoint": "GSH",
            "original_value": 2.0,
            "original_unit": "mM",
        }])
        test_file.write_text(content, encoding="utf-8")
        orig_mtime = test_file.stat().st_mtime

        records, summary = pipeline.ingest_file(test_file)
        assert summary.accepted_records == 1
        assert test_file.read_text(encoding="utf-8") == content
        assert test_file.stat().st_mtime == orig_mtime

    def test_duplicate_detection(self, pipeline, tmp_path):
        """Identical measurement observations within a file trigger a duplicate warning."""
        dup_file = tmp_path / "raw" / "duplicates.json"
        dup_file.parent.mkdir(parents=True, exist_ok=True)
        base_record = {
            "record_id": "REC-DUP-01",
            "study_id": "STUDY-DUP",
            "publication_title": "Duplicate Test",
            "authors": "Author",
            "publication_year": 2024,
            "doi_or_url": "https://doi.org/10.1234/dup",
            "evidence_status": "EXPERIMENTAL",
            "chemical_name": "H2O2",
            "sample_type": "ISOLATED_RBCS",
            "endpoint": "GSH",
            "original_value": 2.0,
            "original_unit": "mM",
        }
        rec2 = dict(base_record)
        rec2["record_id"] = "REC-DUP-02"

        dup_file.write_text(json.dumps([base_record, rec2]), encoding="utf-8")
        records, summary = pipeline.ingest_file(dup_file)

        assert summary.total_records == 2
        assert summary.warnings_count >= 1
        assert len(summary.potential_duplicates) >= 1

    def test_malformed_record_rejected_without_crashing_pipeline(self, pipeline, tmp_path):
        """Invalid records are captured as rejections while valid ones are accepted."""
        mixed_file = tmp_path / "raw" / "mixed.json"
        mixed_file.parent.mkdir(parents=True, exist_ok=True)
        valid_rec = {
            "record_id": "REC-GOOD-01",
            "study_id": "STUDY-MIXED",
            "publication_title": "Mixed Test",
            "authors": "Author",
            "publication_year": 2024,
            "doi_or_url": "https://doi.org/10.1234/mixed",
            "evidence_status": "EXPERIMENTAL",
            "chemical_name": "H2O2",
            "sample_type": "ISOLATED_RBCS",
            "endpoint": "GSH",
            "original_value": 2.0,
            "original_unit": "mM",
        }
        bad_rec = {
            "record_id": "REC-BAD-01",
            "study_id": "STUDY-MIXED",
            # missing publication_title, authors, etc.
            "original_value": -50.0,  # Negative
            "original_unit": "invalid_unit",
        }
        mixed_file.write_text(json.dumps([valid_rec, bad_rec]), encoding="utf-8")
        records, summary = pipeline.ingest_file(mixed_file)

        assert summary.total_records == 2
        assert summary.accepted_records == 1
        assert summary.rejected_records == 1
        assert len(summary.rejection_reasons) == 1
