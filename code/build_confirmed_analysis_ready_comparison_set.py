#!/usr/bin/env python3
"""Create confirmed analysis-ready comparison set using pair confirmation status."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "tables" / "analysis_ready_comparison_set.csv"
PAIR_STATUS = ROOT / "tables" / "analysis_ready_pair_confirmation_status.csv"
OUT = ROOT / "tables" / "analysis_ready_comparison_set_confirmed.csv"
REPORT_OUT = ROOT / "protocol" / "analysis_ready_comparison_set_confirmed_report.zh.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    status_by_comp = {
        row["comparison_id"]: row["pair_confirmation_status"]
        for row in read_csv(PAIR_STATUS)
    }
    rows = []
    for row in read_csv(ANALYSIS):
        copied = dict(row)
        copied["source_confirmation_status"] = status_by_comp.get(row["comparison_id"], "")
        if copied["source_confirmation_status"] == "auto_source_confirmed":
            copied["review_status"] = "auto_source_confirmed_needs_final_audit"
        rows.append(copied)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    by_tier = Counter(row["analysis_tier"] for row in rows)
    by_confirmation = Counter(row["source_confirmation_status"] for row in rows)
    REPORT_OUT.write_text(
        "\n".join([
            "# Confirmed analysis-ready comparison set 报告",
            "",
            "日期：2026-06-19",
            "",
            "## 输出",
            "",
            "- `tables/analysis_ready_comparison_set_confirmed.csv`",
            "",
            "## 候选集",
            "",
            *[f"- {tier}: {count}" for tier, count in sorted(by_tier.items())],
            "",
            "## 来源确认",
            "",
            *[f"- {status}: {count}" for status, count in sorted(by_confirmation.items())],
            "",
            "## 使用边界",
            "",
            "该文件可作为当前统计和 manuscript table 的主输入。`auto_source_confirmed_needs_final_audit` 表示数据层已由本地文本/JSON 自动确认，正式提交前仍建议抽样视觉审计来源页。",
        ]) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
