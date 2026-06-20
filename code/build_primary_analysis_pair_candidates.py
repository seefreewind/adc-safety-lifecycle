#!/usr/bin/env python3
"""Export A-grade source-comparability pairs for primary-analysis review."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "data" / "processed" / "full_cohort_source_comparability_matrix.csv"
OUT = ROOT / "tables" / "primary_analysis_pair_candidates_full_cohort.csv"
REPORT_OUT = ROOT / "protocol" / "primary_analysis_pair_candidates_report.zh.md"


KEEP = [
    "comparison_id", "trial_id", "ae_concept", "source_1", "source_2",
    "source_document_id_1", "source_document_id_2", "arm_id_1", "arm_id_2",
    "number_patients_1", "number_patients_2", "denominator_1", "denominator_2",
    "percentage_1", "percentage_2", "absolute_percentage_difference",
    "reason", "review_status",
]


def main() -> None:
    with MATRIX.open(newline="", encoding="utf-8") as f:
        rows = [row for row in csv.DictReader(f) if row["comparability_grade"] == "A"]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=KEEP)
        writer.writeheader()
        writer.writerows([{key: row.get(key, "") for key in KEEP} for row in rows])

    by_trial = Counter(row["trial_id"] for row in rows)
    by_pair = Counter(" vs ".join(sorted([row["source_1"], row["source_2"]])) for row in rows)
    by_concept = Counter(row["ae_concept"] for row in rows)
    max_diff = max((float(row["absolute_percentage_difference"]) for row in rows if row["absolute_percentage_difference"]), default=0.0)

    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(
        "\n".join([
            "# 主分析候选来源配对报告",
            "",
            "日期：2026-06-18",
            "",
            "## 输出",
            "",
            "- `tables/primary_analysis_pair_candidates_full_cohort.csv`",
            "",
            "## 当前候选",
            "",
            f"- A 级候选配对：{len(rows)}",
            f"- 覆盖 trial：{len(by_trial)}（{', '.join(sorted(by_trial))}）",
            f"- 最大绝对百分比差：{max_diff:.2f} 个百分点",
            "",
            "## 来源配对",
            "",
            *[f"- {pair}: {count}" for pair, count in sorted(by_pair.items())],
            "",
            "## 安全性概念",
            "",
            *[f"- {concept}: {count}" for concept, count in sorted(by_concept.items())],
            "",
            "## 下一步",
            "",
            "这些是自动 A 级候选，不等于最终纳入。下一步应按 trial 检查同一概念是否存在 all-cause 与 treatment-related 重复口径，并优先保留预设核心口径。",
        ]) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
