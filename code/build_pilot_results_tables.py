#!/usr/bin/env python3
"""Build first-pass pilot results tables from the evidence matrix."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "tables"
MATRIX = TABLES / "pilot_core_safety_evidence_matrix.csv"
QUEUE = TABLES / "pilot_manual_verification_queue.csv"
CONCORDANCE = TABLES / "pilot_source_concordance_summary.csv"

OUT_COVERAGE = TABLES / "table1_pilot_source_coverage.csv"
OUT_VALUES = TABLES / "table2_core_safety_preferred_values.csv"
OUT_CONCORDANCE = TABLES / "table3_source_concordance_grade_summary.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def main() -> None:
    TABLES.mkdir(exist_ok=True)
    matrix = read_csv(MATRIX)
    queue = read_csv(QUEUE)
    concordance = read_csv(CONCORDANCE)

    by_trial: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in matrix:
        by_trial[row["trial_id"]].append(row)

    coverage_rows = []
    for trial_id, rows in sorted(by_trial.items()):
        first = rows[0]
        source_counter = Counter()
        for row in rows:
            for source in row["available_sources"].split(";"):
                if source:
                    source_counter[source] += 1
        coverage_rows.append(
            {
                "trial_id": trial_id,
                "acronym": first["acronym"],
                "drug_id": first["drug_id"],
                "core_concepts_total": len(rows),
                "core_concepts_with_any_source": sum(1 for row in rows if row["available_sources"]),
                "core_concepts_with_publication": source_counter["publication"],
                "core_concepts_with_ctgov": source_counter["ClinicalTrials.gov"],
                "core_concepts_with_fda": source_counter["FDA review"],
                "missing_core_concepts": "; ".join(row["concept_label"] for row in rows if not row["available_sources"]),
                "source_status_note": "Padcev FDA clinical review unavailable" if trial_id == "TRIAL003" else "",
            }
        )

    with OUT_COVERAGE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(coverage_rows[0]))
        writer.writeheader()
        writer.writerows(coverage_rows)

    priority_by_key = {(row["trial_id"], row["safety_concept"]): row["priority"] for row in queue}
    value_rows = []
    for row in matrix:
        value_rows.append(
            {
                "trial_id": row["trial_id"],
                "acronym": row["acronym"],
                "drug_id": row["drug_id"],
                "safety_concept": row["safety_concept"],
                "concept_label": row["concept_label"],
                "preferred_source": row["preferred_source_for_manual_review"],
                "preferred_document_id": row["preferred_document_id"],
                "preferred_locator": row["preferred_locator"],
                "number_patients": row["preferred_number_patients"],
                "denominator": row["preferred_denominator"],
                "percentage": row["preferred_percentage"],
                "requires_manual_review": yes_no(priority_by_key.get((row["trial_id"], row["safety_concept"]), "P3") in {"P1", "P2"}),
                "manual_review_priority": priority_by_key.get((row["trial_id"], row["safety_concept"]), ""),
                "adjudication_note": row["adjudication_note"],
            }
        )

    with OUT_VALUES.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(value_rows[0]))
        writer.writeheader()
        writer.writerows(value_rows)

    summary_counter: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for row in concordance:
        key = (row["trial_id"], row["ae_concept"])
        summary_counter[key][row["comparability_grade"]] += int(row["pair_count"])

    concordance_rows = []
    for (trial_id, concept), counts in sorted(summary_counter.items()):
        concordance_rows.append(
            {
                "trial_id": trial_id,
                "safety_concept": concept,
                "a_grade_pairs": counts["A"],
                "b_grade_pairs": counts["B"],
                "c_grade_pairs": counts["C"],
                "primary_analysis_pair_available": yes_no(counts["A"] > 0),
                "sensitivity_pair_available": yes_no(counts["B"] > 0),
                "descriptive_only_pair_count": counts["C"],
            }
        )

    with OUT_CONCORDANCE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(concordance_rows[0]))
        writer.writeheader()
        writer.writerows(concordance_rows)

    print(f"Wrote {len(coverage_rows)} rows to {OUT_COVERAGE.relative_to(ROOT)}")
    print(f"Wrote {len(value_rows)} rows to {OUT_VALUES.relative_to(ROOT)}")
    print(f"Wrote {len(concordance_rows)} rows to {OUT_CONCORDANCE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
