#!/usr/bin/env python3
"""Build a report for expansion publication-reference coverage."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "tables"
PROCESSED = ROOT / "data" / "processed"
PROTOCOL = ROOT / "protocol"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    summary = read_csv(TABLES / "publication_reference_expansion_summary.csv")
    refs = read_csv(PROCESSED / "publication_reference_inventory_expansion.csv")
    total_refs = len(refs)
    trials = len(summary)
    candidate_refs = [row for row in refs if row.get("is_primary_publication_candidate")]
    no_auto_candidate = [
        row for row in summary
        if row.get("primary_candidate_count_or_status") in ("0", "missing_json")
    ]
    result_ref_trials = [
        row for row in summary
        if row.get("result_reference_count") not in ("0", "")
    ]

    lines = [
        "# Publication locator 全队列扩展阶段报告",
        "",
        "日期：2026-06-18",
        "",
        "## 本轮输出",
        "",
        "- `data/processed/publication_reference_inventory_expansion.csv`",
        "- `tables/publication_reference_expansion_summary.csv`",
        "",
        "## CT.gov 引用抽取结果",
        "",
        f"- trial 候选：{trials}",
        f"- CT.gov references 总数：{total_refs}",
        f"- 至少有 RESULT reference 的 trial：{len(result_ref_trials)}",
        f"- 自动标记 primary/possible 候选引用：{len(candidate_refs)}",
        f"- 暂无自动 primary 候选的 trial：{len(no_auto_candidate)}",
        "",
        "## 自动候选引用",
        "",
    ]
    if candidate_refs:
        for row in candidate_refs:
            cite = row["citation"][:180].replace("\n", " ")
            lines.append(f"- `{row['trial_id']}` / {row['acronym']} / PMID {row['pmid'] or 'NA'} / DOI {row['doi'] or 'NA'}：{cite}")
    else:
        lines.append("- 无")

    lines.extend([
        "",
        "## 需要 PubMed/出版社补定位的 trial",
        "",
    ])
    for row in no_auto_candidate:
        lines.append(
            f"- `{row['trial_id']}` / `{row['nct_number']}` / {row['acronym']}："
            f"references={row['reference_count']}, RESULT={row['result_reference_count']}"
        )
    lines.extend([
        "",
        "## 解释边界",
        "",
        "CT.gov references 经常包含背景文献、派生分析、会议摘要或延迟更新的结果文献。自动候选只能作为 locator 起点，不能直接等同于主安全论文。",
        "",
        "下一步需要对暂无自动候选的 trial 进行 PubMed/出版社检索，并优先寻找 primary pivotal publication、supplementary appendix、protocol 或 safety appendix。",
    ])
    (PROTOCOL / "publication_expansion_locator_report.zh.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Wrote protocol/publication_expansion_locator_report.zh.md")


if __name__ == "__main__":
    main()
