#!/usr/bin/env python3
"""Build a prioritized manual verification queue from the pilot evidence matrix."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "tables" / "pilot_core_safety_evidence_matrix.csv"
OUT = ROOT / "tables" / "pilot_manual_verification_queue.csv"


HIGH_PRIORITY_CONCEPTS = {
    "fatal_adverse_event",
    "serious_adverse_event",
    "grade_3_or_higher_adverse_event",
}


def priority(row: dict[str, str]) -> tuple[int, str]:
    note = row["adjudication_note"]
    sources = row["available_sources"].split(";") if row["available_sources"] else []
    concept = row["safety_concept"]
    if "No source" in note:
        return 1, "no extracted source value"
    if concept == "fatal_adverse_event":
        return 1, "fatal outcome requires time-window and causality adjudication"
    if len(sources) >= 2 and "Multiple denominators" in note:
        return 1, "multiple sources with different denominators/populations"
    if concept in HIGH_PRIORITY_CONCEPTS:
        return 2, "high-impact safety concept"
    if "FDA row may use a broader" in note:
        return 2, "FDA approval-review pool may differ from trial population"
    return 3, "standard numeric verification"


def main() -> None:
    with MATRIX.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    queue = []
    for row in rows:
        p, reason = priority(row)
        queue.append(
            {
                "priority": f"P{p}",
                "reason": reason,
                "trial_id": row["trial_id"],
                "acronym": row["acronym"],
                "drug_id": row["drug_id"],
                "safety_concept": row["safety_concept"],
                "concept_label": row["concept_label"],
                "available_sources": row["available_sources"],
                "preferred_source_for_manual_review": row["preferred_source_for_manual_review"],
                "preferred_document_id": row["preferred_document_id"],
                "preferred_locator": row["preferred_locator"],
                "preferred_number_patients": row["preferred_number_patients"],
                "preferred_denominator": row["preferred_denominator"],
                "preferred_percentage": row["preferred_percentage"],
                "adjudication_note": row["adjudication_note"],
            }
        )

    queue.sort(key=lambda r: (r["priority"], r["trial_id"], r["safety_concept"]))

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(queue[0]))
        writer.writeheader()
        writer.writerows(queue)
    print(f"Wrote {len(queue)} verification rows to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
