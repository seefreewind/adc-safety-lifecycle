#!/usr/bin/env python3
"""Run lightweight structural quality checks for processed study tables."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"


REQUIRED_COLUMNS = {
    "drug_master.csv": ["drug_id", "generic_name", "brand_name", "first_fda_approval_date", "verification_status"],
    "ae_observation.csv": ["observation_id", "trial_id", "arm_id", "document_id", "ae_original_term", "denominator"],
    "source_comparability_matrix.csv": ["comparison_id", "comparability_grade", "analysis_use"],
}


def read_header(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as f:
        return next(csv.reader(f))


def main() -> None:
    failures = []
    for filename, required in REQUIRED_COLUMNS.items():
        path = PROCESSED / filename
        if not path.exists():
            failures.append(f"missing file: {filename}")
            continue
        header = read_header(path)
        missing = [col for col in required if col not in header]
        if missing:
            failures.append(f"{filename}: missing columns {missing}")

    if failures:
        print("QC FAIL")
        for item in failures:
            print(item)
        raise SystemExit(1)

    print("QC PASS: required processed-table structures are present.")


if __name__ == "__main__":
    main()

