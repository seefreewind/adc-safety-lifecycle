#!/usr/bin/env python3
"""Build an integrated extraction priority dashboard for the full cohort."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "tables"
PROTOCOL = ROOT / "protocol"
INTERIM = ROOT / "data" / "interim"

READINESS = TABLES / "full_cohort_extraction_readiness.csv"
PUB_CANDIDATES = TABLES / "publication_core_safety_extraction_candidates.csv"
FDA_CANDIDATES = TABLES / "fda_core_safety_extraction_candidates_expansion.csv"
CTGOV_SEED = INTERIM / "ctgov_core_safety_expansion_seed.csv"
OUT = TABLES / "full_cohort_extraction_priority_dashboard.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def trial_counts_from_pub(rows: list[dict[str, str]]) -> dict[str, Counter]:
    counts: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        counts[row["trial_id"]][row["candidate_confidence"]] += 1
    return counts


def trial_counts_from_fda(rows: list[dict[str, str]]) -> dict[str, Counter]:
    counts: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        for trial_id in row["trial_ids"].split(";"):
            if trial_id:
                counts[trial_id][row["candidate_confidence"]] += 1
    return counts


def trial_counts_from_ctgov(rows: list[dict[str, str]]) -> dict[str, Counter]:
    counts: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        counts[row["trial_id"]][row.get("safety_concept", "unknown")] += 1
    return counts


def next_batch(row: dict[str, str], pub: Counter, fda: Counter, ctgov: Counter) -> tuple[str, str]:
    has_pub_high = pub.get("high_candidate", 0) > 0
    has_fda_high = fda.get("high_candidate", 0) > 0
    has_ctgov = sum(ctgov.values()) > 0

    if has_pub_high and has_fda_high and has_ctgov:
        return (
            "batch_1_tri_source_numeric_extraction",
            "先抽 publication high-candidate 表格、FDA high-candidate 审评页和 CT.gov group-level 核心安全行",
        )
    if has_pub_high and has_ctgov:
        return (
            "batch_2_publication_ctgov_numeric_extraction",
            "先抽 publication high-candidate 表格并与 CT.gov 交叉核对；FDA 审评页后续补齐",
        )
    if has_pub_high and has_fda_high:
        return (
            "batch_3_publication_fda_numeric_extraction",
            "CT.gov AE module 不可用；先做 publication-FDA 双来源抽取",
        )
    if pub.get("medium_candidate", 0) or pub.get("locator_only", 0):
        return (
            "batch_4_publication_manual_page_review",
            "先核对 publication 安全页或相邻页，确认是否存在可结构化抽取的核心安全表",
        )
    return (
        "batch_5_source_recheck",
        "重新检查来源文件和页码定位",
    )


def main() -> None:
    readiness = read_csv(READINESS)
    pub_counts = trial_counts_from_pub(read_csv(PUB_CANDIDATES))
    fda_counts = trial_counts_from_fda(read_csv(FDA_CANDIDATES))
    ctgov_counts = trial_counts_from_ctgov(read_csv(CTGOV_SEED))

    out_rows = []
    for row in readiness:
        trial_id = row["trial_id"]
        pub = pub_counts.get(trial_id, Counter())
        fda = fda_counts.get(trial_id, Counter())
        ctgov = ctgov_counts.get(trial_id, Counter())
        batch, action = next_batch(row, pub, fda, ctgov)
        out_rows.append({
            "trial_id": trial_id,
            "drug_id": row["drug_id"],
            "approval_id": row["approval_id"],
            "acronym": row["acronym"],
            "nct_number": row["nct_number"],
            "extraction_readiness": row["extraction_readiness"],
            "extraction_batch": batch,
            "publication_high_candidate_count": str(pub.get("high_candidate", 0)),
            "publication_medium_candidate_count": str(pub.get("medium_candidate", 0)),
            "publication_locator_only_count": str(pub.get("locator_only", 0)),
            "fda_high_candidate_count": str(fda.get("high_candidate", 0)),
            "fda_medium_candidate_count": str(fda.get("medium_candidate", 0)),
            "fda_locator_only_count": str(fda.get("locator_only", 0)),
            "fda_lower_priority_numeric_candidate_count": str(fda.get("lower_priority_numeric_candidate", 0)),
            "ctgov_core_safety_row_count": str(sum(ctgov.values())),
            "recommended_next_action": action,
        })

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0]))
        writer.writeheader()
        writer.writerows(out_rows)

    batch_counts = Counter(row["extraction_batch"] for row in out_rows)
    lines = [
        "# Full-cohort extraction priority dashboard 报告",
        "",
        "日期：2026-06-18",
        "",
        "## 输出",
        "",
        "- `tables/full_cohort_extraction_priority_dashboard.csv`",
        "",
        "## 批次分布",
        "",
    ]
    for batch, count in sorted(batch_counts.items()):
        lines.append(f"- `{batch}`：{count}")

    lines.extend([
        "",
        "## Batch 1 优先抽取 trial",
        "",
    ])
    batch1 = [row for row in out_rows if row["extraction_batch"] == "batch_1_tri_source_numeric_extraction"]
    if batch1:
        for row in batch1:
            lines.append(
                f"- `{row['trial_id']}` {row['acronym']}："
                f"publication high {row['publication_high_candidate_count']}，"
                f"FDA high {row['fda_high_candidate_count']}，"
                f"CT.gov rows {row['ctgov_core_safety_row_count']}"
            )
    else:
        lines.append("- 无")

    lines.extend([
        "",
        "## 解释",
        "",
        "该 dashboard 用于安排抽取顺序，不替代最终 evidence matrix。Batch 1 可优先形成三来源可比性判断；Batch 2/3 可先做双来源；Batch 4 需要先核对 publication 安全页。",
    ])
    (PROTOCOL / "full_cohort_extraction_priority_dashboard_report.zh.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print("Wrote protocol/full_cohort_extraction_priority_dashboard_report.zh.md")


if __name__ == "__main__":
    main()
