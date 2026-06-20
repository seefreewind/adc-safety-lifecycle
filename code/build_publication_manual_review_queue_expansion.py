#!/usr/bin/env python3
"""Build a trial-level manual review queue for expansion publication safety extraction."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "tables"
PROTOCOL = ROOT / "protocol"

TRIALS = PROCESSED / "trial_master_expansion_candidates.csv"
AVAILABILITY = TABLES / "publication_fulltext_availability_expansion.csv"
CTGOV = TABLES / "ctgov_expansion_availability.csv"
SOURCE_STATUS = TABLES / "full_cohort_expansion_source_status.csv"
FDA_LOCATOR_SUMMARY = TABLES / "fda_review_locator_expansion_summary.csv"
LOCATORS = TABLES / "publication_table_locator_expansion_detail.csv"
CANDIDATES = TABLES / "publication_core_safety_extraction_candidates.csv"

QUEUE_OUT = TABLES / "publication_core_safety_manual_review_queue_expansion.csv"
READINESS_OUT = TABLES / "full_cohort_extraction_readiness.csv"


CONFIDENCE_RANK = {
    "high_candidate": 0,
    "medium_candidate": 1,
    "locator_only": 2,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def as_int(value: str | None) -> int:
    if value in (None, ""):
        return 0
    try:
        return int(float(value))
    except ValueError:
        return 0


def snippet_preview(text: str, limit: int = 520) -> str:
    compact = " ".join((text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def review_focus(concepts: str, confidence: str) -> str:
    concept_set = set(filter(None, concepts.split(";")))
    if "grade_3_or_higher_adverse_event" in concept_set:
        return "grade_3_or_higher_adverse_event"
    if "serious_adverse_event" in concept_set:
        return "serious_adverse_event"
    if "adverse_event_leading_to_discontinuation" in concept_set:
        return "adverse_event_leading_to_discontinuation"
    if "dose_reduction" in concept_set or "dose_interruption" in concept_set:
        return "dose_modification"
    if "fatal_adverse_event" in concept_set:
        return "fatal_adverse_event"
    if confidence == "high_candidate":
        return "structured_safety_table"
    return "general_safety_locator"


def suggested_action(row: dict[str, str]) -> str:
    confidence = row.get("candidate_confidence", "")
    concepts = row.get("candidate_concepts", "")
    if confidence == "high_candidate":
        return "优先核对该表格页，抽取核心安全结局的分子、分母、百分比和治疗臂定义"
    if confidence == "medium_candidate":
        return "核对该叙述段是否给出可直接引用的核心安全百分比"
    if concepts:
        return "作为定位入口，人工查看同页或相邻页的安全表格"
    return "人工筛查 P1 安全 locator，判断是否包含可抽取数值"


def candidate_sort_key(row: dict[str, str]) -> tuple[int, int, int, int, str]:
    confidence = row.get("candidate_confidence", "")
    has_table = 0 if row.get("table_mentions") else 1
    numeric_count = -as_int(row.get("numeric_pattern_count"))
    part_rank = 0 if "supplement" in row.get("publication_part", "").lower() else 1
    return (CONFIDENCE_RANK.get(confidence, 9), has_table, numeric_count, part_rank, row.get("page_or_unit", ""))


def locator_to_queue_row(
    seq: int,
    trial: dict[str, str],
    availability: dict[str, str],
    ctgov: dict[str, str],
    status: dict[str, str],
    fda_summary: dict[str, str],
    row: dict[str, str],
) -> dict[str, str]:
    return {
        "queue_id": f"PUBREV{seq:05d}",
        "trial_id": trial["trial_id"],
        "drug_id": trial["drug_id"],
        "acronym": trial["acronym"],
        "nct_number": trial["nct_number"],
        "publication_file_status": availability.get("publication_file_status", ""),
        "ctgov_ae_status": ctgov.get("ctgov_ae_status", ""),
        "fda_p1_present_count_for_drug": status.get("fda_p1_present_count_for_drug", ""),
        "fda_locator_status": fda_summary.get("fda_locator_status", ""),
        "fda_p1_locator_count": fda_summary.get("fda_p1_locator_count", ""),
        "review_focus": review_focus(row.get("candidate_concepts", ""), row.get("candidate_confidence", "")),
        "candidate_confidence": row.get("candidate_confidence", "locator_only"),
        "publication_part": row.get("publication_part", ""),
        "source_file": row.get("source_file", ""),
        "page_or_unit": row.get("page_or_unit", ""),
        "candidate_concepts": row.get("candidate_concepts", ""),
        "numeric_pattern_count": row.get("numeric_pattern_count", "0"),
        "numeric_patterns": row.get("numeric_patterns", ""),
        "table_mentions": row.get("table_mentions", ""),
        "suggested_action": suggested_action(row),
        "snippet_preview": snippet_preview(row.get("snippet", row.get("keyword_hits", ""))),
    }


def readiness_label(
    availability: dict[str, str],
    ctgov: dict[str, str],
    status: dict[str, str],
    fda_summary: dict[str, str],
    counts: Counter,
    locator_count: int,
) -> tuple[str, str]:
    has_main = availability.get("main_article_available") == "yes"
    has_ctgov = ctgov.get("ctgov_ae_status") == "has_ae_module"
    has_fda_file = as_int(status.get("fda_p1_present_count_for_drug")) > 0
    has_fda_review_locator = as_int(fda_summary.get("fda_p1_locator_count")) > 0
    has_high = counts.get("high_candidate", 0) > 0
    has_medium = counts.get("medium_candidate", 0) > 0
    has_locator = locator_count > 0 or counts.get("locator_only", 0) > 0

    if has_main and has_high and has_ctgov and has_fda_review_locator:
        return (
            "ready_for_tri_source_extraction",
            "可优先抽取 publication 核心数值，并与 CT.gov 和 FDA P1 来源做 A/B/C 可比性分级",
        )
    if has_main and has_high and has_ctgov and has_fda_file:
        return (
            "ready_for_publication_ctgov_extraction_fda_locator_pending",
            "可先抽取 publication 和 CT.gov；FDA 文件已在本地，但仍需从低优先级 locator 或 TOC 中确认审评安全页",
        )
    if has_main and has_high and has_fda_review_locator:
        return (
            "ready_for_publication_fda_extraction",
            "CT.gov AE module 不完整或缺失；先做 publication-FDA 双来源抽取",
        )
    if has_main and (has_medium or has_locator):
        return (
            "ready_for_manual_publication_review",
            "主文已齐，需人工核对安全页或相邻页后再结构化抽数",
        )
    return (
        "needs_source_locator_review",
        "需重新检查全文页码定位或来源文件质量",
    )


def main() -> None:
    trials = read_csv(TRIALS)
    availability = {row["trial_id"]: row for row in read_csv(AVAILABILITY)}
    ctgov = {row["trial_id"]: row for row in read_csv(CTGOV)}
    source_status = {row["trial_id"]: row for row in read_csv(SOURCE_STATUS)}
    fda_locator = {row["trial_id"]: row for row in read_csv(FDA_LOCATOR_SUMMARY)} if FDA_LOCATOR_SUMMARY.exists() else {}
    candidates = read_csv(CANDIDATES)
    locators = read_csv(LOCATORS)

    candidates_by_trial: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in candidates:
        candidates_by_trial[row["trial_id"]].append(row)

    p1_locators_by_trial: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in locators:
        if row.get("locator_priority") == "P1":
            p1_locators_by_trial[row["trial_id"]].append(row)

    queue_rows: list[dict[str, str]] = []
    readiness_rows: list[dict[str, str]] = []
    seq = 1

    for trial in trials:
        trial_id = trial["trial_id"]
        trial_avail = availability.get(trial_id, {})
        trial_ctgov = ctgov.get(trial_id, {})
        trial_status = source_status.get(trial_id, {})
        trial_fda_locator = fda_locator.get(trial_id, {})

        selected = sorted(candidates_by_trial.get(trial_id, []), key=candidate_sort_key)[:8]
        if not selected:
            selected = [
                {
                    **row,
                    "candidate_confidence": "locator_only",
                    "candidate_concepts": "",
                    "numeric_pattern_count": "0",
                    "numeric_patterns": "",
                    "snippet": row.get("keyword_hits", ""),
                }
                for row in p1_locators_by_trial.get(trial_id, [])[:5]
            ]

        for row in selected:
            queue_rows.append(locator_to_queue_row(seq, trial, trial_avail, trial_ctgov, trial_status, trial_fda_locator, row))
            seq += 1

        counts = Counter(row.get("candidate_confidence", "") for row in candidates_by_trial.get(trial_id, []))
        locator_count = len(p1_locators_by_trial.get(trial_id, []))
        label, next_action = readiness_label(trial_avail, trial_ctgov, trial_status, trial_fda_locator, counts, locator_count)
        readiness_rows.append({
            "trial_id": trial_id,
            "drug_id": trial["drug_id"],
            "approval_id": trial["approval_id"],
            "acronym": trial["acronym"],
            "nct_number": trial["nct_number"],
            "main_article_available": trial_avail.get("main_article_available", ""),
            "supporting_files_available": trial_avail.get("supplement_or_data_supplement_available", ""),
            "protocol_available": trial_avail.get("protocol_available", ""),
            "publisher_html_available": trial_avail.get("publisher_html_available", ""),
            "ctgov_ae_status": trial_ctgov.get("ctgov_ae_status", ""),
            "ctgov_core_safety_row_count": str(
                as_int(trial_ctgov.get("serious_event_term_count"))
                + as_int(trial_ctgov.get("other_event_term_count"))
                + as_int(trial_ctgov.get("event_group_count"))
            ),
            "fda_p1_present_count_for_drug": trial_status.get("fda_p1_present_count_for_drug", ""),
            "fda_locator_status": trial_fda_locator.get("fda_locator_status", ""),
            "fda_p1_locator_count": trial_fda_locator.get("fda_p1_locator_count", ""),
            "fda_p2_locator_count": trial_fda_locator.get("fda_p2_locator_count", ""),
            "publication_p1_locator_count": str(locator_count),
            "publication_high_candidate_count": str(counts.get("high_candidate", 0)),
            "publication_medium_candidate_count": str(counts.get("medium_candidate", 0)),
            "publication_locator_only_count": str(counts.get("locator_only", 0)),
            "extraction_readiness": label,
            "recommended_next_action": next_action,
        })

    with QUEUE_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(queue_rows[0]))
        writer.writeheader()
        writer.writerows(queue_rows)

    with READINESS_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(readiness_rows[0]))
        writer.writeheader()
        writer.writerows(readiness_rows)

    readiness_counts = Counter(row["extraction_readiness"] for row in readiness_rows)
    confidence_counts = Counter(row["candidate_confidence"] for row in queue_rows)
    no_ctgov = [row for row in readiness_rows if row["ctgov_ae_status"] != "has_ae_module"]
    no_high = [row for row in readiness_rows if as_int(row["publication_high_candidate_count"]) == 0]

    lines = [
        "# Publication core-safety manual review queue 报告",
        "",
        "日期：2026-06-18",
        "",
        "## 输出",
        "",
        "- `tables/publication_core_safety_manual_review_queue_expansion.csv`",
        "- `tables/full_cohort_extraction_readiness.csv`",
        "",
        "## 队列概览",
        "",
        f"- review queue 行数：{len(queue_rows)}",
        f"- 覆盖 trial：{len(readiness_rows)}",
        f"- high-candidate 队列行：{confidence_counts.get('high_candidate', 0)}",
        f"- medium-candidate 队列行：{confidence_counts.get('medium_candidate', 0)}",
        f"- locator-only 队列行：{confidence_counts.get('locator_only', 0)}",
        "",
        "## 抽取就绪度",
        "",
    ]
    for label, count in sorted(readiness_counts.items()):
        lines.append(f"- `{label}`：{count}")

    lines.extend([
        "",
        "## 需要特别注意的 trial",
        "",
        "### CT.gov AE module 缺失或不可用",
        "",
    ])
    if no_ctgov:
        for row in no_ctgov:
            lines.append(f"- `{row['trial_id']}` {row['acronym']}：{row['ctgov_ae_status']}")
    else:
        lines.append("- 无")

    lines.extend([
        "",
        "### Publication 暂无 high-confidence 表格候选",
        "",
    ])
    if no_high:
        for row in no_high:
            lines.append(
                f"- `{row['trial_id']}` {row['acronym']}："
                f"P1 locator {row['publication_p1_locator_count']}，"
                f"medium {row['publication_medium_candidate_count']}，"
                f"locator-only {row['publication_locator_only_count']}"
            )
    else:
        lines.append("- 无")

    lines.extend([
        "",
        "## 使用说明",
        "",
        "该队列是下一步结构化抽取的工作清单，不是最终结果表。每个候选值在进入 publication seed 前仍需记录治疗臂、分母、安全定义、页码/表号和 review status。",
    ])
    (PROTOCOL / "publication_core_safety_manual_review_queue_expansion_report.zh.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {QUEUE_OUT.relative_to(ROOT)}")
    print(f"Wrote {READINESS_OUT.relative_to(ROOT)}")
    print("Wrote protocol/publication_core_safety_manual_review_queue_expansion_report.zh.md")


if __name__ == "__main__":
    main()
