#!/usr/bin/env python3
"""Build a detailed full-cohort source-comparability matrix for adjudication."""

from __future__ import annotations

import csv
import itertools
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "tables"
PROTOCOL = ROOT / "protocol"

OUT = PROCESSED / "full_cohort_source_comparability_matrix_detail.csv"
SUMMARY_OUT = TABLES / "full_cohort_source_comparability_matrix_detail_summary.csv"
REPORT_OUT = PROTOCOL / "full_cohort_source_comparability_matrix_detail_report.zh.md"

CONCEPT_ALIASES = {
    "adverse_event_discontinuation": "adverse_event_leading_to_discontinuation",
    "adverse_event_dose_reduction": "dose_reduction",
    "adverse_event_dose_interruption": "dose_interruption",
    "grade 3 adverse_event": "grade_3_or_higher_adverse_event",
    "grade 4 adverse_event": "grade_4_or_higher_adverse_event",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def normalize_concept(row: dict[str, str]) -> str:
    concept = row.get("canonical_safety_concept") or row.get("safety_concept", "")
    return CONCEPT_ALIASES.get(concept, concept)


def add_source(rows: list[dict[str, str]], source_name: str) -> list[dict[str, str]]:
    out = []
    for row in rows:
        copied = dict(row)
        copied["source_name"] = source_name
        copied["normalized_concept"] = normalize_concept(copied)
        out.append(copied)
    return out


def as_float(value: str) -> float | None:
    try:
        if value in {"", None}:  # type: ignore[comparison-overlap]
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def same_text(a: str, b: str) -> str:
    return "yes" if (a or "").strip().lower() == (b or "").strip().lower() else "no"


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


def populations_look_same(a: str, b: str) -> str:
    aa = (a or "").strip().lower()
    bb = (b or "").strip().lower()
    if aa and bb and aa == bb:
        return "yes"
    if not aa or not bb:
        return "unknown"
    return "no"


def definitions_align(a: dict[str, str], b: dict[str, str]) -> bool:
    same_grade = same_text(a.get("grade_category", ""), b.get("grade_category", "")) == "yes"
    same_causality = same_text(a.get("causality", ""), b.get("causality", "")) == "yes"
    if not same_grade or not same_causality:
        return False
    concept = a["normalized_concept"]
    if concept == "dose_interruption":
        left = (a.get("seriousness", "") or "").lower()
        right = (b.get("seriousness", "") or "").lower()
        return left in {"dose_interruption", "dose_delay"} and right in {"dose_interruption", "dose_delay"}
    return same_text(a.get("seriousness", ""), b.get("seriousness", "")) == "yes"


def grade_pair(a: dict[str, str], b: dict[str, str]) -> tuple[str, str, str]:
    reasons: list[str] = []
    concept = a["normalized_concept"]
    if a.get("arm_id") and b.get("arm_id") and a.get("arm_id") != b.get("arm_id"):
        return "C", "descriptive_only", "different treatment arms or dose cohorts"

    same_definition = definitions_align(a, b)
    denom_pct_value = as_float(denominator_difference_percent(a.get("denominator", ""), b.get("denominator", "")))
    same_population = populations_look_same(a.get("analysis_population", ""), b.get("analysis_population", ""))
    same_arm = same_text(a.get("arm_id", ""), b.get("arm_id", "")) == "yes"

    if concept == "fatal_adverse_event" and "ClinicalTrials.gov" in {a["source_name"], b["source_name"]}:
        return "C", "descriptive_only", "CT.gov all-cause mortality is not directly comparable with fatal AE without adjudication."

    if "ClinicalTrials.gov" in {a["source_name"], b["source_name"]}:
        ctgov_row = a if a["source_name"] == "ClinicalTrials.gov" else b
        notes = (ctgov_row.get("notes", "") or "").lower()
        if "maximum" in notes or "up to" in notes:
            return "C", "descriptive_only", "CT.gov adverse-event time window may differ from publication or FDA primary analysis cutoff."

    if same_definition and denom_pct_value == 0 and same_population == "yes":
        return "A", "primary_analysis", "Same concept definition, denominator, and named analysis population."
    if same_definition and denom_pct_value == 0 and same_arm:
        return "A", "primary_analysis", "Same concept definition, treatment arm, and denominator; analysis population inferred as aligned pending manual confirmation."
    if same_definition and denom_pct_value is not None and denom_pct_value <= 5:
        if same_population == "no":
            reasons.append("analysis population names differ")
        if denom_pct_value > 0:
            reasons.append("denominator differs by <=5%")
        return "B", "sensitivity_analysis", "; ".join(reasons) or "Minor source differences only."

    if not same_definition:
        reasons.append("grade/seriousness/causality definition differs")
    if denom_pct_value is None:
        reasons.append("denominator missing in at least one source")
    elif denom_pct_value > 5:
        reasons.append("denominator differs by >5%")
    if same_population == "no":
        reasons.append("analysis population differs")
    if any("pool" in (row.get("analysis_population", "").lower()) for row in [a, b]):
        reasons.append("approval-review pooled population may not match trial-specific source")
    return "C", "descriptive_only", "; ".join(dict.fromkeys(reasons)) or "Manual review required before comparison."


def col(row: dict[str, str], key: str) -> str:
    return row.get(key, "")


def main() -> None:
    rows = (
        add_source(read_csv(INTERIM / "publication_core_safety_combined_seed.csv"), "publication")
        + add_source(read_csv(INTERIM / "ctgov_core_safety_expansion_seed.csv"), "ClinicalTrials.gov")
        + add_source(read_csv(INTERIM / "fda_core_safety_combined_seed.csv"), "FDA review")
    )

    indexed: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        concept = row.get("normalized_concept", "")
        if concept:
            indexed[(row.get("trial_id", ""), concept)].append(row)

    out_rows: list[dict[str, str]] = []
    seq = 1
    for (trial_id, concept), grouped in sorted(indexed.items()):
        for left, right in itertools.combinations(grouped, 2):
            if left["source_name"] == right["source_name"]:
                continue
            grade, use, reason = grade_pair(left, right)
            out_rows.append({
                "comparison_id": f"FULLDET{seq:06d}",
                "trial_id": trial_id,
                "ae_concept": concept,
                "source_1": left["source_name"],
                "source_2": right["source_name"],
                "observation_id_1": col(left, "observation_id"),
                "observation_id_2": col(right, "observation_id"),
                "arm_id_1": col(left, "arm_id"),
                "arm_id_2": col(right, "arm_id"),
                "document_id_1": col(left, "document_id"),
                "document_id_2": col(right, "document_id"),
                "locator_1": col(left, "page_or_table_locator"),
                "locator_2": col(right, "page_or_table_locator"),
                "term_1": col(left, "ae_original_term"),
                "term_2": col(right, "ae_original_term"),
                "grade_category_1": col(left, "grade_category"),
                "grade_category_2": col(right, "grade_category"),
                "seriousness_1": col(left, "seriousness"),
                "seriousness_2": col(right, "seriousness"),
                "causality_1": col(left, "causality"),
                "causality_2": col(right, "causality"),
                "number_patients_1": col(left, "number_patients"),
                "number_patients_2": col(right, "number_patients"),
                "denominator_1": col(left, "denominator"),
                "denominator_2": col(right, "denominator"),
                "percentage_1": col(left, "percentage"),
                "percentage_2": col(right, "percentage"),
                "absolute_percentage_difference": numeric_difference(col(left, "percentage"), col(right, "percentage")),
                "analysis_population_1": col(left, "analysis_population"),
                "analysis_population_2": col(right, "analysis_population"),
                "comparability_grade": grade,
                "same_arm": same_text(col(left, "arm_id"), col(right, "arm_id")),
                "same_population": populations_look_same(col(left, "analysis_population"), col(right, "analysis_population")),
                "same_ae_definition": "yes" if "definition differs" not in reason else "no",
                "denominator_difference_percent": denominator_difference_percent(col(left, "denominator"), col(right, "denominator")),
                "reason": reason,
                "analysis_use": use,
                "review_status": "auto_needs_review",
                "notes_1": col(left, "notes"),
                "notes_2": col(right, "notes"),
            })
            seq += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0]))
        writer.writeheader()
        writer.writerows(out_rows)

    summary_rows = []
    for grade in sorted({row["comparability_grade"] for row in out_rows}):
        grade_rows = [row for row in out_rows if row["comparability_grade"] == grade]
        summary_rows.append({
            "comparability_grade": grade,
            "comparison_count": str(len(grade_rows)),
            "trial_count": str(len({row["trial_id"] for row in grade_rows})),
        })
    SUMMARY_OUT.parent.mkdir(parents=True, exist_ok=True)
    with SUMMARY_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0]))
        writer.writeheader()
        writer.writerows(summary_rows)

    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(
        "\n".join([
            "# Full-cohort source comparability detail matrix 报告",
            "",
            "日期：2026-06-19",
            "",
            "## 输出",
            "",
            "- `data/processed/full_cohort_source_comparability_matrix_detail.csv`",
            "- `tables/full_cohort_source_comparability_matrix_detail_summary.csv`",
            "",
            "## 用途",
            "",
            "该详细矩阵保留 observation_id、原始 AE 术语、grade、seriousness、causality、来源页和分析人群，用于人工裁决和自动裁决建议复核。",
            "",
            "## 覆盖",
            "",
            f"- 详细配对总数：{len(out_rows)}",
        ]) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Wrote {SUMMARY_OUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
