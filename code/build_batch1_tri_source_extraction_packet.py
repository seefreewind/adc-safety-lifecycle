#!/usr/bin/env python3
"""Create a focused extraction packet for batch 1 tri-source trials."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "tables"
INTERIM = ROOT / "data" / "interim"
PROTOCOL = ROOT / "protocol"

DASHBOARD = TABLES / "full_cohort_extraction_priority_dashboard.csv"
PUB = TABLES / "publication_core_safety_extraction_candidates.csv"
FDA = TABLES / "fda_core_safety_extraction_candidates_expansion.csv"
CTGOV = INTERIM / "ctgov_core_safety_expansion_seed.csv"

PUB_OUT = TABLES / "batch1_publication_extraction_packet.csv"
FDA_OUT = TABLES / "batch1_fda_extraction_packet.csv"
CTGOV_OUT = TABLES / "batch1_ctgov_extraction_packet.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def trial_id_set(value: str) -> set[str]:
    return {part.strip() for part in value.split(";") if part.strip()}


def main() -> None:
    dashboard = read_csv(DASHBOARD)
    batch1 = [row for row in dashboard if row["extraction_batch"] == "batch_1_tri_source_numeric_extraction"]
    batch1_trials = {row["trial_id"] for row in batch1}

    pub_rows = [
        row for row in read_csv(PUB)
        if row["trial_id"] in batch1_trials and row["candidate_confidence"] in {"high_candidate", "medium_candidate"}
    ]
    fda_rows = []
    for row in read_csv(FDA):
        if row["candidate_confidence"] not in {"high_candidate", "lower_priority_numeric_candidate"}:
            continue
        for trial_id in sorted(trial_id_set(row["trial_ids"]) & batch1_trials):
            fda_rows.append({
                "packet_trial_id": trial_id,
                **row,
            })
    ctgov_rows = [row for row in read_csv(CTGOV) if row["trial_id"] in batch1_trials]

    write_csv(PUB_OUT, pub_rows)
    write_csv(FDA_OUT, fda_rows)
    write_csv(CTGOV_OUT, ctgov_rows)

    lines = [
        "# Batch 1 tri-source extraction packet 报告",
        "",
        "日期：2026-06-18",
        "",
        "## 输出",
        "",
        "- `tables/batch1_publication_extraction_packet.csv`",
        "- `tables/batch1_fda_extraction_packet.csv`",
        "- `tables/batch1_ctgov_extraction_packet.csv`",
        "",
        "## Batch 1 trial",
        "",
    ]
    for row in batch1:
        lines.append(f"- `{row['trial_id']}` {row['acronym']}")
    lines.extend([
        "",
        "## 抽取包规模",
        "",
        f"- publication 候选行：{len(pub_rows)}",
        f"- FDA 候选行：{len(fda_rows)}",
        f"- CT.gov 核心安全行：{len(ctgov_rows)}",
        "",
        "## 下一步",
        "",
        "按 trial 逐项抽取核心安全结局，并记录分母、治疗臂、来源页码和可比性限制。FDA pooled safety population 不自动视为与 publication/CT.gov 同一分析集。",
    ])
    (PROTOCOL / "batch1_tri_source_extraction_packet_report.zh.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {PUB_OUT.relative_to(ROOT)}")
    print(f"Wrote {FDA_OUT.relative_to(ROOT)}")
    print(f"Wrote {CTGOV_OUT.relative_to(ROOT)}")
    print("Wrote protocol/batch1_tri_source_extraction_packet_report.zh.md")


if __name__ == "__main__":
    main()
