#!/usr/bin/env python3
"""Summarize accepted A-grade numeric-discordance pairs."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INFILE = ROOT / "tables" / "table4_primary_numeric_discordance_pairs.csv"
OUTFILE = ROOT / "tables" / "analysis_primary_numeric_discordance_summary.csv"


def as_float(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return 0.0


def main() -> None:
    with INFILE.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    diffs = [as_float(row["absolute_percentage_difference"]) for row in rows]
    zero = sum(1 for value in diffs if value == 0)
    nonzero = len(diffs) - zero
    max_diff = max(diffs) if diffs else 0
    mean_diff = sum(diffs) / len(diffs) if diffs else 0

    summary = [
        {
            "accepted_a_grade_pairs": len(rows),
            "zero_difference_pairs": zero,
            "nonzero_difference_pairs": nonzero,
            "mean_absolute_percentage_point_difference": f"{mean_diff:.2f}",
            "maximum_absolute_percentage_point_difference": f"{max_diff:.2f}",
            "accepted_by_user": "yes",
            "acceptance_note": "User accepted the 13 A-grade pairs for pilot primary analysis.",
        }
    ]
    with OUTFILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    print(f"Wrote primary-discordance summary to {OUTFILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
