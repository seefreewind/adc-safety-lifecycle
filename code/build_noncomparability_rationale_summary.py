#!/usr/bin/env python3
"""Summarize why source-comparison pairs were not analysis-ready."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "tables" / "source_comparability_adjudication_queue.csv"
P3P4 = ROOT / "tables" / "p3_p4_source_comparability_adjudication_recommendations.csv"
TABLES = ROOT / "tables"
PROTOCOL = ROOT / "protocol"
MANUSCRIPT = ROOT / "manuscript"

OUT = TABLES / "noncomparability_rationale_summary.csv"
SUPP_MD = MANUSCRIPT / "supplementary_noncomparability_rationale.zh.md"
REPORT_OUT = PROTOCOL / "noncomparability_rationale_summary_report.zh.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def classify(row: dict[str, str]) -> str:
    focus = row.get("adjudication_focus", "")
    reason = row.get("reason", "").lower()
    if "different-arm" in focus:
        return "different_arm_or_dose"
    if "mortality" in focus or "all-cause mortality" in reason:
        return "ctgov_mortality_not_fatal_ae"
    if "AE-definition" in focus or "definition differs" in reason:
        return "ae_definition_or_causality_mismatch"
    if "denominator" in focus or "population" in reason or "denominator differs" in reason:
        return "denominator_or_population_mismatch"
    if "time-window" in focus or "time window" in reason:
        return "ctgov_time_window_difference"
    return "other_manual_review_needed"


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def main() -> None:
    queue = read_csv(QUEUE)
    p3p4 = {row["comparison_id"]: row for row in read_csv(P3P4)} if P3P4.exists() else {}

    rows = []
    by_category: Counter[str] = Counter()
    by_trial_category: dict[tuple[str, str], int] = defaultdict(int)

    for row in queue:
        comp_id = row["comparison_id"]
        rec = p3p4.get(comp_id, {})
        category = classify(row)
        recommended_use = rec.get("recommended_analysis_use", "")
        recommended_grade = rec.get("recommended_grade", "")
        if recommended_use == "sensitivity_analysis_candidate":
            continue
        by_category[category] += 1
        by_trial_category[(row["trial_id"], category)] += 1

    for (trial_id, category), count in sorted(by_trial_category.items()):
        rows.append({
            "trial_id": trial_id,
            "noncomparability_category": category,
            "pair_count": str(count),
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["trial_id", "noncomparability_category", "pair_count"])
        writer.writeheader()
        writer.writerows(rows)

    category_rows = [[category, str(count)] for category, count in sorted(by_category.items())]
    trial_rows = [[row["trial_id"], row["noncomparability_category"], row["pair_count"]] for row in rows]
    SUPP_MD.write_text(
        "\n".join([
            "# Supplementary table. Reasons for non-comparability among source pairs",
            "",
            "## Overall categories",
            "",
            md_table(["Category", "Pair count"], category_rows),
            "",
            "## Trial-level categories",
            "",
            md_table(["Trial ID", "Category", "Pair count"], trial_rows),
            "",
            "注：该表统计未进入 analysis-ready comparison set 的 C 级配对。部分配对因不同治疗臂或剂量组而自动归入低优先级描述性类别。",
        ]) + "\n",
        encoding="utf-8",
    )

    REPORT_OUT.write_text(
        "\n".join([
            "# Noncomparability rationale summary 报告",
            "",
            "日期：2026-06-19",
            "",
            "## 输出",
            "",
            "- `tables/noncomparability_rationale_summary.csv`",
            "- `manuscript/supplementary_noncomparability_rationale.zh.md`",
            "",
            "## 主要原因",
            "",
            *[f"- {category}: {count}" for category, count in sorted(by_category.items())],
        ]) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Wrote {SUPP_MD.relative_to(ROOT)}")
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
