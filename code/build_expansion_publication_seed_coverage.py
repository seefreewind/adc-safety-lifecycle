#!/usr/bin/env python3
"""Summarize publication expansion seed coverage and remaining extraction gaps."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
INTERIM = ROOT / "data" / "interim"
TABLES = ROOT / "tables"
PROTOCOL = ROOT / "protocol"

TRIALS = PROCESSED / "trial_master_expansion_candidates.csv"
PUB_SEED = INTERIM / "publication_core_safety_expansion_seed.csv"
PILOT_PUB_SEED = INTERIM / "publication_core_safety_seed.csv"
PUB_CANDIDATES = TABLES / "publication_core_safety_extraction_candidates.csv"
OUT = TABLES / "expansion_publication_seed_coverage.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def status_for(seed_count: int, high_count: int, medium_count: int, locator_count: int) -> tuple[str, str]:
    if seed_count > 0:
        return "seed_started", "已有结构化 publication seed；继续人工复核并补齐缺失核心概念"
    if high_count > 0:
        return "high_candidate_pending_seed", "已有 high-confidence 表格候选，下一步可结构化抽取"
    if medium_count > 0:
        return "medium_candidate_manual_review", "需人工核对文本/表格上下文后决定是否抽取"
    if locator_count > 0:
        return "locator_only_manual_review", "已有 P1 locator，但自动候选不足；需人工翻页核对"
    return "needs_source_recheck", "需重新检查 publication 文件或页级 locator"


def main() -> None:
    trials = read_csv(TRIALS)
    seed_rows = read_csv(PUB_SEED)
    pilot_seed_rows = read_csv(PILOT_PUB_SEED) if PILOT_PUB_SEED.exists() else []
    candidate_rows = read_csv(PUB_CANDIDATES)

    seed_counts = Counter(row["trial_id"] for row in seed_rows)
    pilot_seed_counts = Counter(row["trial_id"] for row in pilot_seed_rows)
    concept_counts: dict[str, Counter] = defaultdict(Counter)
    for row in seed_rows:
        concept_counts[row["trial_id"]][row["safety_concept"]] += 1
    for row in pilot_seed_rows:
        concept_counts[row["trial_id"]][row["safety_concept"]] += 1

    candidate_counts: dict[str, Counter] = defaultdict(Counter)
    for row in candidate_rows:
        candidate_counts[row["trial_id"]][row["candidate_confidence"]] += 1

    out_rows = []
    for trial in trials:
        tid = trial["trial_id"]
        counts = candidate_counts.get(tid, Counter())
        combined_seed_count = seed_counts.get(tid, 0) + pilot_seed_counts.get(tid, 0)
        status, action = status_for(
            combined_seed_count,
            counts.get("high_candidate", 0),
            counts.get("medium_candidate", 0),
            counts.get("locator_only", 0),
        )
        if pilot_seed_counts.get(tid, 0) and not seed_counts.get(tid, 0):
            status = "pilot_seed_available"
            action = "已有 pilot publication seed；扩展阶段仅需确认是否要补齐额外 publication 数值"
        out_rows.append({
            "trial_id": tid,
            "drug_id": trial["drug_id"],
            "approval_id": trial["approval_id"],
            "acronym": trial["acronym"],
            "publication_seed_status": status,
            "publication_seed_row_count": str(seed_counts.get(tid, 0)),
            "pilot_publication_seed_row_count": str(pilot_seed_counts.get(tid, 0)),
            "combined_publication_seed_row_count": str(combined_seed_count),
            "seed_safety_concepts": ";".join(sorted(concept_counts.get(tid, Counter()))),
            "high_candidate_count": str(counts.get("high_candidate", 0)),
            "medium_candidate_count": str(counts.get("medium_candidate", 0)),
            "locator_only_count": str(counts.get("locator_only", 0)),
            "recommended_next_action": action,
        })

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0]))
        writer.writeheader()
        writer.writerows(out_rows)

    status_counts = Counter(row["publication_seed_status"] for row in out_rows)
    lines = [
        "# Expansion publication seed coverage 报告",
        "",
        "日期：2026-06-18",
        "",
        "## 输出",
        "",
        "- `tables/expansion_publication_seed_coverage.csv`",
        "",
        "## 覆盖概览",
        "",
        f"- expansion publication seed 行数：{len(seed_rows)}",
        f"- pilot publication seed 行数：{len(pilot_seed_rows)}",
        f"- 已有任一 publication seed 的 trial：{sum(1 for row in out_rows if int(row['combined_publication_seed_row_count']) > 0)} / {len(out_rows)}",
    ]
    for status, count in sorted(status_counts.items()):
        lines.append(f"- `{status}`：{count}")
    lines.extend([
        "",
        "## 尚未开始 seed 的 trial",
        "",
    ])
    pending = [row for row in out_rows if row["publication_seed_status"] not in {"seed_started", "pilot_seed_available"}]
    if pending:
        for row in pending:
            lines.append(f"- `{row['trial_id']}` {row['acronym']}：{row['publication_seed_status']}；{row['recommended_next_action']}")
    else:
        lines.append("- 无")

    (PROTOCOL / "expansion_publication_seed_coverage_report.zh.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUT.relative_to(ROOT)}")
    print("Wrote protocol/expansion_publication_seed_coverage_report.zh.md")


if __name__ == "__main__":
    main()
