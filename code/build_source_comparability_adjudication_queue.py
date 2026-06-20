#!/usr/bin/env python3
"""Prioritize C-grade source-comparability pairs for manual adjudication."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "data" / "processed" / "full_cohort_source_comparability_matrix.csv"
OUT = ROOT / "tables" / "source_comparability_adjudication_queue.csv"
REPORT_OUT = ROOT / "protocol" / "source_comparability_adjudication_queue_report.zh.md"

KEEP = [
    "adjudication_priority", "adjudication_focus", "comparison_id", "trial_id",
    "ae_concept", "source_1", "source_2", "source_document_id_1", "source_document_id_2",
    "arm_id_1", "arm_id_2", "number_patients_1", "number_patients_2",
    "denominator_1", "denominator_2", "percentage_1", "percentage_2",
    "absolute_percentage_difference", "same_arm", "same_population",
    "same_ae_definition", "denominator_difference_percent", "reason", "analysis_use",
]


def as_float(value: str) -> float | None:
    try:
        if value == "":
            return None
        return float(value)
    except ValueError:
        return None


def priority(row: dict[str, str]) -> tuple[int, str]:
    reason = row.get("reason", "").lower()
    denom_diff = as_float(row.get("denominator_difference_percent", ""))
    pct_diff = as_float(row.get("absolute_percentage_difference", ""))
    same_arm = row.get("same_arm") == "yes"
    same_definition = row.get("same_ae_definition") == "yes"
    source_pair = {row.get("source_1"), row.get("source_2")}

    if "all-cause mortality is not directly comparable" in reason:
        return 5, "CT.gov mortality descriptive check"
    if (
        same_arm
        and same_definition
        and "ClinicalTrials.gov" in source_pair
        and "time window" in reason
        and denom_diff is not None
        and denom_diff <= 5
        and pct_diff is not None
        and pct_diff <= 10
    ):
        return 1, "CT.gov time-window adjudication"
    if same_arm and same_definition and denom_diff is not None and denom_diff <= 15:
        return 2, "denominator/population adjudication"
    if same_arm and not same_definition and denom_diff is not None and denom_diff <= 5:
        return 3, "AE-definition adjudication"
    if same_arm and same_definition:
        return 4, "large denominator or population difference"
    if same_arm:
        return 5, "same-arm descriptive check"
    return 6, "different-arm or low-priority descriptive check"


def main() -> None:
    with MATRIX.open(newline="", encoding="utf-8") as f:
        c_rows = [row for row in csv.DictReader(f) if row.get("comparability_grade") == "C"]

    output_rows = []
    for row in c_rows:
        rank, focus = priority(row)
        enriched = dict(row)
        enriched["adjudication_priority"] = str(rank)
        enriched["adjudication_focus"] = focus
        output_rows.append(enriched)

    output_rows.sort(key=lambda r: (
        int(r["adjudication_priority"]),
        r.get("trial_id", ""),
        r.get("ae_concept", ""),
        r.get("comparison_id", ""),
    ))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=KEEP)
        writer.writeheader()
        writer.writerows([{key: row.get(key, "") for key in KEEP} for row in output_rows])

    by_priority = Counter(row["adjudication_priority"] for row in output_rows)
    by_focus = Counter(row["adjudication_focus"] for row in output_rows)
    p1_trials = sorted({row["trial_id"] for row in output_rows if row["adjudication_priority"] == "1"})

    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(
        "\n".join([
            "# Source-comparability adjudication queue 报告",
            "",
            "日期：2026-06-18",
            "",
            "## 输出",
            "",
            "- `tables/source_comparability_adjudication_queue.csv`",
            "",
            "## 队列概况",
            "",
            f"- C 级待裁决配对：{len(output_rows)}",
            f"- 最高优先级 trial：{', '.join(p1_trials) if p1_trials else 'none'}",
            "",
            "## 优先级分布",
            "",
            *[f"- P{prio}: {count}" for prio, count in sorted(by_priority.items(), key=lambda item: int(item[0]))],
            "",
            "## 裁决焦点",
            "",
            *[f"- {focus}: {count}" for focus, count in sorted(by_focus.items())],
            "",
            "## 使用建议",
            "",
            "优先处理 P1：这类配对通常同臂、同 AE 定义，只是 CT.gov 时间窗描述触发了保守降级，最可能通过人工核对升级为 A/B 级。",
        ]) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
