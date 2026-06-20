#!/usr/bin/env python3
"""Precheck comparability between expansion publication seed rows and CT.gov rows."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
TABLES = ROOT / "tables"
PROTOCOL = ROOT / "protocol"

PUB = INTERIM / "publication_core_safety_expansion_seed.csv"
CTGOV = INTERIM / "ctgov_core_safety_expansion_seed.csv"
OUT = TABLES / "expansion_pub_ctgov_comparability_precheck.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def norm_pct(value: str) -> float | None:
    try:
        return round(float(value), 3)
    except (TypeError, ValueError):
        return None


def pct_diff(a: str, b: str) -> str:
    pa = norm_pct(a)
    pb = norm_pct(b)
    if pa is None or pb is None:
        return ""
    return f"{abs(pa - pb):.3f}"


def same_denominator(pub: dict[str, str], ct: dict[str, str]) -> bool:
    return pub.get("denominator") not in {"", None} and pub.get("denominator") == ct.get("denominator")


def same_arm(pub: dict[str, str], ct: dict[str, str]) -> bool:
    if pub["arm_id"] == ct["arm_id"]:
        return True
    if pub["arm_id"].startswith(ct["arm_id"]):
        return True
    return False


def comparability(pub: dict[str, str], ct: dict[str, str]) -> tuple[str, str, str]:
    if not same_arm(pub, ct):
        return "C", "not_used_primary", "different or custom arm identifier"
    if not same_denominator(pub, ct):
        return "C", "not_used_primary", "denominator differs"

    pub_concept = pub["safety_concept"]
    ct_concept = ct["safety_concept"]
    pub_causality = pub["causality"]
    ct_causality = ct["causality"]

    if pub_concept == ct_concept and pub_causality == ct_causality:
        return "A", "primary_numeric_comparison_candidate", "same arm, denominator, concept, and causality"
    if pub_concept == ct_concept and pub_causality != ct_causality:
        return "B", "sensitivity_or_descriptive", "same denominator and concept, but causality differs"
    if pub_concept == "fatal_adverse_event" and ct_concept == "fatal_adverse_event":
        return "C", "not_used_primary", "CT.gov row is all-cause mortality; publication may report fatal AE or death-summary subtype"
    return "C", "not_used_primary", "different safety concept or reporting construct"


def main() -> None:
    pub_rows = read_csv(PUB)
    ct_rows = read_csv(CTGOV)

    out_rows = []
    seq = 1
    for pub in pub_rows:
        candidate_ct = [ct for ct in ct_rows if ct["trial_id"] == pub["trial_id"]]
        for ct in candidate_ct:
            grade, use, reason = comparability(pub, ct)
            if grade == "C" and not (same_arm(pub, ct) and same_denominator(pub, ct)):
                continue
            out_rows.append({
                "comparison_id": f"EXPCOMP{seq:05d}",
                "trial_id": pub["trial_id"],
                "publication_observation_id": pub["observation_id"],
                "ctgov_observation_id": ct["observation_id"],
                "publication_arm_id": pub["arm_id"],
                "ctgov_arm_id": ct["arm_id"],
                "publication_safety_concept": pub["safety_concept"],
                "ctgov_safety_concept": ct["safety_concept"],
                "publication_causality": pub["causality"],
                "ctgov_causality": ct["causality"],
                "publication_denominator": pub["denominator"],
                "ctgov_denominator": ct["denominator"],
                "publication_percentage": pub["percentage"],
                "ctgov_percentage": ct["percentage"],
                "absolute_percentage_point_difference": pct_diff(pub["percentage"], ct["percentage"]),
                "comparability_grade": grade,
                "analysis_use": use,
                "reason": reason,
            })
            seq += 1

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0]))
        writer.writeheader()
        writer.writerows(out_rows)

    grade_counts = {}
    for row in out_rows:
        grade_counts[row["comparability_grade"]] = grade_counts.get(row["comparability_grade"], 0) + 1

    lines = [
        "# Expansion publication-CT.gov comparability precheck 报告",
        "",
        "日期：2026-06-18",
        "",
        "## 输出",
        "",
        "- `tables/expansion_pub_ctgov_comparability_precheck.csv`",
        "",
        "## 预检结果",
        "",
        f"- publication seed 行：{len(pub_rows)}",
        f"- 可形成同 trial/arm 或同分母候选比较的行：{len(out_rows)}",
    ]
    for grade in ["A", "B", "C"]:
        lines.append(f"- {grade} 级：{grade_counts.get(grade, 0)}")
    lines.extend([
        "",
        "## 解释",
        "",
        "A 级仅表示 publication 与 CT.gov 在 arm、分母、概念和 causality 上初步一致，仍需人工复核页码和定义。多数 publication Grade >=3 或 TRAE 概览无法与 CT.gov eventGroups 直接比较。",
    ])
    (PROTOCOL / "expansion_pub_ctgov_comparability_precheck_report.zh.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print("Wrote protocol/expansion_pub_ctgov_comparability_precheck_report.zh.md")


if __name__ == "__main__":
    main()
