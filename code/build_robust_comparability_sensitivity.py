#!/usr/bin/env python3
"""Build stratum-level comparability and robust concordance sensitivity tables."""

from __future__ import annotations

import csv
import statistics
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "tables"
MANUSCRIPT = ROOT / "manuscript"
PROTOCOL = ROOT / "protocol"
DATA = ROOT / "data"

FIVE_STATE = TABLES / "five_state_source_reporting_status.csv"
CONFIRMED = TABLES / "analysis_ready_comparison_set_confirmed.csv"
MATRIX = DATA / "processed" / "full_cohort_source_comparability_matrix.csv"

STRATUM_OUT = TABLES / "stratum_level_comparability_metrics.csv"
TRIAL_WEIGHTED_OUT = TABLES / "trial_weighted_concordance_sensitivity.csv"
LOTO_OUT = TABLES / "leave_one_trial_out_concordance.csv"
COUNT_CLASS_OUT = TABLES / "count_rounding_concordance_classification.csv"
COUNT_SUMMARY_OUT = TABLES / "count_rounding_concordance_summary.csv"
MANUSCRIPT_OUT = MANUSCRIPT / "robust_comparability_sensitivity.en.md"
REPORT_OUT = PROTOCOL / "robust_comparability_sensitivity_report.zh.md"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def as_float(value: str) -> float | None:
    try:
        if value == "":
            return None
        return float(value)
    except ValueError:
        return None


def as_int(value: str) -> int | None:
    try:
        if value == "":
            return None
        return int(float(value))
    except ValueError:
        return None


def fmt(value: float | None, digits: int = 2) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}f}"


def mean(values: list[float]) -> float | None:
    return statistics.mean(values) if values else None


def median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def percent(num: int, den: int) -> str:
    return "" if den == 0 else f"{num / den * 100:.1f}"


def matrix_by_id() -> dict[str, dict[str, str]]:
    return {row["comparison_id"]: row for row in read_rows(MATRIX)}


def stratum_metrics() -> list[dict[str, str]]:
    rows = read_rows(FIVE_STATE)
    counts = Counter(row["five_state_status"] for row in rows)
    comparable = counts["comparable_and_concordant"] + counts["comparable_but_discordant"]
    reported = comparable + counts["reported_but_non_comparable"]
    total = sum(counts.values())
    confirmed_pairs = sum(
        int(row["confirmed_analysis_ready_count"])
        for row in rows
        if row["five_state_status"] in {"comparable_and_concordant", "comparable_but_discordant"}
    )
    out = [
        {
            "metric": "all_trial_concept_source_pair_strata",
            "numerator": str(total),
            "denominator": str(total),
            "percent": "100.0",
            "interpretation": "All trial-concept-source-pair strata in the five-state framework.",
        },
        {
            "metric": "jointly_reported_or_noncomparable_strata",
            "numerator": str(reported),
            "denominator": str(total),
            "percent": percent(reported, total),
            "interpretation": "Strata in which both source sides had a related reported value, whether comparable or not.",
        },
        {
            "metric": "stratum_level_comparability_rate",
            "numerator": str(comparable),
            "denominator": str(reported),
            "percent": percent(comparable, reported),
            "interpretation": "Comparable strata among jointly reported strata.",
        },
        {
            "metric": "stratum_level_concordance_among_comparable",
            "numerator": str(counts["comparable_and_concordant"]),
            "denominator": str(comparable),
            "percent": percent(counts["comparable_and_concordant"], comparable),
            "interpretation": "Concordant strata among comparable strata.",
        },
        {
            "metric": "confirmed_pairs_within_comparable_strata",
            "numerator": str(confirmed_pairs),
            "denominator": "",
            "percent": "",
            "interpretation": "Multiple comparison pairs can arise within one stratum when more than one arm, dose cohort, or source-row pairing is confirmed.",
        },
    ]
    return out


def confirmed_rows(tier: str | None = None) -> list[dict[str, str]]:
    rows = read_rows(CONFIRMED)
    return [row for row in rows if tier is None or row["analysis_tier"] == tier]


def summarize_values(values: list[float]) -> dict[str, str]:
    return {
        "comparison_count": str(len(values)),
        "mean_abs_diff_pp": fmt(mean(values)),
        "median_abs_diff_pp": fmt(median(values)),
        "max_abs_diff_pp": fmt(max(values) if values else None),
        "within_1pp_count": str(sum(value <= 1 for value in values)),
        "within_2pp_count": str(sum(value <= 2 for value in values)),
    }


def trial_weighted_rows() -> list[dict[str, str]]:
    out = []
    for tier in ["primary_candidate", "sensitivity_candidate", "all_confirmed"]:
        rows = confirmed_rows(None if tier == "all_confirmed" else tier)
        by_trial: dict[str, list[float]] = defaultdict(list)
        for row in rows:
            value = as_float(row["absolute_percentage_difference"])
            if value is not None:
                by_trial[row["trial_id"]].append(value)
        trial_means = [statistics.mean(values) for values in by_trial.values() if values]
        pair_values = [value for values in by_trial.values() for value in values]
        row = {
            "analysis_set": tier,
            "trial_count": str(len(by_trial)),
            "pair_count": str(len(pair_values)),
            "pair_weighted_mean_abs_diff_pp": fmt(mean(pair_values)),
            "trial_weighted_mean_abs_diff_pp": fmt(mean(trial_means)),
            "trial_weighted_median_abs_diff_pp": fmt(median(trial_means)),
            "trial_weighted_max_trial_mean_abs_diff_pp": fmt(max(trial_means) if trial_means else None),
            "trial_mean_values_pp": ";".join(f"{trial}:{statistics.mean(values):.2f}" for trial, values in sorted(by_trial.items())),
        }
        out.append(row)
    return out


def leave_one_trial_out_rows() -> list[dict[str, str]]:
    out = []
    for tier in ["primary_candidate", "sensitivity_candidate", "all_confirmed"]:
        rows = confirmed_rows(None if tier == "all_confirmed" else tier)
        trials = sorted({row["trial_id"] for row in rows})
        for trial in trials:
            kept = [row for row in rows if row["trial_id"] != trial]
            values = [
                as_float(row["absolute_percentage_difference"])
                for row in kept
            ]
            values = [value for value in values if value is not None]
            summary = summarize_values(values)
            summary.update({
                "analysis_set": tier,
                "excluded_trial_id": trial,
                "remaining_trial_count": str(len({row["trial_id"] for row in kept})),
            })
            out.append(summary)
    return out


def displayed_precision(value: str) -> int:
    if "." not in value:
        return 0
    return len(value.split(".", 1)[1])


def rounding_compatible(n: int, d: int, p1: str, p2: str) -> bool:
    if d == 0:
        return False
    true_pct = n / d * 100
    for pct_text in [p1, p2]:
        pct = as_float(pct_text)
        if pct is None:
            return False
        precision = displayed_precision(pct_text)
        tolerance = 0.5 * (10 ** -precision) + 1e-9
        if abs(pct - round(true_pct, precision)) > tolerance:
            return False
    return True


def count_rounding_rows() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    matrix = matrix_by_id()
    rows = []
    for row in confirmed_rows():
        detail = matrix.get(row["comparison_id"], {})
        n1 = as_int(detail.get("number_patients_1", ""))
        n2 = as_int(detail.get("number_patients_2", ""))
        d1 = as_int(row.get("denominator_1", ""))
        d2 = as_int(row.get("denominator_2", ""))
        diff = as_float(row.get("absolute_percentage_difference", "")) or 0
        if n1 is not None and n2 is not None and d1 is not None and d2 is not None and n1 == n2 and d1 == d2:
            if diff == 0:
                cls = "exact_count_and_percentage_concordance"
            elif rounding_compatible(n1, d1, row["percentage_1"], row["percentage_2"]):
                cls = "rounding_compatible_concordance"
            else:
                cls = "same_count_denominator_percentage_display_difference"
        elif diff <= 2:
            cls = "numerically_close_but_not_count_confirmed"
        else:
            cls = "discordant_or_sensitivity_difference"
        out = dict(row)
        out.update({
            "number_patients_1": "" if n1 is None else str(n1),
            "number_patients_2": "" if n2 is None else str(n2),
            "count_rounding_concordance_class": cls,
        })
        rows.append(out)

    summary = []
    for (tier, cls), count in sorted(Counter((row["analysis_tier"], row["count_rounding_concordance_class"]) for row in rows).items()):
        summary.append({
            "analysis_tier": tier,
            "count_rounding_concordance_class": cls,
            "comparison_count": str(count),
            "percent_within_tier": percent(count, sum(row["analysis_tier"] == tier for row in rows)),
        })
    return rows, summary


def main() -> None:
    strata = stratum_metrics()
    write_csv(STRATUM_OUT, strata, list(strata[0]))

    trial_weighted = trial_weighted_rows()
    write_csv(TRIAL_WEIGHTED_OUT, trial_weighted, list(trial_weighted[0]))

    loto = leave_one_trial_out_rows()
    write_csv(LOTO_OUT, loto, list(loto[0]))

    count_rows, count_summary = count_rounding_rows()
    write_csv(COUNT_CLASS_OUT, count_rows, list(count_rows[0]))
    write_csv(COUNT_SUMMARY_OUT, count_summary, list(count_summary[0]))

    primary_tw = next(row for row in trial_weighted if row["analysis_set"] == "primary_candidate")
    stratum_rate = next(row for row in strata if row["metric"] == "stratum_level_comparability_rate")
    dreamm_loto = next(
        row for row in loto
        if row["analysis_set"] == "primary_candidate" and row["excluded_trial_id"] == "TRIAL002"
    )
    count_primary = [
        row for row in count_summary
        if row["analysis_tier"] == "primary_candidate"
    ]

    manuscript = [
        "# Robust comparability and concordance sensitivity analyses",
        "",
        (
            "The value-pair yield and the stratum-level comparability rate describe different levels "
            "of the data structure. The value-pair yield uses generated source-value pairings as the "
            "denominator, whereas the stratum-level rate uses trial-concept-source-pair strata in which "
            "both sources reported a related safety value."
        ),
        "",
        (
            f"Among jointly reported strata, {stratum_rate['numerator']} of {stratum_rate['denominator']} "
            f"were directly comparable, giving a stratum-level comparability rate of {stratum_rate['percent']}%. "
            "These comparable strata yielded more confirmed comparison pairs because one stratum could contain "
            "more than one arm, dose cohort, or source-row pairing."
        ),
        "",
        (
            "For primary-analysis comparisons, the pair-weighted mean absolute difference was "
            f"{primary_tw['pair_weighted_mean_abs_diff_pp']} percentage points, whereas the trial-weighted "
            f"mean was {primary_tw['trial_weighted_mean_abs_diff_pp']} percentage points. "
            f"After excluding DREAMM-2, the pair-weighted mean absolute difference was "
            f"{dreamm_loto['mean_abs_diff_pp']} percentage points across {dreamm_loto['comparison_count']} "
            "remaining primary-analysis comparisons."
        ),
        "",
        "Count and rounding classification among primary-analysis comparisons:",
        "",
        "| Class | Comparisons | Percent |",
        "| --- | ---: | ---: |",
    ]
    for row in count_primary:
        manuscript.append(
            f"| {row['count_rounding_concordance_class']} | {row['comparison_count']} | {row['percent_within_tier']} |"
        )
    MANUSCRIPT_OUT.write_text("\n".join(manuscript) + "\n", encoding="utf-8")

    report = [
        "# 稳健性与可比性敏感性分析报告",
        "",
        f"- Stratum-level comparability：{stratum_rate['numerator']}/{stratum_rate['denominator']} = {stratum_rate['percent']}%",
        f"- Primary pair-weighted mean abs diff：{primary_tw['pair_weighted_mean_abs_diff_pp']} pp",
        f"- Primary trial-weighted mean abs diff：{primary_tw['trial_weighted_mean_abs_diff_pp']} pp",
        f"- Excluding DREAMM-2 后 primary mean abs diff：{dreamm_loto['mean_abs_diff_pp']} pp",
        "",
        "输出文件：",
        f"- `{STRATUM_OUT.relative_to(ROOT)}`",
        f"- `{TRIAL_WEIGHTED_OUT.relative_to(ROOT)}`",
        f"- `{LOTO_OUT.relative_to(ROOT)}`",
        f"- `{COUNT_CLASS_OUT.relative_to(ROOT)}`",
        f"- `{COUNT_SUMMARY_OUT.relative_to(ROOT)}`",
        f"- `{MANUSCRIPT_OUT.relative_to(ROOT)}`",
    ]
    REPORT_OUT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
