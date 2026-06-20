#!/usr/bin/env python3
"""Build pairwise source comparability rows for pilot core safety outcomes."""

from __future__ import annotations

import csv
import itertools
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "tables"

OUT_MATRIX = PROCESSED / "source_comparability_matrix.csv"
OUT_SUMMARY = TABLES / "pilot_source_concordance_summary.csv"

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


def normalize_concept(concept: str) -> str:
    return CONCEPT_ALIASES.get(concept, concept)


def add_source(rows: list[dict[str, str]], source_name: str) -> list[dict[str, str]]:
    out = []
    for row in rows:
        copied = dict(row)
        copied["source_name"] = source_name
        copied["normalized_concept"] = normalize_concept(copied.get("safety_concept", ""))
        out.append(copied)
    return out


def as_float(value: str) -> float | None:
    try:
        if value == "":
            return None
        return float(value)
    except ValueError:
        return None


def denominator_difference_percent(a: str, b: str) -> str:
    da = as_float(a)
    db = as_float(b)
    if da is None or db is None or max(da, db) == 0:
        return ""
    return f"{abs(da - db) / max(da, db) * 100:.2f}"


def numeric_difference(a: str, b: str) -> str:
    fa = as_float(a)
    fb = as_float(b)
    if fa is None or fb is None:
        return ""
    return f"{abs(fa - fb):.2f}"


def same_text(a: str, b: str) -> str:
    return "yes" if (a or "").strip().lower() == (b or "").strip().lower() else "no"


def populations_look_same(a: str, b: str) -> str:
    aa = (a or "").strip().lower()
    bb = (b or "").strip().lower()
    if aa and bb and aa == bb:
        return "yes"
    if not aa or not bb:
        return "unknown"
    return "no"


def definitions_align(a: dict[str, str], b: dict[str, str]) -> bool:
    concept = a["normalized_concept"]
    same_grade = same_text(a.get("grade_category", ""), b.get("grade_category", "")) == "yes"
    same_causality = same_text(a.get("causality", ""), b.get("causality", "")) == "yes"
    if not same_grade or not same_causality:
        return False

    if concept == "dose_interruption":
        left = (a.get("seriousness", "") or "").lower()
        right = (b.get("seriousness", "") or "").lower()
        return left in {"dose_interruption", "dose_delay"} and right in {"dose_interruption", "dose_delay"}

    return same_text(a.get("seriousness", ""), b.get("seriousness", "")) == "yes"


def grade_pair(a: dict[str, str], b: dict[str, str]) -> tuple[str, str, str]:
    reasons = []
    concept = a["normalized_concept"]
    if a.get("arm_id", "") and b.get("arm_id", "") and a.get("arm_id") != b.get("arm_id"):
        return "C", "descriptive_only", "different treatment arms or dose cohorts"

    same_definition = definitions_align(a, b)
    denom_pct = as_float(denominator_difference_percent(a.get("denominator", ""), b.get("denominator", "")))
    same_population = populations_look_same(a.get("analysis_population", ""), b.get("analysis_population", ""))
    same_arm = same_text(a.get("arm_id", ""), b.get("arm_id", "")) == "yes"

    if concept == "fatal_adverse_event" and "ClinicalTrials.gov" in {a["source_name"], b["source_name"]}:
        return "C", "descriptive_only", "CT.gov all-cause mortality is not directly comparable with fatal AE without adjudication."

    if "ClinicalTrials.gov" in {a["source_name"], b["source_name"]}:
        ctgov_row = a if a["source_name"] == "ClinicalTrials.gov" else b
        notes = (ctgov_row.get("notes", "") or "").lower()
        if "maximum" in notes or "up to" in notes:
            return "C", "descriptive_only", "CT.gov adverse-event time window may differ from publication or FDA primary analysis cutoff."

    if same_definition and denom_pct == 0 and same_population == "yes":
        return "A", "primary_analysis", "Same concept definition, denominator, and named analysis population."

    if same_definition and denom_pct == 0 and same_arm:
        return "A", "primary_analysis", "Same concept definition, treatment arm, and denominator; analysis population inferred as aligned pending manual confirmation."

    if same_definition and denom_pct is not None and denom_pct <= 5:
        if same_population == "no":
            reasons.append("analysis population names differ")
        if denom_pct > 0:
            reasons.append("denominator differs by <=5%")
        return "B", "sensitivity_analysis", "; ".join(reasons) or "Minor source differences only."

    if not same_definition:
        reasons.append("grade/seriousness/causality definition differs")
    if denom_pct is None:
        reasons.append("denominator missing in at least one source")
    elif denom_pct > 5:
        reasons.append("denominator differs by >5%")
    if same_population == "no":
        reasons.append("analysis population differs")
    if any("pool" in (row.get("analysis_population", "").lower()) for row in [a, b]):
        reasons.append("approval-review pooled population may not match trial-specific source")
    return "C", "descriptive_only", "; ".join(dict.fromkeys(reasons)) or "Manual review required before comparison."


def source_pair_label(a: dict[str, str], b: dict[str, str]) -> str:
    return f"{a['source_name']} vs {b['source_name']}"


def main() -> None:
    TABLES.mkdir(exist_ok=True)
    rows = (
        add_source(read_csv(INTERIM / "publication_core_safety_seed.csv"), "publication")
        + add_source(read_csv(INTERIM / "ctgov_core_safety_seed.csv"), "ClinicalTrials.gov")
        + add_source(read_csv(INTERIM / "fda_core_safety_seed.csv"), "FDA review")
    )

    indexed: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        indexed[(row.get("trial_id", ""), row.get("normalized_concept", ""))].append(row)

    matrix_rows: list[dict[str, str]] = []
    seq = 1
    for (trial_id, concept), grouped in sorted(indexed.items()):
        for left, right in itertools.combinations(grouped, 2):
            if left["source_name"] == right["source_name"]:
                continue
            grade, use, reason = grade_pair(left, right)
            matrix_rows.append(
                {
                    "comparison_id": f"COMP{seq:06d}",
                    "trial_id": trial_id,
                    "arm_id": left.get("arm_id", ""),
                    "ae_concept": concept,
                    "source_document_id_1": left.get("document_id", ""),
                    "source_document_id_2": right.get("document_id", ""),
                    "source_1": left.get("source_name", ""),
                    "source_2": right.get("source_name", ""),
                    "number_patients_1": left.get("number_patients", ""),
                    "number_patients_2": right.get("number_patients", ""),
                    "denominator_1": left.get("denominator", ""),
                    "denominator_2": right.get("denominator", ""),
                    "percentage_1": left.get("percentage", ""),
                    "percentage_2": right.get("percentage", ""),
                    "absolute_percentage_difference": numeric_difference(left.get("percentage", ""), right.get("percentage", "")),
                    "comparability_grade": grade,
                    "same_trial": "yes",
                    "same_arm": same_text(left.get("arm_id", ""), right.get("arm_id", "")),
                    "same_dose": "needs_review",
                    "same_population": populations_look_same(left.get("analysis_population", ""), right.get("analysis_population", "")),
                    "cutoff_difference_days": "",
                    "same_ae_definition": "yes" if "definition differs" not in reason else "no",
                    "denominator_difference_percent": denominator_difference_percent(left.get("denominator", ""), right.get("denominator", "")),
                    "reason": reason,
                    "analysis_use": use,
                    "review_status": "auto_needs_review",
                }
            )
            seq += 1

    with OUT_MATRIX.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(matrix_rows[0]))
        writer.writeheader()
        writer.writerows(matrix_rows)

    summary_counter: dict[tuple[str, str, str], int] = defaultdict(int)
    for row in matrix_rows:
        summary_counter[(row["trial_id"], row["ae_concept"], row["comparability_grade"])] += 1

    summary_rows = [
        {
            "trial_id": trial_id,
            "ae_concept": concept,
            "comparability_grade": grade,
            "pair_count": count,
        }
        for (trial_id, concept, grade), count in sorted(summary_counter.items())
    ]
    with OUT_SUMMARY.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0]))
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"Wrote {len(matrix_rows)} source-comparability rows to {OUT_MATRIX.relative_to(ROOT)}")
    print(f"Wrote {len(summary_rows)} summary rows to {OUT_SUMMARY.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
