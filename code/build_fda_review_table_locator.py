#!/usr/bin/env python3
"""Create FDA review table locator rows for the pilot ADC safety project."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "fda_review_table_locator.csv"

HEADER = [
    "locator_id",
    "document_id",
    "drug_id",
    "trial_id",
    "page",
    "section",
    "table_number",
    "table_title",
    "safety_topic",
    "priority",
    "extraction_status",
    "notes",
]


ROWS = [
    # Enhertu / DESTINY-Breast01 approval review.
    ("FDALOC000001", "FDA_ADC007_MDR_761139_ORIG1", "ADC007", "TRIAL001", "171", "Review of Safety", "Table 33", "Summary of Deaths in the Primary Studies", "deaths", "high", "seed_extracted", "HER2-positive breast cancer 5.4 mg/kg pool; not limited to DESTINY-Breast01 N=184."),
    ("FDALOC000002", "FDA_ADC007_MDR_761139_ORIG1", "ADC007", "TRIAL001", "174", "Review of Safety", "Table 35", "Serious Adverse Events in the Primary Studies, by Preferred Term", "serious adverse events", "high", "seed_extracted", "HER2-positive breast cancer 5.4 mg/kg pool."),
    ("FDALOC000003", "FDA_ADC007_MDR_761139_ORIG1", "ADC007", "TRIAL001", "176", "Review of Safety", "Table 37", "Adverse Events Associated with Study Drug Discontinuation", "discontinuation", "high", "seed_extracted", "HER2-positive breast cancer 5.4 mg/kg pool."),
    ("FDALOC000004", "FDA_ADC007_MDR_761139_ORIG1", "ADC007", "TRIAL001", "177", "Review of Safety", "Table 38", "Adverse Events Associated with Dose Interruption", "dose interruption", "high", "seed_extracted", "HER2-positive breast cancer 5.4 mg/kg pool."),
    ("FDALOC000005", "FDA_ADC007_MDR_761139_ORIG1", "ADC007", "TRIAL001", "179", "Review of Safety", "Table 39", "Adverse Events Associated with Dose Reduction", "dose reduction", "high", "seed_extracted", "HER2-positive breast cancer 5.4 mg/kg pool."),
    ("FDALOC000006", "FDA_ADC007_MDR_761139_ORIG1", "ADC007", "TRIAL001", "183", "Review of Safety", "Table 41", "Most Common Adverse Events, by Preferred Term", "any TEAE", "high", "seed_extracted", "HER2-positive breast cancer 5.4 mg/kg pool."),
    ("FDALOC000007", "FDA_ADC007_MDR_761139_ORIG1", "ADC007", "TRIAL001", "185", "Review of Safety", "Table 42", "Adverse Events of at Least Grade 3, by Preferred Term", "grade >=3 adverse events", "high", "seed_extracted", "HER2-positive breast cancer 5.4 mg/kg pool."),

    # Trodelvy / IMMU-132-01 approval review.
    ("FDALOC000008", "FDA_ADC008_MDR_761115_ORIG1", "ADC008", "TRIAL004", "73", "Review of Safety", "Table 22", "Death Narratives from IMMU-132-01 for the mTNBC Population", "deaths", "medium", "located", "Narrative source; aggregate fatal AE requires adjudication."),
    ("FDALOC000009", "FDA_ADC008_MDR_761115_ORIG1", "ADC008", "TRIAL004", "85", "Review of Safety", "Table 24", "Serious Adverse Events in >2% of patients in IMMU-132-01", "serious adverse events", "high", "seed_extracted", "Includes overall safety population and mTNBC efficacy cohort."),
    ("FDALOC000010", "FDA_ADC008_MDR_761115_ORIG1", "ADC008", "TRIAL004", "87", "Review of Safety", "text", "Dose reductions and discontinuations due to adverse effects", "dose reduction; discontinuation", "high", "seed_extracted", "Dose reduction denominator is mTNBC cohort N=108; count not explicitly reported."),
    ("FDALOC000011", "FDA_ADC008_MDR_761115_ORIG1", "ADC008", "TRIAL004", "88", "Review of Safety", "text", "Significant Adverse Events", "grade 3-4 adverse events", "high", "seed_extracted", "Provides aggregate grade 3/4 AE incidence for overall and mTNBC cohorts."),
    ("FDALOC000012", "FDA_ADC008_MDR_761115_ORIG1", "ADC008", "TRIAL004", "88", "Review of Safety", "Table 25", "Most Common Adverse Events in IMMU-132-01", "any AE; grade 3-4 AE", "high", "seed_extracted", "Includes all-grade and grade 3-4 any adverse event rows."),

    # Blenrep / DREAMM-2 approval review.
    ("FDALOC000013", "FDA_ADC009_MDR_761158_ORIG1", "ADC009", "TRIAL002", "147", "Review of Safety", "Table 26", "Summary of Deaths", "deaths", "high", "located", "DREAMM-1/DREAMM-2 pooled safety population."),
    ("FDALOC000014", "FDA_ADC009_MDR_761158_ORIG1", "ADC009", "TRIAL002", "148", "Review of Safety", "Table 27", "Overview of TEAEs in DREAMM-2", "core safety overview", "high", "seed_extracted", "Directly reports core TEAE categories by DREAMM-2 dose cohort."),
    ("FDALOC000015", "FDA_ADC009_MDR_761158_ORIG1", "ADC009", "TRIAL002", "148", "Review of Safety", "Table 28", "Summary of Fatal TEAEs in DREAMM-2", "fatal TEAEs", "high", "seed_extracted", "Directly reports fatal TEAEs by dose cohort."),
    ("FDALOC000016", "FDA_ADC009_MDR_761158_ORIG1", "ADC009", "TRIAL002", "149", "Review of Safety", "Table 30", "Summary of Serious TEAEs in DREAMM-2", "serious TEAEs", "high", "located", "Preferred-term detail."),
    ("FDALOC000017", "FDA_ADC009_MDR_761158_ORIG1", "ADC009", "TRIAL002", "150", "Review of Safety", "Table 31", "AEs Leading to Permanent Discontinuation", "discontinuation", "high", "located", "Preferred-term detail."),
    ("FDALOC000018", "FDA_ADC009_MDR_761158_ORIG1", "ADC009", "TRIAL002", "151", "Review of Safety", "Table 32", "AEs Leading to Dose Reduction", "dose reduction", "high", "located", "Preferred-term detail."),
    ("FDALOC000019", "FDA_ADC009_MDR_761158_ORIG1", "ADC009", "TRIAL002", "152", "Review of Safety", "Table 33", "AEs Leading to Dose Delay", "dose interruption/delay", "high", "located", "Preferred-term detail."),
    ("FDALOC000020", "FDA_ADC009_MDR_761158_ORIG1", "ADC009", "TRIAL002", "154", "Review of Safety", "Table 35", "TEAEs in DREAMM-2", "common TEAEs", "medium", "located", "Preferred-term detail."),
    ("FDALOC000021", "FDA_ADC009_MDR_761158_ORIG1", "ADC009", "TRIAL002", "156", "Review of Safety", "Table 38", "Grade 3+4 AEs", "grade 3-4 TEAEs", "medium", "located", "Preferred-term detail."),

    # Mylotarg / ALFA-0701 medical review.
    ("FDALOC000022", "FDA_ADC001_MEDR_761060_ORIG1", "ADC001", "TRIAL006", "74", "Review of Safety", "text", "Safety assessment limitations and retrospective AE collection for ALFA-0701", "source comparability", "high", "located", "Explains why ALFA-0701 lacks modern all-grade AE capture."),
    ("FDALOC000023", "FDA_ADC001_MEDR_761060_ORIG1", "ADC001", "TRIAL006", "76", "Review of Safety", "text", "Major safety results and deaths", "deaths", "high", "located", "Text source; table images are not fully text-extractable."),
    ("FDALOC000024", "FDA_ADC001_MEDR_761060_ORIG1", "ADC001", "TRIAL006", "80", "Review of Safety", "text", "Fatal treatment-related adverse events and predefined grade 3-4 TEAEs", "fatal AE; grade 3-4 AE", "high", "located", "Useful for adjudication; not a complete modern AE overview."),

    # Padcev current gap.
    ("FDALOC000025", "FDA_ADC006_CHEMR_761137_ORIG1", "ADC006", "TRIAL003", "", "Chemistry Review", "none", "No clinical safety table located in supplied chemistry review", "missing clinical FDA review", "high", "blocked", "Need Padcev BLA 761137 original approval multi-discipline or medical review for FDA safety extraction."),
]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerows(ROWS)
    print(f"Wrote {len(ROWS)} FDA table locator rows to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
