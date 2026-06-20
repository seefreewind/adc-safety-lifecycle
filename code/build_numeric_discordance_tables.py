#!/usr/bin/env python3
"""Build numeric discordance tables for comparable source pairs."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "data" / "processed" / "source_comparability_matrix.csv"
OUT_PRIMARY = ROOT / "tables" / "table4_primary_numeric_discordance_pairs.csv"
OUT_SENS = ROOT / "tables" / "table5_sensitivity_numeric_discordance_pairs.csv"


def read_rows() -> list[dict[str, str]]:
    with MATRIX.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_filtered(path: Path, rows: list[dict[str, str]], grade: str) -> None:
    selected = [row for row in rows if row["comparability_grade"] == grade]
    keep = [
        "comparison_id",
        "trial_id",
        "arm_id",
        "ae_concept",
        "source_1",
        "source_document_id_1",
        "number_patients_1",
        "denominator_1",
        "percentage_1",
        "source_2",
        "source_document_id_2",
        "number_patients_2",
        "denominator_2",
        "percentage_2",
        "absolute_percentage_difference",
        "reason",
        "review_status",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keep)
        writer.writeheader()
        writer.writerows([{key: row.get(key, "") for key in keep} for row in selected])
    print(f"Wrote {len(selected)} rows to {path.relative_to(ROOT)}")


def main() -> None:
    rows = read_rows()
    write_filtered(OUT_PRIMARY, rows, "A")
    write_filtered(OUT_SENS, rows, "B")


if __name__ == "__main__":
    main()
