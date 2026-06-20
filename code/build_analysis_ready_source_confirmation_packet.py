#!/usr/bin/env python3
"""Create a source-confirmation packet for analysis-ready comparisons."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_SET = ROOT / "tables" / "analysis_ready_comparison_set.csv"
DETAIL = ROOT / "data" / "processed" / "full_cohort_source_comparability_matrix_detail.csv"
OUT = ROOT / "tables" / "analysis_ready_source_confirmation_packet.csv"
REPORT_OUT = ROOT / "protocol" / "analysis_ready_source_confirmation_packet_report.zh.md"

FIELDS = [
    "comparison_id", "trial_id", "analysis_tier", "grade_basis",
    "ae_concept", "source_1", "source_2",
    "observation_id_1", "observation_id_2", "document_id_1", "document_id_2",
    "locator_1", "locator_2", "term_1", "term_2",
    "grade_category_1", "grade_category_2", "seriousness_1", "seriousness_2",
    "causality_1", "causality_2", "denominator_1", "denominator_2",
    "percentage_1", "percentage_2", "absolute_percentage_difference",
    "analysis_population_1", "analysis_population_2",
    "confirmation_question", "confirmation_status",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def detail_id_from_comp(comp_id: str) -> str:
    return comp_id.replace("FULLCOMP", "FULLDET")


def question(row: dict[str, str]) -> str:
    if row.get("analysis_tier") == "primary_candidate":
        return "Confirm same arm, denominator, AE definition, and source values before final primary analysis."
    return "Confirm population mismatch/time-window rationale is acceptable for sensitivity analysis only."


def main() -> None:
    detail = {row["comparison_id"]: row for row in read_csv(DETAIL)}
    out_rows = []
    for row in read_csv(ANALYSIS_SET):
        drow = detail.get(detail_id_from_comp(row["comparison_id"]), {})
        merged = {field: "" for field in FIELDS}
        for field in FIELDS:
            if field in drow:
                merged[field] = drow[field]
            if field in row:
                merged[field] = row[field]
        merged["confirmation_question"] = question(row)
        merged["confirmation_status"] = "pending_source_confirmation"
        out_rows.append(merged)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(out_rows)

    by_tier = Counter(row["analysis_tier"] for row in out_rows)
    by_trial = Counter(row["trial_id"] for row in out_rows)
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(
        "\n".join([
            "# Analysis-ready source confirmation packet 报告",
            "",
            "日期：2026-06-19",
            "",
            "## 输出",
            "",
            "- `tables/analysis_ready_source_confirmation_packet.csv`",
            "",
            "## 覆盖",
            "",
            f"- 待确认配对：{len(out_rows)}",
            *[f"- {tier}: {count}" for tier, count in sorted(by_tier.items())],
            "",
            "## Trial 分布",
            "",
            *[f"- {trial}: {count}" for trial, count in sorted(by_trial.items())],
            "",
            "## 用途",
            "",
            "该表是后续人工来源页核对的工作包。每行包含两个来源的 observation_id、document_id、locator、原始术语、口径、分母和百分比。",
        ]) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
