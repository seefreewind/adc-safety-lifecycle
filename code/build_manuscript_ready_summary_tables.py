#!/usr/bin/env python3
"""Build manuscript-ready summary tables from current extraction outputs."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "tables"
MANUSCRIPT = ROOT / "manuscript"
PROTOCOL = ROOT / "protocol"

READINESS = TABLES / "full_cohort_analysis_readiness_summary.csv"
ANALYSIS = TABLES / "analysis_ready_comparison_set_confirmed.csv"
STATS = TABLES / "analysis_ready_comparison_summary_stats.csv"

OUT1 = MANUSCRIPT / "table1_source_coverage_and_readiness.zh.md"
OUT2 = MANUSCRIPT / "table2_analysis_ready_comparisons.zh.md"
REPORT_OUT = PROTOCOL / "manuscript_ready_summary_tables_report.zh.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def build_table1() -> None:
    rows = read_csv(READINESS)
    out_rows = []
    for row in rows:
        out_rows.append([
            row["trial_id"],
            row["short_trial_name"],
            row["publication_seed_rows"],
            row["fda_seed_rows"],
            row["ctgov_seed_rows"],
            row["structured_source_count"],
            row["primary_candidate_pairs"],
            row["sensitivity_candidate_pairs"],
            row["readiness_tier"],
        ])
    content = "\n".join([
        "# Table 1. Source coverage and analysis readiness across pivotal ADC trials",
        "",
        md_table(
            [
                "Trial ID", "Trial", "Publication rows", "FDA rows", "CT.gov rows",
                "Structured sources", "Primary pairs", "Sensitivity pairs", "Readiness tier",
            ],
            out_rows,
        ),
        "",
        "注：Publication/FDA/CT.gov rows 表示当前结构化 seed 行数；Primary/Sensitivity pairs 表示已进入 analysis-ready comparison set 的来源配对数。所有配对仍需最终来源页确认。",
    ])
    OUT1.write_text(content + "\n", encoding="utf-8")


def build_table2() -> None:
    rows = read_csv(ANALYSIS)
    out_rows = []
    for row in rows:
        out_rows.append([
            row["trial_id"],
            row["ae_concept"],
            f"{row['source_1']} vs {row['source_2']}",
            row["percentage_1"],
            row["percentage_2"],
            row["absolute_percentage_difference"],
            row["analysis_tier"],
            row["grade_basis"],
        ])
    content = "\n".join([
        "# Table 2. Analysis-ready source-comparison candidates",
        "",
        md_table(
            [
                "Trial ID", "Safety concept", "Source pair", "Source 1 %", "Source 2 %",
                "Abs. diff. pp", "Analysis tier", "Basis",
            ],
            out_rows,
        ),
        "",
        "注：Abs. diff. pp 为两个来源百分比的绝对差，单位为百分点。Primary candidate 可进入主分析候选；Sensitivity candidate 仅用于敏感性分析候选。",
    ])
    OUT2.write_text(content + "\n", encoding="utf-8")


def main() -> None:
    MANUSCRIPT.mkdir(parents=True, exist_ok=True)
    build_table1()
    build_table2()

    readiness = read_csv(READINESS)
    analysis = read_csv(ANALYSIS)
    stats = read_csv(STATS)
    tier_counts = Counter(row["readiness_tier"] for row in readiness)
    analysis_counts = Counter(row["analysis_tier"] for row in analysis)
    primary_stats = next((row for row in stats if row["analysis_tier"] == "primary_candidate"), {})
    sensitivity_stats = next((row for row in stats if row["analysis_tier"] == "sensitivity_candidate"), {})

    REPORT_OUT.write_text(
        "\n".join([
            "# Manuscript-ready summary tables 报告",
            "",
            "日期：2026-06-19",
            "",
            "## 输出",
            "",
            "- `manuscript/table1_source_coverage_and_readiness.zh.md`",
            "- `manuscript/table2_analysis_ready_comparisons.zh.md`",
            "",
            "## 摘要",
            "",
            *[f"- {tier}: {count} trial" for tier, count in sorted(tier_counts.items())],
            *[f"- {tier}: {count} comparison pairs" for tier, count in sorted(analysis_counts.items())],
            f"- Primary mean abs diff: {primary_stats.get('mean_abs_percentage_difference', 'NA')} pp",
            f"- Sensitivity mean abs diff: {sensitivity_stats.get('mean_abs_percentage_difference', 'NA')} pp",
        ]) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT1.relative_to(ROOT)}")
    print(f"Wrote {OUT2.relative_to(ROOT)}")
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
