#!/usr/bin/env python3
"""Build the current analysis-ready comparison candidate set."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "data" / "processed" / "full_cohort_source_comparability_matrix.csv"
P1 = ROOT / "tables" / "p1_source_comparability_adjudication_recommendations.csv"
P3_P4 = ROOT / "tables" / "p3_p4_source_comparability_adjudication_recommendations.csv"
OUT = ROOT / "tables" / "analysis_ready_comparison_set.csv"
REPORT_OUT = ROOT / "protocol" / "analysis_ready_comparison_set_report.zh.md"

FIELDS = [
    "comparison_id", "trial_id", "ae_concept", "source_1", "source_2",
    "arm_id_1", "arm_id_2", "denominator_1", "denominator_2",
    "percentage_1", "percentage_2", "absolute_percentage_difference",
    "analysis_tier", "analysis_use", "grade_basis", "review_status",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    out_rows: dict[str, dict[str, str]] = {}

    for row in read_csv(MATRIX):
        if row.get("comparability_grade") != "A":
            continue
        out_rows[row["comparison_id"]] = {
            "comparison_id": row["comparison_id"],
            "trial_id": row["trial_id"],
            "ae_concept": row["ae_concept"],
            "source_1": row["source_1"],
            "source_2": row["source_2"],
            "arm_id_1": row["arm_id_1"],
            "arm_id_2": row["arm_id_2"],
            "denominator_1": row["denominator_1"],
            "denominator_2": row["denominator_2"],
            "percentage_1": row["percentage_1"],
            "percentage_2": row["percentage_2"],
            "absolute_percentage_difference": row["absolute_percentage_difference"],
            "analysis_tier": "primary_candidate",
            "analysis_use": "primary_analysis_candidate",
            "grade_basis": "automatic_A_from_full_cohort_matrix",
            "review_status": "needs_source_confirmation",
        }

    for row in read_csv(P1):
        grade = row.get("recommended_grade", "")
        if grade not in {"A", "B"}:
            continue
        out_rows[row["comparison_id"]] = {
            "comparison_id": row["comparison_id"],
            "trial_id": row["trial_id"],
            "ae_concept": row["ae_concept"],
            "source_1": row["source_1"],
            "source_2": row["source_2"],
            "arm_id_1": row["arm_id_1"],
            "arm_id_2": row["arm_id_2"],
            "denominator_1": row["denominator_1"],
            "denominator_2": row["denominator_2"],
            "percentage_1": row["percentage_1"],
            "percentage_2": row["percentage_2"],
            "absolute_percentage_difference": row["absolute_percentage_difference"],
            "analysis_tier": "primary_candidate" if grade == "A" else "sensitivity_candidate",
            "analysis_use": row["recommended_analysis_use"],
            "grade_basis": f"P1_recommended_{grade}",
            "review_status": row["final_review_status"],
        }

    if P3_P4.exists():
        for row in read_csv(P3_P4):
            grade = row.get("recommended_grade", "")
            use = row.get("recommended_analysis_use", "")
            if grade != "B" or use != "sensitivity_analysis_candidate":
                continue
            out_rows[row["comparison_id"]] = {
                "comparison_id": row["comparison_id"],
                "trial_id": row["trial_id"],
                "ae_concept": row["ae_concept"],
                "source_1": row["source_1"],
                "source_2": row["source_2"],
                "arm_id_1": "",
                "arm_id_2": "",
                "denominator_1": row["denominator_1"],
                "denominator_2": row["denominator_2"],
                "percentage_1": row["percentage_1"],
                "percentage_2": row["percentage_2"],
                "absolute_percentage_difference": row["absolute_percentage_difference"],
                "analysis_tier": "sensitivity_candidate",
                "analysis_use": use,
                "grade_basis": "P3_P4_recommended_B",
                "review_status": row["final_review_status"],
            }

    rows = sorted(out_rows.values(), key=lambda r: (r["analysis_tier"], r["trial_id"], r["ae_concept"], r["comparison_id"]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    by_tier = Counter(row["analysis_tier"] for row in rows)
    by_trial = Counter(row["trial_id"] for row in rows)
    by_basis = Counter(row["grade_basis"] for row in rows)

    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(
        "\n".join([
            "# Analysis-ready comparison set 报告",
            "",
            "日期：2026-06-18",
            "",
            "## 输出",
            "",
            "- `tables/analysis_ready_comparison_set.csv`",
            "",
            "## 当前候选集",
            "",
            f"- 总配对：{len(rows)}",
            *[f"- {tier}: {count}" for tier, count in sorted(by_tier.items())],
            "",
            "## 覆盖 trial",
            "",
            *[f"- {trial}: {count}" for trial, count in sorted(by_trial.items())],
            "",
            "## 来源依据",
            "",
            *[f"- {basis}: {count}" for basis, count in sorted(by_basis.items())],
            "",
            "## 使用边界",
            "",
            "该候选集可用于下一步生成描述性结果和差异分布，但仍保留 `needs_source_confirmation`，正式 manuscript 数值前需逐条核对来源页。",
        ]) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
