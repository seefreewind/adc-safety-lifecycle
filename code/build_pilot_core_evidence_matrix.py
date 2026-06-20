#!/usr/bin/env python3
"""Build a source-aware pilot evidence matrix for core safety outcomes."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "tables"

CORE_CONCEPTS = [
    "any_adverse_event",
    "grade_3_or_higher_adverse_event",
    "serious_adverse_event",
    "fatal_adverse_event",
    "adverse_event_leading_to_discontinuation",
    "dose_reduction",
    "dose_interruption",
]

CONCEPT_LABELS = {
    "any_adverse_event": "Any adverse event",
    "grade_3_or_higher_adverse_event": "Grade 3 or higher adverse event",
    "serious_adverse_event": "Serious adverse event",
    "fatal_adverse_event": "Fatal adverse event / death",
    "adverse_event_leading_to_discontinuation": "Adverse event leading to discontinuation",
    "dose_reduction": "Dose reduction",
    "dose_interruption": "Dose interruption",
}

CONCEPT_ALIASES = {
    "adverse_event_discontinuation": "adverse_event_leading_to_discontinuation",
    "adverse_event_dose_reduction": "dose_reduction",
    "adverse_event_dose_interruption": "dose_interruption",
    "grade 3 adverse_event": "grade_3_or_higher_adverse_event",
    "grade 4 adverse_event": "grade_3_or_higher_adverse_event",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def norm_concept(value: str) -> str:
    return CONCEPT_ALIASES.get(value, value)


def add_source(rows: list[dict[str, str]], source_name: str) -> list[dict[str, str]]:
    out = []
    for row in rows:
        copied = dict(row)
        copied["matrix_source"] = source_name
        copied["normalized_concept"] = norm_concept(row.get("safety_concept", ""))
        out.append(copied)
    return out


def source_rank(row: dict[str, str]) -> tuple[int, int, int]:
    source = row["matrix_source"]
    status = row.get("review_status", "")
    population = row.get("analysis_population", "").lower()
    if source == "publication":
        source_score = 0
    elif source == "FDA review":
        source_score = 1
    else:
        source_score = 2
    status_penalty = 1 if "manual" in status else 0
    population_penalty = 1 if any(token in population for token in ["pool", "overall safety population", "multiple tumor"]) else 0
    return source_score, status_penalty, population_penalty


def summarize_rows(rows: list[dict[str, str]]) -> str:
    if not rows:
        return ""
    parts = []
    for row in sorted(rows, key=source_rank):
        n = row.get("number_patients") or "NR"
        d = row.get("denominator") or "NR"
        pct = row.get("percentage") or "NR"
        parts.append(
            f"{row['matrix_source']}|{row.get('document_id','')}|{row.get('page_or_table_locator','')}|"
            f"{row.get('ae_original_term','')}|n={n}/{d}|pct={pct}|"
            f"{row.get('grade_category','')}|{row.get('seriousness','')}|{row.get('causality','')}"
        )
    return " || ".join(parts)


def best_source(rows: list[dict[str, str]]) -> str:
    if not rows:
        return ""
    row = sorted(rows, key=source_rank)[0]
    return row["matrix_source"]


def best_value(rows: list[dict[str, str]]) -> tuple[str, str, str, str, str]:
    if not rows:
        return "", "", "", "", ""
    row = sorted(rows, key=source_rank)[0]
    return (
        row.get("document_id", ""),
        row.get("page_or_table_locator", ""),
        row.get("number_patients", ""),
        row.get("denominator", ""),
        row.get("percentage", ""),
    )


def adjudication_note(rows: list[dict[str, str]], concept: str) -> str:
    if not rows:
        return "No source row extracted yet."
    sources = {row["matrix_source"] for row in rows}
    denoms = {row.get("denominator", "") for row in rows if row.get("denominator")}
    populations = {row.get("analysis_population", "") for row in rows if row.get("analysis_population")}
    if concept == "fatal_adverse_event":
        return "Fatal outcomes need manual adjudication; CT.gov all-cause mortality and publication fatal AE often use different time windows."
    if len(denoms) > 1:
        return "Multiple denominators/populations present; use source-specific values unless denominator alignment is confirmed."
    if "FDA review" in sources and any("pool" in pop.lower() for pop in populations):
        return "FDA row may use a broader approval-review safety pool; do not treat as direct trial-publication replicate without alignment."
    return "Candidate for manual numeric verification."


def main() -> None:
    TABLES.mkdir(exist_ok=True)
    trials = read_csv(PROCESSED / "trial_master.csv")
    all_rows = (
        add_source(read_csv(INTERIM / "publication_core_safety_seed.csv"), "publication")
        + add_source(read_csv(INTERIM / "ctgov_core_safety_seed.csv"), "ClinicalTrials.gov")
        + add_source(read_csv(INTERIM / "fda_core_safety_seed.csv"), "FDA review")
    )

    indexed: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in all_rows:
        indexed[(row.get("trial_id", ""), row.get("normalized_concept", ""))].append(row)

    output_rows: list[dict[str, str]] = []
    for trial in trials:
        for concept in CORE_CONCEPTS:
            rows = indexed.get((trial["trial_id"], concept), [])
            doc, locator, n, d, pct = best_value(rows)
            output_rows.append(
                {
                    "trial_id": trial["trial_id"],
                    "nct_number": trial.get("nct_number", ""),
                    "acronym": trial.get("acronym", ""),
                    "drug_id": trial.get("drug_id", ""),
                    "safety_concept": concept,
                    "concept_label": CONCEPT_LABELS[concept],
                    "available_sources": ";".join(sorted({row["matrix_source"] for row in rows})),
                    "preferred_source_for_manual_review": best_source(rows),
                    "preferred_document_id": doc,
                    "preferred_locator": locator,
                    "preferred_number_patients": n,
                    "preferred_denominator": d,
                    "preferred_percentage": pct,
                    "all_source_values": summarize_rows(rows),
                    "adjudication_note": adjudication_note(rows, concept),
                }
            )

    out = TABLES / "pilot_core_safety_evidence_matrix.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(output_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)
    print(f"Wrote {len(output_rows)} evidence-matrix rows to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
