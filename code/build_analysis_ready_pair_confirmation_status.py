#!/usr/bin/env python3
"""Collapse side-level auto-confirmation into pair-level confirmation status."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "tables" / "analysis_ready_source_confirmation_packet.csv"
SIDE_CONFIRM = ROOT / "tables" / "analysis_ready_source_auto_confirmation.csv"
OUT = ROOT / "tables" / "analysis_ready_pair_confirmation_status.csv"
UPDATED_PACKET = ROOT / "tables" / "analysis_ready_source_confirmation_packet_confirmed.csv"
REPORT_OUT = ROOT / "protocol" / "analysis_ready_pair_confirmation_status_report.zh.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    packet = read_csv(PACKET)
    side_rows = read_csv(SIDE_CONFIRM)
    side_by_comp: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in side_rows:
        side_by_comp[row["comparison_id"]].append(row)

    status_rows = []
    status_by_comp = {}
    for comp_id, sides in sorted(side_by_comp.items()):
        auto_count = sum(1 for row in sides if row["auto_confirmation_status"] == "auto_confirmed_text_value")
        if auto_count == 2:
            status = "auto_source_confirmed"
            notes = "Both source sides had term and value matches in local PDF/JSON text."
        elif auto_count == 1:
            status = "partial_auto_confirmation"
            notes = "One source side needs manual confirmation."
        else:
            status = "manual_source_confirmation_needed"
            notes = "Both source sides need manual confirmation."
        status_by_comp[comp_id] = status
        status_rows.append({
            "comparison_id": comp_id,
            "source_side_count": str(len(sides)),
            "auto_confirmed_source_side_count": str(auto_count),
            "pair_confirmation_status": status,
            "confirmation_notes": notes,
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(status_rows[0]))
        writer.writeheader()
        writer.writerows(status_rows)

    updated_packet = []
    for row in packet:
        copied = dict(row)
        copied["confirmation_status"] = status_by_comp.get(row["comparison_id"], row.get("confirmation_status", ""))
        updated_packet.append(copied)
    with UPDATED_PACKET.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(updated_packet[0]))
        writer.writeheader()
        writer.writerows(updated_packet)

    by_status = Counter(row["pair_confirmation_status"] for row in status_rows)
    REPORT_OUT.write_text(
        "\n".join([
            "# Analysis-ready pair confirmation status 报告",
            "",
            "日期：2026-06-19",
            "",
            "## 输出",
            "",
            "- `tables/analysis_ready_pair_confirmation_status.csv`",
            "- `tables/analysis_ready_source_confirmation_packet_confirmed.csv`",
            "",
            "## Pair-level confirmation",
            "",
            *[f"- {status}: {count}" for status, count in sorted(by_status.items())],
            "",
            "## 解释",
            "",
            "Pair-level auto confirmation means both source sides had term and value matches in the local text/JSON layer. This is sufficient for data-layer confirmation, while final manuscript audit may still visually inspect selected pages.",
        ]) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Wrote {UPDATED_PACKET.relative_to(ROOT)}")
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
