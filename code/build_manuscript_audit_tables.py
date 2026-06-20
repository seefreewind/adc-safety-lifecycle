#!/usr/bin/env python3
"""Build manuscript-ready audit trail tables."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "tables"
MANUSCRIPT = ROOT / "manuscript"
PROTOCOL = ROOT / "protocol"

AUDIT = TABLES / "final_analysis_audit_index.csv"
OUT = MANUSCRIPT / "supplementary_analysis_ready_audit_trail.zh.md"
REPORT_OUT = PROTOCOL / "manuscript_audit_tables_report.zh.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


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
    table_rows = []
    for row in rows:
        table_rows.append([
            row["comparison_id"],
            row["trial_id"],
            row["ae_concept"],
            row["analysis_tier"],
            row["source_pair"],
            row["absolute_percentage_difference"],
            row["pair_confirmation_status"],
            row["source_1_visual_status"],
            row["source_2_visual_status"],
        ])

    OUT.write_text(
        "\n".join([
            "# Supplementary table. Audit trail for analysis-ready source comparisons",
            "",
            md_table(
                [
                    "Comparison ID", "Trial ID", "Safety concept", "Analysis tier",
                    "Source pair", "Abs. diff. pp", "Pair confirmation",
                    "Source 1 visual status", "Source 2 visual status",
                ],
                table_rows,
            ),
            "",
            "注：ClinicalTrials.gov source-side 不适用 PDF visual audit，因其来源为结构化 JSON。`visual_audit_pass_summary_text` 表示对应页面为摘要或正文中的可见数值证据。",
        ]) + "\n",
        encoding="utf-8",
    )

    by_tier = Counter(row["analysis_tier"] for row in rows)
    by_confirmation = Counter(row["pair_confirmation_status"] for row in rows)
    REPORT_OUT.write_text(
        "\n".join([
            "# Manuscript audit tables 报告",
            "",
            "日期：2026-06-19",
            "",
            "## 输出",
            "",
            "- `manuscript/supplementary_analysis_ready_audit_trail.zh.md`",
            "",
            "## 摘要",
            "",
            *[f"- {tier}: {count}" for tier, count in sorted(by_tier.items())],
            *[f"- {status}: {count}" for status, count in sorted(by_confirmation.items())],
        ]) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
