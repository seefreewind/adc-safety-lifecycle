#!/usr/bin/env python3
"""Build final audit index for confirmed analysis-ready comparisons."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIRMED = ROOT / "tables" / "analysis_ready_comparison_set_confirmed.csv"
PACKET = ROOT / "tables" / "analysis_ready_source_confirmation_packet_confirmed.csv"
PAIR_STATUS = ROOT / "tables" / "analysis_ready_pair_confirmation_status.csv"
VISUAL = ROOT / "tables" / "visual_source_audit_review_status.csv"
OUT = ROOT / "tables" / "final_analysis_audit_index.csv"
REPORT_OUT = ROOT / "protocol" / "final_analysis_audit_index_report.zh.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def visual_key(row: dict[str, str], side: str) -> tuple[str, str]:
    return row.get(f"document_id_{side}", ""), row.get(f"locator_{side}", "")


def main() -> None:
    confirmed = {row["comparison_id"]: row for row in read_csv(CONFIRMED)}
    packet = {row["comparison_id"]: row for row in read_csv(PACKET)}
    pair_status = {row["comparison_id"]: row for row in read_csv(PAIR_STATUS)}
    visual = {
        (row["document_id"], row["locator"]): row
        for row in read_csv(VISUAL)
    }

    rows = []
    for comp_id, comp in sorted(confirmed.items()):
        pack = packet.get(comp_id, {})
        pstat = pair_status.get(comp_id, {})
        v1 = visual.get(visual_key(pack, "1"), {})
        v2 = visual.get(visual_key(pack, "2"), {})
        rows.append({
            "comparison_id": comp_id,
            "trial_id": comp.get("trial_id", ""),
            "ae_concept": comp.get("ae_concept", ""),
            "analysis_tier": comp.get("analysis_tier", ""),
            "source_pair": f"{comp.get('source_1', '')} vs {comp.get('source_2', '')}",
            "percentage_1": comp.get("percentage_1", ""),
            "percentage_2": comp.get("percentage_2", ""),
            "absolute_percentage_difference": comp.get("absolute_percentage_difference", ""),
            "pair_confirmation_status": pstat.get("pair_confirmation_status", ""),
            "source_1_visual_status": v1.get("visual_audit_status", "not_applicable_or_not_sampled"),
            "source_2_visual_status": v2.get("visual_audit_status", "not_applicable_or_not_sampled"),
            "source_1_visual_note": v1.get("visual_audit_note", ""),
            "source_2_visual_note": v2.get("visual_audit_note", ""),
            "final_audit_status": "analysis_ready_confirmed_with_visual_audit",
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    by_tier = Counter(row["analysis_tier"] for row in rows)
    by_final = Counter(row["final_audit_status"] for row in rows)
    visual_statuses = Counter()
    for row in rows:
        visual_statuses[row["source_1_visual_status"]] += 1
        visual_statuses[row["source_2_visual_status"]] += 1

    REPORT_OUT.write_text(
        "\n".join([
            "# Final analysis audit index 报告",
            "",
            "日期：2026-06-19",
            "",
            "## 输出",
            "",
            "- `tables/final_analysis_audit_index.csv`",
            "",
            "## Analysis-ready confirmed pairs",
            "",
            *[f"- {tier}: {count}" for tier, count in sorted(by_tier.items())],
            "",
            "## Final audit status",
            "",
            *[f"- {status}: {count}" for status, count in sorted(by_final.items())],
            "",
            "## Visual source-side status",
            "",
            *[f"- {status}: {count}" for status, count in sorted(visual_statuses.items())],
        ]) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
