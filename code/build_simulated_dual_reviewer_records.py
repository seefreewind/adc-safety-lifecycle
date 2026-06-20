#!/usr/bin/env python3
"""Generate simulated duplicate-review records for internal stress testing.

These records are not evidence of real independent human adjudication.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "tables"
PROTOCOL = ROOT / "protocol"

STRATA_OUT = TABLES / "simulated_dual_reviewer_strata_adjudication.csv"
PAIR_OUT = TABLES / "simulated_dual_reviewer_pair_adjudication.csv"
SUMMARY_OUT = TABLES / "simulated_dual_reviewer_agreement_summary.csv"
REPORT_OUT = PROTOCOL / "simulated_dual_reviewer_records_report.zh.md"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def kappa(labels_a: list[str], labels_b: list[str]) -> tuple[float, float]:
    n = len(labels_a)
    observed = sum(a == b for a, b in zip(labels_a, labels_b)) / n if n else 0.0
    ca = Counter(labels_a)
    cb = Counter(labels_b)
    expected = sum((ca[label] / n) * (cb[label] / n) for label in set(ca) | set(cb)) if n else 0.0
    kap = (observed - expected) / (1 - expected) if expected < 1 else 1.0
    return observed, kap


def strata_base_decision(status: str) -> str:
    if status == "comparable_and_concordant":
        return "primary_comparable"
    if status == "comparable_but_discordant":
        return "sensitivity_comparable"
    return "non_comparable"


def build_strata_records() -> list[dict[str, str]]:
    rows = [
        row for row in read_rows(TABLES / "five_state_source_reporting_status.csv")
        if row["five_state_status"] in {"comparable_and_concordant", "comparable_but_discordant", "reported_but_non_comparable"}
    ]
    out = []
    for idx, row in enumerate(rows, 1):
        a = strata_base_decision(row["five_state_status"])
        b = a
        note = "Simulated reviewers agree."
        if row["five_state_status"] == "reported_but_non_comparable" and idx in {9, 23, 41}:
            b = "sensitivity_comparable"
            note = "Simulated reviewer B treated this as borderline sensitivity-comparable."
        elif row["five_state_status"] == "comparable_but_discordant" and idx == 47:
            b = "non_comparable"
            note = "Simulated reviewer B downgraded a discordant comparable stratum."
        out.append({
            "simulation_record_id": f"SIMSTRATA{idx:03d}",
            "trial_id": row["trial_id"],
            "short_trial_name": row["short_trial_name"],
            "safety_concept": row["safety_concept"],
            "source_pair": row["source_pair"],
            "five_state_status_current": row["five_state_status"],
            "simulated_reviewer_A_decision": a,
            "simulated_reviewer_B_decision": b,
            "simulated_agreement": "yes" if a == b else "no",
            "resolution_for_stress_test": a if a == b else "retain_current_project_classification",
            "simulation_note": note,
        })
    return out


def build_pair_records() -> list[dict[str, str]]:
    rows = read_rows(TABLES / "analysis_ready_comparison_set_confirmed.csv")
    out = []
    for idx, row in enumerate(rows, 1):
        a = row["analysis_tier"].replace("_candidate", "")
        b = a
        note = "Simulated reviewers agree."
        if row["analysis_tier"] == "sensitivity_candidate" and idx in {2, 4}:
            b = "non_comparable"
            note = "Simulated reviewer B downgraded this sensitivity pair because alignment was borderline."
        elif row["analysis_tier"] == "primary_candidate" and idx == 17:
            b = "sensitivity"
            note = "Simulated reviewer B downgraded this primary pair to sensitivity in the stress test."
        out.append({
            "simulation_record_id": f"SIMPAIR{idx:03d}",
            "comparison_id": row["comparison_id"],
            "trial_id": row["trial_id"],
            "ae_concept": row["ae_concept"],
            "source_pair": f"{row['source_1']} vs {row['source_2']}",
            "current_analysis_tier": row["analysis_tier"],
            "absolute_percentage_difference": row["absolute_percentage_difference"],
            "simulated_reviewer_A_decision": a,
            "simulated_reviewer_B_decision": b,
            "simulated_agreement": "yes" if a == b else "no",
            "resolution_for_stress_test": a if a == b else "retain_current_project_classification",
            "simulation_note": note,
        })
    return out


def main() -> None:
    strata = build_strata_records()
    pairs = build_pair_records()
    write_csv(STRATA_OUT, strata, list(strata[0]))
    write_csv(PAIR_OUT, pairs, list(pairs[0]))

    s_obs, s_k = kappa([r["simulated_reviewer_A_decision"] for r in strata], [r["simulated_reviewer_B_decision"] for r in strata])
    p_obs, p_k = kappa([r["simulated_reviewer_A_decision"] for r in pairs], [r["simulated_reviewer_B_decision"] for r in pairs])
    summary = [
        {
            "domain": "jointly_reported_strata",
            "record_count": str(len(strata)),
            "simulated_raw_agreement_percent": f"{s_obs * 100:.1f}",
            "simulated_unweighted_kappa": f"{s_k:.2f}",
            "use_boundary": "Internal simulation only; not reportable as real independent human reviewer agreement.",
        },
        {
            "domain": "analysis_ready_pairs",
            "record_count": str(len(pairs)),
            "simulated_raw_agreement_percent": f"{p_obs * 100:.1f}",
            "simulated_unweighted_kappa": f"{p_k:.2f}",
            "use_boundary": "Internal simulation only; not reportable as real independent human reviewer agreement.",
        },
    ]
    write_csv(SUMMARY_OUT, summary, list(summary[0]))
    report = f"""# 模拟双人评审记录报告

- 53 个 jointly reported strata 模拟复核记录：`{STRATA_OUT.relative_to(ROOT)}`
- 28 个 analysis-ready pairs 模拟复核记录：`{PAIR_OUT.relative_to(ROOT)}`
- 模拟一致性汇总：`{SUMMARY_OUT.relative_to(ROOT)}`

重要边界：这些记录是 algorithmic/simulated duplicate review stress test，不是真实独立人工双人审核；不得在投稿稿中写作 real inter-reviewer agreement 或真实 Cohen's kappa。

模拟结果：

- Strata 模拟原始一致率：{s_obs * 100:.1f}%；模拟 κ：{s_k:.2f}
- Pair 模拟原始一致率：{p_obs * 100:.1f}%；模拟 κ：{p_k:.2f}
"""
    REPORT_OUT.write_text(report, encoding="utf-8")
    print(report.strip())


if __name__ == "__main__":
    main()
