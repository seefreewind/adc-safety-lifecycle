#!/usr/bin/env python3
"""Create pilot source-concordance figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "tables"
FIGURES = ROOT / "figures"


def style_axes(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", color="#E5E7EB", linewidth=0.8)
    ax.set_axisbelow(True)


def main() -> None:
    FIGURES.mkdir(exist_ok=True)

    coverage = pd.read_csv(TABLES / "table1_pilot_source_coverage.csv")
    comp = pd.read_csv(ROOT / "data" / "processed" / "source_comparability_matrix.csv")
    disc = pd.read_csv(TABLES / "table4_primary_numeric_discordance_pairs.csv")

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8), constrained_layout=True)

    # Panel A: source coverage.
    y = range(len(coverage))
    axes[0].barh(y, coverage["core_concepts_with_publication"], color="#4C78A8", label="Publication")
    axes[0].barh(y, coverage["core_concepts_with_ctgov"], left=coverage["core_concepts_with_publication"],
                 color="#F58518", label="ClinicalTrials.gov")
    axes[0].barh(
        y,
        coverage["core_concepts_with_fda"],
        left=coverage["core_concepts_with_publication"] + coverage["core_concepts_with_ctgov"],
        color="#54A24B",
        label="FDA",
    )
    axes[0].set_yticks(list(y), coverage["acronym"])
    axes[0].invert_yaxis()
    axes[0].set_xlabel("Extracted core-outcome source count")
    axes[0].set_title("A. Source coverage")
    axes[0].legend(frameon=False, fontsize=8, loc="lower right")
    style_axes(axes[0])

    # Panel B: comparability grade.
    grade_counts = comp["comparability_grade"].value_counts().reindex(["A", "B", "C"], fill_value=0)
    axes[1].bar(grade_counts.index, grade_counts.values, color=["#4C78A8", "#F58518", "#B0B7C3"])
    axes[1].set_ylabel("Source-pair count")
    axes[1].set_xlabel("Comparability grade")
    axes[1].set_title("B. Pairwise comparability")
    for i, value in enumerate(grade_counts.values):
        axes[1].text(i, value + 2, str(value), ha="center", va="bottom", fontsize=9)
    style_axes(axes[1])

    # Panel C: numeric discordance among accepted A-grade pairs.
    disc = disc.copy()
    concept_short = {
        "adverse_event_leading_to_discontinuation": "AE discontinuation",
        "any_adverse_event": "Any AE",
        "dose_interruption": "Dose interruption",
        "dose_reduction": "Dose reduction",
        "fatal_adverse_event": "Fatal AE",
        "serious_adverse_event": "SAE",
    }
    arm_short = {
        "TRIAL002_EG000": "DREAMM-2 2.5",
        "TRIAL002_EG001": "DREAMM-2 3.4",
        "TRIAL004_EG000": "IMMU-132-01",
    }
    disc["label"] = disc["arm_id"].map(arm_short).fillna(disc["trial_id"]) + " " + disc["ae_concept"].map(concept_short).fillna(disc["ae_concept"])
    axes[2].scatter(disc["absolute_percentage_difference"], range(len(disc)), color="#4C78A8", s=28)
    axes[2].set_yticks(range(len(disc)), disc["label"], fontsize=7)
    axes[2].invert_yaxis()
    axes[2].set_xlabel("Absolute percentage-point difference")
    axes[2].set_title("C. Accepted A-grade pairs")
    style_axes(axes[2])

    out_png = FIGURES / "figure1_pilot_source_concordance.png"
    out_pdf = FIGURES / "figure1_pilot_source_concordance.pdf"
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    print(f"Wrote {out_png.relative_to(ROOT)}")
    print(f"Wrote {out_pdf.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
