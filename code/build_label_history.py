#!/usr/bin/env python3
"""Build a label-history worklist from saved FDA/openFDA label files.

This script intentionally does not infer substantive label changes by itself.
It creates a review table that can be audited against dated label versions.
"""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_LABELS = ROOT / "data" / "raw" / "labels"
OUT = ROOT / "data" / "processed" / "label_history.csv"


HEADER = [
    "label_event_id", "drug_id", "label_version_date", "section", "safety_concept",
    "warning_level", "newly_added", "strengthened", "removed",
    "dose_modification_added", "monitoring_added", "boxed_warning",
    "coverage_score", "source_url_or_local_path", "review_status", "notes",
]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for idx, path in enumerate(sorted(RAW_LABELS.glob("**/*")), start=1):
        if not path.is_file():
            continue
        rows.append([
            f"LABEL{idx:05d}", "", "", "", "", "", "", "", "", "", "", "",
            "", str(path), "needs_manual_review", "Populate drug_id/date/section after label version audit.",
        ])

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerows(rows)

    print(f"Wrote {len(rows)} label history review rows.")


if __name__ == "__main__":
    main()

