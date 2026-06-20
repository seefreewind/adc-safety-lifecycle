#!/usr/bin/env python3
"""Extract conservative core-safety numeric candidates from FDA review locators."""

from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "tables"
PROTOCOL = ROOT / "protocol"

LOCATORS = PROCESSED / "fda_review_table_locator_expansion.csv"
SUMMARY = TABLES / "fda_review_locator_expansion_summary.csv"
OUT = TABLES / "fda_core_safety_extraction_candidates_expansion.csv"

NUMERIC_RE = re.compile(r"(?P<n>\d{1,5})\s*\(\s*(?P<pct>\d{1,3}(?:\.\d+)?)\s*%?\s*\)")

CONCEPT_PATTERNS = [
    ("any_adverse_event", ["any adverse event", "any adverse events", "any teae", "patients with any"]),
    ("grade_3_or_higher_adverse_event", ["grade 3 or higher", "grade 3 or 4", "grade 3/4", "grade 3-4", "grade ≥3", "grade >=3", "grade 3", "grade 4"]),
    ("serious_adverse_event", ["serious adverse event", "serious adverse events", "serious teae", "serious teaes", "sae", "saes"]),
    ("fatal_adverse_event", ["death", "deaths", "fatal", "grade 5"]),
    ("adverse_event_leading_to_discontinuation", ["discontinuation", "discontinued", "permanent discontinuation"]),
    ("dose_reduction", ["dose reduction", "dose reductions"]),
    ("dose_interruption", ["dose interruption", "dose interruptions", "dose delay", "dose delays", "dose modification"]),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def concepts_for(text: str) -> list[str]:
    lower = text.lower()
    found = []
    for concept, patterns in CONCEPT_PATTERNS:
        if any(pattern in lower for pattern in patterns):
            found.append(concept)
    return found


def numeric_patterns(text: str) -> list[str]:
    return [f"{m.group('n')} ({m.group('pct')})" for m in NUMERIC_RE.finditer(text)]


def confidence(row: dict[str, str], concepts: list[str], nums: list[str]) -> str:
    if row["locator_priority"] == "P1" and concepts and nums and row.get("table_mentions"):
        return "high_candidate"
    if row["locator_priority"] == "P1" and concepts and nums:
        return "medium_candidate"
    if row["locator_priority"] == "P1" and concepts:
        return "locator_only"
    if row["locator_priority"] == "P2" and concepts and nums:
        return "lower_priority_numeric_candidate"
    return "exclude"


def main() -> None:
    rows = read_csv(LOCATORS)
    out_rows: list[dict[str, str]] = []
    seq = 1

    for row in rows:
        if row["locator_priority"] not in {"P1", "P2"}:
            continue
        snippet = row.get("snippet", "")
        concepts = concepts_for(snippet + " " + row.get("keyword_hits", "") + " " + row.get("table_mentions", ""))
        nums = numeric_patterns(snippet)
        conf = confidence(row, concepts, nums)
        if conf == "exclude":
            continue
        out_rows.append({
            "candidate_id": f"FDACAND{seq:05d}",
            "drug_id": row["drug_id"],
            "candidate_approval_ids": row["candidate_approval_ids"],
            "trial_ids": row["trial_ids"],
            "document_kind": row["document_kind"],
            "source_file": row["source_file"],
            "page_or_unit": row["page_or_unit"],
            "candidate_concepts": ";".join(concepts),
            "numeric_patterns": ";".join(nums[:25]),
            "numeric_pattern_count": len(nums),
            "table_mentions": row.get("table_mentions", ""),
            "locator_priority": row["locator_priority"],
            "candidate_confidence": conf,
            "review_status": "needs_manual_numeric_extraction",
            "snippet": snippet,
        })
        seq += 1

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0]))
        writer.writeheader()
        writer.writerows(out_rows)

    summary = read_csv(SUMMARY)
    confidence_counts = Counter(row["candidate_confidence"] for row in out_rows)
    p1_trials = sorted({
        trial_id
        for row in out_rows
        if row["candidate_confidence"] in {"high_candidate", "medium_candidate", "locator_only"}
        for trial_id in row["trial_ids"].split(";")
        if trial_id
    })
    high_trials = sorted({
        trial_id
        for row in out_rows
        if row["candidate_confidence"] == "high_candidate"
        for trial_id in row["trial_ids"].split(";")
        if trial_id
    })
    no_p1_review = [row for row in summary if row["fda_locator_status"] != "has_p1_review_locator"]

    lines = [
        "# FDA core-safety extraction candidate 扩展报告",
        "",
        "日期：2026-06-18",
        "",
        "## 输出",
        "",
        "- `tables/fda_core_safety_extraction_candidates_expansion.csv`",
        "",
        "## 候选抽取结果",
        "",
        f"- FDA 候选 locator 行：{len(out_rows)}",
        f"- high-confidence 候选：{confidence_counts.get('high_candidate', 0)}",
        f"- medium-confidence 候选：{confidence_counts.get('medium_candidate', 0)}",
        f"- locator-only 候选：{confidence_counts.get('locator_only', 0)}",
        f"- lower-priority numeric 候选：{confidence_counts.get('lower_priority_numeric_candidate', 0)}",
        f"- P1 FDA 候选覆盖 trial：{len(p1_trials)}",
        f"- high-confidence FDA 候选覆盖 trial：{len(high_trials)}",
        "",
        "## 仍缺 P1 FDA review locator 的 trial",
        "",
    ]
    if no_p1_review:
        for row in no_p1_review:
            lines.append(f"- `{row['trial_id']}` {row['acronym']}：{row['fda_locator_status']}，P2 locator {row['fda_p2_locator_count']}")
    else:
        lines.append("- 无")

    lines.extend([
        "",
        "## 使用边界",
        "",
        "FDA 审评文件常含跨研究或 pooled safety population。该表只作为抽取入口，不能直接作为最终安全数值表；进入 seed 前必须确认 trial、arm、分母、分析人群和表格上下文。",
    ])
    (PROTOCOL / "fda_core_safety_extraction_candidates_expansion_report.zh.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print("Wrote protocol/fda_core_safety_extraction_candidates_expansion_report.zh.md")


if __name__ == "__main__":
    main()
