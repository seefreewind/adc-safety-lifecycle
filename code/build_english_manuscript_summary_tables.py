#!/usr/bin/env python3
"""Build English manuscript-ready tables for confirmed concordance results."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "tables"
MANUSCRIPT = ROOT / "manuscript"
PROTOCOL = ROOT / "protocol"

OVERALL = TABLES / "confirmed_concordance_overall_stats.csv"
TRIAL = TABLES / "confirmed_concordance_by_trial.csv"
CONCEPT = TABLES / "confirmed_concordance_by_safety_concept.csv"
OUT = MANUSCRIPT / "tables_confirmed_concordance.en.md"
REPORT_OUT = PROTOCOL / "english_manuscript_summary_tables_report.zh.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def main() -> None:
    overall_rows = read_csv(OVERALL)
    trial_rows = read_csv(TRIAL)
    concept_rows = read_csv(CONCEPT)

    content = [
        "# Manuscript tables: confirmed source concordance",
        "",
        "## Table A. Overall confirmed concordance statistics",
        "",
        md_table(
            [
                "Analysis set", "Comparisons", "Trials", "Safety concepts",
                "Mean abs. diff. (pp)", "Median abs. diff. (pp)", "Max abs. diff. (pp)",
                "Zero diff.", "<=1 pp", "<=2 pp", "<=5 pp",
            ],
            [[
                row["analysis_set"], row["comparison_count"], row["trial_count"],
                row["safety_concept_count"], row["mean_abs_diff_pp"],
                row["median_abs_diff_pp"], row["max_abs_diff_pp"],
                row["zero_diff_count"], row["within_1pp_count"],
                row["within_2pp_count"], row["within_5pp_count"],
            ] for row in overall_rows],
        ),
        "",
        "## Table B. Confirmed concordance by trial",
        "",
        md_table(
            [
                "Trial ID", "Analysis tier", "Comparisons", "Safety concepts",
                "Mean abs. diff. (pp)", "Median abs. diff. (pp)", "Max abs. diff. (pp)",
                "<=1 pp", "<=2 pp", "<=5 pp",
            ],
            [[
                row["trial_id"], row["analysis_tier"], row["comparison_count"],
                row["safety_concept_count"], row["mean_abs_diff_pp"],
                row["median_abs_diff_pp"], row["max_abs_diff_pp"],
                row["within_1pp_count"], row["within_2pp_count"],
                row["within_5pp_count"],
            ] for row in trial_rows],
        ),
        "",
        "## Table C. Confirmed concordance by safety concept",
        "",
        md_table(
            [
                "Safety concept", "Analysis tier", "Comparisons", "Trials",
                "Mean abs. diff. (pp)", "Median abs. diff. (pp)", "Max abs. diff. (pp)",
                "<=1 pp", "<=2 pp", "<=5 pp",
            ],
            [[
                row["ae_concept"], row["analysis_tier"], row["comparison_count"],
                row["trial_count"], row["mean_abs_diff_pp"],
                row["median_abs_diff_pp"], row["max_abs_diff_pp"],
                row["within_1pp_count"], row["within_2pp_count"],
                row["within_5pp_count"],
            ] for row in concept_rows],
        ),
        "",
        "Note: pp denotes percentage points. All rows are based on source-confirmed comparison pairs in `tables/final_analysis_audit_index.csv`.",
    ]
    OUT.write_text("\n".join(content) + "\n", encoding="utf-8")

    REPORT_OUT.write_text(
        "\n".join([
            "# English manuscript summary tables 报告",
            "",
            "日期：2026-06-19",
            "",
            "## 输出",
            "",
            "- `manuscript/tables_confirmed_concordance.en.md`",
        ]) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
