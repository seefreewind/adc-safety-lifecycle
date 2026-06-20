#!/usr/bin/env python3
"""Build confirmed concordance result tables from the final audit index."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "tables"
MANUSCRIPT = ROOT / "manuscript"
PROTOCOL = ROOT / "protocol"

AUDIT = TABLES / "final_analysis_audit_index.csv"
OUT_OVERALL = TABLES / "confirmed_concordance_overall_stats.csv"
OUT_TRIAL = TABLES / "confirmed_concordance_by_trial.csv"
OUT_CONCEPT = TABLES / "confirmed_concordance_by_safety_concept.csv"
OUT_SOURCE_PAIR = TABLES / "confirmed_concordance_by_source_pair.csv"
OUT_MANUSCRIPT = MANUSCRIPT / "confirmed_concordance_results_summary.zh.md"
REPORT_OUT = PROTOCOL / "confirmed_concordance_results_report.zh.md"


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


def summarize(rows: list[dict[str, str]], label_fields: dict[str, str]) -> dict[str, str]:
    diffs = [as_float(row["absolute_percentage_difference"]) for row in rows]
    diffs = [value for value in diffs if value is not None]
    out = dict(label_fields)
    out.update({
        "comparison_count": str(len(rows)),
        "trial_count": str(len({row["trial_id"] for row in rows})),
        "safety_concept_count": str(len({row["ae_concept"] for row in rows})),
        "mean_abs_diff_pp": f"{mean(diffs):.2f}" if diffs else "",
        "median_abs_diff_pp": f"{median(diffs):.2f}" if diffs else "",
        "max_abs_diff_pp": f"{max(diffs):.2f}" if diffs else "",
        "zero_diff_count": str(sum(1 for value in diffs if value == 0)),
        "within_1pp_count": str(sum(1 for value in diffs if value <= 1)),
        "within_2pp_count": str(sum(1 for value in diffs if value <= 2)),
        "within_5pp_count": str(sum(1 for value in diffs if value <= 5)),
    })
    return out


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def main() -> None:
    rows = read_csv(AUDIT)
    primary = [row for row in rows if row["analysis_tier"] == "primary_candidate"]
    sensitivity = [row for row in rows if row["analysis_tier"] == "sensitivity_candidate"]

    overall_rows = [
        summarize(rows, {"analysis_set": "all_confirmed"}),
        summarize(primary, {"analysis_set": "primary_candidate"}),
        summarize(sensitivity, {"analysis_set": "sensitivity_candidate"}),
    ]
    write_csv(OUT_OVERALL, overall_rows)

    trial_rows = []
    for (trial_id, tier), grouped in sorted(group_by(rows, ["trial_id", "analysis_tier"]).items()):
        trial_rows.append(summarize(grouped, {"trial_id": trial_id, "analysis_tier": tier}))
    write_csv(OUT_TRIAL, trial_rows)

    concept_rows = []
    for (concept, tier), grouped in sorted(group_by(rows, ["ae_concept", "analysis_tier"]).items()):
        concept_rows.append(summarize(grouped, {"ae_concept": concept, "analysis_tier": tier}))
    write_csv(OUT_CONCEPT, concept_rows)

    source_pair_rows = []
    for (source_pair, tier), grouped in sorted(group_by(rows, ["source_pair", "analysis_tier"]).items()):
        source_pair_rows.append(summarize(grouped, {"source_pair": source_pair, "analysis_tier": tier}))
    write_csv(OUT_SOURCE_PAIR, source_pair_rows)

    by_tier = Counter(row["analysis_tier"] for row in rows)
    primary_stats = overall_rows[1]
    sensitivity_stats = overall_rows[2]
    manuscript_lines = [
        "# Confirmed concordance results summary",
        "",
        "日期：2026-06-19",
        "",
        "## 核心结果",
        "",
        f"- Confirmed analysis-ready 配对：{len(rows)}",
        f"- 主分析候选：{by_tier.get('primary_candidate', 0)}",
        f"- 敏感性分析候选：{by_tier.get('sensitivity_candidate', 0)}",
        f"- 主分析候选覆盖 trial：{primary_stats['trial_count']}；覆盖 safety concept：{primary_stats['safety_concept_count']}",
        f"- 主分析候选 mean absolute difference：{primary_stats['mean_abs_diff_pp']} percentage points；median：{primary_stats['median_abs_diff_pp']}；max：{primary_stats['max_abs_diff_pp']}",
        f"- 主分析候选中差异为 0 的配对：{primary_stats['zero_diff_count']}/{primary_stats['comparison_count']}；<=1 pp：{primary_stats['within_1pp_count']}/{primary_stats['comparison_count']}；<=2 pp：{primary_stats['within_2pp_count']}/{primary_stats['comparison_count']}",
        f"- 敏感性候选 mean absolute difference：{sensitivity_stats['mean_abs_diff_pp']} percentage points；median：{sensitivity_stats['median_abs_diff_pp']}；max：{sensitivity_stats['max_abs_diff_pp']}",
        "",
        "## Overall statistics",
        "",
        md_table(
            ["Analysis set", "N", "Trials", "Concepts", "Mean diff", "Median diff", "Max diff", "<=1 pp", "<=2 pp", "<=5 pp"],
            [[
                row["analysis_set"], row["comparison_count"], row["trial_count"], row["safety_concept_count"],
                row["mean_abs_diff_pp"], row["median_abs_diff_pp"], row["max_abs_diff_pp"],
                row["within_1pp_count"], row["within_2pp_count"], row["within_5pp_count"],
            ] for row in overall_rows],
        ),
        "",
        "注：所有统计均基于 `tables/final_analysis_audit_index.csv`，即已完成 source confirmation 和 visual audit tracking 的 confirmed analysis-ready 配对。",
    ]
    OUT_MANUSCRIPT.write_text("\n".join(manuscript_lines) + "\n", encoding="utf-8")

    REPORT_OUT.write_text(
        "\n".join([
            "# Confirmed concordance results 报告",
            "",
            "日期：2026-06-19",
            "",
            "## 输出",
            "",
            "- `tables/confirmed_concordance_overall_stats.csv`",
            "- `tables/confirmed_concordance_by_trial.csv`",
            "- `tables/confirmed_concordance_by_safety_concept.csv`",
            "- `tables/confirmed_concordance_by_source_pair.csv`",
            "- `manuscript/confirmed_concordance_results_summary.zh.md`",
            "",
            "## 结果",
            "",
            f"- confirmed pairs: {len(rows)}",
            f"- primary candidates: {by_tier.get('primary_candidate', 0)}",
            f"- sensitivity candidates: {by_tier.get('sensitivity_candidate', 0)}",
            f"- primary mean abs diff: {primary_stats['mean_abs_diff_pp']} pp",
        ]) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT_OVERALL.relative_to(ROOT)}")
    print(f"Wrote {OUT_TRIAL.relative_to(ROOT)}")
    print(f"Wrote {OUT_CONCEPT.relative_to(ROOT)}")
    print(f"Wrote {OUT_SOURCE_PAIR.relative_to(ROOT)}")
    print(f"Wrote {OUT_MANUSCRIPT.relative_to(ROOT)}")
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")


def group_by(rows: list[dict[str, str]], fields: list[str]) -> dict[tuple[str, ...], list[dict[str, str]]]:
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[field] for field in fields)].append(row)
    return grouped


if __name__ == "__main__":
    main()
