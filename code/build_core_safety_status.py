#!/usr/bin/env python3
"""Build a pilot-level status matrix for core safety extraction sources."""

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

CONCEPT_ALIASES = {
    "adverse_event_discontinuation": "adverse_event_leading_to_discontinuation",
    "adverse_event_dose_reduction": "dose_reduction",
    "adverse_event_dose_interruption": "dose_interruption",
    "grade 3 adverse_event": "grade_3_or_higher_adverse_event",
    "grade 4 adverse_event": "grade_3_or_higher_adverse_event",
}

CONCEPT_LABELS = {
    "any_adverse_event": "Any adverse event",
    "grade_3_or_higher_adverse_event": "Grade 3 or higher adverse event",
    "serious_adverse_event": "Serious adverse event",
    "fatal_adverse_event": "Fatal adverse event / death",
    "adverse_event_leading_to_discontinuation": "Adverse event leading to discontinuation",
    "dose_reduction": "Dose reduction",
    "dose_interruption": "Dose interruption",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def index_rows(rows: list[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    indexed: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        concept = CONCEPT_ALIASES.get(row.get("safety_concept", ""), row.get("safety_concept", ""))
        indexed[(row.get("trial_id", ""), concept)].append(row)
    return indexed


def status_for(rows: list[dict[str, str]], source: str) -> tuple[str, str]:
    if not rows:
        return "missing", ""
    review_flags = sorted({row.get("review_status", "") for row in rows if row.get("review_status")})
    denominators = sorted({row.get("denominator", "") for row in rows if row.get("denominator")})
    locators = sorted({row.get("page_or_table_locator", "") for row in rows if row.get("page_or_table_locator")})
    return (
        "extracted_needs_review",
        f"{source}: n_rows={len(rows)}; denominators={';'.join(denominators) or 'not recorded'}; "
        f"review={';'.join(review_flags) or 'not recorded'}; locators={'; '.join(locators[:3])}",
    )


def comparability_note(pub_rows: list[dict[str, str]], ct_rows: list[dict[str, str]], concept: str) -> str:
    if not pub_rows and not ct_rows:
        return "No extracted row yet."
    if pub_rows and not ct_rows:
        return "Publication source available; CT.gov structured core row not available."
    if ct_rows and not pub_rows:
        return "CT.gov structured row available; publication row not yet extracted."
    if concept == "fatal_adverse_event":
        return (
            "Do not directly compare without manual adjudication: CT.gov all-cause mortality often uses longer follow-up "
            "than publication fatal AE reporting."
        )
    pub_denoms = {row.get("denominator", "") for row in pub_rows}
    ct_denoms = {row.get("denominator", "") for row in ct_rows}
    if pub_denoms != ct_denoms:
        return "Both sources available, but denominators differ; compare only after arm/population alignment."
    return "Both sources available; still requires manual check of causality, grade, time window, and population."


def main() -> None:
    TABLES.mkdir(exist_ok=True)
    trials = read_csv(PROCESSED / "trial_master.csv")
    pub_index = index_rows(read_csv(INTERIM / "publication_core_safety_seed.csv"))
    ct_index = index_rows(read_csv(INTERIM / "ctgov_core_safety_seed.csv"))
    fda_index = index_rows(read_csv(INTERIM / "fda_core_safety_seed.csv"))

    rows: list[dict[str, str]] = []
    for trial in trials:
        trial_id = trial["trial_id"]
        for concept in CORE_CONCEPTS:
            pub_rows = pub_index.get((trial_id, concept), [])
            ct_rows = ct_index.get((trial_id, concept), [])
            fda_rows = fda_index.get((trial_id, concept), [])
            pub_status, pub_note = status_for(pub_rows, "publication")
            ct_status, ct_note = status_for(ct_rows, "ClinicalTrials.gov")
            fda_status, fda_note = status_for(fda_rows, "FDA review")
            rows.append(
                {
                    "trial_id": trial_id,
                    "nct_number": trial.get("nct_number", ""),
                    "acronym": trial.get("acronym", ""),
                    "drug_id": trial.get("drug_id", ""),
                    "safety_concept": concept,
                    "concept_label": CONCEPT_LABELS[concept],
                    "publication_status": pub_status,
                    "ctgov_status": ct_status,
                    "fda_status": fda_status,
                    "publication_note": pub_note,
                    "ctgov_note": ct_note,
                    "fda_note": fda_note,
                    "comparability_note": comparability_note(pub_rows, ct_rows, concept),
                    "recommended_next_action": "manual numeric verification" if pub_rows or ct_rows or fda_rows else "manual source review",
                }
            )

    output = TABLES / "pilot_core_safety_source_status.csv"
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
