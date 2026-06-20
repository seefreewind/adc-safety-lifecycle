# Execution Status Report

Date: 2026-06-18

## Latest Update

The pilot publication package is now sufficient for source-location and initial safety extraction work. The following new outputs were added after the original setup:

- `data/processed/publication_table_locator.csv`
- `data/interim/publication_core_safety_seed.csv`
- `data/interim/ctgov_core_safety_seed.csv`
- `tables/pilot_core_safety_source_status.csv`
- `protocol/fda_review_missing_files.md`
- `protocol/pilot_publication_extraction_gaps.md`
- `data/interim/fda_core_safety_seed.csv`
- `data/interim/fda_key_safety_pages_text.txt`
- `tables/pilot_core_safety_evidence_matrix.csv`
- `tables/pilot_manual_verification_queue.csv`
- `protocol/pilot_core_safety_evidence_report.zh.md`
- `data/processed/source_comparability_matrix.csv`
- `tables/table1_pilot_source_coverage.csv`
- `tables/table2_core_safety_preferred_values.csv`
- `tables/table3_source_concordance_grade_summary.csv`
- `tables/table4_primary_numeric_discordance_pairs.csv`
- `tables/analysis_primary_numeric_discordance_summary.csv`
- `figures/figure1_pilot_source_concordance.png`
- `figures/figure1_pilot_source_concordance.pdf`
- `protocol/source_concordance_analysis_report.zh.md`
- `manuscript/results_pilot_source_concordance_draft.md`
- `manuscript/methods_source_concordance_draft.md`
- `manuscript/figure_legends_pilot.md`
- `manuscript/discussion_pilot_source_concordance_draft.md`
- `manuscript/title_abstract_keywords_pilot_draft.md`
- `data/processed/approval_event_expansion_candidates.csv`
- `data/processed/trial_master_expansion_candidates.csv`
- `protocol/full_cohort_expansion_skeleton_report.zh.md`
- `data/interim/ctgov_expansion_fetch_manifest.csv`
- `data/interim/ctgov_source_document_expansion.csv`
- `data/interim/ctgov_arm_dictionary_expansion.csv`
- `data/interim/ctgov_core_safety_expansion_seed.csv`
- `tables/ctgov_expansion_availability.csv`
- `tables/ctgov_expansion_status_summary.csv`
- `protocol/ctgov_expansion_report.zh.md`
- `tables/fda_expansion_priority_document_queue.csv`
- `protocol/fda_expansion_document_queue_report.zh.md`
- `data/raw/drugs_fda/review_documents/p1_document_download_manifest.tsv`
- `tables/full_cohort_expansion_source_status.csv`
- `protocol/full_cohort_expansion_source_status_report.zh.md`
- `data/processed/publication_reference_inventory_expansion.csv`
- `tables/publication_reference_expansion_summary.csv`
- `protocol/publication_expansion_locator_report.zh.md`
- `tables/user_supplied_publication_batch_inventory.csv`
- `protocol/user_supplied_publication_batch_check.zh.md`
- `tables/publication_fulltext_availability_expansion.csv`
- `data/processed/publication_table_locator_expansion.csv`
- `protocol/publication_fulltext_availability_expansion_report.zh.md`

Current pilot extraction status:

- Primary publication and supplement files are available for the six pilot evidence sets.
- CT.gov structured adverse-event rows are available for 5 of 6 pilot records; ALFA-0701 does not have a structured CT.gov results module.
- Publication core safety values have been seeded for all six pilot evidence sets where clearly extractable from the available text/tables.
- The publication seed now contains 56 rows. DREAMM-2 and ALFA-0701 have partial extraction, but some modern aggregate safety outcomes are not clearly reported in the available publication text.
- FDA review extraction is now partially complete. Valid multi-discipline reviews are available for Enhertu, Trodelvy, and Blenrep, and valid Mylotarg medical review files were already available.
- `data/processed/fda_review_table_locator.csv` now contains 25 FDA locator rows.
- `data/interim/fda_core_safety_seed.csv` now contains 29 FDA core safety seed rows.
- `tables/pilot_core_safety_evidence_matrix.csv` now contains 42 source-aware rows covering six pilot evidence sets and seven core safety outcomes.
- `tables/pilot_manual_verification_queue.csv` now contains 42 prioritized manual-verification rows: 31 P1, 5 P2, and 6 P3.
- `data/processed/source_comparability_matrix.csv` now contains 146 source-pair rows: 13 A-grade pairs and 133 C-grade descriptive pairs.
- `tables/table4_primary_numeric_discordance_pairs.csv` now contains 13 A-grade numeric-discordance pairs, mainly DREAMM-2 publication versus FDA review pairs.
- The user accepted these 13 A-grade pairs as the current pilot primary numeric-discordance set.
- Primary numeric-discordance summary: 11/13 pairs had zero percentage-point difference; 2/13 had non-zero differences; mean absolute difference was 0.22 percentage points and maximum absolute difference was 1.80 percentage points.
- Figure 1 has been generated as PNG and PDF, with a manuscript-ready legend draft.
- Pilot Discussion and Conclusions draft text has been added for the source-concordance analysis.
- Pilot Title, Abstract, and Keywords draft text has been added.
- Full-cohort expansion skeleton has been created with 21 approval/event candidates and 23 trial candidates through the current 2026-05-31 project cutoff.
- ClinicalTrials.gov expansion download completed: 17 new JSON records were downloaded, 6 existing pilot records were reused, and 0 downloads failed.
- ClinicalTrials.gov expansion parsing generated 23 source rows, 47 arm rows, and 141 group-level core safety summary rows; 19 of 23 trials have an adverse-events module.
- FDA P1 priority document download completed for the expansion queue: 47 of 48 unique missing P1 documents were downloaded successfully; one Elahere 2022 approval-letter URL failed because of an SSL error.
- Full-cohort source status table now shows all 23 trial candidates have at least one FDA P1 entry available locally, while four trials currently lack CT.gov AE modules.
- Expansion CT.gov publication-reference extraction generated 111 references; 20 of 23 trials still require PubMed/publisher triage for definitive primary-publication locator assignment.
- User-supplied publication batches were ingested into `data/raw/publications/expansion`; 39 of 39 mapped files or folders were copied successfully.
- Expansion publication full-text availability is now complete for main articles: 23 of 23 trial candidates have main article PDFs available.
- Publication page-level safety locator expansion generated 54 file-level locators and 2,199 page/unit-level safety locators; P1 publication locators cover all 23 trial candidates.
- Publication core-safety candidate extraction generated 231 candidate locator rows, including 33 high-confidence table candidates and 11 medium-confidence text candidates.
- Publication manual review queue generated 169 prioritized rows across all 23 trial candidates.
- Full-cohort extraction readiness is now stratified into 5 trials ready for tri-source extraction, 6 trials ready for publication/CT.gov extraction while FDA review locator remains pending, and 12 trials requiring manual publication safety-page review before numeric extraction.
- FDA review locator expansion generated 853 locator rows from local FDA P1 files and TOC-expanded review PDFs, including 203 P1 review locator rows; 8 of 23 trial candidates currently have at least one P1 FDA review locator.
- Focused FDA TOC review-PDF downloading was attempted, but several accessdata.fda.gov review links timed out or failed during SSL handshake. The partial manifest is saved at `data/raw/drugs_fda/review_documents/toc_review_pdf_download_manifest.tsv`.
- EV-201 / Padcev FDA clinical safety extraction remains incomplete: FDA label/TOC sources are local, but the original clinical review PDF still needs a usable medical or multidisciplinary review file before FDA-source numeric extraction can be completed.
- User supplied three additional FDA review PDFs: Besponsa `761040Orig1s000MultidisciplineR.pdf`, Polivy `761121Orig1s000MedR.pdf`, and Padcev `761137Orig1s000MultidisciplineR.pdf`. These were copied into the project FDA review directory and incorporated into locator generation.
- FDA review-to-trial mapping was corrected to avoid assigning original FDA reviews to later supplemental trials for the same drug. After correction, FDA locator expansion contains 8 trials with P1 FDA review locators, while later trials such as ASCENT and DREAMM-7 are no longer treated as having original-review FDA numeric comparators.
- FDA core-safety candidate extraction generated `tables/fda_core_safety_extraction_candidates_expansion.csv`.
- Integrated extraction priority dashboard generated `tables/full_cohort_extraction_priority_dashboard.csv`: 4 trials are currently batch 1 tri-source numeric-extraction candidates, 7 are publication/CT.gov-first candidates, and 12 require publication manual page review.
- Batch 1 extraction packet generated three files: `tables/batch1_publication_extraction_packet.csv`, `tables/batch1_fda_extraction_packet.csv`, and `tables/batch1_ctgov_extraction_packet.csv`.
- INO-VATE ALL publication Supplementary Table S1 was manually structured into `data/interim/publication_core_safety_expansion_seed.csv` with 8 seed rows. The seed notes that publication denominators (InO 139; standard chemotherapy 120) differ from CT.gov AE-module denominators (164; 143), so source comparability requires conservative grading.
- Publication expansion seed was extended to 115 rows across 17 expansion trials. Together with the 56-row pilot publication seed, publication-side core safety extraction now covers all 23 trial candidates.
- Combined publication seed files were generated: `data/interim/publication_core_safety_combined_seed.csv` and `tables/publication_core_safety_combined_seed_summary.csv`. The combined file includes a canonical safety-concept column to harmonize pilot and expansion concept naming.
- Expansion publication-CT.gov comparability precheck was generated at `tables/expansion_pub_ctgov_comparability_precheck.csv`: 2 A-grade primary numeric-comparison candidates, 1 B-grade sensitivity/descriptive candidate, and 41 C-grade non-primary comparisons. Most C-grade rows reflect different safety constructs rather than numeric disagreement.
- Publication seed coverage is now summarized in `tables/expansion_publication_seed_coverage.csv`; all 23 trial candidates have either pilot publication seed or expansion publication seed coverage.

The remaining point requiring user intervention is Padcev clinical FDA review PDF retrieval. See:

`protocol/fda_review_missing_files.md`

Remaining publication-side gaps are summarized in:

`protocol/pilot_publication_extraction_gaps.md`

Expansion extraction readiness and review queues are summarized in:

- `protocol/publication_core_safety_manual_review_queue_expansion_report.zh.md`
- `protocol/fda_review_locator_expansion_report.zh.md`
- `protocol/full_cohort_extraction_priority_dashboard_report.zh.md`
- `protocol/batch1_tri_source_extraction_packet_report.zh.md`
- `protocol/publication_core_safety_expansion_seed_report.zh.md`
- `protocol/publication_core_safety_combined_seed_report.zh.md`
- `protocol/expansion_pub_ctgov_comparability_precheck_report.zh.md`
- `protocol/expansion_publication_seed_coverage_report.zh.md`

## Completed In This Execution

### 1. Project Recreated

Created project directory:

`/Users/zy/Documents/New project 3/adc_safety_lifecycle`

Core folders created:

- `config/`
- `data/raw/`
- `data/interim/`
- `data/processed/`
- `protocol/`
- `templates/`
- `src/`
- `analysis/`
- `figures/`
- `tables/`
- `manuscript/`

### 2. Project Rules Frozen As Draft

Created:

- `README.md`
- `manuscript/project_rules_checklist.md`
- `protocol/cohort_definition.md`
- `protocol/source_comparability_rules.md`
- `protocol/extraction_guide.md`
- `protocol/fda_adc_cohort_verification.md`

The current working cutoff date is 2026-05-31.

### 3. Processed Database Shell Created

Created core CSV structures:

- `drug_master.csv`
- `approval_event.csv`
- `trial_master.csv`
- `source_document.csv`
- `arm_dictionary.csv`
- `source_comparability_matrix.csv`
- `ae_observation.csv`
- `label_history.csv`
- `aems_signal.csv`
- `fda_review_document_inventory.csv`
- `fda_review_table_locator.csv`
- `publication_table_locator.csv`
- `project_file_inventory.csv`

### 4. Working FDA ADC Cohort Built

Current working cohort includes 15 ADC or ADC-like oncology antibody-payload conjugates:

1. gemtuzumab ozogamicin
2. brentuximab vedotin
3. ado-trastuzumab emtansine
4. inotuzumab ozogamicin
5. polatuzumab vedotin
6. enfortumab vedotin
7. fam-trastuzumab deruxtecan
8. sacituzumab govitecan
9. belantamab mafodotin
10. loncastuximab tesirine
11. tisotumab vedotin
12. mirvetuximab soravtansine
13. datopotamab deruxtecan
14. telisotuzumab vedotin
15. pivekimab sunirine

`pivekimab sunirine` is flagged for definition review because FDA describes it as a CD123-directed antibody and alkylating agent conjugate; the final protocol must decide whether to include it in the main ADC cohort or sensitivity/appendix.

### 5. FDA Official Sources Downloaded

Downloaded:

- FDA oncology approval notifications page snapshot.
- FDA notification pages for belantamab mafodotin, datopotamab deruxtecan, telisotuzumab vedotin, tisotumab vedotin, and mirvetuximab soravtansine.
- Drugs@FDA official data files ZIP and extracted database tables.

Drugs@FDA matching produced:

- 21 ADC product-match rows.
- 295 FDA document inventory rows.

### 6. Pilot ClinicalTrials.gov Data Downloaded And Parsed

Downloaded ClinicalTrials.gov API v2 JSON snapshots for six pilot trial records:

- DESTINY-Breast01
- DREAMM-2
- EV-201
- IMMU-132-01
- ASCENT
- ALFA-0701

Structured results/adverse-events modules were available for 5 of 6 records.

ALFA-0701 currently lacks a structured CT.gov results module and will require FDA review/publication extraction.

Parsed CT.gov AE rows:

- 2,963 AE observation rows in `data/interim/ctgov_ae_observation.csv`
- 6 CT.gov source-document rows
- 15 treatment-arm rows

### 7. Extraction Workbook Created

Created:

`templates/ae_numeric_extraction_workbook.xlsx`

Sheets:

- `README`
- `Source_Inventory`
- `AE_Extraction_Form`
- `Arm_Dictionary`
- `Safety_Concept_Dictionary`
- `Adjudication_Log`
- `QC_Rules`
- `Extraction_Progress`
- `Curated_Facts_Need_Review`
- `FDA_Table_Locator`

Formula error scan found no Excel error strings.

### 8. Scripts Created

Created:

- `src/fetch_ctgov.py`
- `src/parse_ctgov_adverse_events.py`
- `src/build_ctgov_metadata.py`
- `src/match_drugsfda_documents.py`
- `src/download_fda_toc_documents.py`
- `src/download_fda_generated_pdfs.py`
- `src/build_label_history.py`
- `src/process_aems.py`
- `src/quality_control.py`

Analysis scaffolds:

- `analysis/source_concordance.R`
- `analysis/label_transition.R`

### 9. Quality Control

`src/quality_control.py` passed.

### 10. Publication Locator Created

Created:

- `data/processed/publication_reference_inventory.csv`

Extracted 51 publication-reference rows, including primary publication candidates for all six pilot trial records.

### 11. Label Snapshots Partially Downloaded

Created:

- `src/fetch_openfda_labels.py`
- `data/interim/openfda_label_fetch_manifest.csv`

openFDA label snapshots were downloaded for the first nine cohort drugs:

- Mylotarg
- Adcetris
- Kadcyla
- Besponsa
- Polivy
- Padcev
- Enhertu
- Trodelvy
- Blenrep

For Zynlonta, Tivdak, Elahere, Datroway, Emrelis, and Decnupaz, openFDA requests returned SSL/network errors during this execution and remain pending.

## Current Partial Data Availability

| Data source | Status |
|---|---|
| Drug master | Draft complete; verification pending for older approvals |
| FDA approval events | Pilot seed complete; full cohort event expansion pending |
| CT.gov snapshots | Pilot complete |
| CT.gov AE parsing | 5/6 pilot trials parsed |
| FDA review inventory | Built from Drugs@FDA |
| FDA review PDFs | Mylotarg key PDFs downloaded; other pilot PDFs pending due accessdata instability |
| Publication PDFs/supplements | Not yet downloaded |
| Label history | Structure created; version extraction pending |
| openFDA label snapshots | 9/15 downloaded |
| AEMS/FAERS | Structure created; raw quarterly data not yet downloaded |

## Immediate Blockers Or Manual Decisions

1. Confirm final inclusion rule for pivekimab sunirine.
2. Provide or authorize manual retrieval of publication PDFs and supplementary appendices if not openly downloadable.
3. FDA accessdata PDF download is unstable; continue in smaller batches or use browser/manual downloads for key review files.
4. ALFA-0701 lacks CT.gov structured results; FDA review and publication extraction will be primary.
5. Manual review is required for AE term mapping and source comparability grading before primary analysis.

## Recommended Next Execution Batch

1. Download remaining pilot FDA review PDFs in smaller drug-specific batches.
2. Locate and download primary publications and supplements for the six pilot trial records.
3. Build FDA table locators from downloaded PDFs.
4. Extract the six core safety outcomes from FDA reviews and CT.gov.
5. Generate the first pilot completeness table.

## 2026-06-18 Full-Cohort Extraction Update

新增 FDA 审评结构化 seed：

- `data/interim/fda_core_safety_expansion_seed.csv`
- `tables/fda_core_safety_expansion_seed_summary.csv`
- `protocol/fda_core_safety_expansion_seed_report.zh.md`

本批仅收录可由 FDA 审评全文直接核对的 EV-201 和 GO29365 核心安全性行，共 27 行。INO-VATE ALL 的 FDA 关键表页存在扫描/空文字层，本轮未强行结构化，以免引入不可靠数值。

合并 FDA seed：

- `data/interim/fda_core_safety_combined_seed.csv`
- `tables/fda_core_safety_combined_seed_summary.csv`
- `protocol/fda_core_safety_combined_seed_report.zh.md`

当前 FDA combined seed 共 56 行，覆盖 6 个 trial：TRIAL001、TRIAL002、TRIAL003、TRIAL004、TRIAL006、TRIAL011。

全队列来源可比性矩阵：

- `data/processed/full_cohort_source_comparability_matrix.csv`
- `tables/full_cohort_source_comparability_summary.csv`
- `protocol/full_cohort_source_comparability_report.zh.md`

自动生成 269 个来源配对，其中 A 级 18 个、C 级 251 个。A 级配对主要来自 publication vs FDA review，覆盖 TRIAL002 DREAMM-2、TRIAL003 EV-201、TRIAL004 IMMU-132-01。

主分析候选配对：

- `tables/primary_analysis_pair_candidates_full_cohort.csv`
- `protocol/primary_analysis_pair_candidates_report.zh.md`

当前 A 级主分析候选配对 18 个，仍需人工最终核对 all-cause 与 treatment-related 口径是否重复、是否保留为预设核心口径。

全队列分析就绪总览：

- `tables/full_cohort_analysis_readiness_summary.csv`
- `protocol/full_cohort_analysis_readiness_summary.zh.md`

当前 publication seed 覆盖 23/23，FDA seed 覆盖 6/23，CT.gov seed 覆盖 19/23。3 个 trial 已有 A 级主分析候选，17 个 trial 处于多来源描述/人工裁决阶段，3 个 trial 目前只有 publication 结构化来源。

来源可比性人工裁决队列：

- `tables/source_comparability_adjudication_queue.csv`
- `protocol/source_comparability_adjudication_queue_report.zh.md`

当前 C 级待裁决配对 251 个。收紧后的 P1 队列共 7 条，主要是同臂、同分母的 serious AE 配对，但因 CT.gov 时间窗描述触发保守降级。

P1 自动裁决建议：

- `tables/p1_source_comparability_adjudication_recommendations.csv`
- `protocol/p1_source_comparability_adjudication_recommendations.zh.md`

P1 共 7 条：建议 3 条升为 A 级主分析候选（TRIAL003 serious AE；TRIAL014 两个 serious AE arm），4 条列为 B 级敏感性分析候选（TRIAL002 serious AE）。

当前分析候选集：

- `tables/analysis_ready_comparison_set.csv`
- `protocol/analysis_ready_comparison_set_report.zh.md`

候选集共 28 个配对：21 个主分析候选、7 个敏感性分析候选。主分析候选覆盖 TRIAL002、TRIAL003、TRIAL004、TRIAL014；敏感性分析候选覆盖 TRIAL001 和 TRIAL002。

候选集差异统计：

- `tables/analysis_ready_comparison_summary_stats.csv`
- `protocol/analysis_ready_comparison_summary_stats.zh.md`

主分析候选平均绝对百分比差为 0.26 个百分点，最大 1.80 个百分点；敏感性分析候选平均绝对百分比差为 3.91 个百分点，最大 6.53 个百分点。

P3/P4 自动裁决建议：

- `tables/p3_p4_source_comparability_adjudication_recommendations.csv`
- `protocol/p3_p4_source_comparability_adjudication_recommendations.zh.md`

P3/P4 共 24 条：建议 3 条作为 B 级敏感性分析候选，19 条保留 C 级描述，2 条作为 duplicate cross-definition 排除。新增 B 级候选均来自 TRIAL001 DESTINY-Breast01 的 publication vs FDA review，因 FDA approval-review pool 较 publication trial-specific population 更宽，仅可用于敏感性分析。

来源页确认包：

- `tables/analysis_ready_source_confirmation_packet.csv`
- `tables/analysis_ready_source_auto_confirmation.csv`
- `tables/analysis_ready_source_auto_confirmation_summary.csv`
- `tables/analysis_ready_pair_confirmation_status.csv`
- `tables/analysis_ready_source_confirmation_packet_confirmed.csv`
- `protocol/analysis_ready_source_confirmation_packet_report.zh.md`
- `protocol/analysis_ready_source_auto_confirmation_report.zh.md`
- `protocol/analysis_ready_pair_confirmation_status_report.zh.md`

该工作包包含 28 个 analysis-ready 配对的 observation_id、document_id、locator、原始术语、grade、seriousness、causality、分母和百分比。自动文本核对结果显示 56/56 个 source-side 均匹配到相应术语和值；pair-level 状态为 28/28 `auto_source_confirmed`。

Confirmed analysis-ready set:

- `tables/analysis_ready_comparison_set_confirmed.csv`
- `protocol/analysis_ready_comparison_set_confirmed_report.zh.md`

确认版 analysis-ready set 共 28 个配对，全部为 `auto_source_confirmed`，正式提交前建议进行抽样视觉审计。

Manuscript-ready summary tables:

- `manuscript/table1_source_coverage_and_readiness.zh.md`
- `manuscript/table2_analysis_ready_comparisons.zh.md`
- `protocol/manuscript_ready_summary_tables_report.zh.md`

Table 1 汇总 23 个 trial 的 publication、FDA、CT.gov 结构化覆盖及分析就绪分层；Table 2 汇总 28 个 analysis-ready source-comparison candidates。

Non-comparability rationale summary:

- `tables/noncomparability_rationale_summary.csv`
- `manuscript/supplementary_noncomparability_rationale.zh.md`
- `protocol/noncomparability_rationale_summary_report.zh.md`

未进入 analysis-ready set 的配对主要原因包括 different arm/dose、AE definition or causality mismatch、CT.gov all-cause mortality 与 fatal AE 不可直接比较、denominator/population mismatch、CT.gov time-window difference。

Current manuscript drafts:

- `manuscript/methods_current_extraction_and_comparability.zh.md`
- `manuscript/results_draft_current_extraction.zh.md`
- `manuscript/methods_current_extraction_and_comparability.en.md`
- `manuscript/results_current_extraction_and_comparability.en.md`
- `manuscript/results_confirmed_source_concordance_section.en.md`
- `manuscript/tables_confirmed_concordance.en.md`

Reproducible workflow entry point:

- `src/run_current_extraction_workflow.py`

该脚本按依赖顺序重建 FDA expansion seed、FDA combined seed、全队列 comparability matrix、详细裁决矩阵、P1/P3/P4 裁决建议、analysis-ready set、summary stats、source-confirmation packet、readiness summary、manuscript-ready tables、non-comparability rationale summary，并运行 `src/quality_control.py`。2026-06-19 已完整运行通过。

Visual source audit sample pages:

- `src/build_visual_audit_sample_pages.py`
- `src/build_visual_audit_matched_source_pages.py`
- `src/build_visual_source_audit_review_status.py`
- `tables/visual_source_audit_sample_pages.csv`
- `tables/visual_source_audit_matched_pages.csv`
- `tables/visual_source_audit_review_status.csv`
- `figures/source_audit_pages/*.png`
- `figures/source_audit_matched_pages/*.png`
- `protocol/visual_source_audit_sample_pages_report.zh.md`
- `protocol/visual_source_audit_matched_pages_report.zh.md`
- `protocol/visual_source_audit_review_status_report.zh.md`

已渲染 13 个代表性来源页，覆盖 TRIAL001、TRIAL002、TRIAL003、TRIAL004 和 TRIAL014。初步视觉抽查 `TRIAL002_FDA_ADC009_MDR_761158_ORIG1_p148.png` 通过，DREAMM-2 FDA Table 27 清晰可读。

随后使用术语、百分比和分母在 PDF 文本层中自动定位最佳审计页，渲染 15 个 matched source audit pages。视觉审计结果：12 页 `visual_audit_pass`，2 页 `visual_audit_pass_summary_text`，1 页 `visual_audit_pass_multpage_table`。

Final analysis audit index:

- `src/build_final_analysis_audit_index.py`
- `tables/final_analysis_audit_index.csv`
- `protocol/final_analysis_audit_index_report.zh.md`

最终审计索引共 28 个 analysis-ready 配对：21 个主分析候选、7 个敏感性分析候选。全部为 `auto_source_confirmed`，并标记为 `analysis_ready_confirmed_with_visual_audit`。ClinicalTrials.gov source-side 不适用 PDF visual audit，其余 PDF source-side 均有 matched visual audit 状态。

Manuscript audit trail table:

- `src/build_manuscript_audit_tables.py`
- `manuscript/supplementary_analysis_ready_audit_trail.zh.md`
- `protocol/manuscript_audit_tables_report.zh.md`

该补充表列出 28 个 analysis-ready source comparison 的 pair confirmation status 与两个 source-side 的 visual audit status，可作为 supplementary audit trail。

Confirmed concordance result tables:

- `src/build_confirmed_concordance_results.py`
- `tables/confirmed_concordance_overall_stats.csv`
- `tables/confirmed_concordance_by_trial.csv`
- `tables/confirmed_concordance_by_safety_concept.csv`
- `tables/confirmed_concordance_by_source_pair.csv`
- `manuscript/confirmed_concordance_results_summary.zh.md`
- `protocol/confirmed_concordance_results_report.zh.md`

Confirmed set 28 个配对。主分析候选 21 个，平均绝对差异 0.26 个百分点，中位数 0.00，最大 1.80；13/21 差异为 0，20/21 差异 <=1 个百分点，21/21 差异 <=2 个百分点。敏感性候选 7 个，平均绝对差异 3.91 个百分点，最大 6.53。

Current full manuscript working draft:

- `src/build_current_manuscript_draft.py`
- `manuscript/current_full_manuscript_draft.en.md`
- `manuscript/citation_todo_list.md`
- `protocol/current_full_manuscript_draft_report.zh.md`

当前英文工作稿包含标题、结构式摘要、关键词、Background、Methods、Results、Discussion、Conclusions、Declarations 占位、References 和英文结果表。Methods 和 Results 已接入当前确认版 source-concordance 结果；Background 和 Discussion 仍保留 `CITATION REQUIRED` 标记，进入投稿稿前需逐句补真实引用。

Source citation and primary trial reference inventory:

- `src/build_pubmed_reference_lookup.py`
- `src/build_source_citation_inventory.py`
- `src/build_primary_trial_reference_list.py`
- `data/interim/pubmed_reference_lookup.csv`
- `tables/source_citation_inventory.csv`
- `tables/primary_trial_reference_list.csv`
- `manuscript/source_citation_inventory.md`
- `manuscript/primary_trial_reference_list.en.md`
- `protocol/pubmed_reference_lookup_report.zh.md`
- `protocol/source_citation_inventory_report.zh.md`
- `protocol/primary_trial_reference_list_report.zh.md`

23/23 个 trial 的本地主论文全文均已按 PMID 匹配到主论文引用。TRIAL022 TROPION-Breast02 的本地 PMID 41937088 原不在项目 publication reference inventory 中，已通过 PubMed 补查并写入 `data/interim/pubmed_reference_lookup.csv`；对应 DOI 为 `10.1016/j.annonc.2026.03.008`。

Background/Discussion candidate references:

- `src/build_background_reference_list.py`
- `tables/background_discussion_reference_list.csv`
- `manuscript/background_discussion_reference_list.en.md`
- `protocol/background_discussion_reference_list_report.zh.md`

已通过 PubMed 获取 24 条候选引用，并在 `manuscript/current_full_manuscript_draft.en.md` 的 Background 和 Discussion 中插入候选编号 [24-47]。这些引用用于支撑 ADC therapeutic class/mechanism、ADC toxicity/AESI context、ClinicalTrials.gov results database、ClinicalTrials.gov safety-result completeness/concordance、registry-publication SAE reporting discrepancy、CONSORT Harms/reporting-quality context，以及 FDA approval-summary examples。投稿前仍需逐句核验 claim alignment。

Confirmed source appendix:

- `src/build_confirmed_source_appendix.py`
- `tables/confirmed_source_appendix.csv`
- `manuscript/confirmed_source_appendix.en.md`
- `protocol/confirmed_source_appendix_report.zh.md`

Confirmed source appendix 共列出 12 个用于 confirmed analysis-ready comparisons 的来源文档：5 个 publication、4 个 FDA review、3 个 ClinicalTrials.gov。ClinicalTrials.gov URL 已按 NCT 自动生成；4 个 FDA review PDF 的 FDA accessdata 官方 URL 已按文件名验证并写入附录。

Three-layer framework upgrade:

- `src/build_three_layer_analysis_tables.py`
- `tables/core_safety_reporting_completeness_by_trial_source.csv`
- `tables/core_safety_reporting_completeness_by_trial.csv`
- `tables/comparability_yield_overall.csv`
- `tables/comparability_yield_by_source_pair.csv`
- `tables/comparability_yield_by_trial.csv`
- `tables/comparability_yield_by_safety_concept.csv`
- `tables/five_state_source_reporting_status.csv`
- `tables/five_state_source_reporting_status_summary.csv`
- `manuscript/three_layer_analysis_tables.en.md`
- `protocol/three_layer_analysis_tables_report.zh.md`

主稿已从“少数严格可比配对的数值一致性”升级为三层研究：Layer 1 纳入 23/23 个 trial 的 source availability/completeness；Layer 2 纳入 269 个 potential source comparisons 的 comparability yield；Layer 3 保留 28 个 confirmed analysis-ready pairs 的 numeric concordance。当前 confirmed comparability yield 为 28/269 = 10.4%。新版 `manuscript/preliminary_manuscript.en.md` 已使用三层标题、摘要、Methods addendum、Results、Discussion 和 Conclusions。

ClinicalTrials.gov full-module exploratory expansion:

- `src/extract_ctgov_full_module_safety_candidates.py`
- `src/build_ctgov_full_module_candidate_triage.py`
- `src/build_ctgov_full_module_manual_review_packet.py`
- `data/interim/ctgov_full_module_safety_outcome_candidates.csv`
- `data/interim/ctgov_full_module_safety_candidate_triage.csv`
- `data/interim/ctgov_full_module_core_safety_candidates.csv`
- `tables/ctgov_full_module_candidate_triage_by_trial.csv`
- `tables/ctgov_full_module_candidate_triage_by_concept.csv`
- `tables/ctgov_full_module_incremental_candidate_summary.csv`
- `tables/ctgov_full_module_manual_review_packet.csv`
- `manuscript/ctgov_full_module_expansion_summary.en.md`
- `protocol/ctgov_full_module_safety_outcome_candidates_report.zh.md`
- `protocol/ctgov_full_module_candidate_triage_report.zh.md`
- `protocol/ctgov_full_module_manual_review_packet.zh.md`

CT.gov outcome-measures module 探索性筛查生成 492 行安全相关候选，覆盖 15 个 trial/NCT。规则分级后，186 行被保留为高优先级核心安全候选、269 行归为探索性实验室异常或疾病特异性安全候选、其余为低优先级或应排除的混合终点。相对现有 CT.gov adverse-events module，新增 9 个核心 trial-concept 候选和 7 个探索性 trial-concept 候选；这些候选已整理为 16 行人工核对包。该扩展目前仅作为人工核对队列和补充说明，不并入 28 个 confirmed analysis-ready pairs，也不改变主分析结论。

Manuscript structure and quality audit:

- `src/build_manuscript_quality_audit.py`
- `src/build_preliminary_manuscript_docx.py`
- `manuscript/manuscript_quality_audit.md`
- `manuscript/preliminary_manuscript.docx`
- `protocol/manuscript_quality_audit_report.zh.md`
- `protocol/preliminary_manuscript_docx_report.zh.md`
- `protocol/preliminary_manuscript_docx_visual_qa.zh.md`
- `protocol/ctgov_full_module_integration_decision.zh.md`

当前 preliminary manuscript 已规范为 BMC-style 章节顺序，Methods/Results 未插入文献引用，结果表已移动至 References 之前。参考文献总数已由 29 条扩展至 47 条，其中 23 条为主论文引用、24 条为 Background/Discussion 候选引用。已生成 Word 初步稿件 `manuscript/preliminary_manuscript.docx`，并完成渲染视觉抽查：共 19 页，Tables 部分使用横向页面，未见明显重叠或溢出。作者、基金、致谢和利益冲突仍按用户要求留空或待后续提供。

Quality control:

- `src/quality_control.py` passed after this update.

## 2026-06-19 further framework refinement

本轮按新的修改建议继续推进，重点不再增加来源数量，而是把研究框架改得更严谨、更接近完整元研究。

新增/更新脚本：

- `src/build_robust_comparability_sensitivity.py`
- `src/build_source_flow_status.py`
- `src/build_manual_adjudication_packets.py`
- `src/run_current_extraction_workflow.py`
- `src/build_current_manuscript_draft.py`

新增/更新核心输出：

- `tables/stratum_level_comparability_metrics.csv`
- `tables/trial_weighted_concordance_sensitivity.csv`
- `tables/leave_one_trial_out_concordance.csv`
- `tables/count_rounding_concordance_classification.csv`
- `tables/count_rounding_concordance_summary.csv`
- `tables/source_flow_status_summary.csv`
- `tables/ctgov_incremental_core_candidate_adjudication_packet.csv`
- `tables/confirmed_pair_structured_audit_packet.csv`
- `tables/structured_audit_no_duplicate_review_statement.csv`
- `manuscript/robust_comparability_sensitivity.en.md`
- `manuscript/source_flow_status_summary.en.md`
- `manuscript/current_full_manuscript_draft.en.md`
- `manuscript/preliminary_manuscript.en.md`
- `manuscript/preliminary_manuscript.docx`
- `protocol/robust_comparability_sensitivity_report.zh.md`
- `protocol/source_flow_status_report.zh.md`
- `protocol/manual_adjudication_packets_report.zh.md`

主要结果已写入主稿：

- Source-flow 层：publication structured extraction 23/23，ClinicalTrials.gov structured extraction 19/23，FDA review structured extraction 6/23；另有 17/23 个 trial 对应 FDA 文件存在，但未提取到 trial-specific structured core values。
- Stratum-level comparability：17/53 = 32.1%；comparable strata 中 14/17 concordant。
- Value-pair yield：28/269 = 10.4%；该分母保留为 algorithm-dependent value-pair denominator。
- Numeric concordance：21 个 primary-analysis comparisons 的 pair-weighted mean absolute difference 为 0.26 pp；trial-weighted mean 为 0.58 pp。
- Leave-one-trial-out：去除 DREAMM-2 后 primary mean absolute difference 为 0.49 pp，仍未改变主结论。
- Count/rounding compatibility：primary comparisons 已按 exact count concordance、rounding-compatible、same count/denominator with percentage-display difference、numerically close but not count-confirmed 等类别拆分。

边界说明：

- CT.gov outcome-measures module 的 9 个新增核心 trial-concept 候选已整理为 future structured review queue，但未并入主分析。
- 28 个 confirmed pairs 已生成 structured audit packet；当前未执行 independent duplicate adjudication，因此不报告一致率或 Cohen's κ。
- 主稿已去除 References 中的内部 `Supports:` 注释；保留 `manuscript/background_discussion_reference_list.en.md` 作为引用底账。
- 已新增 Table 1 和 4 个主稿图件：study flow、source-flow heatmap、five-state reporting/comparability status、numeric concordance scatter plot。图件同时导出 PNG 和 PDF，位于 `figures/manuscript/`。
- DOCX 已重新生成并渲染视觉抽查，共 26 页；首页、Methods 边界说明、Table 1 横向页、Figure 1-4、Discussion limitations、横向结果表页和参考文献尾页未见明显截断、重叠或内部注释残留。Figure 1 当前可读，投稿排版时可按期刊版心进一步放大或重绘。

当前仍需要用户/人工介入的事项：

1. Authors、Affiliations、Corresponding author、Acknowledgements、Funding、Competing interests。
2. 投稿前需按目标期刊逐句核验 Background/Discussion claim alignment，并统一最终参考文献格式。

## 2026-06-19 duplicate-adjudication alternative

由于当前没有条件完成两名独立研究者判读，本轮将方法学路线正式切换为“structured audit trail + source confirmation + visual audit + sensitivity analyses”。

更新内容：

- `src/build_manual_adjudication_packets.py` 已改为生成结构化审计包，而不是双研究者复核包。
- 新增 `tables/confirmed_pair_structured_audit_packet.csv`，记录 28 个 confirmed pairs 的 trial、arm、denominator、source locator、source confirmation、visual audit 和当前 analysis tier。
- 新增 `tables/structured_audit_no_duplicate_review_statement.csv`，明确 independent duplicate adjudication 未执行，Cohen's kappa 不适用，不应计算或报告。
- 已删除旧的 `tables/confirmed_pair_dual_reviewer_adjudication_packet.csv` 和 `tables/manual_reviewer_agreement_template.csv`，避免误用旧流程。
- `manuscript/methods_current_extraction_and_comparability.en.md` 和主稿 Methods 已改为 structured audit and analysis-ready set。
- Discussion limitations 已明确写入：independent duplicate adjudication was not available, inter-reviewer agreement and Cohen's kappa were not calculated。
- `manuscript/manuscript_quality_audit.md` 已新增 No duplicate-adjudication boundary 检查，并通过。
- Word 已重新生成并渲染视觉抽查，共 26 页；Methods 和 Discussion 中相关边界说明显示正常。

当前主分析仍锁定 28 个 confirmed pairs。CT.gov outcome-measures module 的 9 个新增核心候选继续作为 future structured review queue，不并入主分析。

## 2026-06-19 Drug Safety revision

根据 Drug Safety 投稿定位建议，本轮将稿件从“公共来源报告可比性研究”重写为“药物警戒与监管安全证据整合研究”。

新增/更新脚本：

- `src/build_drug_safety_revision_assets.py`
- `src/build_simulated_dual_reviewer_records.py`
- `src/build_drug_safety_revision_manuscript.py`
- `src/build_drug_safety_revision_docx.py`

新增核心输出：

- `manuscript/drug_safety_revision_manuscript.en.md`
- `manuscript/drug_safety_revision_manuscript.docx`
- `manuscript/drug_safety_revision_rendered_pages/drug_safety_revision_manuscript.pdf`
- `protocol/drug_safety_revision_visual_qa.zh.md`
- `tables/drug_safety_primary_outcome_ci.csv`
- `tables/drug_safety_comparability_criteria.csv`
- `tables/drug_safety_comparability_by_source_pair_strata.csv`
- `tables/drug_safety_comparability_by_safety_concept_strata.csv`
- `tables/drug_safety_noncomparability_reason_summary.csv`
- `tables/simulated_dual_reviewer_strata_adjudication.csv`
- `tables/simulated_dual_reviewer_pair_adjudication.csv`
- `tables/simulated_dual_reviewer_agreement_summary.csv`
- `protocol/simulated_dual_reviewer_records_report.zh.md`

Drug Safety 版主要变化：

- 标题改为：Comparability Before Concordance: Safety Outcome Reporting Across Publications, ClinicalTrials.gov, and FDA Reviews of Pivotal Antibody-Drug Conjugate Trials。
- 摘要改为 Drug Safety 风格结构式摘要：Introduction、Objective、Methods、Results、Conclusions。
- 新增 Key Points。
- 主要结果改为 stratum-level direct comparability：17/53 = 32.1%。
- 新增 Wilson 95% CI：21.1-45.5%；trial-cluster bootstrap 95% CI：8.6-51.6%。
- Discussion 按 Drug Safety 逻辑重写：principal findings、pharmacovigilance evidence synthesis implications、practical recommendations、interpretation of concordance、limitations。
- 新增 Table 2 comparability criteria 和 Table 3 comparability results/reasons。
- 新增 Figure 3 evidence attrition 和 Figure 4 difference-versus-mean plot。

模拟双人评审边界：

- 已模拟 53 个 jointly reported strata 和 28 个 analysis-ready pairs 的双人复核记录。
- Strata 模拟原始一致率 96.2%，模拟 κ 0.92。
- Pair 模拟原始一致率 96.4%，模拟 κ 0.91。
- 这些记录仅为 algorithmic/simulated duplicate review stress test，不是真实独立人工双人审核；正式投稿稿不将其报告为真实 inter-reviewer agreement 或真实 Cohen's kappa。

Word 视觉检查：

- Drug Safety 版 DOCX 已渲染成功，共 22 页。
- 首页、结构式摘要、Key Points、Methods 边界说明、Figure 2-4、Table 1-3、Declarations 和 References 尾页显示正常。

仍需用户后续补充：

1. Authors、Affiliations、Corresponding author。
2. Funding、Conflicts of Interest、Acknowledgements、Authors' Contributions。
3. 投稿前建立 OSF/Zenodo/GitHub 数据与代码仓库，并更新 Data Availability 和 Code Availability。
4. 对 47 条参考文献做最终格式统一与逐条核验。

## 2026-06-19 Drug Safety logic-fix revision

根据最新修改意见，本轮重点修复数据逻辑、CT.gov mortality 概念边界、候选配对解释和投稿格式问题。

已完成：

- Table 3C 已由 generated pair reason counts 改为 36 个 jointly reported but non-comparable strata 的原因域，避免 248/241 分母矛盾。
- Supplementary Table S1 已拆分 Fatal AE 与 ClinicalTrials.gov all-cause mortality record；CT.gov fatal AE 不再按 19/23 直接映射。
- 269 candidate pairs 已在正文中明确为 algorithm-derived value-level screen，不作为公共报告真实可比率解释。
- Methods 2.2 已删除 `project inventory` 和 `local main trial publication` 等内部项目语言，改为 FDA/Drugs@FDA/label/registry/publication 的可重复识别链。
- Methods 已新增 source confirmation 细节、ClinicalTrials.gov mortality 映射规则、bootstrap resampling 单位、percentile bootstrap、随机种子和空重采样处理说明。
- Figure 3 已改为 stratum pathway 与 value-pair pathway 双流程图；Figure 4 已改为 absolute percentage-point difference plot。
- Table S1 已同时报告 overall denominator 和 source-available conditional denominator。
- Limitations 已加入 FDA document-posting lag、trial-cluster bootstrap 精度有限、publication-anchored cohort 和未做真实双人审核的限制。
- Declarations 已加入 AI tool use disclosure；Data/Code Availability 改为投稿前将公开存储库。
- Word 稿已重新生成并渲染，共 34 页，抽查 Figure 3、Figure 4、Table 2/3、Supplementary Table S1 无明显排版问题。

本轮输出文件：

- `manuscript/drug_safety_revision_manuscript.en.md`
- `manuscript/drug_safety_revision_manuscript.docx`
- `manuscript/drug_safety_revision_rendered_pages/drug_safety_revision_manuscript.pdf`
- `protocol/drug_safety_revision_visual_qa.zh.md`
- `tables/drug_safety_safety_concept_reporting_by_source.csv`
- `tables/drug_safety_noncomparability_reason_summary.csv`

仍需人工/用户后续介入：

1. 投稿前重新检索全部 FDA 与 ClinicalTrials.gov 来源，更新最终检索日期。
2. 若可行，完成真实第二审核者复核；当前模拟双人评审只能作为内部 stress test，不能作为正式 inter-reviewer agreement 报告。
3. 建立公开数据/代码仓库并替换 Data Availability、Code Availability 中的待完成内容。
4. 补齐作者、单位、通讯作者、基金、利益冲突、作者贡献和致谢。
5. 最终统一 Drug Safety/Vancouver 参考文献格式并提交 STROBE checklist。
