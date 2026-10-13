"""
CLI Command for Running the Experimental Data Ingestion Pipeline (Task 4).

Usage:
    python scripts/ingest_data.py [--raw-dir data/raw] [--processed-dir data/processed]
"""

import argparse
from pathlib import Path

from vblood.data.pipeline import DataIngestionPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest and validate raw experimental data into V-Blood.")
    parser.add_argument("--raw-dir", default="data/raw", help="Path to directory containing raw CSV and JSON files.")
    parser.add_argument("--processed-dir", default="data/processed", help="Path to processed output directory.")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    pipeline = DataIngestionPipeline(raw_dir=raw_dir, processed_dir=args.processed_dir)

    print("=" * 80)
    print("V-BLOOD: EXPERIMENTAL DATA INGESTION PIPELINE (TASK 4)")
    print(f"Scanning raw data directory: {raw_dir}")
    print("=" * 80)

    raw_files = list(raw_dir.glob("*.json")) + list(raw_dir.glob("*.csv"))
    if not raw_files:
        print(f"No .json or .csv files found in {raw_dir}.")
        return

    all_accepted = []

    for f in raw_files:
        print(f"\nProcessing: {f.name}...")
        try:
            records, summary = pipeline.ingest_file(f)
            all_accepted.extend(records)

            print(f"  Total records: {summary.total_records}")
            print(f"  Accepted:      {summary.accepted_records}")
            print(f"  Rejected:      {summary.rejected_records}")
            print(f"  Warnings:      {summary.warnings_count}")
            print(f"  Provenance:    {summary.provenance_completeness_pct}%")

            if summary.conversions_performed:
                print("  Unit conversions:")
                for conv in summary.conversions_performed:
                    print(f"    - {conv}")

            if summary.rejection_reasons:
                print("  Rejections:")
                for rej in summary.rejection_reasons:
                    print(f"    ! {rej}")

            if summary.potential_duplicates:
                print("  Potential duplicates:")
                for dup in summary.potential_duplicates:
                    print(f"    ? {dup}")

            # Save per-dataset processed file
            out_name = f.stem + "_processed"
            saved_path = pipeline.save_processed_records(records, output_basename=out_name)
            print(f"  Wrote processed records to: {saved_path}")

        except Exception as e:
            print(f"  ERROR processing {f.name}: {e}")

    # Also save aggregate processed file
    agg_path = pipeline.save_processed_records(all_accepted, output_basename="all_experimental_records")
    print("\n" + "=" * 80)
    print(f"Ingestion complete. Total accepted records across all files: {len(all_accepted)}")
    print(f"Aggregate processed dataset: {agg_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
