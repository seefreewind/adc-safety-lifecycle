#!/usr/bin/env python3
"""Assemble a Drug Safety-targeted manuscript revision."""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript"
TABLES = ROOT / "tables"
FIGURES = ROOT / "figures"
PROTOCOL = ROOT / "protocol"
OUT = MANUSCRIPT / "drug_safety_revision_manuscript.en.md"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def get_row(path: Path, key: str, value: str) -> dict[str, str]:
    for row in read_csv_rows(path):
        if row[key] == value:
            return row
    raise ValueError(f"Missing {value} in {path}")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def clean_reference_markdown(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if line.lstrip().startswith("- Supports:"):
            continue
        if "should be rechecked" in line:
            continue
        if "Final submission formatting" in line:
            continue
        line = re.sub(r"\s+PubMed:\s+https?://pubmed\.ncbi\.nlm\.nih\.gov/\d+/?", "", line)
        if line.startswith("# Primary trial publication references"):
            continue
        elif line.startswith("# Background and Discussion candidate references"):
            continue
        else:
            lines.append(line)
    return "\n".join(lines)


def md_table(rows: list[dict[str, str]], fields: list[tuple[str, str]]) -> str:
    lines = [
        "| " + " | ".join(label for _, label in fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(key, "")) for key, _ in fields) + " |")
    return "\n".join(lines)


def figure_link(path: Path, alt: str) -> str:
    return f"![{alt}]({path.resolve()})"


def table1() -> str:
    rows = read_csv_rows(TABLES / "table1_included_trial_characteristics.csv")
    fields = [
        ("trial_id", "Trial ID"),
        ("short_trial_name", "Trial"),
        ("nct_number", "NCT"),
        ("phase", "Phase"),
        ("design", "Design"),
        ("publication_status", "Publication"),
        ("ctgov_status", "ClinicalTrials.gov"),
        ("fda_review_status", "FDA review"),
        ("core_concepts_reported_any_source_count", "Core concepts reported"),
    ]
    return "### Table 1. Included pivotal ADC trials and structured source status\n\n" + md_table(rows, fields) + "\n\nNote: Core concepts reported refers to the number of seven predefined aggregate safety outcomes reported in at least one public source."


def table2() -> str:
    rows = read_csv_rows(TABLES / "drug_safety_comparability_criteria.csv")
    fields = [
        ("dimension", "Dimension"),
        ("primary_comparable", "Primary comparable"),
        ("sensitivity_only", "Sensitivity only"),
        ("non_comparable", "Non-comparable"),
    ]
    return "### Table 2. Cross-source safety outcome comparability criteria\n\n" + md_table(rows, fields)


def table3() -> str:
    source_rows = read_csv_rows(TABLES / "drug_safety_comparability_by_source_pair_strata.csv")
    concept_rows = read_csv_rows(TABLES / "drug_safety_comparability_by_safety_concept_strata.csv")
    reason_rows = read_csv_rows(TABLES / "drug_safety_noncomparability_reason_summary.csv")
    return "\n\n".join([
        "### Table 3. Cross-source comparability results and reasons for non-comparability",
        "A. Comparability by source pair",
        md_table(source_rows, [("source_pair", "Source pair"), ("jointly_reported_strata", "Jointly reported strata"), ("directly_comparable_strata", "Directly comparable strata"), ("directly_comparable_percent", "%"), ("wilson_95_ci", "Wilson 95% CI")]),
        "B. Comparability by safety concept",
        md_table(concept_rows, [("safety_concept", "Safety concept"), ("jointly_reported_strata", "Jointly reported strata"), ("directly_comparable_strata", "Directly comparable strata"), ("directly_comparable_percent", "%")]),
        "C. Primary mutually exclusive reason for non-comparability",
        md_table(reason_rows, [("reason", "Primary reason"), ("non_comparable_stratum_count", "Non-comparable strata"), ("percent", "%")]),
        "Note: Panel C is based on jointly reported strata classified as reported but non-comparable. When more than one mismatch was present, the primary reason was assigned using the following priority: ClinicalTrials.gov mortality mapping, ClinicalTrials.gov serious-adverse-event group or window metadata, FDA regulatory population or definition mismatch, and other denominator, arm, definition, causality, or timing mismatch.",
    ])


def table4() -> str:
    rows = read_csv_rows(TABLES / "count_rounding_concordance_summary.csv")
    fields = [
        ("analysis_tier", "Analysis tier"),
        ("count_rounding_concordance_class", "Count-compatibility class"),
        ("comparison_count", "Comparisons"),
        ("percent_within_tier", "% within tier"),
    ]
    return "### Table 4. Count-compatibility classes among confirmed comparison pairs\n\n" + md_table(rows, fields)


def supplementary_tables() -> str:
    concept_rows = read_csv_rows(TABLES / "drug_safety_safety_concept_reporting_by_source.csv")
    trial_rows = read_csv_rows(TABLES / "drug_safety_trial_level_comparability_distribution.csv")
    loto_rows = read_csv_rows(TABLES / "leave_one_trial_out_concordance.csv")
    primary_loto = [row for row in loto_rows if row["analysis_set"] == "primary_candidate"]
    parts = [
        "### Supplementary Table S1. Availability of prespecified aggregate safety concepts within extracted source modules",
        md_table(concept_rows, [("safety_concept", "Safety concept"), ("publication", "Publication"), ("ClinicalTrials.gov", "ClinicalTrials.gov"), ("FDA review", "FDA review")]),
        "Note: ClinicalTrials.gov all-cause mortality records were tabulated separately and were not classified as fatal adverse-event reporting unless the registry definition explicitly supported that mapping. A zero indicates that the prespecified aggregate concept was not available in the extracted module, not that no related safety information existed anywhere in the registry record.",
        "### Supplementary Table S2. Trial-level comparability distribution",
        md_table(trial_rows, [("trial_id", "Trial ID"), ("jointly_reported_strata", "Jointly reported strata"), ("directly_comparable_strata", "Directly comparable strata"), ("directly_comparable_percent", "%")]),
        "### Supplementary Table S3. Leave-one-trial-out analysis for primary comparisons",
        md_table(primary_loto, [("excluded_trial_id", "Excluded trial"), ("remaining_trial_count", "Remaining trials"), ("comparison_count", "Comparisons"), ("mean_abs_diff_pp", "Mean absolute difference, pp"), ("median_abs_diff_pp", "Median, pp"), ("max_abs_diff_pp", "Maximum, pp"), ("within_2pp_count", "Within 2 pp")]),
    ]
    return "\n\n".join(parts)


def build() -> str:
    ci = read_csv_rows(TABLES / "drug_safety_primary_outcome_ci.csv")[0]
    trial_comparability_summary = read_csv_rows(TABLES / "drug_safety_trial_level_comparability_summary.csv")[0]
    primary = get_row(TABLES / "confirmed_concordance_overall_stats.csv", "analysis_set", "primary_candidate")
    sensitivity = get_row(TABLES / "confirmed_concordance_overall_stats.csv", "analysis_set", "sensitivity_candidate")
    trial_weighted = get_row(TABLES / "trial_weighted_concordance_sensitivity.csv", "analysis_set", "primary_candidate")
    dreamm_loto = get_row(TABLES / "leave_one_trial_out_concordance.csv", "excluded_trial_id", "TRIAL002")
    count_exact = get_row(TABLES / "count_rounding_concordance_summary.csv", "count_rounding_concordance_class", "exact_count_and_percentage_concordance")
    count_same_ndiff = get_row(TABLES / "count_rounding_concordance_summary.csv", "count_rounding_concordance_class", "same_count_denominator_percentage_display_difference")
    count_rounding = get_row(TABLES / "count_rounding_concordance_summary.csv", "count_rounding_concordance_class", "rounding_compatible_concordance")
    count_close = get_row(TABLES / "count_rounding_concordance_summary.csv", "count_rounding_concordance_class", "numerically_close_but_not_count_confirmed")
    primary_refs = clean_reference_markdown(read_text(MANUSCRIPT / "primary_trial_reference_list.en.md"))
    background_refs = clean_reference_markdown(read_text(MANUSCRIPT / "background_discussion_reference_list.en.md"))

    fig1 = FIGURES / "manuscript" / "figure1_study_flow.png"
    fig2 = FIGURES / "manuscript" / "figure2_source_flow_heatmap.png"
    fig3 = FIGURES / "drug_safety_revision" / "figure3_drug_safety_attrition.png"
    fig4 = FIGURES / "drug_safety_revision" / "figure4_difference_vs_mean.png"

    return f"""# Cross-Source Comparability of Aggregate Safety Outcomes in Pivotal Antibody-Drug Conjugate Trials: A Regulatory Evidence Study

Authors: Da Lin1, Yu Zhang1

Affiliations: 1. Department of Ophthalmology, The Second Affiliated Hospital of Wenzhou Medical University, No. 109 Xueyuan West Road, Lucheng District, Wenzhou, Zhejiang Province, China

Corresponding author: Yu Zhang, No. 109 Xueyuan West Road, Lucheng District, Wenzhou, Zhejiang Province, China. Telephone: +86 15258639970. Email: 395630568@qq.com. Fax: Not available. ORCID: 0000-0001-8579-3692

## Abstract

### Introduction

Safety outcomes from pivotal drug trials are distributed across journal publications, clinical trial registries, and regulatory review documents. Differences in treatment arm, analysis population, denominator, adverse-event definition, causality attribution, and reporting window may limit valid integration of these sources.

### Objective

To evaluate the availability, comparability, and numerical concordance of core safety outcomes reported across public evidence sources for pivotal antibody-drug conjugate trials.

### Methods

We conducted a publication-anchored cross-sectional pharmacovigilance and regulatory evidence study of 23 pivotal antibody-drug conjugate trials. Seven aggregate safety outcomes were extracted from publications and supplementary materials, ClinicalTrials.gov results records, and US Food and Drug Administration review documents. Cross-source comparisons were assessed across trial, treatment arm, analysis population, denominator, safety concept, grade or seriousness, causality attribution, and reporting window. Numerical concordance was evaluated only among source-confirmed comparable pairs using pair-weighted, trial-weighted, leave-one-trial-out, and count-compatibility analyses.

### Results

Structured safety values were identified in publications for all 23 trials, in ClinicalTrials.gov records for 19 trials, and in trial-specific FDA review data for six trials. Among {ci['denominator']} trial-concept-source-pair strata in which related safety outcomes were reported by both sources, {ci['numerator']} were directly comparable ({ci['percent']}%; trial-cluster bootstrap 95% CI {ci['trial_cluster_bootstrap_95_ci_low_percent']}-{ci['trial_cluster_bootstrap_95_ci_high_percent']}; unclustered Wilson 95% CI {ci['wilson_95_ci_low_percent']}-{ci['wilson_95_ci_high_percent']}). The trial-level median directly comparable proportion was {trial_comparability_summary['median_directly_comparable_percent']}% (IQR {trial_comparability_summary['iqr_low_percent']}-{trial_comparability_summary['iqr_high_percent']}%). Among {primary['comparison_count']} primary comparisons from four trials, the trial-weighted mean absolute difference was {trial_weighted['trial_weighted_mean_abs_diff_pp']} percentage points and the pair-weighted mean was {primary['mean_abs_diff_pp']} percentage points. Most excluded strata involved differences in treatment arm, safety definition, analysis population, denominator, causality attribution, or reporting window.

### Conclusions

Among source pairs reporting related aggregate safety outcomes, direct comparability was frequently limited by differences in treatment arm, analysis population, denominator, safety definition, causality attribution, and observation window. In the limited subset of strictly aligned comparisons from four trials, observed numerical differences were small. Pharmacovigilance assessments and safety evidence syntheses should distinguish source availability, outcome reporting, comparability, and numerical concordance before interpreting cross-source differences.

## Key Points

- Safety outcomes with similar labels across publications, trial registries, and regulatory reviews frequently represented different treatment arms, populations, denominators, definitions, or reporting windows.
- Only approximately one third of jointly reported safety strata were suitable for direct comparison, although numerical differences were generally small after strict alignment.
- Pharmacovigilance assessments should establish cross-source comparability before interpreting numerical agreement or disagreement.

## Keywords

antibody-drug conjugate; pharmacovigilance; drug safety; ClinicalTrials.gov; FDA review; adverse events; regulatory science; evidence synthesis

## Introduction

Aggregate safety results from pivotal oncology trials are commonly consulted across several public sources, including journal publications, clinical trial registries, regulatory review documents, and product labels [24-29,36-43]. These sources are often treated as interchangeable in evidence synthesis, yet they may describe different treatment arms, safety populations, denominators, causality rules, adverse-event definitions, and observation windows [26-29,36-40]. In drug safety assessment, such differences can create the appearance of numerical disagreement even when underlying event reporting is not truly conflicting.

Antibody-drug conjugates (ADCs) provide a relevant setting for evaluating this problem. ADCs are an expanding oncology drug class with payload-, target-, and organ-specific toxicity patterns, and pivotal ADC trials often support regulatory decisions under accelerated or indication-specific approval pathways [24,25,30-35,41-47]. Because public safety evidence for these agents is distributed across publications, ClinicalTrials.gov, and FDA reviews, cross-source integration requires more than matching adverse-event labels.

The central premise of this study was that comparability should be established before concordance is interpreted. We therefore evaluated public safety reporting for pivotal ADC trials as a pharmacovigilance and regulatory evidence problem. The primary outcome was the proportion of jointly reported trial-concept-source-pair strata that were directly comparable. Secondary outcomes included source availability, reporting completeness for seven aggregate safety outcomes, reasons for non-comparability, and numerical concordance conditional on source-confirmed comparability.

## Methods

### Study Design

We conducted a publication-anchored cross-sectional pharmacovigilance and regulatory evidence study evaluating the reporting, comparability, and numerical concordance of aggregate safety outcomes across public sources for pivotal ADC trials. The unit of trial inclusion was the pivotal ADC clinical trial, and the unit of the primary comparability outcome was the trial-concept-source-pair stratum.

### Study Cohort and Eligibility Criteria

FDA-approved ADC products and indications were screened from FDA approval announcements, prescribing information, Drugs@FDA records, product labels, and review-document inventories through 31 May 2026. For each indication or regulatory package considered in the project inventory, approval-supporting, accelerated-approval, confirmatory, and indication-specific trials were identified from FDA multidisciplinary reviews, approval summaries, product labels, trial registry records, and primary trial publications. ADCs were operationally defined as therapeutic agents composed of a monoclonal antibody or antibody fragment linked to a cytotoxic payload. A pivotal trial was defined as a trial identified in regulatory or publication records as central to approval, accelerated approval, confirmatory evaluation, or an indication-specific efficacy and safety assessment. Single-arm trials supporting accelerated approval and randomized confirmatory or phase III trials were eligible. When a trial included multiple ADC dose cohorts or treatment arms, each arm was retained in the source-comparison data structure, but trial-level inclusion was counted once.

The analytic cohort was publication-anchored: a trial was included in the main manuscript dataset only when a primary trial publication was available and could be matched to the regulatory or registry trial record. This design ensured that all included trials had at least one peer-reviewed public safety source and allowed the study to focus on cross-source transmission of aggregate safety summaries rather than complete regulatory-trial enumeration. It should therefore not be interpreted as a complete regulatory-anchored cohort of all ADC approvals or supplemental indications. Withdrawn or superseded indications were not excluded if the pivotal trial remained relevant to the ADC safety evidence base. The resulting cohort included 23 pivotal ADC trials. The regulatory role and eligibility rationale for each included trial are provided in the supplementary audit files.

### Data Sources and Safety Outcomes

For each trial, we integrated three public source types: primary publications and supplementary materials, ClinicalTrials.gov results records, and FDA review documents. Seven aggregate safety outcomes were evaluated: any adverse event, grade 3 or higher adverse event, serious adverse event, fatal adverse event, adverse event leading to discontinuation, dose interruption or delay, and dose reduction. ClinicalTrials.gov all-cause mortality records were tracked separately and were not classified as fatal adverse-event reporting unless the registry definition explicitly supported that mapping. Each extracted row retained source type, document identifier, source locator, treatment arm, denominator, percentage, numerator when available, analysis population, adverse-event concept, grade or seriousness, causality attribution, and available timing metadata.

### Comparability Assessment

Cross-source comparisons were generated within trial and safety-concept strata. Comparability was evaluated using rule-based criteria covering trial identity, treatment arm and dose, analysis population, denominator, safety concept, grade or seriousness, causality attribution, and observation window. Primary-comparable pairs required close alignment across these dimensions. Sensitivity-only pairs were retained when a limited denominator, population, or terminology difference was documented and judged capable of affecting interpretation without making the pair unusable. Non-comparable pairs were excluded from numerical concordance when they involved different treatment arms or dose cohorts, incompatible safety definitions, all-cause mortality compared with fatal adverse events, substantial denominator or population differences, causality mismatch, or insufficient timing metadata.

Both sides of each analysis-ready pair were rechecked against the original publication table, FDA review page, or archived ClinicalTrials.gov results record. Source confirmation required agreement in the reported term, numerical value, denominator when available, treatment arm, analysis population, and source locator. PDF-derived values were confirmed from page or table locators, and ClinicalTrials.gov-derived values were confirmed from the structured results module used in the project archive. A structured audit trail was used rather than formal independent duplicate adjudication. Each retained pair preserved the relevant source locator, source-confirmation status, visual-audit status, and reason for inclusion. Because independent duplicate reviewer fields were not collected, inter-reviewer agreement and Cohen's kappa were not calculated.

Trial-concept-source-pair strata and value-level comparison pairs were distinct analytic units. A stratum was defined by a trial, safety concept, and source pair. A single stratum could generate more than one value-level pair when more than one dose cohort, treatment arm, or source row was present. For example, a publication-FDA stratum with two matched dose cohorts could contribute two primary comparison pairs after the arm, denominator, population, and safety definition were confirmed. Numerical summaries were therefore restricted to confirmed value-level pairs and were interpreted separately from the stratum-level primary comparability outcome.

### Outcomes and Statistical Analysis

The primary outcome was stratum-level direct comparability among jointly reported safety strata. The numerator was the number of jointly reported trial-concept-source-pair strata classified as directly comparable, and the denominator was the number of strata in which both source sides reported a related safety value. The primary uncertainty interval was a trial-cluster percentile-bootstrap 95% confidence interval using 10,000 resamples of trials. Each bootstrap resample selected trials with replacement and retained all jointly reported strata within each selected trial; resamples with no jointly reported stratum would have been skipped, although none occurred in the implemented analysis. The random seed was 20260619. A Wilson 95% confidence interval was calculated as an unclustered supplementary description.

Secondary analyses summarized source availability, availability of prespecified aggregate safety concepts within extracted source modules, comparability by source pair and safety concept, reasons for non-comparability, and numerical concordance among confirmed analysis-ready pairs. Numerical concordance was summarized using trial-weighted and pair-weighted mean absolute percentage-point differences. Leave-one-trial-out analyses assessed whether results were driven by individual trials. Count-compatibility classes distinguished exact count and percentage concordance, rounding-compatible concordance, same count and denominator with displayed percentage differences, and numerical closeness without count confirmation.

### Use of Artificial Intelligence Tools

During manuscript preparation and code development, an OpenAI large language model was used for language editing, coding assistance, and internal consistency checks. The tool was not used as an independent reviewer for trial inclusion, data extraction, or final comparability adjudication. The authors reviewed the analytic tables, code outputs, and manuscript text and take responsibility for the final work.

## Results

### Availability of Public Safety Evidence

The analysis included 23 pivotal ADC trials. Structured publication safety values were available for all 23 trials, ClinicalTrials.gov adverse-event module values for 19 trials, and trial-specific structured FDA review values for six trials. FDA documents were retrieved for additional ADC products or review packages, but document retrieval did not necessarily mean that trial-specific, structurally extractable safety values were available.

### Availability of Prespecified Aggregate Safety Concepts

Six trials reported all seven core aggregate safety outcomes in at least one public source. Availability of prespecified aggregate safety concepts varied by source type and safety concept (Table 1; Online Resource 1). Publications provided the broadest structured source base by design. ClinicalTrials.gov adverse-events module records more consistently captured serious adverse events and mortality-related records than dose-modification outcomes; however, registry all-cause mortality records were not treated as fatal adverse-event records unless the registry definition supported that mapping. A zero in the ClinicalTrials.gov module summary means that the prespecified aggregate concept was not available in the extracted adverse-events module, not that no related safety information existed elsewhere in the registry record. Trial-specific FDA structured extraction was available for fewer trials.

### Cross-Source Comparability

Among {ci['denominator']} jointly reported trial-concept-source-pair strata, {ci['numerator']} were directly comparable, corresponding to a stratum-level direct comparability proportion of {ci['percent']}% (trial-cluster bootstrap 95% CI {ci['trial_cluster_bootstrap_95_ci_low_percent']}-{ci['trial_cluster_bootstrap_95_ci_high_percent']}; unclustered Wilson 95% CI {ci['wilson_95_ci_low_percent']}-{ci['wilson_95_ci_high_percent']}). The trial-level median directly comparable proportion was {trial_comparability_summary['median_directly_comparable_percent']}% (IQR {trial_comparability_summary['iqr_low_percent']}-{trial_comparability_summary['iqr_high_percent']}%; Online Resource 2). A separate value-level screen generated 269 algorithm-derived candidate pairings, of which 28 were retained as analysis-ready. This value-pair yield reflected the screening algorithm, multiple arms, dose cohorts, and repeated source rows within some strata, and was not interpreted as the primary public-reporting comparability rate (Fig. 1; Table 2; Table 3).

Non-comparability was most often explained by ClinicalTrials.gov mortality records not being classifiable as fatal adverse-event reporting, registry serious adverse-event records differing by group, arm, population, or window metadata, and FDA regulatory safety populations or definitions not aligning with publication strata. These exclusions indicate that many public safety values with similar labels were related but not interchangeable.

### Conditional Numerical Concordance

In the limited subset of strictly aligned comparisons from four trials, observed numerical differences were small. Among {primary['comparison_count']} primary comparisons, the trial-weighted mean absolute difference was {trial_weighted['trial_weighted_mean_abs_diff_pp']} percentage points and the pair-weighted mean was {primary['mean_abs_diff_pp']} percentage points. All primary comparisons were within 2 percentage points (Fig. 4). After excluding DREAMM-2, which contributed the largest number of primary comparisons, the pair-weighted mean absolute difference was {dreamm_loto['mean_abs_diff_pp']} percentage points across {dreamm_loto['comparison_count']} remaining primary comparisons; the full leave-one-trial-out results are provided in Online Resource 3. Sensitivity comparisons had a pair-weighted mean absolute difference of {sensitivity['mean_abs_diff_pp']} percentage points and a maximum difference of {sensitivity['max_abs_diff_pp']} percentage points. Count-compatibility review showed {count_exact['comparison_count']} exact count and percentage matches, {count_same_ndiff['comparison_count']} same-count and same-denominator pairs with displayed percentage differences, {count_rounding['comparison_count']} rounding-compatible pair, and {count_close['comparison_count']} numerically close but count-unconfirmed pairs in the primary set (Table 4).

### Exploratory ClinicalTrials.gov Outcome-Measures Screen

An exploratory screen of the ClinicalTrials.gov outcome-measures module identified 492 safety-related candidate rows, including 186 high-priority core candidates, 269 laboratory-abnormality or disease-specific exploratory candidates, and 37 lower-priority or duplicate-context safety-related candidates that were retained only in the manual-review queue. Relative to the adverse-events module, this screen identified nine incremental core trial-concept candidates. These candidates were retained as a future structured review queue and were not merged into the primary comparability or concordance analyses.

## Figures

### Fig. 1 Study flow and analysis layers

{figure_link(fig1, 'Figure 1. Study flow and analysis layers')}

Fig. 1 summarizes the publication-anchored trial cohort and the three analysis layers used to separate source flow, comparability, value-pair yield, and numeric concordance.

### Fig. 2 Availability of structured safety data by trial and source

{figure_link(fig2, 'Figure 2. Source-flow heatmap')}

Fig. 2 shows whether each source type produced structured trial-specific safety values, only a retrieved source without structured core values, or no linked source.

### Fig. 3 Flow from reported safety evidence to comparable analyses

{figure_link(fig3, 'Figure 3. Evidence flow')}

Fig. 3 separates the stratum pathway used for the primary comparability outcome from the value-pair pathway used for conditional numerical concordance. Counts in the two pathways use different units and should not be read as a single attrition sequence.

### Fig. 4 Absolute difference-versus-mean plot of confirmed comparison pairs

{figure_link(fig4, 'Figure 4. Absolute difference-versus-mean plot')}

Fig. 4 plots the absolute percentage-point difference between source percentages against the mean of the two source percentages for confirmed comparison pairs. The 2 percentage-point line is a descriptive reference line, not a formal equivalence threshold or limit of agreement.

## Tables

{table1()}

{table2()}

{table3()}

{table4()}

## Discussion

### Principal Findings

The principal finding was not numerical disagreement between public sources, but the limited proportion of jointly reported safety outcomes that could validly be compared. Only about one third of jointly reported strata were directly comparable, and the cluster-bootstrap interval was wide, indicating limited precision after accounting for trial clustering. The main barriers were differences in treatment arm or dose, denominator, analysis population, causality attribution, safety definition, and reporting window. In the limited subset of strictly aligned comparisons, observed numerical differences were small, whereas sensitivity comparisons showed larger differences. This pattern supports comparability assessment as a necessary step before interpreting cross-source safety differences.

### Implications for Pharmacovigilance Evidence Synthesis

For pharmacovigilance evidence synthesis, a safety outcome label alone is insufficient to establish comparability. Serious adverse events, grade 3 or higher adverse events, treatment-related adverse events, fatal adverse events, and all-cause mortality represent different constructs and should not be combined without checking definitions and observation windows [27-29,36-40]. Similarly, a pooled regulatory safety population cannot automatically substitute for a trial-specific publication population, and cumulative safety percentages can differ when data cutoffs or follow-up windows differ. Without these checks, cross-source evidence synthesis may generate apparent safety differences that reflect metadata mismatch rather than conflicting safety information.

### Practical Recommendations

Publicly reported aggregate safety outcomes should include a minimum metadata set: trial and treatment arm, dose or regimen, numerator, denominator, analysis population, event definition, grade or seriousness, causality attribution, observation window, data cutoff, and source table or locator. Trial publications should provide n/N and percentages rather than percentages alone. ClinicalTrials.gov records should make clearer distinctions among serious adverse events, fatal adverse events, all-cause mortality, and treatment-related fatal events. Regulatory reviews should, where possible, present both pooled approval-review safety populations and pivotal-trial-specific safety populations with treatment arm, denominator, and data cutoff. Systematic reviewers and pharmacovigilance researchers should perform comparability assessment before selecting or pooling public safety percentages.

### Interpretation of Concordance

Concordance across publications, ClinicalTrials.gov, and FDA reviews should not be interpreted as independent validation of underlying safety events. These sources commonly derive from overlapping sponsor-level trial datasets, similar data cutoffs, and related statistical outputs. Concordance in this study therefore reflects consistency in public transmission of aggregate safety results after alignment, not proof that all events were captured or that one source is a gold standard.

### Limitations

This study has limitations. First, the current cohort was publication-anchored and should not be interpreted as a complete regulatory-anchored enumeration of all ADC approvals, supplemental indications, or confirmatory trials through the cutoff date. This design also makes publication availability partly design-determined rather than a fully independent empirical finding. Second, trial-specific structured FDA review extraction was available for only six trials, limiting three-source comparisons. Recently approved indications may also have been disproportionately classified as lacking structured regulatory data because of document-posting lag near the source-search cutoff. Third, the primary numerical concordance analysis included 21 comparisons from four trials, with DREAMM-2 contributing multiple pairs. Fourth, the trial-cluster bootstrap interval for the primary comparability proportion was wide, indicating limited precision after accounting for clustering within trials. Fifth, independent duplicate adjudication was not performed; a structured audit trail, visual-source confirmation, trial-weighted summaries, leave-one-trial-out analyses, and count-compatibility checks were used to reduce this limitation, but inter-reviewer agreement was not measured. Sixth, the study used publicly available aggregate safety information and did not include clinical study reports, case-report forms, or sponsor databases. Seventh, the seven core aggregate outcomes were selected to study cross-source transmission of aggregate safety summaries and do not represent the full ADC toxicity spectrum, including interstitial lung disease, ocular toxicity, neuropathy, or hepatic events [30-35]. Finally, the study focused on FDA and ClinicalTrials.gov sources, and generalizability to other regulatory systems requires further evaluation.

## Conclusions

Among source pairs reporting related aggregate safety outcomes, direct comparability was frequently limited by differences in treatment arm, analysis population, denominator, safety definition, causality attribution, and observation window. In the limited subset of strictly aligned comparisons, observed numerical differences were small. These findings support explicit metadata-based comparability assessment before aggregate safety results from publications, trial registries, and regulatory reviews are combined or interpreted as concordant.

## Supplementary Information

{supplementary_tables()}

Additional supplementary materials include the final analysis audit index, structured audit packet, source-confirmation outputs, non-comparability rationale tables, and ClinicalTrials.gov outcome-measures candidate triage files.

## Acknowledgements

None.

## Declarations

### Funding

The authors received no specific funding for this work.

### Conflicts of Interest

The authors declare no competing interests.

### Ethics Approval

Not applicable. This study used publicly available aggregate trial reports and regulatory documents.

### Consent to Participate

Not applicable.

### Consent for Publication

Not applicable.

### Availability of Data and Material

The derived analytic tables, comparability decisions, audit outputs, figure source files, and analysis code are available in Zenodo at https://zenodo.org/records/20768613 and GitHub at https://github.com/seefreewind/adc-safety-lifecycle. Copyrighted full-text articles, publisher supplementary files, and FDA source PDFs are not redistributed.

### Code Availability

The custom code used to generate the analytic summaries, uncertainty estimates, audit outputs, and figures is available in the Zenodo record at https://zenodo.org/records/20768613 and in the GitHub repository at https://github.com/seefreewind/adc-safety-lifecycle.

### Authors' Contributions

Da Lin and Yu Zhang conceived and designed the study. Da Lin curated public-source data, performed comparability assessment, generated analytic outputs, and drafted the manuscript. Yu Zhang supervised the study, contributed to methodology, interpretation, and manuscript revision, and is the corresponding author. Both authors read and approved the final manuscript.

## References

{primary_refs}

{background_refs}
"""


def main() -> None:
    OUT.write_text(build() + "\n", encoding="utf-8")
    report = f"""# Drug Safety 下一版稿件生成报告

- 已生成：`{OUT.relative_to(ROOT)}`
- 已按 Drug Safety 方向重写标题、结构式摘要、Key Points、Methods、Results、Discussion、Declarations。
- 已将 17/53 作为主要结果，并加入 Wilson CI 和 trial-cluster bootstrap CI。
- 已加入 Table 2 comparability criteria、Table 3 comparability results/reasons、Figure 3 attrition、Figure 4 difference-versus-mean。
- 模拟双人评审记录仅作为 internal stress-test supplementary artifact，不作为真实 inter-reviewer agreement。
"""
    (PROTOCOL / "drug_safety_revision_manuscript_report.zh.md").write_text(report, encoding="utf-8")
    print(report.strip())


if __name__ == "__main__":
    main()
