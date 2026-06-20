#!/usr/bin/env python3
"""Summarize percentage differences in the analysis-ready comparison set."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from statistics import mean, median


ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / "tables" / "analysis_ready_comparison_set.csv"
OUT = ROOT / "tables" / "analysis_ready_comparison_summary_stats.csv"
REPORT_OUT = ROOT / "protocol" / "analysis_ready_comparison_summary_stats.zh.md"


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


def summarize(rows: list[dict[str, str]], label: str) -> dict[str, str]:
    diffs = [as_float(row["absolute_percentage_difference"]) for row in rows]
    diffs = [value for value in diffs if value is not None]
    return {
        "analysis_tier": label,
        "comparison_count": str(len(rows)),
        "trial_count": str(len({row["trial_id"] for row in rows})),
        "mean_abs_percentage_difference": f"{mean(diffs):.2f}" if diffs else "",
        "median_abs_percentage_difference": f"{median(diffs):.2f}" if diffs else "",
        "max_abs_percentage_difference": f"{max(diffs):.2f}" if diffs else "",
        "source_pairs": ";".join(sorted({" vs ".join(sorted([row["source_1"], row["source_2"]])) for row in rows})),
        "safety_concepts": ";".join(sorted({row["ae_concept"] for row in rows})),
    }


def main() -> None:
    rows = read_csv(IN)
    summary = [summarize(rows, "all_candidates")]
    for tier in sorted({row["analysis_tier"] for row in rows}):
        summary.append(summarize([row for row in rows if row["analysis_tier"] == tier], tier))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)

    by_tier = Counter(row["analysis_tier"] for row in rows)
    primary = [row for row in rows if row["analysis_tier"] == "primary_candidate"]
    sensitivity = [row for row in rows if row["analysis_tier"] == "sensitivity_candidate"]
    primary_diffs = [as_float(row["absolute_percentage_difference"]) for row in primary]
    primary_diffs = [value for value in primary_diffs if value is not None]
    sens_diffs = [as_float(row["absolute_percentage_difference"]) for row in sensitivity]
    sens_diffs = [value for value in sens_diffs if value is not None]

    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(
        "\n".join([
            "# Analysis-ready comparison summary statistics",
            "",
            "日期：2026-06-18",
            "",
            "## 输出",
            "",
            "- `tables/analysis_ready_comparison_summary_stats.csv`",
            "",
            "## 主要结果",
            "",
            f"- 候选配对总数：{len(rows)}",
            *[f"- {tier}: {count}" for tier, count in sorted(by_tier.items())],
            f"- 主分析候选平均绝对百分比差：{mean(primary_diffs):.2f} 个百分点" if primary_diffs else "- 主分析候选平均绝对百分比差：NA",
            f"- 主分析候选最大绝对百分比差：{max(primary_diffs):.2f} 个百分点" if primary_diffs else "- 主分析候选最大绝对百分比差：NA",
            f"- 敏感性候选平均绝对百分比差：{mean(sens_diffs):.2f} 个百分点" if sens_diffs else "- 敏感性候选平均绝对百分比差：NA",
            f"- 敏感性候选最大绝对百分比差：{max(sens_diffs):.2f} 个百分点" if sens_diffs else "- 敏感性候选最大绝对百分比差：NA",
            "",
            "## 解释",
            "",
            "这些统计只描述当前候选配对之间的百分比差异，不能替代最终人工核对。结果显示当前主分析候选的来源间差异总体很小。",
        ]) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
