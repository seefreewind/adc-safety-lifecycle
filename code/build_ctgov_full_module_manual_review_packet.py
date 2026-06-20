#!/usr/bin/env python3
"""Build a compact manual-review packet for incremental CT.gov full-module candidates."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TABLES = ROOT / "tables"
PROTOCOL = ROOT / "protocol"

TRIAGE_IN = DATA / "interim" / "ctgov_full_module_safety_candidate_triage.csv"
CSV_OUT = TABLES / "ctgov_full_module_manual_review_packet.csv"
MD_OUT = PROTOCOL / "ctgov_full_module_manual_review_packet.zh.md"


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def join_unique(rows: list[dict[str, str]], key: str, limit: int = 6) -> str:
    values = []
    for row in rows:
        value = row.get(key, "").strip()
        if value and value not in values:
            values.append(value)
    if len(values) > limit:
        return "; ".join(values[:limit]) + f"; ... (+{len(values) - limit})"
    return "; ".join(values)


def range_text(rows: list[dict[str, str]], key: str) -> str:
    values = []
    for row in rows:
        try:
            values.append(float(row.get(key, "")))
        except ValueError:
            continue
    if not values:
        return ""
    if min(values) == max(values):
        return f"{values[0]:g}"
    return f"{min(values):g}-{max(values):g}"


def recommendation(concept: str, triage_class: str) -> str:
    if triage_class == "core_candidate_needs_manual_mapping":
        if concept in {"dose_interruption", "dose_reduction", "adverse_event_leading_to_discontinuation"}:
            return "优先核对；若 arm、denominator、time frame 与 publication/FDA 可对齐，可进入后续扩展比较。"
        if concept == "any_adverse_event":
            return "谨慎核对；先确认是否为总体 AE 而非 PRO-CTCAE 症状子集或特定模块。"
        return "优先核对；确认定义后再决定是否进入扩展比较。"
    return "仅作探索性补充；暂不进入核心 AE concordance。"


def main() -> None:
    rows = [
        row for row in read_rows(TRIAGE_IN)
        if row.get("candidate_is_incremental_to_ae_module") == "yes"
        and row.get("triage_class") in {
            "core_candidate_needs_manual_mapping",
            "exploratory_candidate_needs_manual_mapping",
        }
    ]
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                row.get("trial_id") or row.get("nct_number", ""),
                row.get("mapped_safety_concept", ""),
                row.get("triage_class", ""),
            )
        ].append(row)

    packet = []
    for (trial, concept, triage_class), group in sorted(grouped.items()):
        packet.append({
            "trial_id": trial,
            "short_trial_name": group[0].get("short_trial_name", ""),
            "nct_number": group[0].get("nct_number", ""),
            "mapped_safety_concept": concept,
            "triage_class": triage_class,
            "candidate_rows": str(len(group)),
            "outcome_titles": join_unique(group, "outcome_title", 4),
            "groups_or_arms": join_unique(group, "group_title", 8),
            "unit_of_measure": join_unique(group, "unit_of_measure", 3),
            "value_range": range_text(group, "value"),
            "denominator_range": range_text(group, "denominator"),
            "calculated_percentage_range": range_text(group, "calculated_percentage"),
            "time_frames": join_unique(group, "time_frame", 3),
            "review_recommendation": recommendation(concept, triage_class),
        })

    fieldnames = list(packet[0]) if packet else [
        "trial_id",
        "mapped_safety_concept",
        "triage_class",
        "candidate_rows",
    ]
    write_csv(CSV_OUT, packet, fieldnames)

    lines = [
        "# CT.gov full-module manual review packet",
        "",
        "该文件只列出相对现有 CT.gov adverse-events module 的增量候选。它是后续人工核对清单，不代表已经进入主分析。",
        "",
        f"- 明细表：`{CSV_OUT.relative_to(ROOT)}`",
        f"- 增量 trial-concept 数：{len(packet)}",
        "",
        "| Trial | Concept | Class | Rows | Recommendation |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for row in packet:
        lines.append(
            f"| {row['short_trial_name'] or row['trial_id']} | {row['mapped_safety_concept']} | "
            f"{row['triage_class']} | {row['candidate_rows']} | {row['review_recommendation']} |"
        )
    lines.extend([
        "",
        "## 下一步判定标准",
        "",
        "1. 只优先核对 high/core_candidate 行。",
        "2. 对每个候选确认 arm 是否对应 ADC 主分析治疗组，denominator 是否为安全集，time frame 是否与 publication/FDA 的安全报告窗口一致。",
        "3. DREAMM-2 的 PRO-CTCAE symptomatic AE 候选应先判定是否为症状子集；若不是总体 AE，不应并入核心 any AE。",
        "4. 实验室异常、VOD/SOS 等探索性候选可以保留为补充材料或后续 AESI/事件级分析，不应直接改变当前主分析。",
    ])
    MD_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
