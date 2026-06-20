#!/usr/bin/env python3
"""Summarize CT.gov expansion availability in tables and a Chinese report."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "tables"
INTERIM = ROOT / "data" / "interim"
PROTOCOL = ROOT / "protocol"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    availability = read_csv(TABLES / "ctgov_expansion_availability.csv")
    fetch = read_csv(INTERIM / "ctgov_expansion_fetch_manifest.csv")
    core = read_csv(INTERIM / "ctgov_core_safety_expansion_seed.csv")

    downloaded = sum(1 for row in fetch if row["fetch_status"] == "downloaded")
    already = sum(1 for row in fetch if row["fetch_status"] == "already_present")
    failed = [row for row in fetch if row["fetch_status"] == "failed"]
    has_ae = [row for row in availability if row["ctgov_ae_status"] == "has_ae_module"]
    no_ae = [row for row in availability if row["ctgov_ae_status"] != "has_ae_module"]
    with_denominator = [row for row in core if row.get("denominator")]
    fatal_rows = [row for row in core if row.get("safety_concept") == "fatal_adverse_event"]
    serious_rows = [row for row in core if row.get("safety_concept") == "serious_adverse_event"]

    status_summary_path = TABLES / "ctgov_expansion_status_summary.csv"
    with status_summary_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerows([
            ["candidate_trials", len(availability)],
            ["already_present_json", already],
            ["newly_downloaded_json", downloaded],
            ["failed_downloads", len(failed)],
            ["trials_with_ae_module", len(has_ae)],
            ["trials_without_ae_module", len(no_ae)],
            ["ctgov_core_summary_rows", len(core)],
            ["core_rows_with_denominator", len(with_denominator)],
            ["fatal_group_summary_rows", len(fatal_rows)],
            ["serious_group_summary_rows", len(serious_rows)],
        ])

    lines = [
        "# ClinicalTrials.gov 全队列扩展阶段报告",
        "",
        "日期：2026-06-18",
        "",
        "## 本轮输出",
        "",
        "- `data/interim/ctgov_expansion_fetch_manifest.csv`",
        "- `data/interim/ctgov_source_document_expansion.csv`",
        "- `data/interim/ctgov_arm_dictionary_expansion.csv`",
        "- `data/interim/ctgov_core_safety_expansion_seed.csv`",
        "- `tables/ctgov_expansion_availability.csv`",
        "- `tables/ctgov_expansion_status_summary.csv`",
        "",
        "## 下载与解析结果",
        "",
        f"- 候选 trial 数：{len(availability)}",
        f"- 已存在 CT.gov JSON：{already}",
        f"- 本轮新增下载 JSON：{downloaded}",
        f"- 下载失败：{len(failed)}",
        f"- 有 adverse-events module 的 trial：{len(has_ae)}",
        f"- 暂无 adverse-events module 的 trial：{len(no_ae)}",
        f"- 生成 CT.gov group-level 核心安全汇总行：{len(core)}",
        f"- 其中有分母的核心安全汇总行：{len(with_denominator)}",
        "",
        "## 暂无 CT.gov AE 模块的 trial",
        "",
    ]
    if no_ae:
        for row in no_ae:
            lines.append(f"- `{row['trial_id']}` / `{row['nct_number']}` / {row['acronym']}")
    else:
        lines.append("- 无")
    lines.extend([
        "",
        "## 解释边界",
        "",
        "CT.gov adverse-events module 中的 all-cause mortality、serious adverse events 和 non-serious adverse events 目前只作为来源级别证据，不直接等同于论文或 FDA review 中的 fatal AE、treatment-related death 或 grade 3+ AE。",
        "",
        "尤其是 mortality 行通常有更长随访窗口，必须继续沿用试点阶段规则：没有手工确认时间窗、分母、治疗臂和定义一致前，不进入 numeric-discordance 主分析。",
        "",
        "## 下一步",
        "",
        "1. 先用该表筛选 19 个有 CT.gov AE 模块的 trial，生成扩展 source-coverage 初表。",
        "2. 对 4 个暂无 AE 模块的 trial，后续主要依赖 publication、FDA review 和 label。",
        "3. 继续下载/定位 FDA review、label 和 approval letter，并扩展 publication locator。",
    ])
    (PROTOCOL / "ctgov_expansion_report.zh.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {status_summary_path.relative_to(ROOT)}")
    print("Wrote protocol/ctgov_expansion_report.zh.md")


if __name__ == "__main__":
    main()
