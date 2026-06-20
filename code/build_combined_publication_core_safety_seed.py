#!/usr/bin/env python3
"""Combine pilot and expansion publication core-safety seed rows."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
TABLES = ROOT / "tables"
PROTOCOL = ROOT / "protocol"

PILOT = INTERIM / "publication_core_safety_seed.csv"
EXPANSION = INTERIM / "publication_core_safety_expansion_seed.csv"
OUT = INTERIM / "publication_core_safety_combined_seed.csv"
SUMMARY_OUT = TABLES / "publication_core_safety_combined_seed_summary.csv"

CANONICAL_CONCEPT = {
    "adverse_event_discontinuation": "adverse_event_leading_to_discontinuation",
    "adverse_event_dose_interruption": "dose_interruption",
    "adverse_event_dose_reduction": "dose_reduction",
    "grade 3 adverse_event": "grade_3_or_higher_adverse_event",
    "grade 4 adverse_event": "grade_3_or_higher_adverse_event",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    pilot = read_csv(PILOT)
    expansion = read_csv(EXPANSION)
    rows = []
    for source_batch, source_rows in [("pilot", pilot), ("expansion", expansion)]:
        for row in source_rows:
            merged = dict(row)
            merged["publication_seed_batch"] = source_batch
            merged["canonical_safety_concept"] = CANONICAL_CONCEPT.get(
                merged.get("safety_concept", ""),
                merged.get("safety_concept", ""),
            )
            rows.append(merged)

    fieldnames = list(rows[0])
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    by_trial = Counter(row["trial_id"] for row in rows)
    by_batch = Counter(row["publication_seed_batch"] for row in rows)
    summary_rows = []
    for trial_id in sorted(by_trial):
        trial_rows = [row for row in rows if row["trial_id"] == trial_id]
        summary_rows.append({
            "trial_id": trial_id,
            "combined_publication_seed_row_count": str(len(trial_rows)),
            "pilot_seed_row_count": str(sum(1 for row in trial_rows if row["publication_seed_batch"] == "pilot")),
            "expansion_seed_row_count": str(sum(1 for row in trial_rows if row["publication_seed_batch"] == "expansion")),
            "safety_concepts": ";".join(sorted({row["safety_concept"] for row in trial_rows})),
            "canonical_safety_concepts": ";".join(sorted({row["canonical_safety_concept"] for row in trial_rows})),
            "review_status_values": ";".join(sorted({row["review_status"] for row in trial_rows})),
        })

    with SUMMARY_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0]))
        writer.writeheader()
        writer.writerows(summary_rows)

    lines = [
        "# Combined publication core-safety seed 报告",
        "",
        "日期：2026-06-18",
        "",
        "## 输出",
        "",
        "- `data/interim/publication_core_safety_combined_seed.csv`",
        "- `tables/publication_core_safety_combined_seed_summary.csv`",
        "",
        "## 覆盖",
        "",
        f"- combined seed 行数：{len(rows)}",
        f"- pilot seed 行数：{by_batch.get('pilot', 0)}",
        f"- expansion seed 行数：{by_batch.get('expansion', 0)}",
        f"- 覆盖 trial：{len(by_trial)}",
        "",
        "## 使用边界",
        "",
        "该合并文件用于后续来源可比性和全队列描述分析。所有 `needs_review` 行仍需在进入最终 manuscript 数值前人工核对。",
    ]
    (PROTOCOL / "publication_core_safety_combined_seed_report.zh.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Wrote {SUMMARY_OUT.relative_to(ROOT)}")
    print("Wrote protocol/publication_core_safety_combined_seed_report.zh.md")


if __name__ == "__main__":
    main()
