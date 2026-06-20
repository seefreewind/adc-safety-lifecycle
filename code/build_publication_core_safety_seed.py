#!/usr/bin/env python3
"""Create a publication-side seed extraction table for core safety outcomes.

Rows are limited to values that were clear in text-extracted publication tables.
Anything requiring table-image interpretation or source-definition adjudication is
left for manual review rather than guessed.
"""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "interim" / "publication_core_safety_seed.csv"


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
        f"PUBCORE{seq:05d}", trial, arm, doc, "primary publication/supplement",
        locator, term, term, "", "", "", concept, grade, seriousness, causality,
        "", n_patients, denom, pct, "", population, "", "script:build_publication_core_safety_seed.py",
        status, notes,
    ]


def main() -> None:
    rows = []
    seq = 1

    # DESTINY-Breast01, Supplementary Table S3, RP2D N=184.
    destiny = [
        ("TEAEs", "any_adverse_event", "all grades", "any", "all-cause", 183, 184, 99.5),
        ("Drug-related TEAEs", "any_adverse_event", "all grades", "any", "treatment-related", 183, 184, 99.5),
        ("TEAEs grade >=3", "grade_3_or_higher_adverse_event", "grade >=3", "any", "all-cause", 105, 184, 57.1),
        ("Drug-related TEAEs grade >=3", "grade_3_or_higher_adverse_event", "grade >=3", "any", "treatment-related", 89, 184, 48.4),
        ("Serious TEAEs", "serious_adverse_event", "all grades", "serious", "all-cause", 42, 184, 22.8),
        ("Drug-related serious TEAEs", "serious_adverse_event", "all grades", "serious", "treatment-related", 23, 184, 12.5),
        ("TEAEs leading to T-DXd discontinuation", "adverse_event_discontinuation", "all grades", "discontinuation", "all-cause", 28, 184, 15.2),
        ("Drug-related TEAEs leading to T-DXd discontinuation", "adverse_event_discontinuation", "all grades", "discontinuation", "treatment-related", 27, 184, 14.7),
        ("TEAEs leading to dose reduction", "adverse_event_dose_reduction", "all grades", "dose_reduction", "all-cause", 43, 184, 23.4),
        ("Drug-related TEAEs leading to dose reduction", "adverse_event_dose_reduction", "all grades", "dose_reduction", "treatment-related", 40, 184, 21.7),
        ("TEAEs leading to dose interruption", "adverse_event_dose_interruption", "all grades", "dose_interruption", "all-cause", 65, 184, 35.3),
        ("Drug-related TEAEs leading to dose interruption", "adverse_event_dose_interruption", "all grades", "dose_interruption", "treatment-related", 53, 184, 28.8),
        ("TEAEs leading to death", "fatal_adverse_event", "all grades", "fatal", "all-cause", 9, 184, 4.9),
        ("Drug-related TEAEs leading to death", "fatal_adverse_event", "all grades", "fatal", "treatment-related", 2, 184, 1.1),
    ]
    for item in destiny:
        rows.append(row(seq, "TRIAL001", "TRIAL001_EG000", "PUB_DESTINY_APP",
                        "Supplementary Table S3, appendix p11", *item,
                        population="RP2D safety population",
                        notes="Text extracted from DESTINY-Breast01 NEJM supplement."))
        seq += 1

    # DESTINY-Breast01 ILD from Supplementary Table S5 / main narrative.
    rows.append(row(seq, "TRIAL001", "TRIAL001_EG000", "PUB_DESTINY_APP",
                    "Supplementary Table S5, appendix p15", "Interstitial lung disease (ILD)",
                    "interstitial_lung_disease_pneumonitis", "all grades", "any", "all-cause",
                    25, 184, 13.6, "RP2D safety population",
                    "Grade 3=1, Grade 4=0 in supplement; fatal adjudicated ILD described in main text.",
                    "needs_review"))
    seq += 1
    rows.append(row(seq, "TRIAL001", "TRIAL001_EG000", "PUB_DESTINY_MAIN",
                    "main text p9", "ILD deaths attributed by independent adjudication",
                    "interstitial_lung_disease_pneumonitis", "grade 5", "fatal", "treatment-related/adjudicated",
                    4, 184, 2.2, "RP2D safety population",
                    "Main text states four deaths attributed to ILD by independent adjudication.",
                    "needs_review"))
    seq += 1

    # DREAMM-2, main article safety narrative and appendix Table S1.
    dreamm = [
        ("Any adverse event", "any_adverse_event", "all grades", "any", "all-cause", 93, 95, 98.0,
         "main article p6", "2.5 mg/kg safety population"),
        ("Any adverse event", "any_adverse_event", "all grades", "any", "all-cause", 99, 99, 100.0,
         "main article p6", "3.4 mg/kg safety population"),
        ("Serious adverse events", "serious_adverse_event", "all grades", "serious", "all-cause", 38, 95, 40.0,
         "main article p7 and appendix Table S1 p10", "2.5 mg/kg safety population"),
        ("Serious adverse events", "serious_adverse_event", "all grades", "serious", "all-cause", 47, 99, 47.0,
         "main article p7 and appendix Table S1 p10", "3.4 mg/kg safety population"),
        ("Death because of serious adverse event", "fatal_adverse_event", "grade 5", "fatal", "all-cause", 3, 95, 3.0,
         "main article p7-8", "2.5 mg/kg safety population"),
        ("Death because of serious adverse event", "fatal_adverse_event", "grade 5", "fatal", "all-cause", 7, 99, 7.0,
         "main article p7-8", "3.4 mg/kg safety population"),
        ("Potentially treatment-related death", "fatal_adverse_event", "grade 5", "fatal", "potentially treatment-related", 1, 95, 1.1,
         "main article p8", "2.5 mg/kg safety population"),
        ("Potentially treatment-related death", "fatal_adverse_event", "grade 5", "fatal", "potentially treatment-related", 1, 99, 1.0,
         "main article p8", "3.4 mg/kg safety population"),
        ("Adverse events leading to dose delays", "adverse_event_dose_interruption", "all grades", "dose_delay", "all-cause", 51, 95, 54.0,
         "main article p6", "2.5 mg/kg safety population"),
        ("Adverse events leading to dose delays", "adverse_event_dose_interruption", "all grades", "dose_delay", "all-cause", 61, 99, 62.0,
         "main article p6", "3.4 mg/kg safety population"),
        ("Adverse events leading to dose reductions", "adverse_event_dose_reduction", "all grades", "dose_reduction", "all-cause", 28, 95, 29.0,
         "main article p6", "2.5 mg/kg safety population"),
        ("Adverse events leading to dose reductions", "adverse_event_dose_reduction", "all grades", "dose_reduction", "all-cause", 41, 99, 41.0,
         "main article p6", "3.4 mg/kg safety population"),
        ("Adverse events leading to permanent treatment discontinuation", "adverse_event_discontinuation", "all grades", "discontinuation", "all-cause", 8, 95, 8.0,
         "main article p6", "2.5 mg/kg safety population"),
        ("Adverse events leading to permanent treatment discontinuation", "adverse_event_discontinuation", "all grades", "discontinuation", "all-cause", 10, 99, 10.0,
         "main article p6", "3.4 mg/kg safety population"),
    ]
    for term, concept, grade, seriousness, causality, n, d, pct, locator, population in dreamm:
        arm_id = "TRIAL002_EG000" if population.startswith("2.5 mg/kg") else "TRIAL002_EG001"
        rows.append(row(seq, "TRIAL002", arm_id, "PUB_DREAMM_MAIN",
                        locator, term, concept, grade, seriousness, causality,
                        n, d, pct, population,
                        "DREAMM-2 Lancet Oncology text extraction; verify against source table/narrative before analysis.",
                        "needs_review"))
        seq += 1

    # EV-201, appendix tables A3/A4, N=125.
    ev201 = [
        ("All adverse events", "any_adverse_event", "all grades", "any", "treatment-related", 117, 125, 94.0, "Table A3"),
        ("All adverse events", "grade_3_or_higher_adverse_event", "grade >=3", "any", "treatment-related", 68, 125, 54.0, "Table A3"),
        ("All adverse events", "any_adverse_event", "all grades", "any", "all-cause", 125, 125, 100.0, "Table A4"),
        ("All adverse events", "grade_3_or_higher_adverse_event", "grade >=3", "any", "all-cause", 91, 125, 73.0, "Table A4"),
    ]
    for term, concept, grade, seriousness, causality, n, d, pct, table in ev201:
        rows.append(row(seq, "TRIAL003", "TRIAL003_EG000", "PUB_EV201_MAIN",
                        f"{table}, PDF p17", term, concept, grade, seriousness, causality,
                        n, d, pct, "safety analysis set",
                        "EV-201 appendix table in JCO PDF.", "needs_review"))
        seq += 1
    rows.append(row(seq, "TRIAL003", "TRIAL003_EG000", "PUB_EV201_MAIN",
                    "main text p7", "Treatment-related death outside safety reporting period",
                    "fatal_adverse_event", "grade 5", "fatal", "treatment-related",
                    1, 125, 0.8, "safety analysis set",
                    "Narrative says one treatment-related death occurred outside the safety reporting period and no other treatment-related deaths.",
                    "needs_manual_adjudication"))
    seq += 1

    # IMMU-132-01, supplementary Table S1, mTNBC efficacy population N=108.
    immu = [
        ("Any adverse reaction", "any_adverse_event", "all grades", "any", "all-cause", 419, 420, 100.0),
        ("Any adverse reaction grade 3", "grade_3_or_higher_adverse_event", "grade 3", "any", "all-cause", 290, 420, 69.0),
        ("Any adverse reaction grade 4", "grade_3_or_higher_adverse_event", "grade 4", "any", "all-cause", 78, 420, 19.0),
        ("Discontinued treatment due to adverse event", "adverse_event_discontinuation", "all grades", "discontinuation", "all-cause", 3, 108, 2.8),
        ("Discontinued treatment due to death", "fatal_adverse_event", "all grades", "fatal", "all-cause", 0, 108, 0.0),
    ]
    for item in immu[:3]:
        rows.append(row(seq, "TRIAL004", "TRIAL004_EG000", "PUB_IMMU_APP",
                        "Supplementary Table S3, appendix p23-24", *item,
                        population="overall safety population",
                        notes="Overall safety population includes multiple tumor types; use separately from mTNBC efficacy population.",
                        status="needs_manual_adjudication"))
        seq += 1
    for item in immu[3:]:
        rows.append(row(seq, "TRIAL004", "TRIAL004_EG000", "PUB_IMMU_APP",
                        "Supplementary Table S1, appendix p18", *item,
                        population="mTNBC efficacy population",
                        notes="Discontinuation reasons, not full AE incidence table.",
                        status="needs_review"))
        seq += 1

    # ASCENT, main Table 3 treatment-related safety population.
    ascent = [
        ("Any adverse event", "any_adverse_event", "all grades", "any", "treatment-related", 252, 258, 98.0),
        ("Any adverse event", "grade 3 adverse_event", "grade 3", "any", "treatment-related", 117, 258, 45.0),
        ("Any adverse event", "grade 4 adverse_event", "grade 4", "any", "treatment-related", 48, 258, 19.0),
        ("Serious treatment-related adverse events", "serious_adverse_event", "all grades", "serious", "treatment-related", 39, 258, 15.0),
        ("Dose reductions due to adverse events", "adverse_event_dose_reduction", "all grades", "dose_reduction", "all-cause", 57, 258, 22.0),
        ("Adverse events leading to treatment discontinuation", "adverse_event_discontinuation", "all grades", "discontinuation", "all-cause", 12, 258, 5.0),
        ("Deaths owing to adverse events", "fatal_adverse_event", "grade 5", "fatal", "all-cause", 3, 258, 1.2),
        ("Treatment-related deaths", "fatal_adverse_event", "grade 5", "fatal", "treatment-related", 0, 258, 0.0),
    ]
    for item in ascent[:3]:
        rows.append(row(seq, "TRIAL005", "TRIAL005_EG000", "PUB_ASCENT_MAIN",
                        "Table 3, main article p10", *item,
                        population="safety population, sacituzumab govitecan arm",
                        notes="Treatment-related AE table; all-cause TEAEs are in appendix Table S1 for selected events.",
                        status="needs_review"))
        seq += 1
    for item in ascent[3:]:
        rows.append(row(seq, "TRIAL005", "TRIAL005_EG000", "PUB_ASCENT_MAIN",
                        "main article safety results p5", *item,
                        population="safety population, sacituzumab govitecan arm",
                        notes="Safety narrative extraction from ASCENT main article; verify rounding before analysis.",
                        status="needs_review"))
        seq += 1

    # ALFA-0701, main article Table 4, gemtuzumab ozogamicin arm.
    alfa = [
        ("Induction death", "fatal_adverse_event", "grade 5", "fatal", "all-cause", 9, 139, 6.0,
         "Table 4, main article p7", "randomized gemtuzumab ozogamicin group"),
        ("Treatment-related death during CR or CRp", "fatal_adverse_event", "grade 5", "fatal", "treatment-related", 2, 113, 2.0,
         "Table 4, main article p7", "gemtuzumab ozogamicin responders with CR/CRp"),
        ("Grade 3 and 4 haemorrhage", "grade_3_or_higher_adverse_event", "grade 3-4", "any", "all-cause", 12, 139, 9.0,
         "Table 4, main article p7", "randomized gemtuzumab ozogamicin group"),
        ("Grade 3 and 4 cardiac adverse events", "grade_3_or_higher_adverse_event", "grade 3-4", "any", "all-cause", 11, 139, 8.0,
         "Table 4, main article p7", "randomized gemtuzumab ozogamicin group"),
        ("Grade 3 and 4 liver adverse events", "grade_3_or_higher_adverse_event", "grade 3-4", "any", "all-cause", 18, 139, 13.0,
         "Table 4, main article p7", "randomized gemtuzumab ozogamicin group"),
        ("Grade 3 and 4 skin or mucosa adverse events", "grade_3_or_higher_adverse_event", "grade 3-4", "any", "all-cause", 32, 139, 23.0,
         "Table 4, main article p7", "randomized gemtuzumab ozogamicin group"),
        ("Grade 3 and 4 gastrointestinal adverse events", "grade_3_or_higher_adverse_event", "grade 3-4", "any", "all-cause", 22, 139, 16.0,
         "Table 4, main article p7", "randomized gemtuzumab ozogamicin group"),
        ("Grade 3 and 4 pulmonary adverse events", "grade_3_or_higher_adverse_event", "grade 3-4", "any", "all-cause", 16, 139, 12.0,
         "Table 4, main article p7", "randomized gemtuzumab ozogamicin group"),
    ]
    for term, concept, grade, seriousness, causality, n, d, pct, locator, population in alfa:
        rows.append(row(seq, "TRIAL006", "TRIAL006_EG000", "PUB_ALFA_MAIN",
                        locator, term, concept, grade, seriousness, causality,
                        n, d, pct, population,
                        "ALFA-0701 Lancet Table 4 extraction. These are category-level toxicity rows, not a total any-AE row.",
                        "needs_manual_adjudication"))
        seq += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerows(rows)
    print(f"Wrote {len(rows)} publication core safety seed rows to {OUT}.")


if __name__ == "__main__":
    main()
