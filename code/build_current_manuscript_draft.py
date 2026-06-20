#!/usr/bin/env python3
"""Assemble the current analysis into a manuscript working draft."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript"
PROTOCOL = ROOT / "protocol"
TABLES = ROOT / "tables"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def get_row(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str]:
    for row in rows:
        if row[key] == value:
            return row
    raise ValueError(f"Missing row where {key}={value}")


def count_where(rows: list[dict[str, str]], key: str, value: str) -> int:
    return sum(1 for row in rows if row.get(key) == value)


def get_metric(path: Path, metric: str) -> dict[str, str]:
    return get_row(read_csv_rows(path), "metric", metric)


def demote_markdown_headings(text: str, from_level: int = 2) -> str:
    prefix = "#" * from_level + " "
    return "\n".join(
        ("#" + line) if line.startswith(prefix) else line
        for line in text.splitlines()
    )


def clean_reference_markdown(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if line.lstrip().startswith("- Supports:"):
            continue
        if line.startswith("# Primary trial publication references"):
            lines.append("### Primary trial publication references")
        elif line.startswith("# Background and Discussion candidate references"):
            lines.append("### Background and Discussion references")
        else:
            lines.append(line)
    return "\n".join(lines)


def build_three_layer_results(
    primary: dict[str, str],
    sensitivity: dict[str, str],
) -> str:
    completeness = read_csv_rows(TABLES / "core_safety_reporting_completeness_by_trial.csv")
    comparability = get_row(
        read_csv_rows(TABLES / "comparability_yield_overall.csv"),
        "comparison_scope",
        "all_potential_source_pairs",
    )
    pair_rows = read_csv_rows(TABLES / "comparability_yield_by_source_pair.csv")
    five_state_rows = read_csv_rows(TABLES / "five_state_source_reporting_status_summary.csv")
    stratum_rate = get_metric(TABLES / "stratum_level_comparability_metrics.csv", "stratum_level_comparability_rate")
    stratum_concordance = get_metric(TABLES / "stratum_level_comparability_metrics.csv", "stratum_level_concordance_among_comparable")
    confirmed_pairs_in_strata = get_metric(TABLES / "stratum_level_comparability_metrics.csv", "confirmed_pairs_within_comparable_strata")
    trial_weighted = get_row(
        read_csv_rows(TABLES / "trial_weighted_concordance_sensitivity.csv"),
        "analysis_set",
        "primary_candidate",
    )
    dreamm_loto = get_row(
        [row for row in read_csv_rows(TABLES / "leave_one_trial_out_concordance.csv") if row["analysis_set"] == "primary_candidate"],
        "excluded_trial_id",
        "TRIAL002",
    )
    count_summary = [
        row for row in read_csv_rows(TABLES / "count_rounding_concordance_summary.csv")
        if row["analysis_tier"] == "primary_candidate"
    ]
    source_dist: dict[str, int] = {}
    for row in completeness:
        source_dist[row["structured_source_count"]] = source_dist.get(row["structured_source_count"], 0) + 1

    all_seven = sum(
        1 for row in completeness if row["core_concepts_reported_any_source_count"] == "7"
    )
    source_flow = {row["source_type"]: row for row in read_csv_rows(TABLES / "source_flow_status_summary.csv") if row["extraction_state"] == "structured_value_extracted"}
    fda_no_values = next(
        (
            row["trial_source_count"] for row in read_csv_rows(TABLES / "source_flow_status_summary.csv")
            if row["source_type"] == "FDA review" and row["extraction_state"] == "source_retrieved_no_structured_core_values"
        ),
        "0",
    )
    pub_n = source_flow.get("publication", {}).get("trial_source_count", "0")
    ctgov_n = source_flow.get("ClinicalTrials.gov", {}).get("trial_source_count", "0")
    fda_n = source_flow.get("FDA review", {}).get("trial_source_count", "0")

    pair_table = [
        "| Source pair | Potential comparisons | Confirmed analysis-ready | Confirmed yield (%) |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in pair_rows:
        pair_table.append(
            f"| {row['source_pair']} | {row['comparison_count']} | {row['confirmed_analysis_ready_count']} | {row['confirmed_comparability_yield_percent']} |"
        )

    five_state_table = [
        "| Status | Strata | Percent |",
        "| --- | ---: | ---: |",
    ]
    for row in five_state_rows:
        five_state_table.append(
            f"| {row['five_state_status']} | {row['stratum_count']} | {row['stratum_percent']} |"
        )

    return f"""## Results

### Layer 1: source flow and completeness across pivotal ADC trials

The source-flow and completeness layer included all 23 included pivotal trials. The cohort was publication-anchored; therefore, primary-publication availability for all trials was expected by design. Structured publication safety values were extracted for {pub_n} of 23 trials, ClinicalTrials.gov adverse-events module values for {ctgov_n} trials, and FDA review values for {fda_n} trials. FDA priority documents were present locally at the drug level for another {fda_no_values} trial-source records, but these files did not yield trial-specific structured core safety values in the current extraction. Across the seven prespecified core safety concepts, {all_seven} trials reported all seven concepts in at least one public source.

The source-count distribution was {source_dist.get('1', 0)} trials with one structured source, {source_dist.get('2', 0)} with two sources, and {source_dist.get('3', 0)} with three sources. This layer therefore used the full cohort rather than only the subset of trials that later yielded strictly comparable source pairs.

### Layer 2: comparability yield across potential source pairs

The source-comparability screen generated {comparability['comparison_count']} potential cross-source value pairings across trial, arm, and safety-concept strata. Automated rules classified {comparability['grade_A_count']} value pairings as grade A, {comparability['grade_B_count']} as grade B, and {comparability['grade_C_count']} as grade C. After prespecified rule-based grading and structured source confirmation, {comparability['confirmed_analysis_ready_count']} value pairings were retained as analysis-ready, corresponding to a value-pair yield of {comparability['confirmed_comparability_yield_percent']}%. This denominator is algorithm-dependent because trials with multiple arms, dose cohorts, or source rows can generate more potential value pairings.

{chr(10).join(pair_table)}

The main source-level pattern was that publication-FDA comparisons generated the highest confirmed yield, whereas ClinicalTrials.gov comparisons were more often limited by adverse-event time windows, all-cause mortality definitions, or registry module structure. Thus, the dominant issue was not large disagreement among aligned values, but the difficulty of establishing aligned definitions, denominators, analysis populations, and reporting windows across public sources.

### Layer 2b: five-state reporting status

For trial-by-concept-by-source-pair strata, source reporting was classified as unavailable, not reported in both sources, reported but non-comparable, comparable but discordant, or comparable and concordant. This five-state framing separated absence of a source from absence of a safety value and from reported values that could not be compared directly.

{chr(10).join(five_state_table)}

Among strata in which both source sides reported a related safety value, {stratum_rate['numerator']} of {stratum_rate['denominator']} were directly comparable, giving a stratum-level comparability rate of {stratum_rate['percent']}%. Among comparable strata, {stratum_concordance['numerator']} of {stratum_concordance['denominator']} were concordant. The {confirmed_pairs_in_strata['numerator']} confirmed comparison pairs arose from {stratum_rate['numerator']} comparable strata because one stratum could include more than one treatment arm, dose cohort, or source-row pairing.

### Layer 3: numeric concordance among confirmed comparable pairs

The confirmed numeric-concordance layer included {int(primary['comparison_count']) + int(sensitivity['comparison_count'])} source-comparison pairs: {primary['comparison_count']} primary-analysis comparisons and {sensitivity['comparison_count']} sensitivity-analysis comparisons. Primary-analysis comparisons covered DREAMM-2, EV-201, IMMU-132-01, and innovaTV 301. Sensitivity-analysis comparisons covered DESTINY-Breast01 and DREAMM-2.

Among the {primary['comparison_count']} primary-analysis comparisons, the pair-weighted mean absolute source difference was {primary['mean_abs_diff_pp']} percentage points, the median was {primary['median_abs_diff_pp']} percentage points, and the maximum was {primary['max_abs_diff_pp']} percentage points. {primary['zero_diff_count']} primary comparisons had zero difference, {primary['within_1pp_count']} were within 1 percentage point, and all {primary['comparison_count']} were within 2 percentage points. Because comparisons were clustered within trials, we also calculated trial-weighted summaries. The trial-weighted mean absolute difference was {trial_weighted['trial_weighted_mean_abs_diff_pp']} percentage points. After excluding DREAMM-2, which contributed the largest number of primary comparisons, the pair-weighted mean absolute difference was {dreamm_loto['mean_abs_diff_pp']} percentage points across {dreamm_loto['comparison_count']} remaining primary comparisons. Sensitivity-analysis comparisons had a pair-weighted mean absolute difference of {sensitivity['mean_abs_diff_pp']} percentage points and a maximum difference of {sensitivity['max_abs_diff_pp']} percentage points.

### Count and rounding compatibility

For confirmed comparisons, we classified concordance using event counts, denominators, percentages, and displayed percentage precision when these fields were available.

| Concordance class | Primary comparisons | Percent |
| --- | ---: | ---: |
{chr(10).join(f"| {row['count_rounding_concordance_class']} | {row['comparison_count']} | {row['percent_within_tier']} |" for row in count_summary)}

### Reasons for non-comparability

Pairs not retained in the confirmed analysis-ready set were most commonly excluded because they compared different treatment arms or dose cohorts, used different adverse-event definitions or causality rules, involved denominator or analysis-population differences, compared ClinicalTrials.gov all-cause mortality with fatal adverse events, or reflected ClinicalTrials.gov time-window differences. These exclusions indicate that many apparent cross-source safety values were related but not interchangeable."""


def build_ctgov_full_module_results() -> str:
    incremental_path = TABLES / "ctgov_full_module_incremental_candidate_summary.csv"
    concept_path = TABLES / "ctgov_full_module_candidate_triage_by_concept.csv"
    if not incremental_path.exists() or not concept_path.exists():
        return ""

    incremental_rows = read_csv_rows(incremental_path)
    concept_rows = read_csv_rows(concept_path)
    core_incremental = [
        row for row in incremental_rows
        if row.get("triage_class") == "core_candidate_needs_manual_mapping"
    ]
    exploratory_incremental = [
        row for row in incremental_rows
        if row.get("triage_class") == "exploratory_candidate_needs_manual_mapping"
    ]
    all_candidate_rows = sum(int(row["candidate_rows"]) for row in concept_rows)
    core_rows = sum(
        int(row["candidate_rows"])
        for row in concept_rows
        if "core_candidate_needs_manual_mapping" in row.get("triage_classes", "")
    )
    exploratory_rows = sum(
        int(row["candidate_rows"])
        for row in concept_rows
        if "exploratory_candidate_needs_manual_mapping" in row.get("triage_classes", "")
    )
    covered_trials = len({
        row.get("trial_or_nct", "")
        for row in incremental_rows
        if row.get("trial_or_nct", "")
    })

    return (
        "### Exploratory CT.gov full-module screen\n\n"
        "Because the structured ClinicalTrials.gov adverse-events module may not contain every "
        "safety-relevant aggregate outcome, we performed a prespecified exploratory screen of the "
        "ClinicalTrials.gov outcome-measures module. This screen identified "
        f"{all_candidate_rows} safety-related candidate rows. Rule-based triage retained {core_rows} rows "
        "as high-priority core safety candidates requiring manual mapping review and "
        f"{exploratory_rows} rows as exploratory laboratory-abnormality or disease-specific safety candidates. "
        f"Relative to the adverse-events module, the screen identified {len(core_incremental)} incremental "
        f"core trial-concept candidates and {len(exploratory_incremental)} incremental exploratory "
        f"trial-concept candidates across {covered_trials} trial records. These candidates were not merged "
        "into the primary concordance analysis pending manual confirmation of outcome definition, denominator, "
        "time window, and treatment-arm alignment."
    )


def build_background() -> str:
    return """## Background

Antibody-drug conjugates (ADCs) have become an increasingly important therapeutic class across hematologic malignancies and solid tumors, and pivotal ADC trials frequently support accelerated or regular regulatory approvals [24,25,41-43]. Safety interpretation is central to these approvals because ADCs combine target-mediated delivery with cytotoxic payloads, creating adverse-event profiles that may differ across payload class, linker design, target expression, tumor type, and treatment setting [24,25,30,31].

The safety evidence supporting an ADC approval is not contained in a single public source. Primary trial publications, supplementary appendices, ClinicalTrials.gov results records, FDA labels, and FDA multidisciplinary or medical reviews may each report overlapping but non-identical adverse-event outcomes [26,27,41-43]. These sources can differ in analysis population, treatment arm, dose cohort, data cutoff, causality attribution, event grouping, and follow-up window, which means that numerically similar safety percentages are not necessarily directly comparable [27-29].

Existing evaluations of clinical-trial reporting have shown that trial registries and publications can vary in completeness and specificity, including for harms reporting [27-29,36-40]. For ADCs, this issue is particularly relevant because treatment discontinuation, dose reduction, dose interruption, serious adverse events, and fatal adverse events are often needed to understand tolerability across the product lifecycle [30-35,44-47].

In the present study, we developed a source-aware workflow to extract, standardize, confirm, and compare core safety outcomes across public evidence sources for pivotal ADC trials. The objective was not to determine which source was correct, but to identify which source pairs were sufficiently aligned for numeric concordance analysis and to describe why other apparently related values should remain non-comparable."""


def build_abstract(primary: dict[str, str], sensitivity: dict[str, str]) -> str:
    completeness = read_csv_rows(TABLES / "core_safety_reporting_completeness_by_trial.csv")
    stratum_rate = get_metric(TABLES / "stratum_level_comparability_metrics.csv", "stratum_level_comparability_rate")
    trial_weighted = get_row(
        read_csv_rows(TABLES / "trial_weighted_concordance_sensitivity.csv"),
        "analysis_set",
        "primary_candidate",
    )
    all_seven = sum(
        1 for row in completeness if row["core_concepts_reported_any_source_count"] == "7"
    )
    return f"""## Abstract

### Background

ADC safety outcomes are reported across journal publications, trial registries, and regulatory review documents. Direct comparison across these sources can be limited by differences in treatment arm, denominator, safety population, adverse-event definition, and reporting window. We evaluated public ADC safety reporting as a three-layer problem: source availability and completeness, source-pair comparability, and numeric concordance among confirmed comparable pairs.

### Methods

We constructed a source-aware extraction and comparability workflow for 23 included pivotal ADC trials. Core safety concepts included any adverse event, grade 3 or higher adverse event, serious adverse event, fatal adverse event, adverse event leading to discontinuation, dose interruption or delay, and dose reduction. Safety values were extracted from publications and supplementary materials, FDA review documents, and ClinicalTrials.gov results records. We first assessed source flow and reporting completeness across all trials, then graded cross-source comparisons by alignment of trial, arm, denominator, population, causality, event definition, and time window. We reported both stratum-level comparability and value-pair yield, and assessed numeric concordance using pair-weighted, trial-weighted, leave-one-trial-out, and count/rounding-compatible summaries.

### Results

Publication-based structured safety values were extracted for all 23 included trials, FDA review values for 6 trials, and ClinicalTrials.gov event-group values for 19 trials. {all_seven} trials reported all seven core safety concepts in at least one public source. Among jointly reported trial-concept-source-pair strata, {stratum_rate['numerator']} of {stratum_rate['denominator']} were directly comparable, giving a stratum-level comparability rate of {stratum_rate['percent']}%. The value-pair screen generated 269 potential pairings, of which 28 were retained as analysis-ready. Among {primary['comparison_count']} primary-analysis comparisons, the pair-weighted mean absolute source difference was {primary['mean_abs_diff_pp']} percentage points and the trial-weighted mean was {trial_weighted['trial_weighted_mean_abs_diff_pp']} percentage points. All primary comparisons were within 2 percentage points.

### Conclusions

All 23 included pivotal ADC trials contributed to source-flow and completeness analyses, whereas numeric concordance was restricted to a smaller adjudicated subset. Source-confirmed core safety values were closely concordant when comparison was restricted to aligned trial populations and adverse-event definitions, but most jointly reportable safety strata were not directly comparable. ADC safety evidence synthesis should therefore preserve source-level metadata and distinguish retrieval, structured extraction, comparability, and numeric concordance."""


def build_discussion(primary: dict[str, str], sensitivity: dict[str, str]) -> str:
    comparability = get_row(
        read_csv_rows(TABLES / "comparability_yield_overall.csv"),
        "comparison_scope",
        "all_potential_source_pairs",
    )
    stratum_rate = get_metric(TABLES / "stratum_level_comparability_metrics.csv", "stratum_level_comparability_rate")
    trial_weighted = get_row(
        read_csv_rows(TABLES / "trial_weighted_concordance_sensitivity.csv"),
        "analysis_set",
        "primary_candidate",
    )
    return f"""## Discussion

In this source-aware analysis of pivotal ADC trial safety reporting, all 23 included trials contributed to the source-flow and completeness layer, {stratum_rate['denominator']} jointly reported strata contributed to the stratum-level comparability analysis, {comparability['comparison_count']} generated value pairings contributed to the value-pair yield analysis, and {int(primary['comparison_count']) + int(sensitivity['comparison_count'])} confirmed pairs contributed to the numeric-concordance layer. This structure changes the interpretation of the study: the main finding is not simply that a small subset of aligned values agreed numerically, but that public ADC safety evidence often becomes non-comparable before numeric disagreement can even be assessed.

The source-flow layer showed complete publication retrieval by design, intermediate ClinicalTrials.gov adverse-event module extraction, and narrower trial-specific FDA review extraction. This pattern is expected for a publication-anchored public-evidence study, but it matters methodologically: a missing regulatory or registry source is different from a retrieved source that does not report a specific safety outcome, and both are different from a retrieved source that reports a value that cannot be structured. The five-state classification was therefore useful because it separated unavailable source strata, not-reported strata, reported but non-comparable values, and confirmed comparable values.

The comparability layer showed that {stratum_rate['numerator']} of {stratum_rate['denominator']} jointly reported strata were directly comparable, while only {comparability['confirmed_analysis_ready_count']} of {comparability['comparison_count']} generated value pairings were retained after prespecified grading and source confirmation. Publication-FDA comparisons had the highest confirmed yield, whereas ClinicalTrials.gov comparisons were more often limited by adverse-event module structure, all-cause mortality definitions, or registry time windows [26-29,36-40]. This finding supports a conservative approach to source synthesis: values that appear to describe similar safety concepts should not be treated as interchangeable unless arm, denominator, analysis population, causality, grade, seriousness, and time window can be aligned.

The numeric-concordance layer showed close agreement once such alignment was achieved. Among primary-analysis comparisons, the pair-weighted mean absolute difference was {primary['mean_abs_diff_pp']} percentage points and all {primary['comparison_count']} primary comparisons were within 2 percentage points. The trial-weighted mean was higher, at {trial_weighted['trial_weighted_mean_abs_diff_pp']} percentage points, showing that pair-weighted summaries were influenced by trials contributing many comparison pairs. The larger differences observed among sensitivity comparisons, with a mean absolute difference of {sensitivity['mean_abs_diff_pp']} percentage points and a maximum of {sensitivity['max_abs_diff_pp']} percentage points, were consistent with the reasons for downgrading: broader FDA approval-review safety populations in some cases and registry time-window or reporting-structure differences in others. These differences should not be interpreted as source error without further source-specific review.

Concordance across publications, ClinicalTrials.gov, and FDA reviews should not be interpreted as independent replication of underlying safety events. These sources commonly derive from overlapping sponsor-level trial datasets, similar data cutoffs, and related statistical outputs. Concordance in this study therefore primarily reflects consistency in the public transmission of safety results derived from overlapping trial datasets, rather than independent verification that all safety events were captured or that one source should be treated as a gold standard.

An exploratory screen of the ClinicalTrials.gov outcome-measures module indicated that registry records may contain additional safety-relevant aggregate outcomes outside the adverse-events module. We did not incorporate these candidates into the primary analysis because many require manual confirmation of treatment arm, denominator, analysis population, outcome definition, and time window. This decision preserves the specificity of the confirmed concordance analysis while creating a transparent queue for future extension of the data model.

This workflow has several strengths. It retains source provenance for each extracted value, maps source-specific adverse-event wording to prespecified safety concepts, separates primary and sensitivity comparisons, and requires both data-layer and visual-source confirmation before a pair is considered analysis-ready. The final audit index also records why source sides passed confirmation, which makes the analysis traceable during manuscript review. Because independent duplicate adjudication was not feasible for the current draft, the analysis was deliberately kept conservative: ClinicalTrials.gov outcome-measures candidates were not merged into the primary analysis, and the confirmed comparison set was evaluated using pair-weighted, trial-weighted, leave-one-trial-out, and count-compatibility summaries.

The study also has limitations. First, the current analysis is restricted to public sources and cannot resolve differences that arise from unpublished case-report forms, sponsor databases, or internal FDA datasets. Second, trial-specific FDA review structured extraction was available for only a subset of the 23 included trials, limiting the number of three-source comparisons. Third, independent duplicate adjudication was not available, so inter-reviewer agreement and Cohen's kappa were not calculated. To reduce the effect of this limitation, we used prespecified comparability rules, retained source locators and visual-audit status for confirmed pairs, separated primary and sensitivity analyses, and reported trial-weighted and leave-one-trial-out summaries. Fourth, the current version evaluates seven core aggregate safety concepts; event-level adverse events and adverse events of special interest should be evaluated in a subsequent analysis with appropriate trial-level clustering, especially because ADC toxicities may be organ-specific or payload-related [30-35].

Overall, these findings support a layered approach to ADC safety evidence synthesis. Availability and completeness should be assessed across all pivotal trials; comparability yield should be assessed across all generated source pairs; and numeric concordance should be reserved for source-confirmed comparable pairs. This framework prevents a small set of highly aligned pairs from carrying the entire interpretation while still preserving the high-confidence concordance analysis where it is justified."""


def build_citation_todos() -> str:
    todos = [
        ("ADC approvals and clinical development landscape", "Background paragraph 1", "candidate citations inserted [24,25,41-43]; final claim-alignment check required"),
        ("ADC mechanism and safety-profile overview", "Background paragraph 1", "candidate citations inserted [24,25,30,31]; final claim-alignment check required"),
        ("Public safety reporting across publications, registries, labels, and FDA reviews", "Background paragraph 2", "candidate citations inserted [26,27,41-43]; final claim-alignment check required"),
        ("Harms-reporting concordance across ClinicalTrials.gov and publications", "Background paragraph 3", "candidate citations inserted [27-29,36-40]; final claim-alignment check required"),
        ("ADC adverse-event profile and AESI context", "Background paragraph 3 and limitations", "candidate citations inserted [30-35,44-47]; final claim-alignment check required"),
        ("Use and limitations of ClinicalTrials.gov adverse-event modules", "Discussion paragraph 2", "candidate citations inserted [26-29,36-40]; final claim-alignment check required"),
        ("Trial-publication references for the 23 included pivotal ADC trials", "References and trial cohort table", "23/23 local main articles matched by PMID"),
        ("FDA review and label sources used for source confirmation", "References or data-source appendix", "public FDA accessdata URLs listed in confirmed source appendix"),
        ("ClinicalTrials.gov records used for source confirmation", "Data availability and source appendix", "ClinicalTrials.gov URLs listed in confirmed source appendix"),
    ]
    lines = [
        "# Citation TODO list for current manuscript draft",
        "",
        "This file lists citation needs that must be verified against real sources before the draft is submission-ready. No placeholder below should be converted into a numbered reference until the source has been checked for claim alignment.",
        "",
        "| Need | Manuscript location | Status |",
        "| --- | --- | --- |",
    ]
    for need, location, status in todos:
        lines.append(f"| {need} | {location} | {status} |")
    return "\n".join(lines)


def build_figures_and_table1() -> str:
    path = MANUSCRIPT / "manuscript_figures_and_table1.en.md"
    if path.exists():
        return read_text(path)
    return "## Figures and Trial Characteristics\n\nFigure and Table 1 materials have not yet been generated."


def main() -> None:
    MANUSCRIPT.mkdir(exist_ok=True)
    PROTOCOL.mkdir(exist_ok=True)

    overall = read_csv_rows(TABLES / "confirmed_concordance_overall_stats.csv")
    primary = get_row(overall, "analysis_set", "primary_candidate")
    sensitivity = get_row(overall, "analysis_set", "sensitivity_candidate")

    methods = read_text(MANUSCRIPT / "methods_current_extraction_and_comparability.en.md")
    if methods.startswith("# Methods draft:"):
        methods = methods.replace("# Methods draft: source extraction and comparability assessment", "## Methods", 1)
        methods = methods.replace("Date: 2026-06-19\n\n", "", 1)
    methods = demote_markdown_headings(methods)
    methods = methods.replace("### Methods", "## Methods", 1)
    methods = (
        methods
        + "\n\n### Three-layer analysis framework\n\n"
        "The analysis was organized into three layers. The first layer assessed source flow and reporting completeness across all 23 included trials. For each trial and source type, we recorded whether each of seven core safety concepts was reported and whether reported rows included a denominator, percentage, analysis population, data cutoff, and causality description. Source flow was separated into source retrieval, structured value extraction, concept reporting, and cross-source comparability. The second layer assessed comparability at two levels. Stratum-level comparability used trial-concept-source-pair strata in which both source sides reported a related safety value as the denominator. Value-pair yield used all generated source-value pairings as the denominator; this denominator can be larger because one stratum may include more than one treatment arm, dose cohort, or source-row pairing. The third layer assessed numeric concordance only among confirmed analysis-ready comparisons. To separate absence of a source from non-reporting and non-comparability, each trial-by-concept-by-source-pair stratum was also classified as unavailable, not reported in both sources, reported but non-comparable, comparable but discordant, or comparable and concordant."
        + "\n\n### Robustness and count-compatibility analyses\n\n"
        "Because multiple comparison pairs could arise from the same trial, numeric concordance was summarized using both pair-weighted and trial-weighted means. Trial-weighted analyses first calculated the mean absolute difference within each trial and then averaged trial-level means. Leave-one-trial-out analyses repeated the primary concordance summary after excluding each contributing trial in turn. For confirmed comparison pairs, concordance was further classified using event counts, denominators, displayed percentages, and displayed percentage precision. Classes included exact count and percentage concordance, rounding-compatible concordance, same count and denominator with a percentage display difference, numerically close but not count-confirmed, and discordant or sensitivity difference."
        + "\n\n### Structured audit and evidence boundary\n\n"
        "A structured audit trail was used as the feasibility-appropriate alternative to independent duplicate adjudication. Each retained pair was required to preserve trial, arm, denominator, safety-concept, population, source locator, source-confirmation, and visual-audit metadata. Inter-reviewer agreement was not calculated because independent duplicate reviewer fields were not collected. The ClinicalTrials.gov outcome-measures extension was therefore kept as a future review queue and was not merged into the primary comparability or concordance analyses."
        + "\n\n### Exploratory ClinicalTrials.gov full-module candidate screen\n\n"
        "As an exploratory extension, we screened the ClinicalTrials.gov outcome-measures module for safety-related aggregate outcomes that were not necessarily represented in the adverse-events module. Candidate outcomes were identified using prespecified safety terms and were triaged into high-priority core candidates, exploratory laboratory-abnormality or disease-specific safety candidates, low-priority safety-related candidates, and excluded mixed efficacy-safety endpoints. This screen was used to define a manual-review queue only; candidate rows were not incorporated into the primary comparability or concordance analyses."
    )
    results = read_text(MANUSCRIPT / "results_confirmed_source_concordance_section.en.md")
    if results.startswith("# Results"):
        results = results.replace("# Results", "## Results", 1)
    tables = read_text(MANUSCRIPT / "tables_confirmed_concordance.en.md")
    if tables.startswith("# Manuscript tables:"):
        tables = tables.replace("# Manuscript tables: confirmed source concordance", "## Tables", 1)
    tables = demote_markdown_headings(tables)
    tables = tables.replace("### Tables", "## Tables", 1)
    primary_references_path = MANUSCRIPT / "primary_trial_reference_list.en.md"
    primary_references = (
        clean_reference_markdown(read_text(primary_references_path))
        if primary_references_path.exists()
        else "Primary trial publication references have not yet been generated."
    )
    background_references_path = MANUSCRIPT / "background_discussion_reference_list.en.md"
    background_references = (
        clean_reference_markdown(read_text(background_references_path))
        if background_references_path.exists()
        else "Background and Discussion candidate references have not yet been generated."
    )

    draft = "\n\n".join(
        [
            "# Availability, comparability, and concordance of core safety outcomes across public evidence sources for pivotal antibody-drug conjugate trials",
            "",
            build_abstract(primary, sensitivity),
            "## Keywords\n\nantibody-drug conjugate; adverse event; FDA review; ClinicalTrials.gov; safety reporting; source concordance; regulatory evidence",
            build_background(),
            methods,
            build_three_layer_results(primary, sensitivity),
            build_ctgov_full_module_results(),
            build_figures_and_table1(),
            build_discussion(primary, sensitivity),
            "## Conclusions\n\nAcross 23 included pivotal ADC trials, public safety evidence was broadly available in publications but less consistently available as structured trial-specific values in FDA review documents and ClinicalTrials.gov records. Among jointly reported strata, only a subset was directly comparable, and the broader value-pair screen showed that most generated source pairings could not be compared directly because of differences in source structure, denominator, treatment arm, adverse-event definition, causality, or reporting window. When comparisons were restricted to source-confirmed aligned pairs, core safety outcomes showed close numeric concordance. Public ADC safety evidence synthesis should therefore distinguish source retrieval, reporting completeness, structured extraction, comparability, and numeric concordance rather than treating all reported safety percentages as interchangeable.",
            tables,
            "## Supplementary Information\n\nSupplementary audit materials include the final analysis audit index, the analysis-ready source-comparison audit trail, the confirmed source appendix, non-comparability rationale summaries, source-confirmation outputs, and the exploratory ClinicalTrials.gov full-module candidate triage tables.",
            "## Acknowledgements\n\nTo be completed.",
            "## Authors' contributions\n\nTo be completed.",
            "## Funding\n\nTo be completed.",
            "## Availability of data and materials\n\nAll extracted tables, source-confirmation packets, audit indices, source appendices, and manuscript drafts are currently stored in the project workspace. ClinicalTrials.gov and FDA review source links used in confirmed source comparisons are listed in the confirmed source appendix.",
            "## Ethics approval and consent to participate\n\nNot applicable. This study used publicly available aggregate trial reports and regulatory documents.",
            "## Consent for publication\n\nNot applicable.",
            "## Competing interests\n\nTo be completed.",
            "## References\n\nThe references below include 23 primary trial publications matched to local main-article files by PMID, followed by Background and Discussion references fetched from PubMed. Final submission formatting and claim-level verification are still required.\n\n"
            + primary_references
            + "\n\n"
            + background_references,
        ]
    )

    (MANUSCRIPT / "current_full_manuscript_draft.en.md").write_text(draft + "\n", encoding="utf-8")
    (MANUSCRIPT / "citation_todo_list.md").write_text(build_citation_todos() + "\n", encoding="utf-8")

    report = f"""# 当前英文主稿草稿生成报告

- 已生成：`manuscript/current_full_manuscript_draft.en.md`
- 已生成：`manuscript/citation_todo_list.md`
- 主稿包含：标题、结构式摘要、关键词、Background、Methods、Results、Discussion、Conclusions、Declarations 占位、References 占位、英文结果表。
- 主稿已加入 CT.gov outcome-measures module 探索性候选筛查说明；该部分不改变主分析的 28 个 confirmed analysis-ready pairs。
- 主稿已加入 stratum-level comparability、trial-weighted concordance、leave-one-trial-out、event-count/rounding compatibility 与 source-flow 分层结果。
- 已规范标题层级，并将结果表移动到 References 之前。
- 当前主分析比较：{primary['comparison_count']} 个；平均绝对差异 {primary['mean_abs_diff_pp']} 个百分点；最大 {primary['max_abs_diff_pp']} 个百分点。
- 当前敏感性比较：{sensitivity['comparison_count']} 个；平均绝对差异 {sensitivity['mean_abs_diff_pp']} 个百分点；最大 {sensitivity['max_abs_diff_pp']} 个百分点。
- 已将双人判读不可行时的替代方案写入主稿：structured audit trail、source confirmation、visual audit、trial-weighted/leave-one-trial-out 敏感性分析；不报告 Cohen's kappa。
- 注意：Background 和 Discussion 已插入候选引用编号；进入投稿稿前仍需逐句核验 claim alignment，并最终统一参考文献格式。
"""
    (PROTOCOL / "current_full_manuscript_draft_report.zh.md").write_text(report, encoding="utf-8")
    print(report.strip())


if __name__ == "__main__":
    main()
