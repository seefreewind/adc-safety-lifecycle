#!/usr/bin/env python3
"""Build curated publication table locators for the pilot studies."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "publication_table_locator.csv"
PUB = ROOT / "data" / "raw" / "publications" / "pilot"


ROWS = [
    # DESTINY-Breast01
    ["PUBLOC0001", "PUB_DESTINY_MAIN", "ADC007", "TRIAL001", "main article", "7,10", "Table 2", "Adverse events at RP2D", "core safety outcomes; common TEAEs; ILD narrative", "high", "ready_for_extraction", "Main article table split across PDF page 10; references supplement S3-S5."],
    ["PUBLOC0002", "PUB_DESTINY_APP", "ADC007", "TRIAL001", "supplementary appendix", "11", "Supplementary Table S3", "Overall Safety of T-DXd in Patients Treated at RP2D", "core safety outcomes", "highest", "ready_for_extraction", str(PUB / "DESTINYBreast01_Modi_2019_NEJM_appendix.pdf")],
    ["PUBLOC0003", "PUB_DESTINY_APP", "ADC007", "TRIAL001", "supplementary appendix", "12-13", "Supplementary Table S4", "TEAEs in >10% of all enrolled patients", "common TEAEs all enrolled", "medium", "ready_for_extraction", str(PUB / "DESTINYBreast01_Modi_2019_NEJM_appendix.pdf")],
    ["PUBLOC0004", "PUB_DESTINY_APP", "ADC007", "TRIAL001", "supplementary appendix", "14-15", "Supplementary Table S5", "TEAEs in >10% of RP2D patients, regardless of causality", "common TEAEs; ILD", "high", "ready_for_extraction", str(PUB / "DESTINYBreast01_Modi_2019_NEJM_appendix.pdf")],
    ["PUBLOC0005", "PUB_DESTINY_APP", "ADC007", "TRIAL001", "supplementary appendix", "17-18", "Supplementary Table S6", "Guidelines for T-DXd-induced ILD", "dose modification and monitoring", "medium", "locator_only", str(PUB / "DESTINYBreast01_Modi_2019_NEJM_appendix.pdf")],

    # DREAMM-2
    ["PUBLOC0006", "PUB_DREAMM_MAIN", "ADC009", "TRIAL002", "main article", "7-11", "Table 2", "Adverse events by grade in safety population", "common TEAEs; ocular toxicity; deaths narrative", "highest", "ready_for_extraction", str(PUB / "DREAMM2_Lonial_2019_LancetOncol_PMID31859245.pdf")],
    ["PUBLOC0007", "PUB_DREAMM_APP", "ADC009", "TRIAL002", "supplementary appendix", "10-11", "Table S1", "Serious adverse events and adverse events of special interest", "SAEs; AESI; ocular toxicity; thrombocytopenia; infusion reactions", "highest", "ready_for_extraction", str(PUB / "DREAMM2_Lonial_2019_LancetOncol_appendix.pdf")],
    ["PUBLOC0008", "PUB_DREAMM_APP", "ADC009", "TRIAL002", "supplementary appendix", "46-49", "Protocol Tables 7-9", "Dose modification guidelines", "dose modification rules; corneal-related AE management", "medium", "locator_only", str(PUB / "DREAMM2_Lonial_2019_LancetOncol_appendix.pdf")],

    # EV-201
    ["PUBLOC0009", "PUB_EV201_MAIN", "ADC006", "TRIAL003", "main article", "4-5", "Safety section", "Safety narrative", "core safety narrative; composite events; discontinuation/death narrative", "high", "ready_for_extraction", str(PUB / "EV201_Rosenberg_2019_JCO_PMID31356140.pdf")],
    ["PUBLOC0010", "PUB_EV201_MAIN", "ADC006", "TRIAL003", "main article", "17", "Table A3", "Treatment-related AEs occurring in >=10% of patients", "treatment-related common AEs", "high", "ready_for_extraction", str(PUB / "EV201_Rosenberg_2019_JCO_PMID31356140.pdf")],
    ["PUBLOC0011", "PUB_EV201_MAIN", "ADC006", "TRIAL003", "main article", "17", "Table A4", "All AEs occurring in >=10% of patients", "all-cause common AEs", "high", "ready_for_extraction", str(PUB / "EV201_Rosenberg_2019_JCO_PMID31356140.pdf")],
    ["PUBLOC0012", "PUB_EV201_MAIN", "ADC006", "TRIAL003", "main article", "18-22", "Tables A5-A6", "Composite AE search terms and time-to-event summary", "AESI definitions and timing", "medium", "locator_only", str(PUB / "EV201_Rosenberg_2019_JCO_PMID31356140.pdf")],

    # IMMU-132-01
    ["PUBLOC0013", "PUB_IMMU_MAIN", "ADC008", "TRIAL004", "main article", "7-8", "Safety section/Table 2", "Safety and common adverse events in mTNBC efficacy population", "core safety narrative; common AEs", "highest", "ready_for_extraction", str(PUB / "IMMU13201_Bardia_2019_NEJM_PMID30786188.pdf")],
    ["PUBLOC0014", "PUB_IMMU_APP", "ADC008", "TRIAL004", "supplementary appendix", "18-19", "Table S1", "Treatment discontinuation in overall safety and mTNBC populations", "discontinuation reasons including AE/death", "highest", "ready_for_extraction", str(PUB / "IMMU13201_Bardia_2019_NEJM_appendix.pdf")],
    ["PUBLOC0015", "PUB_IMMU_APP", "ADC008", "TRIAL004", "supplementary appendix", "23-24", "Table S3", "AEs in >=10% by worst CTCAE grade in overall safety population", "common AEs; grade distribution", "high", "ready_for_extraction", str(PUB / "IMMU13201_Bardia_2019_NEJM_appendix.pdf")],
    ["PUBLOC0016", "PUB_IMMU_APP", "ADC008", "TRIAL004", "supplementary appendix", "25", "Table S4", "AEs of special interest by UGT1A1 genotype", "UGT1A1 safety subgroup", "medium", "locator_only", str(PUB / "IMMU13201_Bardia_2019_NEJM_appendix.pdf")],

    # ASCENT
    ["PUBLOC0017", "PUB_ASCENT_MAIN", "ADC008", "TRIAL005", "main article", "10", "Table 3", "Treatment-related AEs in safety population", "core treatment-related safety; common AEs", "highest", "ready_for_extraction", str(PUB / "ASCENT_Bardia_2021_NEJM_PMID33882206.pdf")],
    ["PUBLOC0018", "PUB_ASCENT_APP", "ADC008", "TRIAL005", "supplementary appendix", "27-28", "Table S1", "TEAEs any grade >=10% and grade >=3 >=5%", "all-cause TEAEs; common AEs", "highest", "ready_for_extraction", str(PUB / "ASCENT_Bardia_2021_NEJM_appendix.pdf")],
    ["PUBLOC0019", "PUB_ASCENT_APP", "ADC008", "TRIAL005", "supplementary appendix", "26", "Figure S8", "Dose modifications for neutropenia and non-neutropenic toxicity", "dose modification rules", "medium", "locator_only", str(PUB / "ASCENT_Bardia_2021_NEJM_appendix.pdf")],

    # ALFA-0701
    ["PUBLOC0020", "PUB_ALFA_MAIN", "ADC001", "TRIAL006", "main article", "5,7", "Tables 2-4", "Outcomes and grade 3-4 adverse events", "death; severe hematologic/nonhematologic AEs; hemorrhage; VOD/SOS", "highest", "needs_manual_table_review", str(PUB / "ALFA0701_Castaigne_2012_Lancet_PMID22482940.pdf")],
    ["PUBLOC0021", "PUB_ALFA_APP", "ADC001", "TRIAL006", "supplementary appendix", "1-16", "Supplementary appendix", "Definitions and historical comparison", "definitions; limited direct AE numeric extraction", "low", "locator_only", str(PUB / "ALFA0701_Castaigne_2012_Lancet_appendix.pdf")],
]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "locator_id", "document_id", "drug_id", "trial_id", "publication_part",
            "page", "table_or_figure", "title", "safety_topic", "priority",
            "extraction_status", "notes",
        ])
        writer.writerows(ROWS)
    print(f"Wrote {len(ROWS)} publication table locator rows to {OUT}.")


if __name__ == "__main__":
    main()

