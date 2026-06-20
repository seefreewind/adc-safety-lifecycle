#!/usr/bin/env python3
"""Build Drug Safety-targeted tables, uncertainty estimates, and figures."""

from __future__ import annotations

import csv
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "tables"
FIGURES = ROOT / "figures" / "drug_safety_revision"
MANUSCRIPT = ROOT / "manuscript"
PROTOCOL = ROOT / "protocol"

CORE_CONCEPTS = [
    ("any_adverse_event", "Any AE"),
    ("grade_3_or_higher_adverse_event", "Grade >=3 AE"),
    ("serious_adverse_event", "Serious AE"),
    ("fatal_adverse_event", "Fatal AE"),
    ("adverse_event_leading_to_discontinuation", "Discontinuation"),
    ("dose_interruption", "Interruption/delay"),
    ("dose_reduction", "Dose reduction"),
]

PALETTE = {
    "blue": "#2F6B9A",
    "teal": "#2A9D8F",
    "green": "#6A994E",
    "amber": "#DDA15E",
    "red": "#BC4749",
    "gray": "#8D99AE",
    "light": "#F3F6F8",
    "dark": "#1F2933",
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def md_table(rows: list[dict[str, str]], fields: list[tuple[str, str]]) -> str:
    lines = [
        "| " + " | ".join(label for _, label in fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(key, "")) for key, _ in fields) + " |")
    return "\n".join(lines)


def wilson_ci(x: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    phat = x / n
    denom = 1 + z * z / n
    centre = (phat + z * z / (2 * n)) / denom
    half = z * math.sqrt((phat * (1 - phat) / n) + (z * z / (4 * n * n))) / denom
    return max(0, centre - half), min(1, centre + half)


def bootstrap_cluster_ci(rows: list[dict[str, str]], reps: int = 10000) -> tuple[float, float]:
    rng = random.Random(20260619)
    by_trial: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_trial[row["trial_id"]].append(row)
    trials = sorted(by_trial)
    rates = []
    for _ in range(reps):
        sampled = [rng.choice(trials) for _ in trials]
        denom = 0
        num = 0
        for trial in sampled:
            for row in by_trial[trial]:
                denom += 1
                if row["five_state_status"].startswith("comparable_"):
                    num += 1
        if denom:
            rates.append(num / denom)
    rates.sort()
    return rates[int(0.025 * len(rates))], rates[int(0.975 * len(rates))]


def build_primary_outcome_table() -> dict[str, str]:
    rows = [
        row for row in read_rows(TABLES / "five_state_source_reporting_status.csv")
        if row["five_state_status"] in {"comparable_and_concordant", "comparable_but_discordant", "reported_but_non_comparable"}
    ]
    x = sum(1 for row in rows if row["five_state_status"].startswith("comparable_"))
    n = len(rows)
    lo, hi = wilson_ci(x, n)
    blo, bhi = bootstrap_cluster_ci(rows)
    out = {
        "metric": "stratum_level_direct_comparability",
        "numerator": str(x),
        "denominator": str(n),
        "percent": f"{x / n * 100:.1f}",
        "wilson_95_ci_low_percent": f"{lo * 100:.1f}",
        "wilson_95_ci_high_percent": f"{hi * 100:.1f}",
        "trial_cluster_bootstrap_95_ci_low_percent": f"{blo * 100:.1f}",
        "trial_cluster_bootstrap_95_ci_high_percent": f"{bhi * 100:.1f}",
        "bootstrap_reps": "10000",
    }
    write_csv(TABLES / "drug_safety_primary_outcome_ci.csv", [out], list(out))
    return out


def build_safety_concept_completeness() -> list[dict[str, str]]:
    rows = read_rows(TABLES / "core_safety_reporting_completeness_by_trial_source.csv")
    by_source = defaultdict(list)
    for row in rows:
        by_source[row["source_type"]].append(row)
    out = []
    concepts = CORE_CONCEPTS + [("ctgov_all_cause_mortality", "All-cause mortality record")]
    for concept, label in concepts:
        line = {"safety_concept": label}
        for source in ["publication", "ClinicalTrials.gov", "FDA review"]:
            source_rows = by_source[source]
            available_rows = [row for row in source_rows if row["source_available"] == "yes"]
            if concept == "ctgov_all_cause_mortality":
                count = sum(1 for row in source_rows if source == "ClinicalTrials.gov" and row.get("reports_fatal_adverse_event") == "yes")
                available_count = sum(1 for row in available_rows if source == "ClinicalTrials.gov" and row.get("reports_fatal_adverse_event") == "yes")
            elif concept == "fatal_adverse_event" and source == "ClinicalTrials.gov":
                count = 0
                available_count = 0
            else:
                key = "reports_" + concept
                count = sum(1 for row in source_rows if row.get(key) == "yes")
                available_count = sum(1 for row in available_rows if row.get(key) == "yes")
            if available_rows:
                line[source] = f"{count}/{len(source_rows)} overall; {available_count}/{len(available_rows)} available"
            else:
                line[source] = f"{count}/{len(source_rows)} overall; not available"
        out.append(line)
    write_csv(TABLES / "drug_safety_safety_concept_reporting_by_source.csv", out, ["safety_concept", "publication", "ClinicalTrials.gov", "FDA review"])
    return out


def build_comparability_by_source_pair() -> list[dict[str, str]]:
    strata = [
        row for row in read_rows(TABLES / "five_state_source_reporting_status.csv")
        if row["five_state_status"] in {"comparable_and_concordant", "comparable_but_discordant", "reported_but_non_comparable"}
    ]
    out = []
    for pair in sorted({row["source_pair"] for row in strata}):
        rows = [row for row in strata if row["source_pair"] == pair]
        x = sum(1 for row in rows if row["five_state_status"].startswith("comparable_"))
        n = len(rows)
        lo, hi = wilson_ci(x, n)
        out.append({
            "source_pair": pair,
            "jointly_reported_strata": str(n),
            "directly_comparable_strata": str(x),
            "directly_comparable_percent": f"{x / n * 100:.1f}" if n else "0.0",
            "wilson_95_ci": f"{lo * 100:.1f}-{hi * 100:.1f}",
        })
    write_csv(TABLES / "drug_safety_comparability_by_source_pair_strata.csv", out, list(out[0]))
    return out


def build_comparability_by_concept() -> list[dict[str, str]]:
    strata = [
        row for row in read_rows(TABLES / "five_state_source_reporting_status.csv")
        if row["five_state_status"] in {"comparable_and_concordant", "comparable_but_discordant", "reported_but_non_comparable"}
    ]
    label_by_key = dict(CORE_CONCEPTS)
    label_by_key["fatal_adverse_event"] = "Fatal AE / mortality-related"
    out = []
    for concept in [key for key, _ in CORE_CONCEPTS]:
        rows = [row for row in strata if row["safety_concept"] == concept]
        x = sum(1 for row in rows if row["five_state_status"].startswith("comparable_"))
        n = len(rows)
        out.append({
            "safety_concept": label_by_key[concept],
            "jointly_reported_strata": str(n),
            "directly_comparable_strata": str(x),
            "directly_comparable_percent": f"{x / n * 100:.1f}" if n else "0.0",
        })
    write_csv(TABLES / "drug_safety_comparability_by_safety_concept_strata.csv", out, list(out[0]))
    return out


def build_noncomparability_reasons() -> list[dict[str, str]]:
    counter = Counter()
    noncomparable = [
        row for row in read_rows(TABLES / "five_state_source_reporting_status.csv")
        if row["five_state_status"] == "reported_but_non_comparable"
    ]
    for row in noncomparable:
        pair = row["source_pair"]
        concept = row["safety_concept"]
        if concept == "fatal_adverse_event" and "ClinicalTrials.gov" in pair:
            reason = "ClinicalTrials.gov mortality record not classifiable as fatal adverse-event reporting"
        elif concept == "serious_adverse_event" and "ClinicalTrials.gov" in pair:
            reason = "Serious adverse-event reporting differed by registry group, arm, population, or window metadata"
        elif "FDA review" in pair and "publication" in pair:
            reason = "FDA regulatory safety population or definition not aligned with publication stratum"
        else:
            reason = "Other denominator, arm, definition, causality, or timing mismatch"
        counter[reason] += 1
    total = sum(counter.values())
    out = []
    for reason, count in counter.most_common():
        out.append({
            "reason": reason,
            "non_comparable_stratum_count": str(count),
            "percent": f"{count / total * 100:.1f}" if total else "0.0",
        })
    write_csv(TABLES / "drug_safety_noncomparability_reason_summary.csv", out, list(out[0]))
    return out


def build_trial_level_comparability_distribution() -> list[dict[str, str]]:
    strata = [
        row for row in read_rows(TABLES / "five_state_source_reporting_status.csv")
        if row["five_state_status"] in {"comparable_and_concordant", "comparable_but_discordant", "reported_but_non_comparable"}
    ]
    by_trial: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in strata:
        by_trial[row["trial_id"]].append(row)
    out = []
    rates = []
    for trial_id in sorted(by_trial):
        rows = by_trial[trial_id]
        n = len(rows)
        x = sum(1 for row in rows if row["five_state_status"].startswith("comparable_"))
        rate = x / n * 100 if n else 0.0
        rates.append(rate)
        out.append({
            "trial_id": trial_id,
            "jointly_reported_strata": str(n),
            "directly_comparable_strata": str(x),
            "directly_comparable_percent": f"{rate:.1f}",
        })
    rates_sorted = sorted(rates)
    if rates_sorted:
        q1, median, q3 = np.percentile(rates_sorted, [25, 50, 75])
        summary = [{
            "trial_count": str(len(rates_sorted)),
            "median_directly_comparable_percent": f"{median:.1f}",
            "iqr_low_percent": f"{q1:.1f}",
            "iqr_high_percent": f"{q3:.1f}",
        }]
        write_csv(TABLES / "drug_safety_trial_level_comparability_summary.csv", summary, list(summary[0]))
    write_csv(TABLES / "drug_safety_trial_level_comparability_distribution.csv", out, list(out[0]))
    return out


def build_comparability_criteria_table() -> list[dict[str, str]]:
    rows = [
        {
            "dimension": "Trial",
            "primary_comparable": "Same trial",
            "sensitivity_only": "Not applicable",
            "non_comparable": "Different trials",
        },
        {
            "dimension": "Treatment arm/dose",
            "primary_comparable": "Same treatment arm and dose cohort",
            "sensitivity_only": "Documented pooling or cohort alignment with the same ADC regimen",
            "non_comparable": "Different treatment arms or dose cohorts",
        },
        {
            "dimension": "Analysis population",
            "primary_comparable": "Same safety population",
            "sensitivity_only": "Trial-specific population compared with a documented broader regulatory safety population",
            "non_comparable": "Clearly different or insufficiently described populations",
        },
        {
            "dimension": "Denominator",
            "primary_comparable": "Identical or inferably identical",
            "sensitivity_only": "Documented denominator difference with same arm and interpretable population relationship",
            "non_comparable": "Unexplained or large denominator difference",
        },
        {
            "dimension": "Safety concept",
            "primary_comparable": "Same aggregate safety concept",
            "sensitivity_only": "Closely related but not identical concept",
            "non_comparable": "Different safety concepts",
        },
        {
            "dimension": "Grade/seriousness",
            "primary_comparable": "Same grade or seriousness definition",
            "sensitivity_only": "Definition not fully explicit but no identified conflicting grade or seriousness rule",
            "non_comparable": "Grade >=3 AE mixed with serious AE or incompatible definition",
        },
        {
            "dimension": "Causality",
            "primary_comparable": "Both all-cause or both treatment-related",
            "sensitivity_only": "Broader causality category with clear metadata",
            "non_comparable": "All-cause directly compared with treatment-related without alignment",
        },
        {
            "dimension": "Observation window",
            "primary_comparable": "Same cutoff or clearly aligned safety window",
            "sensitivity_only": "Window not fully explicit but no identified conflicting cutoff",
            "non_comparable": "Clearly different or unalignable reporting windows",
        },
    ]
    write_csv(TABLES / "drug_safety_comparability_criteria.csv", rows, list(rows[0]))
    return rows


def savefig(fig: plt.Figure, stem: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIGURES / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def figure3_attrition(primary_ci: dict[str, str]) -> None:
    fig, ax = plt.subplots(figsize=(8.8, 2.8), constrained_layout=True)
    ax.axis("off")
    ax.set_title("Flow from reported safety evidence to comparable analyses", loc="left", fontsize=10.5, weight="bold", color=PALETTE["dark"])

    boxes = [
        (0.09, 0.67, "Stratum\npathway", PALETTE["blue"]),
        (0.33, 0.67, "483\nsource-pair strata", PALETTE["gray"]),
        (0.58, 0.67, f"{primary_ci['denominator']}\njointly reported", PALETTE["amber"]),
        (0.82, 0.67, f"{primary_ci['numerator']}\ndirectly comparable", PALETTE["green"]),
        (0.09, 0.29, "Value-pair\npathway", PALETTE["blue"]),
        (0.33, 0.29, "269\ncandidate pairs", PALETTE["gray"]),
        (0.58, 0.29, "28\nanalysis-ready", PALETTE["teal"]),
        (0.82, 0.29, "21 primary\n+ 7 sensitivity", PALETTE["red"]),
    ]
    for x, y, text, color in boxes:
        ax.text(x, y, text, transform=ax.transAxes, ha="center", va="center", fontsize=9, color="white",
                bbox=dict(boxstyle="round,pad=0.45", facecolor=color, edgecolor="none"))
    for y in (0.66, 0.28):
        for x1, x2 in [(0.42, 0.49), (0.66, 0.74)]:
            ax.annotate("", xy=(x2, y), xytext=(x1, y), xycoords=ax.transAxes,
                        arrowprops=dict(arrowstyle="->", color=PALETTE["dark"], lw=1.2))
    ax.text(0.50, 0.05, "Counts use different units by pathway; the value-pair yield is an algorithm-generated screen.",
            transform=ax.transAxes, ha="center", va="center", fontsize=8, color=PALETTE["dark"])
    savefig(fig, "figure3_drug_safety_attrition")


def figure4_difference_vs_mean() -> None:
    rows = read_rows(TABLES / "analysis_ready_comparison_set_confirmed.csv")
    fig, ax = plt.subplots(figsize=(6.2, 4.8), constrained_layout=True)
    for tier, label, color, marker in [
        ("primary_candidate", "Primary", PALETTE["blue"], "o"),
        ("sensitivity_candidate", "Sensitivity", PALETTE["amber"], "s"),
    ]:
        subset = [row for row in rows if row["analysis_tier"] == tier]
        means = [(float(row["percentage_1"]) + float(row["percentage_2"])) / 2 for row in subset]
        diffs = [abs(float(row["percentage_2"]) - float(row["percentage_1"])) for row in subset]
        ax.scatter(means, diffs, s=55, color=color, marker=marker, label=f"{label} (n={len(subset)})", edgecolor="white", linewidth=0.6)
    ax.axhline(2, color=PALETTE["gray"], linewidth=0.8, linestyle=":")
    ax.set_xlabel("Mean of the two source percentages")
    ax.set_ylabel("Absolute percentage-point difference")
    ax.set_title("Absolute difference versus mean for confirmed pairs", loc="left", fontsize=10.5, weight="bold", color=PALETTE["dark"])
    ax.text(0.98, 0.96, "Dotted line = descriptive 2 pp reference", transform=ax.transAxes,
            ha="right", va="top", fontsize=8, color=PALETTE["dark"])
    ax.legend(frameon=False, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    savefig(fig, "figure4_difference_vs_mean")


def write_markdown_tables(
    ci: dict[str, str],
    concept_rows: list[dict[str, str]],
    criteria_rows: list[dict[str, str]],
    source_rows: list[dict[str, str]],
    safety_rows: list[dict[str, str]],
    reason_rows: list[dict[str, str]],
    trial_level_rows: list[dict[str, str]],
) -> None:
    text = "\n\n".join([
        "# Drug Safety revision tables and estimates",
        f"Primary outcome: {ci['numerator']}/{ci['denominator']} jointly reported strata were directly comparable ({ci['percent']}%; Wilson 95% CI {ci['wilson_95_ci_low_percent']}-{ci['wilson_95_ci_high_percent']}; trial-cluster bootstrap 95% CI {ci['trial_cluster_bootstrap_95_ci_low_percent']}-{ci['trial_cluster_bootstrap_95_ci_high_percent']}).",
        "## Safety concept reporting by source",
        md_table(concept_rows, [("safety_concept", "Safety concept"), ("publication", "Publication"), ("ClinicalTrials.gov", "ClinicalTrials.gov"), ("FDA review", "FDA review")]),
        "## Cross-source safety outcome comparability criteria",
        md_table(criteria_rows, [("dimension", "Dimension"), ("primary_comparable", "Primary comparable"), ("sensitivity_only", "Sensitivity only"), ("non_comparable", "Non-comparable")]),
        "## Comparability by source pair",
        md_table(source_rows, [("source_pair", "Source pair"), ("jointly_reported_strata", "Jointly reported strata"), ("directly_comparable_strata", "Directly comparable strata"), ("directly_comparable_percent", "%"), ("wilson_95_ci", "Wilson 95% CI")]),
        "## Comparability by safety concept",
        md_table(safety_rows, [("safety_concept", "Safety concept"), ("jointly_reported_strata", "Jointly reported strata"), ("directly_comparable_strata", "Directly comparable strata"), ("directly_comparable_percent", "%")]),
        "## Reasons for non-comparability among generated pairs",
        md_table(reason_rows, [("reason", "Reason"), ("non_comparable_stratum_count", "Non-comparable strata"), ("percent", "%")]),
        "## Trial-level comparability distribution",
        md_table(trial_level_rows, [("trial_id", "Trial ID"), ("jointly_reported_strata", "Jointly reported strata"), ("directly_comparable_strata", "Directly comparable strata"), ("directly_comparable_percent", "%")]),
    ])
    (MANUSCRIPT / "drug_safety_revision_tables.en.md").write_text(text + "\n", encoding="utf-8")


def main() -> None:
    ci = build_primary_outcome_table()
    concept_rows = build_safety_concept_completeness()
    source_rows = build_comparability_by_source_pair()
    safety_rows = build_comparability_by_concept()
    reason_rows = build_noncomparability_reasons()
    trial_level_rows = build_trial_level_comparability_distribution()
    criteria_rows = build_comparability_criteria_table()
    figure3_attrition(ci)
    figure4_difference_vs_mean()
    write_markdown_tables(ci, concept_rows, criteria_rows, source_rows, safety_rows, reason_rows, trial_level_rows)
    report = f"""# Drug Safety revision assets report

- Primary outcome: {ci['numerator']}/{ci['denominator']} = {ci['percent']}%
- Wilson 95% CI: {ci['wilson_95_ci_low_percent']}-{ci['wilson_95_ci_high_percent']}%
- Trial-cluster bootstrap 95% CI: {ci['trial_cluster_bootstrap_95_ci_low_percent']}-{ci['trial_cluster_bootstrap_95_ci_high_percent']}%
- Generated Drug Safety tables and figures in `tables/`, `figures/drug_safety_revision/`, and `manuscript/drug_safety_revision_tables.en.md`.
"""
    (PROTOCOL / "drug_safety_revision_assets_report.zh.md").write_text(report, encoding="utf-8")
    print(report.strip())


if __name__ == "__main__":
    main()
