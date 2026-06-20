#!/usr/bin/env python3
"""Extract safety-related candidates from full ClinicalTrials.gov results modules."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "clinicaltrials"
DATA = ROOT / "data"
TABLES = ROOT / "tables"
PROTOCOL = ROOT / "protocol"

OUT = DATA / "interim" / "ctgov_full_module_safety_outcome_candidates.csv"
SUMMARY_OUT = TABLES / "ctgov_full_module_safety_outcome_candidate_summary.csv"
REPORT_OUT = PROTOCOL / "ctgov_full_module_safety_outcome_candidates_report.zh.md"

SAFETY_PATTERN = re.compile(
    r"\b(adverse event|adverse events|treatment[- ]emergent|TEAE|AE|SAE|serious adverse|"
    r"laboratory abnormal|toxicity|dose interruption|dose reduction|dose modification|"
    r"discontinuation due to|discontinued .* adverse|veno-occlusive|sinusoidal obstruction)\b",
    re.IGNORECASE,
)

EXCLUSION_PATTERN = re.compile(
    r"\bprogression[- ]free|overall survival|duration of response|objective response|"
    r"time to response|clinical benefit|disease progression|death from any cause|"
    r"EuroQol|EQ-5D|quality of life|pharmacokinetic|concentration|clearance\b",
    re.IGNORECASE,
)


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def nct_to_trial() -> dict[str, dict[str, str]]:
    mapping = {}
    for row in read_rows(DATA / "processed" / "trial_master_expansion_candidates.csv"):
        if row.get("nct_number"):
            mapping[row["nct_number"]] = row
    return mapping


def is_safety_measure(measure: dict) -> bool:
    title = measure.get("title", "") or ""
    description = measure.get("description", "") or ""
    population = measure.get("populationDescription", "") or ""
    text = " ".join([title, description, population, measure.get("unitOfMeasure", "") or ""])
    if not SAFETY_PATTERN.search(text):
        return False
    if EXCLUSION_PATTERN.search(title) and not SAFETY_PATTERN.search(title):
        return False
    return True


def concept_from_text(text: str) -> str:
    t = text.lower()
    if "serious adverse" in t or "sae" in t:
        return "serious_adverse_event"
    if "discontinu" in t and "adverse" in t:
        return "adverse_event_leading_to_discontinuation"
    if "dose interruption" in t or "dose delay" in t:
        return "dose_interruption"
    if "dose reduction" in t:
        return "dose_reduction"
    if "grade 3" in t or ">/= grade 3" in t or ">= grade 3" in t or "laboratory abnormal" in t:
        return "grade_3_or_higher_adverse_event_or_lab_abnormality"
    if "adverse event" in t or "teae" in t or re.search(r"\bae\b", t):
        return "any_adverse_event"
    if "veno-occlusive" in t or "sinusoidal obstruction" in t:
        return "veno_occlusive_disease_or_sinusoidal_obstruction"
    return "safety_related_other"


def denominator_map(measure: dict) -> dict[str, str]:
    out = {}
    for denom in measure.get("denoms", []) or []:
        if (denom.get("units") or "").lower().startswith("participant"):
            for count in denom.get("counts", []) or []:
                out[count.get("groupId", "")] = str(count.get("value", ""))
    return out


def group_map(measure: dict) -> dict[str, dict[str, str]]:
    return {group.get("id", ""): group for group in measure.get("groups", []) or []}


def as_float(value: str) -> float | None:
    try:
        if value in {"", None}:  # type: ignore[comparison-overlap]
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def calculated_percentage(value: str, denominator: str, unit: str) -> str:
    if "percentage" in (unit or "").lower():
        return value
    numerator = as_float(value)
    denom = as_float(denominator)
    if numerator is None or denom in {None, 0}:
        return ""
    return f"{numerator / denom * 100:.3f}"


def iter_measurements(measure: dict):
    for class_idx, klass in enumerate(measure.get("classes", []) or []):
        class_title = klass.get("title", "") or ""
        categories = klass.get("categories", []) or [{"measurements": klass.get("measurements", []) or []}]
        for category_idx, category in enumerate(categories or []):
            category_title = category.get("title", "") or ""
            for measurement in category.get("measurements", []) or []:
                yield class_idx, class_title, category_idx, category_title, measurement


def main() -> None:
    mapping = nct_to_trial()
    rows: list[dict[str, str]] = []
    seq = 1
    for path in sorted(RAW.glob("*.json")):
        nct = path.stem
        trial = mapping.get(nct, {})
        data = json.loads(path.read_text(encoding="utf-8"))
        measures = (
            data.get("resultsSection", {})
            .get("outcomeMeasuresModule", {})
            .get("outcomeMeasures", [])
            or []
        )
        for measure_idx, measure in enumerate(measures):
            if not is_safety_measure(measure):
                continue
            denoms = denominator_map(measure)
            groups = group_map(measure)
            unit = measure.get("unitOfMeasure", "") or ""
            measure_text = " ".join([
                measure.get("title", "") or "",
                measure.get("description", "") or "",
            ])
            for class_idx, class_title, category_idx, category_title, measurement in iter_measurements(measure):
                group_id = measurement.get("groupId", "")
                group = groups.get(group_id, {})
                value = str(measurement.get("value", ""))
                denominator = denoms.get(group_id, "")
                concept_text = " ".join([measure_text, class_title, category_title])
                rows.append({
                    "candidate_id": f"CTFULL{seq:06d}",
                    "trial_id": trial.get("trial_id", ""),
                    "short_trial_name": trial.get("acronym", ""),
                    "nct_number": nct,
                    "module": "outcomeMeasuresModule",
                    "outcome_index": str(measure_idx),
                    "outcome_type": measure.get("type", ""),
                    "outcome_title": measure.get("title", ""),
                    "outcome_description": measure.get("description", ""),
                    "population_description": measure.get("populationDescription", ""),
                    "time_frame": measure.get("timeFrame", ""),
                    "unit_of_measure": unit,
                    "class_index": str(class_idx),
                    "class_title": class_title,
                    "category_index": str(category_idx),
                    "category_title": category_title,
                    "group_id": group_id,
                    "group_title": group.get("title", ""),
                    "group_description": group.get("description", ""),
                    "value": value,
                    "denominator": denominator,
                    "calculated_percentage": calculated_percentage(value, denominator, unit),
                    "mapped_safety_concept": concept_from_text(concept_text),
                    "candidate_use_status": "ctgov_full_module_candidate_needs_mapping_review",
                })
                seq += 1

    fieldnames = [
        "candidate_id",
        "trial_id",
        "short_trial_name",
        "nct_number",
        "module",
        "outcome_index",
        "outcome_type",
        "outcome_title",
        "outcome_description",
        "population_description",
        "time_frame",
        "unit_of_measure",
        "class_index",
        "class_title",
        "category_index",
        "category_title",
        "group_id",
        "group_title",
        "group_description",
        "value",
        "denominator",
        "calculated_percentage",
        "mapped_safety_concept",
        "candidate_use_status",
    ]
    write_csv(OUT, rows, fieldnames)

    summary = []
    by_trial = defaultdict(list)
    for row in rows:
        by_trial[row["trial_id"] or row["nct_number"]].append(row)
    for key, grouped in sorted(by_trial.items()):
        summary.append({
            "trial_or_nct": key,
            "short_trial_name": grouped[0].get("short_trial_name", ""),
            "candidate_rows": str(len(grouped)),
            "candidate_outcomes": str(len({row["outcome_index"] for row in grouped})),
            "mapped_concepts": ";".join(sorted({row["mapped_safety_concept"] for row in grouped})),
        })
    write_csv(SUMMARY_OUT, summary, list(summary[0]) if summary else ["trial_or_nct", "candidate_rows"])

    concept_counts = Counter(row["mapped_safety_concept"] for row in rows)
    report = [
        "# CT.gov full-module safety outcome candidates 报告",
        "",
        f"- 输出：`{OUT.relative_to(ROOT)}`",
        f"- 汇总：`{SUMMARY_OUT.relative_to(ROOT)}`",
        f"- 候选行数：{len(rows)}",
        f"- 覆盖 trial/NCT 数：{len(by_trial)}",
        "",
        "## Mapped concept counts",
        "",
    ]
    report.extend(f"- {concept}: {count}" for concept, count in sorted(concept_counts.items()))
    report.extend([
        "",
        "说明：该表仅为 CT.gov outcomeMeasuresModule 安全候选，不自动并入核心 safety seed。进入分析前需要核对 group/denominator、时间窗、是否与 publication/FDA 人群一致。",
    ])
    REPORT_OUT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
