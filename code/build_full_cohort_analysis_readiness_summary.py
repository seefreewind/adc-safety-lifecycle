#!/usr/bin/env python3
"""Summarize extraction and comparison readiness for the full cohort."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
INTERIM = ROOT / "data" / "interim"
TABLES = ROOT / "tables"
PROTOCOL = ROOT / "protocol"

TRIAL_MASTER = PROCESSED / "trial_master_expansion_candidates.csv"
PUB = INTERIM / "publication_core_safety_combined_seed.csv"
FDA = INTERIM / "fda_core_safety_combined_seed.csv"
CTGOV = INTERIM / "ctgov_core_safety_expansion_seed.csv"
MATRIX = PROCESSED / "full_cohort_source_comparability_matrix.csv"
ANALYSIS_SET = TABLES / "analysis_ready_comparison_set.csv"
OUT = TABLES / "full_cohort_analysis_readiness_summary.csv"
REPORT_OUT = PROTOCOL / "full_cohort_analysis_readiness_summary.zh.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def count_by_trial(rows: list[dict[str, str]]) -> Counter[str]:
    return Counter(row["trial_id"] for row in rows if row.get("trial_id"))


def main() -> None:
    trials = read_csv(TRIAL_MASTER)
    if not trials:
        trials = [{"trial_id": f"TRIAL{i:03d}", "short_trial_name": ""} for i in range(1, 24)]

    pub_counts = count_by_trial(read_csv(PUB))
    fda_counts = count_by_trial(read_csv(FDA))
    ctgov_counts = count_by_trial(read_csv(CTGOV))

    comparisons = read_csv(MATRIX)
    grade_counts: dict[str, Counter[str]] = defaultdict(Counter)
    source_pairs: dict[str, set[str]] = defaultdict(set)
    for row in comparisons:
        trial = row.get("trial_id", "")
        if not trial:
            continue
        grade_counts[trial][row.get("comparability_grade", "")] += 1
        source_pairs[trial].add(" vs ".join(sorted([row.get("source_1", ""), row.get("source_2", "")])))

    analysis_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in read_csv(ANALYSIS_SET):
        trial = row.get("trial_id", "")
        if trial:
            analysis_counts[trial][row.get("analysis_tier", "")] += 1

    rows = []
    for trial in sorted(trials, key=lambda r: r.get("trial_id", "")):
        trial_id = trial.get("trial_id", "")
        pub_n = pub_counts.get(trial_id, 0)
        fda_n = fda_counts.get(trial_id, 0)
        ctgov_n = ctgov_counts.get(trial_id, 0)
        sources = sum(1 for value in [pub_n, fda_n, ctgov_n] if value > 0)
        a_pairs = grade_counts[trial_id].get("A", 0)
        b_pairs = grade_counts[trial_id].get("B", 0)
        c_pairs = grade_counts[trial_id].get("C", 0)
        primary_candidates = analysis_counts[trial_id].get("primary_candidate", 0)
        sensitivity_candidates = analysis_counts[trial_id].get("sensitivity_candidate", 0)
        if primary_candidates:
            readiness = "primary_pair_candidate"
        elif sensitivity_candidates:
            readiness = "sensitivity_pair_candidate"
        elif sources >= 2:
            readiness = "multi_source_descriptive_or_manual_review"
        elif sources == 1:
            readiness = "single_source_only"
        else:
            readiness = "not_started"
        rows.append({
            "trial_id": trial_id,
            "short_trial_name": trial.get("acronym", trial.get("short_trial_name", trial.get("trial_name", ""))),
            "publication_seed_rows": str(pub_n),
            "fda_seed_rows": str(fda_n),
            "ctgov_seed_rows": str(ctgov_n),
            "structured_source_count": str(sources),
            "comparability_A_pairs": str(a_pairs),
            "comparability_B_pairs": str(b_pairs),
            "comparability_C_pairs": str(c_pairs),
            "primary_candidate_pairs": str(primary_candidates),
            "sensitivity_candidate_pairs": str(sensitivity_candidates),
            "source_pairs_present": ";".join(sorted(source_pairs.get(trial_id, set()))),
            "readiness_tier": readiness,
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    tier_counts = Counter(row["readiness_tier"] for row in rows)
    source_count_dist = Counter(row["structured_source_count"] for row in rows)
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(
        "\n".join([
            "# Full-cohort analysis readiness summary",
            "",
            "日期：2026-06-18",
            "",
            "## 输出",
            "",
            "- `tables/full_cohort_analysis_readiness_summary.csv`",
            "",
            "## 队列覆盖",
            "",
            f"- 试验总数：{len(rows)}",
            f"- publication seed 覆盖：{sum(1 for row in rows if int(row['publication_seed_rows']) > 0)}",
            f"- FDA seed 覆盖：{sum(1 for row in rows if int(row['fda_seed_rows']) > 0)}",
            f"- CT.gov seed 覆盖：{sum(1 for row in rows if int(row['ctgov_seed_rows']) > 0)}",
            f"- 主分析候选覆盖：{sum(1 for row in rows if int(row['primary_candidate_pairs']) > 0)} 个 trial",
            f"- 敏感性候选覆盖：{sum(1 for row in rows if int(row['sensitivity_candidate_pairs']) > 0)} 个 trial",
            "",
            "## 结构化来源数量",
            "",
            *[f"- {source_count} 个来源：{count} 个 trial" for source_count, count in sorted(source_count_dist.items())],
            "",
            "## 就绪分层",
            "",
            *[f"- {tier}: {count}" for tier, count in sorted(tier_counts.items())],
            "",
            "## 建议",
            "",
            "下一步优先处理 `multi_source_descriptive_or_manual_review` 中的 C 级配对：其中不少只是分母、随访窗口或 AE 口径差异，需要人工裁决后才能升级为敏感性分析或主分析。",
        ]) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
