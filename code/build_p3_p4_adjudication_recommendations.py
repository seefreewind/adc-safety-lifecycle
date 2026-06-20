#!/usr/bin/env python3
"""Recommend outcomes for P3/P4 comparability adjudication candidates."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "tables" / "source_comparability_adjudication_queue.csv"
DETAIL = ROOT / "data" / "processed" / "full_cohort_source_comparability_matrix_detail.csv"
OUT = ROOT / "tables" / "p3_p4_source_comparability_adjudication_recommendations.csv"
REPORT_OUT = ROOT / "protocol" / "p3_p4_source_comparability_adjudication_recommendations.zh.md"

FIELDS = [
    "comparison_id", "trial_id", "ae_concept", "source_1", "source_2",
    "term_1", "term_2", "grade_category_1", "grade_category_2",
    "seriousness_1", "seriousness_2", "causality_1", "causality_2",
    "denominator_1", "denominator_2", "percentage_1", "percentage_2",
    "absolute_percentage_difference", "adjudication_priority",
    "recommended_grade", "recommended_analysis_use", "recommendation_reason",
    "final_review_status",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def as_float(value: str) -> float | None:
    try:
        if value == "":
            return None
        return float(value)
    except ValueError:
        return None


def detail_id_from_comp(comp_id: str) -> str:
    return comp_id.replace("FULLCOMP", "FULLDET")


def recommend(row: dict[str, str], priority: str) -> tuple[str, str, str]:
    diff = as_float(row.get("absolute_percentage_difference", "")) or 999.0
    denom_diff = as_float(row.get("denominator_difference_percent", "")) or 999.0
    causality_1 = (row.get("causality_1", "") or "").lower()
    causality_2 = (row.get("causality_2", "") or "").lower()
    source_pair = {row.get("source_1", ""), row.get("source_2", "")}
    population_1 = (row.get("analysis_population_1", "") or "").lower()
    population_2 = (row.get("analysis_population_2", "") or "").lower()
    term_1 = (row.get("term_1", "") or "").lower()
    term_2 = (row.get("term_2", "") or "").lower()

    if priority == "3":
        if causality_1 != causality_2:
            if diff <= 2 and "fatal" in row.get("ae_concept", ""):
                return (
                    "C",
                    "contextual_support_only",
                    "Fatal-event percentages are close, but all-cause and treatment-related causality definitions differ; keep as contextual support, not quantitative concordance.",
                )
            if "all adverse events" in term_1 and ("drug-related" in term_2 or "treatment-related" in term_2):
                return (
                    "exclude",
                    "duplicate_cross_definition",
                    "This is a cross-match between all-cause and treatment-related AE rows; the matched same-causality pair is handled elsewhere.",
                )
            return (
                "C",
                "descriptive_only",
                "Definitions differ by causality; retain for narrative comparison only.",
            )
        return (
            "C",
            "descriptive_only",
            "Definition mismatch remains after detailed review; not suitable for quantitative concordance.",
        )

    if priority == "4":
        if "pool" in population_1 or "pool" in population_2:
            if diff <= 3 and "FDA review" in source_pair:
                return (
                    "B",
                    "sensitivity_analysis_candidate",
                    "FDA approval-review pool differs from trial-specific publication population, but the percentage difference is small; use only in sensitivity analysis after source confirmation.",
                )
            return (
                "C",
                "descriptive_only",
                "FDA approval-review pool differs from the trial-specific source; difference or denominator mismatch is too large for sensitivity analysis.",
            )
        if denom_diff > 50:
            return (
                "C",
                "descriptive_only",
                "Denominators differ substantially, indicating different analysis populations.",
            )
        if diff <= 3:
            return (
                "B",
                "sensitivity_analysis_candidate",
                "Definitions align and percentage difference is small, but denominator/population mismatch prevents primary-analysis use.",
            )
        return (
            "C",
            "descriptive_only",
            "Population or denominator mismatch remains too large for quantitative concordance.",
        )

    return ("C", "descriptive_only", "Priority outside P3/P4.")


def main() -> None:
    queue = {
        row["comparison_id"]: row
        for row in read_csv(QUEUE)
        if row.get("adjudication_priority") in {"3", "4"}
    }
    detail_by_comp = {
        row["comparison_id"]: row
        for row in read_csv(DETAIL)
    }

    out_rows = []
    for comp_id, qrow in sorted(queue.items()):
        detail = detail_by_comp.get(detail_id_from_comp(comp_id))
        if not detail:
            continue
        grade, use, reason = recommend(detail, qrow["adjudication_priority"])
        merged = {field: "" for field in FIELDS}
        for field in FIELDS:
            if field in detail:
                merged[field] = detail[field]
        merged["comparison_id"] = comp_id
        merged["adjudication_priority"] = qrow["adjudication_priority"]
        merged["recommended_grade"] = grade
        merged["recommended_analysis_use"] = use
        merged["recommendation_reason"] = reason
        merged["final_review_status"] = "recommended_needs_source_confirmation"
        out_rows.append(merged)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(out_rows)

    by_grade = Counter(row["recommended_grade"] for row in out_rows)
    by_use = Counter(row["recommended_analysis_use"] for row in out_rows)
    by_trial = Counter(row["trial_id"] for row in out_rows)

    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(
        "\n".join([
            "# P3/P4 source-comparability adjudication recommendations",
            "",
            "日期：2026-06-19",
            "",
            "## 输出",
            "",
            "- `tables/p3_p4_source_comparability_adjudication_recommendations.csv`",
            "",
            "## 建议结果",
            "",
            f"- P3/P4 配对：{len(out_rows)}",
            *[f"- 推荐 {grade}: {count}" for grade, count in sorted(by_grade.items())],
            "",
            "## 分析用途",
            "",
            *[f"- {use}: {count}" for use, count in sorted(by_use.items())],
            "",
            "## 覆盖 trial",
            "",
            *[f"- {trial}: {count}" for trial, count in sorted(by_trial.items())],
            "",
            "## 解释",
            "",
            "P3 中多数为 all-cause 与 treatment-related 的交叉匹配，不建议升级为主分析。P4 中仅当 FDA 审评池与 publication/CT.gov 的百分比差较小且定义一致时，建议作为敏感性分析候选。",
        ]) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
