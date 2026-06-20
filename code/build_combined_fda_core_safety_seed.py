#!/usr/bin/env python3
"""Combine pilot and expansion FDA core-safety seed rows."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
TABLES = ROOT / "tables"
PROTOCOL = ROOT / "protocol"

PILOT = INTERIM / "fda_core_safety_seed.csv"
EXPANSION = INTERIM / "fda_core_safety_expansion_seed.csv"
OUT = INTERIM / "fda_core_safety_combined_seed.csv"
SUMMARY_OUT = TABLES / "fda_core_safety_combined_seed_summary.csv"
REPORT_OUT = PROTOCOL / "fda_core_safety_combined_seed_report.zh.md"

CANONICAL_CONCEPT = {
    "adverse_event_discontinuation": "adverse_event_leading_to_discontinuation",
    "adverse_event_dose_interruption": "dose_interruption",
    "adverse_event_dose_reduction": "dose_reduction",
    "grade 3 adverse_event": "grade_3_or_higher_adverse_event",
    "grade 4 adverse_event": "grade_4_or_higher_adverse_event",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    rows: list[dict[str, str]] = []
    for batch, path in [("pilot", PILOT), ("expansion", EXPANSION)]:
        for source_row in read_csv(path):
            row = dict(source_row)
            row["fda_seed_batch"] = batch
            row["canonical_safety_concept"] = CANONICAL_CONCEPT.get(
                row.get("safety_concept", ""),
                row.get("safety_concept", ""),
            )
            rows.append(row)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    by_trial = Counter(row["trial_id"] for row in rows)
    by_batch = Counter(row["fda_seed_batch"] for row in rows)
    summary_rows = []
    for trial_id in sorted(by_trial):
        trial_rows = [row for row in rows if row["trial_id"] == trial_id]
        summary_rows.append({
            "trial_id": trial_id,
            "combined_fda_seed_row_count": str(len(trial_rows)),
            "pilot_seed_row_count": str(sum(1 for row in trial_rows if row["fda_seed_batch"] == "pilot")),
            "expansion_seed_row_count": str(sum(1 for row in trial_rows if row["fda_seed_batch"] == "expansion")),
            "document_ids": ";".join(sorted({row["document_id"] for row in trial_rows})),
            "safety_concepts": ";".join(sorted({row["safety_concept"] for row in trial_rows})),
            "canonical_safety_concepts": ";".join(sorted({row["canonical_safety_concept"] for row in trial_rows})),
            "review_status_values": ";".join(sorted({row["review_status"] for row in trial_rows})),
        })

    SUMMARY_OUT.parent.mkdir(parents=True, exist_ok=True)
    with SUMMARY_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0]))
        writer.writeheader()
        writer.writerows(summary_rows)

    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(
        "\n".join([
            "# Combined FDA core-safety seed 报告",
            "",
            "日期：2026-06-18",
            "",
            "## 输出",
            "",
            "- `data/interim/fda_core_safety_combined_seed.csv`",
            "- `tables/fda_core_safety_combined_seed_summary.csv`",
            "",
            "## 覆盖",
            "",
            f"- combined FDA seed 行数：{len(rows)}",
            f"- pilot seed 行数：{by_batch.get('pilot', 0)}",
            f"- expansion seed 行数：{by_batch.get('expansion', 0)}",
            f"- 覆盖 trial：{len(by_trial)}",
            "",
            "## 使用边界",
            "",
            "该合并文件用于 FDA 来源的结构化安全性初稿和后续三源比较。所有 `needs_review` 或 `needs_manual_adjudication` 行仍需人工核对后才能进入最终 manuscript 数值。",
        ]) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Wrote {SUMMARY_OUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
