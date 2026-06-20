#!/usr/bin/env python3
"""Extract conservative core-safety numeric candidates from publication snippets."""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SNIPPETS = ROOT / "tables" / "publication_safety_snippets_expansion.csv"
OUT = ROOT / "tables" / "publication_core_safety_extraction_candidates.csv"
PROTOCOL = ROOT / "protocol"

NUMERIC_RE = re.compile(r"(?P<n>\d{1,4})\s*\(\s*(?P<pct>\d{1,3}(?:\.\d+)?)\s*\)")

CONCEPT_PATTERNS = [
    ("any_adverse_event", ["any adverse event", "any adverse events", "any ae", "any teae", "patients with any"]),
    ("grade_3_or_higher_adverse_event", ["grade 3 or higher", "grade 3 or 4", "grade 3-4", "grade ≥3", "grade >=3", "grade 3", "grade 4"]),
    ("serious_adverse_event", ["serious adverse event", "serious adverse events", "sae", "saes"]),
    ("fatal_adverse_event", ["death", "deaths", "fatal", "grade 5"]),
    ("adverse_event_leading_to_discontinuation", ["discontinuation", "discontinued", "treatment discontinuation"]),
    ("dose_reduction", ["dose reduction", "dose reductions", "reduced dose"]),
    ("dose_interruption", ["dose interruption", "dose interruptions", "dose delay", "dose delays", "delayed dose"]),
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
    values = []
    for match in NUMERIC_RE.finditer(text):
        values.append(f"{match.group('n')} ({match.group('pct')})")
    return values


def confidence(row: dict[str, str], concepts: list[str], nums: list[str]) -> str:
    part = row["publication_part"]
    tables = row.get("table_mentions", "")
    if row["locator_priority"] == "P1" and concepts and nums and ("Table" in tables or "table" in tables):
        return "high_candidate"
    if row["locator_priority"] == "P1" and concepts and nums:
        return "medium_candidate"
    if concepts:
        return "locator_only"
    return "exclude"


def main() -> None:
    rows = read_csv(SNIPPETS)
    out_rows = []
    seq = 1
    for row in rows:
        if row["locator_priority"] != "P1":
            continue
        snippet = row.get("snippet", "")
        concepts = concepts_for(snippet + " " + row.get("keyword_hits", ""))
        nums = numeric_patterns(snippet)
        conf = confidence(row, concepts, nums)
        if conf == "exclude":
            continue
        out_rows.append({
            "candidate_id": f"PUBCAND{seq:05d}",
            "trial_id": row["trial_id"],
            "drug_id": row["drug_id"],
            "document_id": row["document_id"],
            "publication_part": row["publication_part"],
            "source_file": row["source_file"],
            "page_or_unit": row["page_or_unit"],
            "candidate_concepts": ";".join(concepts),
            "numeric_patterns": ";".join(nums[:20]),
            "numeric_pattern_count": len(nums),
            "table_mentions": row.get("table_mentions", ""),
            "candidate_confidence": conf,
            "review_status": "needs_manual_numeric_extraction",
            "snippet": snippet,
        })
        seq += 1

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0]))
        writer.writeheader()
        writer.writerows(out_rows)

    high = [row for row in out_rows if row["candidate_confidence"] == "high_candidate"]
    med = [row for row in out_rows if row["candidate_confidence"] == "medium_candidate"]
    trials = sorted({row["trial_id"] for row in out_rows})
    high_trials = sorted({row["trial_id"] for row in high})
    lines = [
        "# Publication core-safety extraction candidate 报告",
        "",
        "日期：2026-06-18",
        "",
        "## 输出",
        "",
        "- `tables/publication_core_safety_extraction_candidates.csv`",
        "",
        "## 候选抽取结果",
        "",
        f"- 候选 locator 行：{len(out_rows)}",
        f"- high-confidence 表格候选：{len(high)}",
        f"- medium-confidence 文本候选：{len(med)}",
        f"- 覆盖 trial：{len(trials)}",
        f"- high-confidence 覆盖 trial：{len(high_trials)}",
        "",
        "## 使用边界",
        "",
        "该表只用于定位和人工/脚本复核，不作为最终安全数值表。原因是同一页可能同时包含多个治疗臂、多个 AE 概念或多个分母，自动正则无法可靠判断哪一个数字属于哪个核心结局。",
        "",
        "## 下一步",
        "",
        "1. 对 high-confidence 候选优先做结构化数值抽取。",
        "2. 对 medium-confidence 候选保留为 narrative cross-check。",
        "3. 抽取后的数值进入 expansion publication seed，并与 CT.gov/FDA 来源重新做 A/B/C 可比性分级。",
    ]
    (PROTOCOL / "publication_core_safety_extraction_candidates_report.zh.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print("Wrote protocol/publication_core_safety_extraction_candidates_report.zh.md")


if __name__ == "__main__":
    main()
