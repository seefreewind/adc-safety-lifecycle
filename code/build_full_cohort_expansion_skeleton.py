#!/usr/bin/env python3
"""Build full-cohort expansion candidate approval and trial skeletons."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
PROTOCOL = ROOT / "protocol"


APPROVAL_HEADER = [
    "approval_id",
    "drug_id",
    "approval_date",
    "indication",
    "tumor_type",
    "line_of_therapy",
    "monotherapy_or_combination",
    "accelerated_or_regular",
    "original_or_supplemental",
    "pivotal_trial_nct",
    "pivotal_trial_name",
    "primary_endpoint",
    "approval_status",
    "source_url",
    "verification_status",
    "notes",
]


TRIAL_HEADER = [
    "trial_id",
    "drug_id",
    "approval_id",
    "nct_number",
    "acronym",
    "phase",
    "randomized",
    "controlled",
    "blinded",
    "single_arm",
    "indication",
    "experimental_regimen",
    "comparator",
    "safety_population",
    "data_cutoff_date",
    "median_followup",
    "ctcae_version",
    "publication_doi",
    "supplement_available",
    "verification_status",
    "notes",
]


APPROVAL_ROWS = [
    ["APP001", "ADC007", "2019-12-20", "Unresectable or metastatic HER2-positive breast cancer after prior anti-HER2-based regimen", "breast cancer", "later-line", "monotherapy", "accelerated", "original", "NCT03248492", "DESTINY-Breast01", "objective response rate", "approved", "", "pilot_verified", "Pilot approval event"],
    ["APP002", "ADC009", "2020-08-05", "Relapsed or refractory multiple myeloma after at least four prior therapies", "multiple myeloma", "later-line", "monotherapy", "accelerated", "original", "NCT03525678", "DREAMM-2", "overall response rate", "withdrawn_then_reapproved", "https://www.fda.gov/drugs/resources-information-approved-drugs/fda-approves-belantamab-mafodotin-blmf-relapsed-or-refractory-multiple-myeloma", "pilot_verified", "Pilot approval event; 2025 reapproval modeled separately"],
    ["APP003", "ADC006", "2019-12-18", "Locally advanced or metastatic urothelial cancer after platinum and PD-1/PD-L1 inhibitor", "urothelial cancer", "later-line", "monotherapy", "accelerated", "original", "NCT03219333", "EV-201", "objective response rate", "approved", "", "pilot_verified", "Pilot approval event"],
    ["APP004", "ADC008", "2020-04-22", "Metastatic triple-negative breast cancer after at least two prior therapies", "breast cancer", "later-line", "monotherapy", "accelerated", "original", "NCT01631552", "IMMU-132-01", "objective response rate", "converted_to_regular", "", "pilot_verified", "Pilot original accelerated approval evidence"],
    ["APP005", "ADC008", "", "Metastatic triple-negative breast cancer confirmatory evidence", "breast cancer", "later-line", "monotherapy", "regular_or_confirmatory", "supplemental_or_conversion", "NCT02574455", "ASCENT", "progression-free survival", "confirmatory_evidence", "", "pilot_verified", "Pilot confirmatory evidence"],
    ["APP006", "ADC001", "2017-09-01", "Newly diagnosed CD33-positive AML and relapsed/refractory CD33-positive AML", "acute myeloid leukemia", "frontline and relapsed/refractory", "combination_or_monotherapy", "regular", "reapproval", "NCT00927498", "ALFA-0701", "event-free survival", "reapproved", "https://www.accessdata.fda.gov/drugsatfda_docs/nda/2017/761060Orig1s000Orig1Orig2s000Approv.pdf", "pilot_verified", "Pilot reapproval evidence"],
    ["APP007", "ADC002", "2011-08-19", "Relapsed Hodgkin lymphoma and systemic anaplastic large-cell lymphoma", "lymphoma", "later-line", "monotherapy", "accelerated", "original", "NCT00848926;NCT00866047", "SG035-0003;SG035-0004", "objective response rate", "approved", "https://www.accessdata.fda.gov/drugsatfda_docs/appletter/2011/125388s000,125399s000ltr.pdf", "needs_manual_verification", "Two single-arm pivotal studies; represented by two trial rows"],
    ["APP008", "ADC003", "2013-02-22", "HER2-positive metastatic breast cancer previously treated with trastuzumab and a taxane", "breast cancer", "later-line", "monotherapy", "regular", "original", "NCT00829166", "EMILIA", "progression-free survival and overall survival", "approved", "https://www.accessdata.fda.gov/drugsatfda_docs/nda/2013/125427Orig1s000Approv.pdf", "needs_manual_verification", ""],
    ["APP009", "ADC004", "2017-08-17", "Relapsed or refractory B-cell precursor acute lymphoblastic leukemia", "acute lymphoblastic leukemia", "relapsed/refractory", "monotherapy", "regular", "original", "NCT01564784", "INO-VATE ALL", "complete remission", "approved", "https://www.fda.gov/drugs/resources-information-approved-drugs/fda-approves-inotuzumab-ozogamicin-relapsed-or-refractory-b-cell-precursor-all", "needs_manual_verification", ""],
    ["APP010", "ADC005", "2019-06-10", "Relapsed or refractory diffuse large B-cell lymphoma in combination with bendamustine and rituximab", "lymphoma", "later-line", "combination", "accelerated", "original", "NCT02257567", "GO29365", "complete response rate", "approved", "", "needs_manual_verification", ""],
    ["APP011", "ADC010", "2021-04-23", "Relapsed or refractory large B-cell lymphoma after at least two systemic therapies", "lymphoma", "later-line", "monotherapy", "accelerated", "original", "NCT03589469", "LOTIS-2", "overall response rate", "approved", "", "needs_manual_verification", ""],
    ["APP012", "ADC011", "2021-09-20", "Recurrent or metastatic cervical cancer with disease progression on or after chemotherapy", "cervical cancer", "later-line", "monotherapy", "accelerated", "original", "NCT03438396", "innovaTV 204", "overall response rate", "converted_to_regular", "", "needs_manual_verification", "2024 regular approval modeled separately"],
    ["APP013", "ADC011", "2024-04-29", "Recurrent or metastatic cervical cancer with disease progression on or after chemotherapy", "cervical cancer", "later-line", "monotherapy", "regular", "conversion", "NCT04697628", "innovaTV 301", "overall survival", "approved", "https://www.fda.gov/drugs/resources-information-approved-drugs/fda-approves-tisotumab-vedotin-tftv-recurrent-or-metastatic-cervical-cancer", "needs_manual_verification", ""],
    ["APP014", "ADC012", "2022-11-14", "FR-alpha positive platinum-resistant epithelial ovarian, fallopian tube, or primary peritoneal cancer", "ovarian cancer", "later-line", "monotherapy", "accelerated", "original", "NCT04296890", "SORAYA", "overall response rate", "converted_to_regular", "", "needs_manual_verification", ""],
    ["APP015", "ADC012", "2024-03-22", "FR-alpha positive platinum-resistant epithelial ovarian, fallopian tube, or primary peritoneal cancer", "ovarian cancer", "later-line", "monotherapy", "regular", "conversion", "NCT04209855", "MIRASOL", "progression-free survival", "approved", "https://www.fda.gov/drugs/resources-information-approved-drugs/fda-approves-mirvetuximab-soravtansine-gynx-fra-positive-platinum-resistant-epithelial-ovarian", "needs_manual_verification", ""],
    ["APP016", "ADC009", "2025-10-23", "Relapsed or refractory multiple myeloma in combination regimens", "multiple myeloma", "later-line", "combination", "regular", "reapproval", "NCT04246047;NCT04484623", "DREAMM-7;DREAMM-8", "progression-free survival", "reapproved", "https://www.fda.gov/drugs/resources-information-approved-drugs/fda-approves-belantamab-mafodotin-blmf-relapsed-or-refractory-multiple-myeloma", "needs_manual_verification", "Two confirmatory phase 3 studies represented by two trial rows"],
    ["APP017", "ADC013", "2025-01-17", "Unresectable or metastatic HR-positive, HER2-negative breast cancer after endocrine-based therapy and chemotherapy", "breast cancer", "later-line", "monotherapy", "regular", "original", "NCT05104866", "TROPION-Breast01", "progression-free survival", "approved", "https://www.fda.gov/drugs/resources-information-approved-drugs/fda-approves-datopotamab-deruxtecan-dlnk-unresectable-or-metastatic-hr-positive-her2-negative-breast", "needs_manual_verification", ""],
    ["APP018", "ADC013", "2025-06-23", "Locally advanced or metastatic EGFR-mutated NSCLC after EGFR-directed therapy and platinum-based chemotherapy", "non-small cell lung cancer", "later-line", "monotherapy", "accelerated", "supplemental", "NCT04484142", "TROPION-Lung05", "overall response rate", "approved", "", "needs_manual_verification", "Within current 2026-05-31 project cutoff; FDA page/source URL still needs direct verification."],
    ["APP019", "ADC014", "2025-05-14", "Previously treated non-squamous NSCLC with high c-Met protein overexpression", "non-small cell lung cancer", "later-line", "monotherapy", "accelerated", "original", "NCT03539536", "LUMINOSITY", "overall response rate", "approved", "https://www.fda.gov/drugs/resources-information-approved-drugs/fda-grants-accelerated-approval-telisotuzumab-vedotin-tllv-nsclc-high-c-met-protein-overexpression", "needs_manual_verification", ""],
    ["APP020", "ADC013", "2026-05-22", "Unresectable or metastatic triple-negative breast cancer not candidates for PD-1/PD-L1 inhibitor therapy", "breast cancer", "first-line metastatic", "monotherapy", "regular", "supplemental", "NCT05374512", "TROPION-Breast02", "progression-free survival and overall survival", "approved", "https://www.fda.gov/drugs/resources-information-approved-drugs/fda-approves-datopotamab-deruxtecan-dlnk-unresectable-or-metastatic-triple-negative-breast-cancer", "official_page_checked", "Within current cutoff; include as expansion candidate"],
    ["APP021", "ADC015", "2026-05-27", "Blastic plasmacytoid dendritic cell neoplasm", "hematologic malignancy", "adult BPDCN", "monotherapy", "regular", "original", "NCT03386513", "CADENZA", "composite complete remission", "approved", "https://www.fda.gov/drugs/resources-information-approved-drugs/fda-approves-pivekimab-sunirine-pvzy-blastic-plasmacytoid-dendritic-cell-neoplasm-ultra-rare", "official_page_checked", "Definition-review flag: FDA describes CD123-directed antibody and alkylating agent conjugate"],
]


TRIAL_ROWS = [
    ["TRIAL001", "ADC007", "APP001", "NCT03248492", "DESTINY-Breast01", "2", "no", "no", "no", "yes", "HER2-positive metastatic breast cancer", "trastuzumab deruxtecan", "", "", "", "", "", "", "yes", "pilot_verified", "Pilot"],
    ["TRIAL002", "ADC009", "APP002", "NCT03525678", "DREAMM-2", "2", "no", "no", "no", "yes", "relapsed or refractory multiple myeloma", "belantamab mafodotin 2.5 mg/kg and 3.4 mg/kg", "", "", "", "", "", "", "yes", "pilot_verified", "Pilot"],
    ["TRIAL003", "ADC006", "APP003", "NCT03219333", "EV-201", "2", "no", "no", "no", "yes", "locally advanced or metastatic urothelial cancer", "enfortumab vedotin", "", "", "", "", "", "", "yes", "pilot_verified", "Pilot"],
    ["TRIAL004", "ADC008", "APP004", "NCT01631552", "IMMU-132-01", "1/2", "no", "no", "no", "yes", "metastatic triple-negative breast cancer", "sacituzumab govitecan", "", "", "", "", "", "", "yes", "pilot_verified", "Pilot original accelerated approval"],
    ["TRIAL005", "ADC008", "APP005", "NCT02574455", "ASCENT", "3", "yes", "yes", "no", "no", "metastatic triple-negative breast cancer", "sacituzumab govitecan", "single-agent chemotherapy", "", "", "", "", "", "yes", "pilot_verified", "Pilot confirmatory evidence"],
    ["TRIAL006", "ADC001", "APP006", "NCT00927498", "ALFA-0701", "3", "yes", "yes", "no", "no", "acute myeloid leukemia", "gemtuzumab ozogamicin plus chemotherapy", "chemotherapy", "", "", "", "", "", "yes", "pilot_verified", "Pilot"],
    ["TRIAL007", "ADC002", "APP007", "NCT00848926", "SG035-0003", "2", "no", "no", "no", "yes", "relapsed or refractory Hodgkin lymphoma", "brentuximab vedotin", "", "", "", "", "", "", "", "needs_manual_verification", "Adcetris original approval pivotal study"],
    ["TRIAL008", "ADC002", "APP007", "NCT00866047", "SG035-0004", "2", "no", "no", "no", "yes", "systemic anaplastic large-cell lymphoma", "brentuximab vedotin", "", "", "", "", "", "", "", "needs_manual_verification", "Adcetris original approval pivotal study"],
    ["TRIAL009", "ADC003", "APP008", "NCT00829166", "EMILIA", "3", "yes", "yes", "no", "no", "HER2-positive metastatic breast cancer", "ado-trastuzumab emtansine", "lapatinib plus capecitabine", "", "", "", "", "", "", "needs_manual_verification", "Kadcyla original approval pivotal study"],
    ["TRIAL010", "ADC004", "APP009", "NCT01564784", "INO-VATE ALL", "3", "yes", "yes", "no", "no", "relapsed or refractory B-cell precursor ALL", "inotuzumab ozogamicin", "standard intensive chemotherapy", "", "", "", "", "", "", "needs_manual_verification", "Besponsa original approval pivotal study"],
    ["TRIAL011", "ADC005", "APP010", "NCT02257567", "GO29365", "1/2", "yes", "yes", "no", "no", "relapsed or refractory diffuse large B-cell lymphoma", "polatuzumab vedotin plus bendamustine and rituximab", "bendamustine and rituximab", "", "", "", "", "", "", "needs_manual_verification", "Polivy original approval pivotal study"],
    ["TRIAL012", "ADC010", "APP011", "NCT03589469", "LOTIS-2", "2", "no", "no", "no", "yes", "relapsed or refractory large B-cell lymphoma", "loncastuximab tesirine", "", "", "", "", "", "", "", "needs_manual_verification", "Zynlonta original approval pivotal study"],
    ["TRIAL013", "ADC011", "APP012", "NCT03438396", "innovaTV 204", "2", "no", "no", "no", "yes", "recurrent or metastatic cervical cancer", "tisotumab vedotin", "", "", "", "", "", "", "", "needs_manual_verification", "Tivdak accelerated approval pivotal study"],
    ["TRIAL014", "ADC011", "APP013", "NCT04697628", "innovaTV 301", "3", "yes", "yes", "no", "no", "recurrent or metastatic cervical cancer", "tisotumab vedotin", "investigator's choice chemotherapy", "", "", "", "", "", "", "needs_manual_verification", "Tivdak regular approval confirmatory study"],
    ["TRIAL015", "ADC012", "APP014", "NCT04296890", "SORAYA", "3", "no", "no", "no", "yes", "FR-alpha positive platinum-resistant ovarian cancer", "mirvetuximab soravtansine", "", "", "", "", "", "", "", "needs_manual_verification", "Elahere accelerated approval pivotal study"],
    ["TRIAL016", "ADC012", "APP015", "NCT04209855", "MIRASOL", "3", "yes", "yes", "no", "no", "FR-alpha positive platinum-resistant ovarian cancer", "mirvetuximab soravtansine", "investigator's choice chemotherapy", "", "", "", "", "", "", "needs_manual_verification", "Elahere regular approval confirmatory study"],
    ["TRIAL017", "ADC009", "APP016", "NCT04246047", "DREAMM-7", "3", "yes", "yes", "no", "no", "relapsed or refractory multiple myeloma", "belantamab mafodotin plus bortezomib and dexamethasone", "daratumumab plus bortezomib and dexamethasone", "", "", "", "", "", "", "needs_manual_verification", "Blenrep reapproval study"],
    ["TRIAL018", "ADC009", "APP016", "NCT04484623", "DREAMM-8", "3", "yes", "yes", "no", "no", "relapsed or refractory multiple myeloma", "belantamab mafodotin plus pomalidomide and dexamethasone", "pomalidomide plus bortezomib and dexamethasone", "", "", "", "", "", "", "needs_manual_verification", "Blenrep reapproval study"],
    ["TRIAL019", "ADC013", "APP017", "NCT05104866", "TROPION-Breast01", "3", "yes", "yes", "no", "no", "HR-positive HER2-negative metastatic breast cancer", "datopotamab deruxtecan", "investigator's choice chemotherapy", "", "", "", "", "", "", "needs_manual_verification", "Datroway original approval pivotal study"],
    ["TRIAL020", "ADC013", "APP018", "NCT04484142", "TROPION-Lung05", "2", "no", "no", "no", "yes", "EGFR-mutated non-small cell lung cancer", "datopotamab deruxtecan", "", "", "", "", "", "", "", "needs_manual_verification", "Datroway NSCLC supplemental evidence"],
    ["TRIAL021", "ADC014", "APP019", "NCT03539536", "LUMINOSITY", "2", "no", "no", "no", "yes", "non-squamous NSCLC with high c-Met expression", "telisotuzumab vedotin", "", "", "", "", "", "", "", "needs_manual_verification", "Emrelis original approval pivotal study"],
    ["TRIAL022", "ADC013", "APP020", "NCT05374512", "TROPION-Breast02", "3", "yes", "yes", "no", "no", "triple-negative breast cancer", "datopotamab deruxtecan", "investigator's choice chemotherapy", "", "", "", "", "", "", "official_page_checked", "Datroway 2026 TNBC supplemental evidence"],
    ["TRIAL023", "ADC015", "APP021", "NCT03386513", "CADENZA", "1/2", "no", "no", "no", "yes", "blastic plasmacytoid dendritic cell neoplasm", "pivekimab sunirine", "", "", "", "", "", "", "", "official_page_checked", "Definition-review ADC-like conjugate"],
]


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def write_report() -> None:
    included = [row for row in APPROVAL_ROWS if row[14] != "after_cutoff_or_needs_date_policy"]
    after_cutoff = [row for row in APPROVAL_ROWS if row[14] == "after_cutoff_or_needs_date_policy"]
    lines = [
        "# 全队列扩展骨架阶段报告",
        "",
        "日期：2026-06-18",
        "",
        "## 本轮输出",
        "",
        "- `data/processed/approval_event_expansion_candidates.csv`",
        "- `data/processed/trial_master_expansion_candidates.csv`",
        "",
        "## 当前策略",
        "",
        "本表是扩展候选骨架，不直接替代试点主分析表。试点 6 个 evidence sets 和 13 个已接受 A 级配对保持不变。",
        "",
        "扩展阶段优先覆盖原始批准、撤回/再批准、加速批准转正式批准、以及 2026-05-31 截止前会改变 ADC 安全生命周期叙事的关键补充证据。",
        "",
        "## 候选规模",
        "",
        f"- approval/event 候选：{len(APPROVAL_ROWS)}",
        f"- 其中当前可进入扩展候选：{len(included)}",
        f"- 需按截止日期政策暂缓或单独标记：{len(after_cutoff)}",
        f"- trial 候选：{len(TRIAL_ROWS)}",
        "",
        "## 需要人工规则确认的点",
        "",
        "- `ADC015 pivekimab sunirine`：FDA 描述为 CD123-directed antibody and alkylating agent conjugate，建议主分析暂列 definition-review，敏感性分析可剔除。",
        "- `APP018 datopotamab deruxtecan EGFR-mutated NSCLC`：当前记录为 2025-06-23，在 2026-05-31 项目截止日前；本轮纳入扩展候选，但 FDA 直接来源 URL 仍需补齐。",
        "- `APP007 Adcetris` 和 `APP016 Blenrep reapproval`：单一 approval event 对应两个 pivotal/confirmatory trials，后续分析应按 trial-outcome-source 链条拆分。",
        "",
        "## 下一步",
        "",
        "1. 用 `trial_master_expansion_candidates.csv` 下载新增 ClinicalTrials.gov JSON。",
        "2. 解析新增 CT.gov adverse-events module，生成扩展 CT.gov 可用性报告。",
        "3. 再进入 FDA review/label 下载和 publication locator 扩展。",
    ]
    PROTOCOL.mkdir(exist_ok=True)
    (PROTOCOL / "full_cohort_expansion_skeleton_report.zh.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    write_csv(PROCESSED / "approval_event_expansion_candidates.csv", APPROVAL_HEADER, APPROVAL_ROWS)
    write_csv(PROCESSED / "trial_master_expansion_candidates.csv", TRIAL_HEADER, TRIAL_ROWS)
    write_report()
    print(f"Wrote {len(APPROVAL_ROWS)} approval candidates.")
    print(f"Wrote {len(TRIAL_ROWS)} trial candidates.")


if __name__ == "__main__":
    main()
