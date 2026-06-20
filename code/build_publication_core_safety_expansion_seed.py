#!/usr/bin/env python3
"""Build manually verified publication core-safety seed rows for expansion trials."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
PROTOCOL = ROOT / "protocol"
OUT = INTERIM / "publication_core_safety_expansion_seed.csv"

HEADER = [
    "observation_id",
    "trial_id",
    "arm_id",
    "document_id",
    "source_type",
    "page_or_table_locator",
    "ae_original_term",
    "ae_standardized_term",
    "meddra_pt",
    "meddra_soc",
    "smq",
    "safety_concept",
    "grade_category",
    "seriousness",
    "causality",
    "number_events",
    "number_patients",
    "denominator",
    "percentage",
    "reporting_threshold",
    "analysis_population",
    "data_cutoff_date",
    "extractor",
    "review_status",
    "notes",
]


def obs(seq: int, **kwargs: object) -> dict[str, str]:
    row = {key: "" for key in HEADER}
    row.update({
        "observation_id": f"PUBEXP{seq:05d}",
        "source_type": "primary publication/supplement",
        "meddra_pt": "",
        "meddra_soc": "",
        "smq": "",
        "number_events": "",
        "reporting_threshold": "",
        "data_cutoff_date": "",
        "extractor": "script:build_publication_core_safety_expansion_seed.py",
        "review_status": "needs_review",
    })
    for key, value in kwargs.items():
        row[key] = "" if value is None else str(value)
    return row


def add(rows: list[dict[str, str]], **kwargs: object) -> None:
    rows.append(obs(len(rows) + 1, **kwargs))


def main() -> None:
    rows: list[dict[str, str]] = []

    # INO-VATE ALL. Publication safety denominators differ from CT.gov AE-module denominators.
    ino_notes = "INO-VATE ALL Supplementary Table S1; publication denominators differ from CT.gov AE module safety populations (CT.gov InO 164, investigator choice 143), so cross-source comparability requires manual grading."
    for arm_id, denom, values in [
        ("TRIAL010_PUB_INO", 139, [(136, 98, "Any AE", "all grades", "all-cause"), (126, 91, "Any AE", "grade >=3", "all-cause"), (119, 86, "Treatment-related Any AE", "all grades", "treatment-related"), (96, 69, "Treatment-related Any AE", "grade >=3", "treatment-related")]),
        ("TRIAL010_PUB_STANDARD_CHEMOTHERAPY", 120, [(119, 99, "Any AE", "all grades", "all-cause"), (114, 95, "Any AE", "grade >=3", "all-cause"), (109, 91, "Treatment-related Any AE", "all grades", "treatment-related"), (93, 78, "Treatment-related Any AE", "grade >=3", "treatment-related")]),
    ]:
        for n, pct, term, grade, causality in values:
            add(rows, trial_id="TRIAL010", arm_id=arm_id, document_id="EXPUB_TRIAL010_0001", page_or_table_locator="Supplementary Table S1, appendix p12/page_or_unit 13", ae_original_term=term, ae_standardized_term=term, safety_concept="any_adverse_event", grade_category=grade, seriousness="any", causality=causality, number_patients=n, denominator=denom, percentage=pct, analysis_population="publication safety population in Supplementary Table S1", notes=ino_notes)

    # innovaTV 204 single-arm supplement.
    tv204_notes = "innovaTV 204 supplement; single-arm safety population N=101."
    for n, pct, term, concept, grade, seriousness, causality, locator in [
        (101, 100, "Patients with >=1 AE", "any_adverse_event", "all grades", "any", "all-cause", "Supplementary Table S5, page_or_unit 23"),
        (61, 60, "Patients with >=1 AE", "grade_3_or_higher_adverse_event", "grade >=3", "any", "all-cause", "Supplementary Table S5, page_or_unit 23"),
        (13, 13, "Patients with >=1 treatment-related serious AE", "serious_adverse_event", "all grades", "serious", "treatment-related", "Supplementary Table S3, page_or_unit 20"),
        (12, 12, "Patients with TRAEs leading to treatment discontinuation", "adverse_event_leading_to_discontinuation", "all grades", "any", "treatment-related", "Supplementary Table S4, page_or_unit 21"),
    ]:
        add(rows, trial_id="TRIAL013", arm_id="TRIAL013_EG000", document_id="EXPUB_TRIAL013_0001", page_or_table_locator=locator, ae_original_term=term, ae_standardized_term=term, safety_concept=concept, grade_category=grade, seriousness=seriousness, causality=causality, number_patients=n, denominator=101, percentage=pct, analysis_population="publication safety population", notes=tv204_notes)

    # innovaTV 301 randomized trial.
    tv301_notes = "innovaTV 301 supplement; most rows use safety population TV N=250 and chemotherapy N=239. Fatal-event table uses death-summary denominator TV N=253 and chemotherapy N=249."
    for arm_id, denom, vals in [
        ("TRIAL014_EG000", 250, [(219, 87.6, "Treatment-related adverse event", "any_adverse_event", "all grades", "any", "treatment-related", "Supplementary Table S6, page_or_unit 35"), (73, 29.2, "Treatment-related adverse event", "grade_3_or_higher_adverse_event", "grade >=3", "any", "treatment-related", "Supplementary Table S6, page_or_unit 35"), (82, 32.8, "Patients with >=1 treatment-emergent serious adverse event", "serious_adverse_event", "all grades", "serious", "all-cause", "Supplementary Table S7, page_or_unit 36"), (37, 14.8, "Patients with permanent treatment discontinuation", "adverse_event_leading_to_discontinuation", "all grades", "any", "all-cause", "Supplementary Table S5, page_or_unit 32"), (133, 53.2, "Patients with any dose modification", "dose_modification", "all grades", "any", "all-cause", "Supplementary Table S5, page_or_unit 32")]),
        ("TRIAL014_EG001", 239, [(204, 85.4, "Treatment-related adverse event", "any_adverse_event", "all grades", "any", "treatment-related", "Supplementary Table S6, page_or_unit 35"), (108, 45.2, "Treatment-related adverse event", "grade_3_or_higher_adverse_event", "grade >=3", "any", "treatment-related", "Supplementary Table S6, page_or_unit 35"), (94, 39.3, "Patients with >=1 treatment-emergent serious adverse event", "serious_adverse_event", "all grades", "serious", "all-cause", "Supplementary Table S7, page_or_unit 36"), (9, 3.8, "Patients with permanent treatment discontinuation", "adverse_event_leading_to_discontinuation", "all grades", "any", "all-cause", "Supplementary Table S5, page_or_unit 32"), (136, 56.9, "Patients with any dose modification", "dose_modification", "all grades", "any", "all-cause", "Supplementary Table S5, page_or_unit 32")]),
    ]:
        for n, pct, term, concept, grade, seriousness, causality, locator in vals:
            add(rows, trial_id="TRIAL014", arm_id=arm_id, document_id="EXPUB_TRIAL014_0001", page_or_table_locator=locator, ae_original_term=term, ae_standardized_term=term, safety_concept=concept, grade_category=grade, seriousness=seriousness, causality=causality, number_patients=n, denominator=denom, percentage=pct, analysis_population="publication safety population", notes=tv301_notes)
    for arm_id, denom, n, pct in [("TRIAL014_PUB_TV_DEATH_SUMMARY", 253, 4, 1.6), ("TRIAL014_PUB_CHEMO_DEATH_SUMMARY", 249, 5, 2.0)]:
        add(rows, trial_id="TRIAL014", arm_id=arm_id, document_id="EXPUB_TRIAL014_0001", page_or_table_locator="Supplementary Table S8, page_or_unit 37", ae_original_term="Fatal adverse event", ae_standardized_term="Fatal adverse event", safety_concept="fatal_adverse_event", grade_category="grade 5", seriousness="fatal", causality="all-cause", number_patients=n, denominator=denom, percentage=pct, analysis_population="publication death-summary population", notes=tv301_notes)

    # MIRASOL dose-modification rows. Overall AE overview is not in the current high-confidence snippets.
    mirasol_notes = "MIRASOL supplement Table S2 reports AEs leading to dose reduction or dose delay/hold; denominators in this table (MIRV 218, chemotherapy 207) differ from CT.gov arm denominators (227, 226)."
    for arm_id, denom, vals in [
        ("TRIAL016_PUB_MIRV_TABLES2", 218, [(74, 34, "Adverse events leading to dose reduction", "dose_reduction"), (117, 54, "Adverse events leading to dose delay/hold", "dose_interruption")]),
        ("TRIAL016_PUB_CHEMO_TABLES2", 207, [(50, 24, "Adverse events leading to dose reduction", "dose_reduction"), (111, 54, "Adverse events leading to dose delay/hold", "dose_interruption")]),
    ]:
        for n, pct, term, concept in vals:
            add(rows, trial_id="TRIAL016", arm_id=arm_id, document_id="EXPUB_TRIAL016_0001", page_or_table_locator="Supplementary Table S2, page_or_unit 26", ae_original_term=term, ae_standardized_term=term, safety_concept=concept, grade_category="all grades", seriousness="any", causality="all-cause", number_patients=n, denominator=denom, percentage=pct, analysis_population="publication supplement Table S2 population", notes=mirasol_notes)

    # DREAMM-7 main article safety table.
    dreamm7_notes = "DREAMM-7 main article Table 3; randomized safety population BVd N=242, DVd N=246. FDA original DREAMM-2 review is not used as a DREAMM-7 numeric comparator."
    for arm_id, denom, values in [
        ("TRIAL017_EG000", 242, [(242, 100, "Any adverse event", "all grades"), (230, 95, "Any adverse event", "grade >=3")]),
        ("TRIAL017_EG001", 246, [(246, 100, "Any adverse event", "all grades"), (192, 78, "Any adverse event", "grade >=3")]),
    ]:
        for n, pct, term, grade in values:
            add(rows, trial_id="TRIAL017", arm_id=arm_id, document_id="EXPUB_TRIAL017_0001", page_or_table_locator="Main article Table 3, page_or_unit 11", ae_original_term=term, ae_standardized_term=term, safety_concept="any_adverse_event" if grade == "all grades" else "grade_3_or_higher_adverse_event", grade_category=grade, seriousness="any", causality="all-cause", number_patients=n, denominator=denom, percentage=pct, analysis_population="publication safety population", notes=dreamm7_notes)

    # DREAMM-8 main article safety table.
    dreamm8_notes = "DREAMM-8 main article Table 3; randomized safety population BPd N=150, PVd N=145. Serious AE, discontinuation, dose-reduction, fatal AE, and dose-delay percentages are reported in text/Table S12-S13 but not all corresponding counts are visible in the main article text layer, so only clear Table 3 n(%) rows are seeded here."
    for arm_id, denom, values in [
        ("TRIAL018_PUB_BPD", 150, [(149, 99, "Any adverse event", "all grades"), (141, 94, "Any adverse event", "grade >=3")]),
        ("TRIAL018_PUB_PVD", 145, [(139, 96, "Any adverse event", "all grades"), (110, 76, "Any adverse event", "grade >=3")]),
    ]:
        for n, pct, term, grade in values:
            add(rows, trial_id="TRIAL018", arm_id=arm_id, document_id="EXPUB_TRIAL018_0001", page_or_table_locator="Main article Table 3, page_or_unit 10", ae_original_term=term, ae_standardized_term=term, safety_concept="any_adverse_event" if grade == "all grades" else "grade_3_or_higher_adverse_event", grade_category=grade, seriousness="any", causality="all-cause", number_patients=n, denominator=denom, percentage=pct, analysis_population="publication safety population", notes=dreamm8_notes)

    # TROPION-Breast02 TRAE overview.
    tropion_b02_notes = "TROPION-Breast02 main article Table 3 reports treatment-related adverse events in the safety population; CT.gov AE module is unavailable."
    for arm_id, denom, vals in [
        ("TRIAL022_PUB_DATODXD", 319, [(296, 93, "Any TRAE", "any_adverse_event", "all grades", "any"), (105, 33, "Grade >=3 TRAE", "grade_3_or_higher_adverse_event", "grade >=3", "any"), (29, 9, "Serious TRAE", "serious_adverse_event", "all grades", "serious"), (76, 24, "TRAE associated with dose interruption", "dose_interruption", "all grades", "any"), (85, 27, "TRAE associated with dose reduction", "dose_reduction", "all grades", "any"), (14, 4, "TRAE associated with treatment discontinuation", "adverse_event_leading_to_discontinuation", "all grades", "any"), (0, 0, "TRAE associated with death", "fatal_adverse_event", "grade 5", "fatal")]),
        ("TRIAL022_PUB_CHEMOTHERAPY", 309, [(257, 83, "Any TRAE", "any_adverse_event", "all grades", "any"), (89, 29, "Grade >=3 TRAE", "grade_3_or_higher_adverse_event", "grade >=3", "any"), (26, 8, "Serious TRAE", "serious_adverse_event", "all grades", "serious"), (60, 19, "TRAE associated with dose interruption", "dose_interruption", "all grades", "any"), (56, 18, "TRAE associated with dose reduction", "dose_reduction", "all grades", "any"), (23, 7, "TRAE associated with treatment discontinuation", "adverse_event_leading_to_discontinuation", "all grades", "any"), (0, 0, "TRAE associated with death", "fatal_adverse_event", "grade 5", "fatal")]),
    ]:
        for n, pct, term, concept, grade, seriousness in vals:
            add(rows, trial_id="TRIAL022", arm_id=arm_id, document_id="EXPUB_TRIAL022_0001", page_or_table_locator="Main article Table 3, page_or_unit 37", ae_original_term=term, ae_standardized_term=term, safety_concept=concept, grade_category=grade, seriousness=seriousness, causality="treatment-related", number_patients=n, denominator=denom, percentage=pct, analysis_population="publication safety population", notes=tropion_b02_notes)

    # LUMINOSITY target approval cohort.
    luminosity_notes = "LUMINOSITY accepted manuscript and Appendix Table A5; seeded rows are for the non-squamous EGFR-wildtype NSCLC cohort (N=172), the approval-relevant population. CT.gov AE module is unavailable."
    for n, pct, term, concept, grade, causality, seriousness, locator in [
        (167, 97.1, "Adverse event", "any_adverse_event", "all grades", "all-cause", "any", "Appendix Table A5, page_or_unit 47"),
        (97, 56.4, "Adverse event", "grade_3_or_higher_adverse_event", "grade >=3", "all-cause", "any", "Appendix Table A5, page_or_unit 47"),
        (140, 81.4, "Treatment-related adverse event", "any_adverse_event", "all grades", "treatment-related", "any", "Appendix Table A5, page_or_unit 47"),
        (48, 27.9, "Treatment-related adverse event", "grade_3_or_higher_adverse_event", "grade >=3", "treatment-related", "any", "Appendix Table A5, page_or_unit 47"),
        (2, 1.2, "Possibly related grade 5 adverse event", "fatal_adverse_event", "grade 5", "treatment-related", "fatal", "Main article safety text, page_or_unit 15"),
    ]:
        add(rows, trial_id="TRIAL021", arm_id="TRIAL021_PUB_NSQ_EGFR_WT", document_id="EXPUB_TRIAL021_0001", page_or_table_locator=locator, ae_original_term=term, ae_standardized_term=term, safety_concept=concept, grade_category=grade, seriousness=seriousness, causality=causality, number_patients=n, denominator=172, percentage=pct, analysis_population="publication non-squamous EGFR-wildtype NSCLC safety population", notes=luminosity_notes)

    # LOTIS-2 supplement Table S9.
    lotis2_notes = "LOTIS-2 supplementary Table S9; as-treated population N=145. This table provides TEAE overview rather than preferred-term detail."
    for n, pct, term, concept, grade, seriousness, causality in [
        (143, 98.6, "Any TEAE", "any_adverse_event", "all grades", "any", "all-cause"),
        (105, 72.4, "Any Grade >=3 TEAE", "grade_3_or_higher_adverse_event", "grade >=3", "any", "all-cause"),
        (117, 80.7, "Any TEAE related to loncastuximab tesirine", "any_adverse_event", "all grades", "any", "treatment-related"),
        (75, 51.7, "Any TEAE leading to dose delay or reduction", "dose_modification", "all grades", "any", "all-cause"),
        (34, 23.4, "Any TEAE leading to loncastuximab tesirine discontinuation", "adverse_event_leading_to_discontinuation", "all grades", "any", "all-cause"),
        (57, 39.3, "Any serious TEAE", "serious_adverse_event", "all grades", "serious", "all-cause"),
        (8, 5.5, "Any TEAE with fatal outcome", "fatal_adverse_event", "grade 5", "fatal", "all-cause"),
    ]:
        add(rows, trial_id="TRIAL012", arm_id="TRIAL012_PUB_LONCASTUXIMAB", document_id="EXPUB_TRIAL012_0001", page_or_table_locator="Supplementary Table S9, page_or_unit 22", ae_original_term=term, ae_standardized_term=term, safety_concept=concept, grade_category=grade, seriousness=seriousness, causality=causality, number_patients=n, denominator=145, percentage=pct, analysis_population="publication as-treated population", notes=lotis2_notes)

    # TROPION-Breast01 main article summary text.
    tropion_b01_notes = "TROPION-Breast01 main article safety text; safety populations Dato-DXd N=360 and ICC N=351. Several overview rows are reported as percentages only in the accessible text layer, so number_patients is intentionally left blank."
    for arm_id, denom, vals in [
        ("TRIAL019_PUB_DATODXD", 360, [(None, 93.6, "TRAEs occurred", "any_adverse_event", "all grades", "any"), (None, 20.8, "Grade >=3 TRAEs", "grade_3_or_higher_adverse_event", "grade >=3", "any"), (None, 5.8, "Serious TRAEs", "serious_adverse_event", "all grades", "serious")]),
        ("TRIAL019_PUB_ICC", 351, [(None, 86.3, "TRAEs occurred", "any_adverse_event", "all grades", "any"), (None, 44.7, "Grade >=3 TRAEs", "grade_3_or_higher_adverse_event", "grade >=3", "any"), (None, 9.1, "Serious TRAEs", "serious_adverse_event", "all grades", "serious")]),
    ]:
        for n, pct, term, concept, grade, seriousness in vals:
            add(rows, trial_id="TRIAL019", arm_id=arm_id, document_id="EXPUB_TRIAL019_0001", page_or_table_locator="Main article safety text, page_or_unit 7", ae_original_term=term, ae_standardized_term=term, safety_concept=concept, grade_category=grade, seriousness=seriousness, causality="treatment-related", number_patients=n, denominator=denom, percentage=pct, analysis_population="publication safety population", notes=tropion_b01_notes)

    # TROPION-Lung05 main article Table 3 and safety text.
    tropion_l05_notes = "TROPION-Lung05 main article Table 3/safety text; safety population N=137. Overview is treatment-related and single-arm."
    for n, pct, term, concept, grade, seriousness in [
        (129, 94.2, "TRAEs", "any_adverse_event", "all grades", "any"),
        (39, 28.5, "Grade >=3 TRAEs", "grade_3_or_higher_adverse_event", "grade >=3", "any"),
        (27, 19.7, "Dose reductions because of TRAEs", "dose_reduction", "all grades", "any"),
        (29, 21.2, "Dose delays because of TRAEs", "dose_interruption", "all grades", "any"),
        (7, 5.1, "Discontinuations because of TRAEs", "adverse_event_leading_to_discontinuation", "all grades", "any"),
        (1, 0.7, "Treatment-related ILD/pneumonitis grade 5", "fatal_adverse_event", "grade 5", "fatal"),
    ]:
        add(rows, trial_id="TRIAL020", arm_id="TRIAL020_PUB_DATODXD", document_id="EXPUB_TRIAL020_0001", page_or_table_locator="Main article Table 3 and safety text, page_or_unit 4/9", ae_original_term=term, ae_standardized_term=term, safety_concept=concept, grade_category=grade, seriousness=seriousness, causality="treatment-related", number_patients=n, denominator=137, percentage=pct, analysis_population="publication safety population", notes=tropion_l05_notes)

    # CADENZA main article Table 3 and data supplement Table S7.
    cadenza_notes = "CADENZA Table 3/Supplementary Table S7; seeded total BPDCN safety population rows (N=84). This ADC-like agent remains definition-review flagged in the project cohort."
    for n, pct, term, concept, grade, seriousness, causality, locator in [
        (83, 99, "Any AE", "any_adverse_event", "all grades", "any", "all-cause", "Main article Table 3, page_or_unit 9"),
        (61, 73, "Drug-related AE", "any_adverse_event", "all grades", "any", "treatment-related", "Main article Table 3, page_or_unit 9"),
        (66, 79, "Any grade >=3 AE", "grade_3_or_higher_adverse_event", "grade >=3", "any", "all-cause", "Main article Table 3, page_or_unit 9"),
        (30, 36, "Drug-related grade >=3 AE", "grade_3_or_higher_adverse_event", "grade >=3", "any", "treatment-related", "Main article Table 3, page_or_unit 9"),
        (43, 51, "Any serious AE", "serious_adverse_event", "all grades", "serious", "all-cause", "Main article Table 3, page_or_unit 9"),
        (20, 24, "Drug-related serious AE", "serious_adverse_event", "all grades", "serious", "treatment-related", "Main article Table 3, page_or_unit 9"),
        (21, 25, "Any events leading to dose delay", "dose_interruption", "all grades", "any", "all-cause", "Supplementary Table S7, page_or_unit 26"),
    ]:
        add(rows, trial_id="TRIAL023", arm_id="TRIAL023_PUB_TOTAL_BPDCN", document_id="EXPUB_TRIAL023_0001", page_or_table_locator=locator, ae_original_term=term, ae_standardized_term=term, safety_concept=concept, grade_category=grade, seriousness=seriousness, causality=causality, number_patients=n, denominator=84, percentage=pct, analysis_population="publication total BPDCN safety population", notes=cadenza_notes)

    # Early/legacy publication partial safety summaries.
    brentux_hl_notes = "SG035-0003 Hodgkin lymphoma main article safety text; safety population N=102. Some rows are reported as percentages only, so number_patients is left blank when not directly reported."
    for n, pct, term, concept, grade, seriousness in [
        (None, 55, "Adverse events of grade 3 or higher", "grade_3_or_higher_adverse_event", "grade >=3", "any"),
        (20, 19.6, "Adverse events leading to treatment discontinuation", "adverse_event_leading_to_discontinuation", "all grades", "any"),
        (None, 47, "Doses delayed because of adverse events", "dose_interruption", "all grades", "any"),
        (11, 10.8, "Doses reduced because of adverse events", "dose_reduction", "all grades", "any"),
        (0, 0, "Deaths attributed to study drug", "fatal_adverse_event", "grade 5", "fatal"),
    ]:
        add(rows, trial_id="TRIAL007", arm_id="TRIAL007_PUB_BRENTUXIMAB", document_id="EXPUB_TRIAL007_0001", page_or_table_locator="Main article safety text, page_or_unit 4", ae_original_term=term, ae_standardized_term=term, safety_concept=concept, grade_category=grade, seriousness=seriousness, causality="all-cause" if concept != "fatal_adverse_event" else "treatment-related", number_patients=n, denominator=102, percentage=pct, analysis_population="publication safety population", notes=brentux_hl_notes)

    brentux_alcl_notes = "SG035-0004 systemic ALCL main article safety text/Table 3; safety population N=58. Some rows are reported as percentages only, so number_patients is left blank when not directly reported."
    for n, pct, term, concept, grade, seriousness, causality in [
        (None, 60, "Adverse events of grade 3 or higher", "grade_3_or_higher_adverse_event", "grade >=3", "any", "all-cause"),
        (14, 24, "Adverse events leading to treatment discontinuation", "adverse_event_leading_to_discontinuation", "all grades", "any", "all-cause"),
        (None, 40, "Doses delayed because of adverse events", "dose_interruption", "all grades", "any", "all-cause"),
        (7, 12.1, "Doses reduced because of adverse events", "dose_reduction", "all grades", "any", "all-cause"),
        (6, 10.3, "Deaths within 30 days of last administration", "fatal_adverse_event", "grade 5", "fatal", "all-cause"),
        (0, 0, "Deaths attributed to study drug", "fatal_adverse_event", "grade 5", "fatal", "treatment-related"),
    ]:
        add(rows, trial_id="TRIAL008", arm_id="TRIAL008_PUB_BRENTUXIMAB", document_id="EXPUB_TRIAL008_0001", page_or_table_locator="Main article safety text/Table 3, page_or_unit 4/5", ae_original_term=term, ae_standardized_term=term, safety_concept=concept, grade_category=grade, seriousness=seriousness, causality=causality, number_patients=n, denominator=58, percentage=pct, analysis_population="publication safety population", notes=brentux_alcl_notes)

    emilia_notes = "EMILIA main article safety text; safety population T-DM1 N=490 and lapatinib-capecitabine N=488. Comparator discontinuation/dose-reduction rows are component-specific where noted."
    for arm_id, denom, vals in [
        ("TRIAL009_PUB_TDM1", 490, [(76, 15.5, "Serious adverse events", "serious_adverse_event", "all grades", "serious", "all-cause"), (None, 40.8, "Adverse events of grade 3 or 4", "grade_3_or_higher_adverse_event", "grade 3/4", "any", "all-cause"), (29, 5.9, "Treatment discontinuation because of adverse events", "adverse_event_leading_to_discontinuation", "all grades", "any", "all-cause"), (None, 16.3, "Dose reduction", "dose_reduction", "all grades", "any", "all-cause"), (1, 0.2, "Deaths attributed to adverse events within 30 days", "fatal_adverse_event", "grade 5", "fatal", "all-cause")]),
        ("TRIAL009_PUB_LAPATINIB_CAPECITABINE", 488, [(88, 18.0, "Serious adverse events", "serious_adverse_event", "all grades", "serious", "all-cause"), (None, 57.0, "Adverse events of grade 3 or 4", "grade_3_or_higher_adverse_event", "grade 3/4", "any", "all-cause"), (4, 0.8, "Deaths attributed to adverse events within 30 days", "fatal_adverse_event", "grade 5", "fatal", "all-cause")]),
        ("TRIAL009_PUB_LAPATINIB_COMPONENT", 488, [(37, 7.6, "Lapatinib discontinued because of adverse events", "adverse_event_leading_to_discontinuation", "all grades", "any", "all-cause"), (None, 27.3, "Lapatinib dose reduction", "dose_reduction", "all grades", "any", "all-cause")]),
        ("TRIAL009_PUB_CAPECITABINE_COMPONENT", 488, [(46, 9.4, "Capecitabine discontinued because of adverse events", "adverse_event_leading_to_discontinuation", "all grades", "any", "all-cause"), (None, 53.4, "Capecitabine dose reduction", "dose_reduction", "all grades", "any", "all-cause")]),
    ]:
        for n, pct, term, concept, grade, seriousness, causality in vals:
            add(rows, trial_id="TRIAL009", arm_id=arm_id, document_id="EXPUB_TRIAL009_0001", page_or_table_locator="Main article safety text, page_or_unit 6/7", ae_original_term=term, ae_standardized_term=term, safety_concept=concept, grade_category=grade, seriousness=seriousness, causality=causality, number_patients=n, denominator=denom, percentage=pct, analysis_population="publication safety population", notes=emilia_notes)

    go29365_notes = "GO29365 main article safety text/Table 3; randomized safety-evaluable population N=39 per arm. Rows are partial because the accessible main table emphasizes common AEs and selected safety outcomes rather than a complete AE overview."
    for arm_id, n, pct, term, concept, grade, seriousness, causality in [
        ("TRIAL011_PUB_POLA_BR", 9, 23.1, "Fatal adverse events", "fatal_adverse_event", "grade 5", "fatal", "all-cause"),
        ("TRIAL011_PUB_BR", 11, 28.2, "Fatal adverse events", "fatal_adverse_event", "grade 5", "fatal", "all-cause"),
        ("TRIAL011_PUB_POLA_BR", 2, 5.1, "Polatuzumab vedotin dose reduction due to peripheral neuropathy", "dose_reduction", "all grades", "any", "all-cause"),
        ("TRIAL011_PUB_POLA_BR", 17, 43.6, "Peripheral neuropathy", "other_specific_safety_event", "all grades", "any", "all-cause"),
    ]:
        add(rows, trial_id="TRIAL011", arm_id=arm_id, document_id="EXPUB_TRIAL011_0001", page_or_table_locator="Main article safety text/Table 3, page_or_unit 8/9", ae_original_term=term, ae_standardized_term=term, safety_concept=concept, grade_category=grade, seriousness=seriousness, causality=causality, number_patients=n, denominator=39, percentage=pct, analysis_population="publication randomized safety-evaluable population", notes=go29365_notes)

    soraya_notes = "SORAYA main article safety text; safety population N=106. Several overview rows are reported as percentages only; number_patients is left blank when not directly stated."
    for n, pct, term, concept, grade, seriousness, causality, locator in [
        (None, 86, "TRAEs", "any_adverse_event", "all grades", "any", "treatment-related", "Main article safety text, page_or_unit 5/6"),
        (None, 30, "Grade 3 or above TRAEs", "grade_3_or_higher_adverse_event", "grade >=3", "any", "treatment-related", "Main article discussion text, page_or_unit 8"),
        (None, 9, "Serious grade >=3 TRAEs", "serious_adverse_event", "grade >=3", "serious", "treatment-related", "Main article safety text, page_or_unit 6"),
        (None, 33, "TRAEs leading to dose delay", "dose_interruption", "all grades", "any", "treatment-related", "Main article safety text, page_or_unit 6/7"),
        (None, 20, "TRAEs leading to dose reduction", "dose_reduction", "all grades", "any", "treatment-related", "Main article safety text, page_or_unit 7"),
        (None, 9, "TRAEs leading to treatment discontinuation", "adverse_event_leading_to_discontinuation", "all grades", "any", "treatment-related", "Main article safety text, page_or_unit 7"),
        (0, 0, "Treatment-related death after autopsy adjudication", "fatal_adverse_event", "grade 5", "fatal", "treatment-related", "Main article safety text, page_or_unit 7"),
    ]:
        add(rows, trial_id="TRIAL015", arm_id="TRIAL015_PUB_MIRV", document_id="EXPUB_TRIAL015_0001", page_or_table_locator=locator, ae_original_term=term, ae_standardized_term=term, safety_concept=concept, grade_category=grade, seriousness=seriousness, causality=causality, number_patients=n, denominator=106, percentage=pct, analysis_population="publication safety population", notes=soraya_notes)

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER)
        writer.writeheader()
        writer.writerows(rows)

    trial_counts = Counter(row["trial_id"] for row in rows)
    lines = [
        "# Publication core-safety expansion seed 报告",
        "",
        "日期：2026-06-18",
        "",
        "## 输出",
        "",
        "- `data/interim/publication_core_safety_expansion_seed.csv`",
        "",
        "## 当前已抽取",
        "",
        f"- seed 行数：{len(rows)}",
        f"- 覆盖 trial：{len(trial_counts)}",
        "",
    ]
    for trial_id, count in sorted(trial_counts.items()):
        lines.append(f"- `{trial_id}`：{count} 行")
    lines.extend([
        "",
        "## 使用边界",
        "",
        "该 seed 只纳入表格行清楚、分母清楚的 publication 数值。AESI-only、subgroup-only 或无法确认主分析集的表暂不写入核心 seed。所有记录仍标记为 `needs_review`，进入 source comparability 前需人工核对 arm、分母和定义。",
    ])
    (PROTOCOL / "publication_core_safety_expansion_seed_report.zh.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print("Wrote protocol/publication_core_safety_expansion_seed_report.zh.md")


if __name__ == "__main__":
    main()
