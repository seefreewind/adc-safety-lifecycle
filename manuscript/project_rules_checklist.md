# Project Rules Checklist

## Manuscript Rules

- Use a BMC-style clinical/database research article structure unless a target journal overrides it.
- Use in-text references in the main text, not only a reference list.
- Cite background, rationale, prior-work comparison, interpretation, and limitation claims sentence by sentence.
- Do not place literature citations in Methods or Results unless required for a database, guideline, or methodological source.
- Keep Methods reproducible: data source, date accessed, inclusion/exclusion criteria, software, versions, thresholds, and parameters must be explicit.
- Keep Results descriptive and statistical; do not interpret mechanisms in Results.
- Keep causal and clinical-translation wording conservative.
- Do not describe public-data, pharmacovigilance, MR, or machine-learning findings as clinically validated unless independent validation is available.
- Aim for about 50 references for the full manuscript unless the target journal has a different limit.
- Insert figures into Word manuscript near the first result paragraph where each is discussed when figure files exist.

## ADC Safety Lifecycle Rules

- The primary study object is not only the drug, but the chain of drug, approval event, pivotal trial, treatment arm, AE concept, and source document.
- Separate original accelerated approval evidence from confirmatory evidence.
- Do not compare sources unless safety population, data cutoff, treatment arm, dose, and AE definition are graded.
- A-grade source pairs are used for primary concordance analyses.
- B-grade source pairs are used only in sensitivity analyses.
- C-grade source pairs are summarized descriptively.
- For the current pilot analysis, the 13 A-grade pairs in `tables/table4_primary_numeric_discordance_pairs.csv` were accepted by the user as the primary numeric-discordance set on 2026-06-18.
- AEMS/FAERS has no exposed denominator; do not report incidence.
- Label change claims require a dated label version and section-level evidence.
- ClinicalTrials.gov outcomeMeasuresModule safety candidates are exploratory unless manually confirmed for treatment arm, denominator, analysis population, event definition, and time window.
- The user accepted on 2026-06-19 that the CT.gov full-module candidates should remain a supplementary manual-review queue and should not be merged into the 28 confirmed analysis-ready source pairs.

## Audit Fields Required For Extracted Values

- `document_id`
- `source_type`
- `source_url_or_local_path`
- `page_or_table_locator`
- `trial_id`
- `arm_id`
- `ae_original_term`
- `ae_standardized_term`
- `grade_category`
- `number_patients`
- `denominator`
- `percentage`
- `analysis_population`
- `data_cutoff_date`
- `extractor`
- `review_status`
