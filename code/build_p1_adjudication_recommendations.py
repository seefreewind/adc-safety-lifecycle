#!/usr/bin/env python3
"""Recommend adjudication outcomes for highest-priority comparability pairs."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "tables" / "source_comparability_adjudication_queue.csv"
OUT = ROOT / "tables" / "p1_source_comparability_adjudication_recommendations.csv"
REPORT_OUT = ROOT / "protocol" / "p1_source_comparability_adjudication_recommendations.zh.md"

KEEP = [
    "comparison_id", "trial_id", "ae_concept", "source_1", "source_2",
    "arm_id_1", "arm_id_2", "denominator_1", "denominator_2",
    "percentage_1", "percentage_2", "absolute_percentage_difference",
    "recommended_grade", "recommended_analysis_use", "recommendation_reason",
    "final_review_status",
]


def as_float(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return 999.0


def recommend(row: dict[str, str]) -> tuple[str, str, str]:
    diff = as_float(row.get("absolute_percentage_difference", ""))
    trial = row.get("trial_id", "")
    if diff <= 1.0:
        return (
            "A",
            "primary_analysis_candidate",
            "Same arm and denominator; serious AE percentage differs by <=1 percentage point. Recommend upgrade after source-page confirmation.",
        )
    if diff <= 7.0:
        return (
            "B",
            "sensitivity_analysis_candidate",
            "Same arm and denominator, but CT.gov serious AE percentage differs by 1-7 percentage points, likely reflecting time-window or cutoff differences.",
        )
    return (
        "C",
        "descriptive_only",
        f"{trial} remains descriptive because the percentage difference is too large for automatic upgrade.",
    )


def main() -> None:
    with QUEUE.open(newline="", encoding="utf-8") as f:
        rows = [row for row in csv.DictReader(f) if row.get("adjudication_priority") == "1"]

    out_rows = []
    for row in rows:
        grade, use, reason = recommend(row)
        enriched = {key: row.get(key, "") for key in KEEP}
        enriched["recommended_grade"] = grade
        enriched["recommended_analysis_use"] = use
        enriched["recommendation_reason"] = reason
        enriched["final_review_status"] = "recommended_needs_source_confirmation"
        out_rows.append(enriched)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=KEEP)
        writer.writeheader()
        writer.writerows(out_rows)

    by_grade = Counter(row["recommended_grade"] for row in out_rows)
    by_trial = Counter(row["trial_id"] for row in out_rows)

    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(
        "\n".join([
            "# P1 source-comparability adjudication recommendations",
            "",
            "日期：2026-06-18",
            "",
            "## 输出",
            "",
            "- `tables/p1_source_comparability_adjudication_recommendations.csv`",
            "",
            "## 建议结果",
            "",
            f"- P1 配对：{len(out_rows)}",
            *[f"- 推荐 {grade} 级：{count}" for grade, count in sorted(by_grade.items())],
            "",
            "## 覆盖 trial",
            "",
            *[f"- {trial}: {count}" for trial, count in sorted(by_trial.items())],
            "",
            "## 解释",
            "",
            "该文件是自动裁决建议，不是最终裁决。建议进入正式统计前逐条核对来源页，尤其确认 CT.gov serious AE 时间窗是否可接受。",
        ]) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
