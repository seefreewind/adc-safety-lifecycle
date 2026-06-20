#!/usr/bin/env python3
"""Extract B-grade source-comparability pairs as manual upgrade candidates."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "data" / "processed" / "source_comparability_matrix.csv"
OUT = ROOT / "tables" / "comparability_upgrade_candidates.csv"


def main() -> None:
    with MATRIX.open(newline="", encoding="utf-8") as f:
        rows = [row for row in csv.DictReader(f) if row["comparability_grade"] == "B"]

    for row in rows:
        row["upgrade_question"] = (
            "Can the two source rows be treated as the same safety population and dose cohort after checking source definitions?"
        )
        row["proposed_manual_action"] = (
            "If arm, denominator, safety population, grade, causality, and cutoff align, upgrade to A; otherwise keep B."
        )

    if rows:
        with OUT.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    print(f"Wrote {len(rows)} upgrade-candidate rows to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
