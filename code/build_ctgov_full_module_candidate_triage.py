#!/usr/bin/env python3
"""Triage CT.gov full-module safety outcome candidates before manual mapping."""

from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TABLES = ROOT / "tables"
MANUSCRIPT = ROOT / "manuscript"
PROTOCOL = ROOT / "protocol"

IN_CANDIDATES = DATA / "interim" / "ctgov_full_module_safety_outcome_candidates.csv"
CORE_SEED = DATA / "interim" / "ctgov_core_safety_seed.csv"
EXPANSION_SEED = DATA / "interim" / "ctgov_core_safety_expansion_seed.csv"

TRIAGED_OUT = DATA / "interim" / "ctgov_full_module_safety_candidate_triage.csv"
CORE_CANDIDATE_OUT = DATA / "interim" / "ctgov_full_module_core_safety_candidates.csv"
TRIAL_SUMMARY_OUT = TABLES / "ctgov_full_module_candidate_triage_by_trial.csv"
CONCEPT_SUMMARY_OUT = TABLES / "ctgov_full_module_candidate_triage_by_concept.csv"
INCREMENTAL_OUT = TABLES / "ctgov_full_module_incremental_candidate_summary.csv"
REPORT_OUT = PROTOCOL / "ctgov_full_module_candidate_triage_report.zh.md"
MANUSCRIPT_OUT = MANUSCRIPT / "ctgov_full_module_expansion_summary.en.md"

CORE_REVIEW_CONCEPTS = {
    "any_adverse_event",
    "serious_adverse_event",
    "adverse_event_leading_to_discontinuation",
    "dose_interruption",
    "dose_reduction",
}

EXPLORATORY_CONCEPTS = {
    "grade_3_or_higher_adverse_event_or_lab_abnormality",
    "veno_occlusive_disease_or_sinusoidal_obstruction",
}

EXCLUDE_MIXED_ENDPOINT = re.compile(
    r"\b(time to treatment failure|treatment failure|progression|disease progression|"
    r"death from any cause|kaplan[- ]meier|median time)\b",
    re.IGNORECASE,
)

NON_NUMERIC_UNITS = re.compile(r"\b(months?|days?|weeks?|hazard ratio|score|scale)\b", re.IGNORECASE)


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


def combined_ctgov_seed_rows() -> list[dict[str, str]]:
    return read_rows(CORE_SEED) + read_rows(EXPANSION_SEED)


def existing_ctgov_concepts_by_trial() -> dict[str, set[str]]:
    concepts: dict[str, set[str]] = defaultdict(set)
    for row in combined_ctgov_seed_rows():
        trial = row.get("trial_id", "")
        concept = row.get("safety_concept", "")
        if trial and concept:
            concepts[trial].add(concept)
    return concepts


def triage_row(row: dict[str, str], existing: dict[str, set[str]]) -> dict[str, str]:
    concept = row.get("mapped_safety_concept", "")
    title = row.get("outcome_title", "")
    description = row.get("outcome_description", "")
    unit = row.get("unit_of_measure", "")
    text = " ".join([title, description, unit])
    trial = row.get("trial_id", "") or row.get("nct_number", "")

    if EXCLUDE_MIXED_ENDPOINT.search(text):
        review_class = "exclude_non_core_mixed_endpoint"
        priority = "exclude"
        rationale = "Mixed efficacy/safety or time-to-event endpoint, not a core aggregate safety outcome."
    elif concept in CORE_REVIEW_CONCEPTS:
        review_class = "core_candidate_needs_manual_mapping"
        priority = "high"
        rationale = "Potential core aggregate safety outcome from the CT.gov outcome module."
    elif concept in EXPLORATORY_CONCEPTS:
        review_class = "exploratory_candidate_needs_manual_mapping"
        priority = "medium"
        rationale = "Potential safety signal or laboratory-abnormality outcome; keep separate from core AE concordance."
    elif NON_NUMERIC_UNITS.search(unit):
        review_class = "exclude_non_core_or_nonpercentage"
        priority = "exclude"
        rationale = "Non-percentage/count outcome unit is not suitable for current cross-source percentage comparison."
    else:
        review_class = "low_priority_safety_related_other"
        priority = "low"
        rationale = "Safety-related text was detected, but the concept is not a prespecified core outcome."

    candidate_is_incremental = "yes"
    if concept in existing.get(trial, set()):
        candidate_is_incremental = "no_existing_ctgov_ae_module_has_same_concept"
    elif review_class.startswith("exclude"):
        candidate_is_incremental = "no_excluded_from_incremental_review"

    out = dict(row)
    out.update({
        "triage_class": review_class,
        "manual_review_priority": priority,
        "triage_rationale": rationale,
        "candidate_is_incremental_to_ae_module": candidate_is_incremental,
    })
    return out


def group_values(rows: list[dict[str, str]], key: str) -> str:
    return ";".join(sorted({row.get(key, "") for row in rows if row.get(key, "")}))


def main() -> None:
    rows = read_rows(IN_CANDIDATES)
    existing = existing_ctgov_concepts_by_trial()
    triaged = [triage_row(row, existing) for row in rows]
    fieldnames = list(triaged[0]) if triaged else [
        "candidate_id",
        "trial_id",
        "mapped_safety_concept",
        "triage_class",
        "manual_review_priority",
    ]
    write_csv(TRIAGED_OUT, triaged, fieldnames)

    core_candidates = [
        row for row in triaged
        if row.get("triage_class") == "core_candidate_needs_manual_mapping"
    ]
    write_csv(CORE_CANDIDATE_OUT, core_candidates, fieldnames)

    by_trial = defaultdict(list)
    for row in triaged:
        by_trial[row.get("trial_id") or row.get("nct_number")].append(row)
    trial_summary = []
    for trial, grouped in sorted(by_trial.items()):
        core_grouped = [row for row in grouped if row.get("triage_class") == "core_candidate_needs_manual_mapping"]
        exploratory_grouped = [
            row for row in grouped
            if row.get("triage_class") == "exploratory_candidate_needs_manual_mapping"
        ]
        incremental_core = [
            row for row in core_grouped
            if row.get("candidate_is_incremental_to_ae_module") == "yes"
        ]
        trial_summary.append({
            "trial_or_nct": trial,
            "short_trial_name": grouped[0].get("short_trial_name", ""),
            "all_candidate_rows": str(len(grouped)),
            "core_candidate_rows": str(len(core_grouped)),
            "core_candidate_concepts": group_values(core_grouped, "mapped_safety_concept"),
            "incremental_core_candidate_rows": str(len(incremental_core)),
            "incremental_core_candidate_concepts": group_values(incremental_core, "mapped_safety_concept"),
            "exploratory_candidate_rows": str(len(exploratory_grouped)),
            "exploratory_candidate_concepts": group_values(exploratory_grouped, "mapped_safety_concept"),
            "excluded_or_low_priority_rows": str(
                len(grouped) - len(core_grouped) - len(exploratory_grouped)
            ),
        })
    write_csv(TRIAL_SUMMARY_OUT, trial_summary, list(trial_summary[0]) if trial_summary else ["trial_or_nct"])

    concept_summary = []
    for concept in sorted({row.get("mapped_safety_concept", "") for row in triaged}):
        grouped = [row for row in triaged if row.get("mapped_safety_concept") == concept]
        concept_summary.append({
            "mapped_safety_concept": concept,
            "candidate_rows": str(len(grouped)),
            "trials_or_ncts": str(len({row.get("trial_id") or row.get("nct_number") for row in grouped})),
            "triage_classes": group_values(grouped, "triage_class"),
            "incremental_rows": str(sum(row.get("candidate_is_incremental_to_ae_module") == "yes" for row in grouped)),
        })
    write_csv(CONCEPT_SUMMARY_OUT, concept_summary, list(concept_summary[0]) if concept_summary else ["mapped_safety_concept"])

    incremental_summary = []
    by_trial_concept = defaultdict(list)
    for row in triaged:
        if row.get("candidate_is_incremental_to_ae_module") != "yes":
            continue
        if row.get("triage_class") not in {
            "core_candidate_needs_manual_mapping",
            "exploratory_candidate_needs_manual_mapping",
        }:
            continue
        key = (row.get("trial_id") or row.get("nct_number"), row.get("mapped_safety_concept", ""))
        by_trial_concept[key].append(row)
    for (trial, concept), grouped in sorted(by_trial_concept.items()):
        incremental_summary.append({
            "trial_or_nct": trial,
            "short_trial_name": grouped[0].get("short_trial_name", ""),
            "mapped_safety_concept": concept,
            "candidate_rows": str(len(grouped)),
            "outcome_titles": group_values(grouped, "outcome_title"),
            "triage_class": group_values(grouped, "triage_class"),
            "manual_review_priority": group_values(grouped, "manual_review_priority"),
        })
    write_csv(INCREMENTAL_OUT, incremental_summary, list(incremental_summary[0]) if incremental_summary else ["trial_or_nct"])

    class_counts = Counter(row.get("triage_class", "") for row in triaged)
    priority_counts = Counter(row.get("manual_review_priority", "") for row in triaged)
    incremental_core_pairs = {
        (row.get("trial_id") or row.get("nct_number"), row.get("mapped_safety_concept", ""))
        for row in core_candidates
        if row.get("candidate_is_incremental_to_ae_module") == "yes"
    }
    incremental_exploratory_pairs = {
        (row.get("trial_id") or row.get("nct_number"), row.get("mapped_safety_concept", ""))
        for row in triaged
        if row.get("triage_class") == "exploratory_candidate_needs_manual_mapping"
        and row.get("candidate_is_incremental_to_ae_module") == "yes"
    }

    report = [
        "# CT.gov full-module candidate triage 报告",
        "",
        "## 输出文件",
        "",
        f"- 候选分级明细：`{TRIAGED_OUT.relative_to(ROOT)}`",
        f"- 核心候选明细：`{CORE_CANDIDATE_OUT.relative_to(ROOT)}`",
        f"- 按试验汇总：`{TRIAL_SUMMARY_OUT.relative_to(ROOT)}`",
        f"- 按概念汇总：`{CONCEPT_SUMMARY_OUT.relative_to(ROOT)}`",
        f"- 相对 AE module 的增量候选：`{INCREMENTAL_OUT.relative_to(ROOT)}`",
        "",
        "## 主要结果",
        "",
        f"- 全模块 outcome 候选行数：{len(triaged)}",
        f"- 覆盖 trial/NCT 数：{len(by_trial)}",
        f"- 高优先级核心候选行数：{len(core_candidates)}",
        f"- 相对现有 CT.gov AE module 新增的核心 trial-concept 候选数：{len(incremental_core_pairs)}",
        f"- 相对现有 CT.gov AE module 新增的探索性 trial-concept 候选数：{len(incremental_exploratory_pairs)}",
        "",
        "## Triage class counts",
        "",
    ]
    report.extend(f"- {key}: {value}" for key, value in sorted(class_counts.items()))
    report.extend(["", "## Priority counts", ""])
    report.extend(f"- {key}: {value}" for key, value in sorted(priority_counts.items()))
    report.extend([
        "",
        "## 使用建议",
        "",
        "1. 暂不把这些候选直接并入主分析。",
        "2. 优先人工核对 `core_candidate_needs_manual_mapping` 中相对 AE module 新增的 trial-concept。",
        "3. `grade_3_or_higher_adverse_event_or_lab_abnormality` 主要来自实验室异常或安全专题，应作为探索性补充，不与核心 AE 发生率直接合并。",
        "4. `exclude_non_core_mixed_endpoint` 多为 treatment failure/time-to-treatment-failure 等混合疗效-安全终点，应从核心安全一致性分析中排除。",
    ])
    REPORT_OUT.write_text("\n".join(report) + "\n", encoding="utf-8")

    manuscript_summary = [
        "# CT.gov Full-Module Candidate Expansion",
        "",
        (
            "A prespecified exploratory screen of the ClinicalTrials.gov outcome-measures module "
            f"identified {len(triaged)} safety-related candidate rows across {len(by_trial)} trial records. "
            f"After rule-based triage, {len(core_candidates)} rows were retained as high-priority core safety "
            f"candidates requiring manual mapping review, corresponding to {len(incremental_core_pairs)} "
            "trial-concept candidates not already represented by the structured adverse-events module."
        ),
        "",
        (
            "These candidates were not merged into the primary concordance analysis. Mixed efficacy-safety "
            "endpoints such as treatment failure were excluded from the core set, and laboratory-abnormality "
            "or disease-specific safety outcomes were kept as exploratory candidates pending manual review."
        ),
    ]
    MANUSCRIPT_OUT.write_text("\n".join(manuscript_summary) + "\n", encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
