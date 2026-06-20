#!/usr/bin/env python3
"""Create FDA-review seed rows for core safety outcomes."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "interim" / "fda_core_safety_seed.csv"

HEADER = [
    "observation_id", "trial_id", "arm_id", "document_id", "source_type",
    "page_or_table_locator", "ae_original_term", "ae_standardized_term",
    "meddra_pt", "meddra_soc", "smq", "safety_concept", "grade_category",
    "seriousness", "causality", "number_events", "number_patients",
    "denominator", "percentage", "reporting_threshold", "analysis_population",
    "data_cutoff_date", "extractor", "review_status", "notes",
]


def row(seq, trial, arm, doc, locator, term, concept, grade, seriousness, causality,
        n_patients, denom, pct, population, notes="", status="needs_review"):
    return [
        f"FDACORE{seq:05d}", trial, arm, doc, "FDA review",
        locator, term, term, "", "", "", concept, grade, seriousness, causality,
        "", n_patients, denom, pct, "", population, "", "script:build_fda_core_safety_seed.py",
        status, notes,
    ]


def main() -> None:
    rows = []
    seq = 1

    # Enhertu, BLA 761139 multi-disciplinary review. HER2-positive breast cancer 5.4 mg/kg pool N=234.
    enhertu = [
        ("Subjects with Any TEAE", "any_adverse_event", "all grades", "any", "all-cause", 233, 234, 99.6, "Table 41, FDA review p183"),
        ("Subjects with Any TEAE CTCAE at Least Grade 3", "grade_3_or_higher_adverse_event", "grade >=3", "any", "all-cause", 117, 234, 50.0, "Table 42, FDA review p185"),
        ("Subjects with Any Serious TEAE", "serious_adverse_event", "all grades", "serious", "all-cause", 47, 234, 20.1, "Table 35, FDA review p174"),
        ("Any Death", "fatal_adverse_event", "all grades", "fatal", "all-cause", 28, 234, 12.0, "Table 33, FDA review p171"),
        ("Adverse Event as primary cause of death", "fatal_adverse_event", "all grades", "fatal", "all-cause/adverse-event primary cause", 7, 234, 3.0, "Table 33, FDA review p171"),
        ("Any TEAE associated with study drug discontinuation", "adverse_event_discontinuation", "all grades", "discontinuation", "all-cause", 22, 234, 9.4, "Table 37, FDA review p176"),
        ("Any TEAE associated with dose interruption", "adverse_event_dose_interruption", "all grades", "dose_interruption", "all-cause", 78, 234, 33.3, "Table 38, FDA review p177"),
        ("Any TEAE associated with dose reduction", "adverse_event_dose_reduction", "all grades", "dose_reduction", "all-cause", 42, 234, 17.9, "Table 39, FDA review p179"),
    ]
    for item in enhertu:
        rows.append(row(seq, "TRIAL001", "TRIAL001_EG000", "FDA_ADC007_MDR_761139_ORIG1",
                        item[8], item[0], item[1], item[2], item[3], item[4],
                        item[5], item[6], item[7],
                        "HER2-positive breast cancer 5.4 mg/kg FDA safety pool",
                        "FDA approval-review pool is broader than DESTINY-Breast01 RP2D safety population; do not directly compare without population alignment.",
                        "needs_manual_adjudication"))
        seq += 1

    # Blenrep, BLA 761158 multi-disciplinary review. DREAMM-2 dose cohorts.
    for arm, denom, entries in [
        ("TRIAL002_EG000", 95, [
            ("Any Grade TEAEs", "any_adverse_event", "all grades", "any", "all-cause", 93, 98.0),
            ("Severe (Grade 3-4) TEAEs", "grade_3_or_higher_adverse_event", "grade 3-4", "any", "all-cause", 78, 82.0),
            ("Fatal (Grade 5) TEAEs", "fatal_adverse_event", "grade 5", "fatal", "all-cause", 3, 3.0),
            ("Serious TEAEs (SAEs)", "serious_adverse_event", "all grades", "serious", "all-cause", 38, 40.0),
            ("Discontinuation due to TEAEs", "adverse_event_discontinuation", "all grades", "discontinuation", "all-cause", 8, 8.0),
            ("Dose interruption due to TEAEs", "adverse_event_dose_interruption", "all grades", "dose_interruption", "all-cause", 51, 54.0),
            ("Dose reduction due to TEAEs", "adverse_event_dose_reduction", "all grades", "dose_reduction", "all-cause", 28, 29.0),
        ]),
        ("TRIAL002_EG001", 99, [
            ("Any Grade TEAEs", "any_adverse_event", "all grades", "any", "all-cause", 99, 100.0),
            ("Severe (Grade 3-4) TEAEs", "grade_3_or_higher_adverse_event", "grade 3-4", "any", "all-cause", 81, 82.0),
            ("Fatal (Grade 5) TEAEs", "fatal_adverse_event", "grade 5", "fatal", "all-cause", 7, 7.0),
            ("Serious TEAEs (SAEs)", "serious_adverse_event", "all grades", "serious", "all-cause", 47, 48.0),
            ("Discontinuation due to TEAEs", "adverse_event_discontinuation", "all grades", "discontinuation", "all-cause", 10, 10.0),
            ("Dose interruption due to TEAEs", "adverse_event_dose_interruption", "all grades", "dose_interruption", "all-cause", 61, 62.0),
            ("Dose reduction due to TEAEs", "adverse_event_dose_reduction", "all grades", "dose_reduction", "all-cause", 41, 41.0),
        ]),
    ]:
        for term, concept, grade, seriousness, causality, n, pct in entries:
            rows.append(row(seq, "TRIAL002", arm, "FDA_ADC009_MDR_761158_ORIG1",
                            "Table 27, FDA review p148", term, concept, grade, seriousness, causality,
                            n, denom, pct, "DREAMM-2 safety population",
                            "Direct FDA analysis of DREAMM-2 safety population; cohort-specific values.",
                            "needs_review"))
            seq += 1

    # Trodelvy, BLA 761115 multi-disciplinary review. IMMU-132-01.
    trodelvy = [
        ("Any adverse event", "any_adverse_event", "all grades", "any", "all-cause", 108, 108, 100.0, "Table 25, FDA review p88", "mTNBC efficacy cohort"),
        ("Any adverse event grade 3-4", "grade_3_or_higher_adverse_event", "grade 3-4", "any", "all-cause", 78, 108, 72.2, "Table 25, FDA review p88", "mTNBC efficacy cohort"),
        ("Any serious adverse reaction", "serious_adverse_event", "all grades", "serious", "all-cause", 36, 108, 33.0, "Table 24, FDA review p85", "mTNBC efficacy cohort"),
        ("Any serious adverse reaction grade 3-4", "serious_adverse_event", "grade 3-4", "serious", "all-cause", 27, 108, 25.0, "Table 24, FDA review p85", "mTNBC efficacy cohort"),
        ("Dose reductions due to adverse reactions", "adverse_event_dose_reduction", "all grades", "dose_reduction", "all-cause", "", 108, 33.0, "FDA review text p86", "mTNBC efficacy cohort"),
        ("Discontinued trial therapy due to TEAEs", "adverse_event_discontinuation", "all grades", "discontinuation", "all-cause", 5, 108, 4.6, "FDA review text p87", "mTNBC efficacy cohort"),
    ]
    for item in trodelvy:
        rows.append(row(seq, "TRIAL004", "TRIAL004_EG000", "FDA_ADC008_MDR_761115_ORIG1",
                        item[8], item[0], item[1], item[2], item[3], item[4],
                        item[5], item[6], item[7], item[9],
                        "FDA safety update review of IMMU-132-01; verify cohort definition before comparison with NEJM publication.",
                        "needs_review"))
        seq += 1

    # Mylotarg, BLA 761060 medical review. These are adjudication aids, not complete core overview rows.
    rows.append(row(seq, "TRIAL006", "TRIAL006_EG000", "FDA_ADC001_MEDR_761060_ORIG1",
                    "FDA review text p77", "Treatment-related mortality higher in GO arm",
                    "fatal_adverse_event", "grade 5", "fatal", "treatment-related",
                    "", 139, 6.0, "ALFA-0701 GO arm",
                    "FDA reviewer text reports treatment-related mortality was 6% in GO arm vs 2% control; exact numerator not text-extractable from table image.",
                    "needs_manual_adjudication"))
    seq += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerows(rows)
    print(f"Wrote {len(rows)} FDA core safety seed rows to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
