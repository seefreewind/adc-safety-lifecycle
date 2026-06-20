#!/usr/bin/env python3
"""Create conservative FDA-review seed rows for expansion trials."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "interim" / "fda_core_safety_expansion_seed.csv"
SUMMARY_OUT = ROOT / "tables" / "fda_core_safety_expansion_seed_summary.csv"
REPORT_OUT = ROOT / "protocol" / "fda_core_safety_expansion_seed_report.zh.md"

HEADER = [
    "observation_id", "trial_id", "arm_id", "document_id", "source_type",
    "page_or_table_locator", "ae_original_term", "ae_standardized_term",
    "meddra_pt", "meddra_soc", "smq", "safety_concept", "grade_category",
    "seriousness", "causality", "number_events", "number_patients",
    "denominator", "percentage", "reporting_threshold", "analysis_population",
    "data_cutoff_date", "extractor", "review_status", "notes",
]


def pct(n: int, denom: int) -> str:
    return f"{(n / denom) * 100:.1f}"


def row(
    seq: int,
    trial_id: str,
    arm_id: str,
    document_id: str,
    locator: str,
    term: str,
    concept: str,
    grade: str,
    seriousness: str,
    causality: str,
    n_patients: int | str,
    denominator: int,
    percentage: float | str,
    population: str,
    notes: str,
    status: str = "needs_review",
) -> list[str]:
    return [
        f"FDAEXP{seq:05d}", trial_id, arm_id, document_id, "FDA review",
        locator, term, term, "", "", "", concept, grade, seriousness, causality,
        "", str(n_patients), str(denominator), str(percentage), "", population, "",
        "script:build_fda_core_safety_expansion_seed.py", status, notes,
    ]


def add_padcev(rows: list[list[str]], seq: int) -> int:
    """EV-201 Cohort 1 rows from FDA Table 74."""
    document = "FDA_ADC006_MDR_761137_ORIG1"
    trial = "TRIAL003"
    arm = "TRIAL003_EG000"
    denominator = 125
    population = "EV-201 Cohort 1 1.25 mg/kg FDA safety analysis group"
    note = (
        "FDA Table 74 reports multiple enfortumab vedotin safety groups; these rows use "
        "EV-201 Cohort 1 because it is the pivotal cohort aligned to the original Padcev approval. "
        "Compare only against publication rows using the same cohort/population."
    )
    entries = [
        ("TEAE", "any_adverse_event", "all grades", "any", "all-cause", 125, "100.0"),
        ("Drug-related TEAE", "any_adverse_event", "all grades", "any", "treatment-related", 117, "93.6"),
        ("Serious TEAE", "serious_adverse_event", "all grades", "serious", "all-cause", 58, "46.4"),
        ("Drug-related serious TEAE", "serious_adverse_event", "all grades", "serious", "treatment-related", 24, "19.2"),
        ("TEAE leading to death", "fatal_adverse_event", "grade 5", "fatal", "all-cause", 7, "5.6"),
        ("Drug-related TEAE leading to death", "fatal_adverse_event", "grade 5", "fatal", "treatment-related", 0, "0.0"),
        ("TEAE leading to withdrawal of study drug", "adverse_event_discontinuation", "all grades", "discontinuation", "all-cause", 20, "16.0"),
        ("Drug-related TEAE leading to withdrawal of study drug", "adverse_event_discontinuation", "all grades", "discontinuation", "treatment-related", 15, "12.0"),
        ("TEAE leading to dose reduction", "adverse_event_dose_reduction", "all grades", "dose_reduction", "all-cause", 43, "34.4"),
        ("Drug-related TEAE leading to dose reduction", "adverse_event_dose_reduction", "all grades", "dose_reduction", "treatment-related", 40, "32.0"),
        ("TEAE leading to dose interruption", "adverse_event_dose_interruption", "all grades", "dose_interruption", "all-cause", 80, "64.0"),
        ("TEAE with NCI-CTCAE >= Grade 3", "grade_3_or_higher_adverse_event", "grade >=3", "any", "all-cause", 91, "72.8"),
        ("Drug-related TEAE with NCI-CTCAE >= Grade 3", "grade_3_or_higher_adverse_event", "grade >=3", "any", "treatment-related", 68, "54.4"),
    ]
    for term, concept, grade, seriousness, causality, n, percentage in entries:
        rows.append(row(
            seq, trial, arm, document, "Table 74, FDA review pp184-185",
            term, concept, grade, seriousness, causality, n, denominator, percentage,
            population, note,
        ))
        seq += 1
    return seq


def add_polivy(rows: list[list[str]], seq: int) -> int:
    """GO29365 primary safety population rows from FDA Tables 16-17."""
    document = "FDA_ADC005_MEDR_761121_ORIG1"
    trial = "TRIAL011"
    population_note = (
        "FDA primary safety population for GO29365 DLBCL. These denominators differ from some "
        "publication randomized efficacy denominators and should be checked before direct comparison."
    )
    arms = [
        ("TRIAL011_EG000", "Pola + BR primary safety population", 45, [
            ("Any SAE", "serious_adverse_event", "all grades", "serious", "all-cause", 29, "64.0", "Table 16, FDA review p49"),
            ("Any grade >=3 AE", "grade_3_or_higher_adverse_event", "grade >=3", "any", "all-cause", 38, "84.0", "Table 16, FDA review p49"),
            ("Any grade >=4 AE", "grade_4_or_higher_adverse_event", "grade >=4", "any", "all-cause", 26, "58.0", "Table 16, FDA review p49"),
            ("Any study drug discontinuation due to AE", "adverse_event_discontinuation", "all grades", "discontinuation", "all-cause", 14, "31.0", "Table 17, FDA review p50"),
            ("Any study drug dose reduction due to AE", "adverse_event_dose_reduction", "all grades", "dose_reduction", "all-cause", 8, "18.0", "Table 17, FDA review p50"),
            ("Any study drug dose interruption due to AE", "adverse_event_dose_interruption", "all grades", "dose_interruption", "all-cause", 23, "51.0", "Table 17, FDA review p50"),
            ("Fatal AEs in absence of NALT or PD", "fatal_adverse_event", "grade 5", "fatal", "all-cause", 4, "9.0", "FDA review p46 text"),
        ]),
        ("TRIAL011_EG001", "BR primary safety population", 39, [
            ("Any SAE", "serious_adverse_event", "all grades", "serious", "all-cause", 24, "62.0", "Table 16, FDA review p49"),
            ("Any grade >=3 AE", "grade_3_or_higher_adverse_event", "grade >=3", "any", "all-cause", 29, "74.0", "Table 16, FDA review p49"),
            ("Any grade >=4 AE", "grade_4_or_higher_adverse_event", "grade >=4", "any", "all-cause", 21, "54.0", "Table 16, FDA review p49"),
            ("Any study drug discontinuation due to AE", "adverse_event_discontinuation", "all grades", "discontinuation", "all-cause", 6, "15.0", "Table 17, FDA review p50"),
            ("Any study drug dose reduction due to AE", "adverse_event_dose_reduction", "all grades", "dose_reduction", "all-cause", 4, "10.0", "Table 17, FDA review p50"),
            ("Any study drug dose interruption due to AE", "adverse_event_dose_interruption", "all grades", "dose_interruption", "all-cause", 15, "38.0", "Table 17, FDA review p50"),
            ("Fatal AEs in absence of NALT or PD", "fatal_adverse_event", "grade 5", "fatal", "all-cause", 6, "15.0", "FDA review p46 text"),
        ]),
    ]
    for arm, population, denominator, entries in arms:
        for term, concept, grade, seriousness, causality, n, percentage, locator in entries:
            rows.append(row(
                seq, trial, arm, document, locator, term, concept, grade, seriousness,
                causality, n, denominator, percentage, population, population_note,
            ))
            seq += 1
    return seq


def main() -> None:
    rows: list[list[str]] = []
    seq = 1
    seq = add_padcev(rows, seq)
    seq = add_polivy(rows, seq)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerows(rows)

    by_trial = Counter(r[1] for r in rows)
    summary_rows = []
    for trial_id in sorted(by_trial):
        trial_rows = [r for r in rows if r[1] == trial_id]
        summary_rows.append({
            "trial_id": trial_id,
            "fda_expansion_seed_row_count": str(len(trial_rows)),
            "arm_count": str(len({r[2] for r in trial_rows})),
            "document_ids": ";".join(sorted({r[3] for r in trial_rows})),
            "safety_concepts": ";".join(sorted({r[11] for r in trial_rows})),
            "review_status_values": ";".join(sorted({r[23] for r in trial_rows})),
        })
    SUMMARY_OUT.parent.mkdir(parents=True, exist_ok=True)
    with SUMMARY_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0]))
        writer.writeheader()
        writer.writerows(summary_rows)

    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(
        "\n".join([
            "# FDA expansion core-safety seed 报告",
            "",
            "日期：2026-06-18",
            "",
            "## 输出",
            "",
            "- `data/interim/fda_core_safety_expansion_seed.csv`",
            "- `tables/fda_core_safety_expansion_seed_summary.csv`",
            "",
            "## 本批收录",
            "",
            f"- FDA expansion seed 行数：{len(rows)}",
            f"- 覆盖 trial：{len(by_trial)}（TRIAL003 EV-201；TRIAL011 GO29365）",
            "",
            "## 未强行收录",
            "",
            "- TRIAL010 INO-VATE ALL：FDA 审评文件关键安全表页存在扫描/空文字层，当前仅把出版物 seed 作为主结构化来源；后续若需要 FDA 数值，可走页面渲染/OCR 复核。",
            "- 后续同药物补充适应证试验未使用原始批准审评数值，避免把旧 FDA 审评池误配到 DREAMM-7、DREAMM-8、TROPION-Breast02 等后期试验。",
            "",
            "## 使用边界",
            "",
            "所有行均标记为 `needs_review`，进入最终稿或正式统计前仍需核对分母、分析人群和是否适合与 publication/CT.gov 直接比较。",
        ]) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Wrote {SUMMARY_OUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
