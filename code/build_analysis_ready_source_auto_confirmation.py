#!/usr/bin/env python3
"""Auto-check analysis-ready source values against local source files."""

from __future__ import annotations

import csv
import json
import re
from functools import lru_cache
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "tables" / "analysis_ready_source_confirmation_packet.csv"
OUT = ROOT / "tables" / "analysis_ready_source_auto_confirmation.csv"
SUMMARY_OUT = ROOT / "tables" / "analysis_ready_source_auto_confirmation_summary.csv"
REPORT_OUT = ROOT / "protocol" / "analysis_ready_source_auto_confirmation_report.zh.md"

DOC_PATHS = {
    "PUB_DREAMM_MAIN": ROOT / "data/raw/publications/pilot/DREAMM2_Lonial_2019_LancetOncol_PMID31859245.pdf",
    "PUB_EV201_MAIN": ROOT / "data/raw/publications/pilot/EV201_Rosenberg_2019_JCO_PMID31356140.pdf",
    "PUB_IMMU_APP": ROOT / "data/raw/publications/pilot/IMMU13201_Bardia_2019_NEJM_appendix.pdf",
    "PUB_DESTINY_APP": ROOT / "data/raw/publications/expansion/TRIAL001/DESTINYBreast01_Modi_2020_NEJM_appendix_usercopy.pdf",
    "EXPUB_TRIAL014_0001": ROOT / "data/raw/publications/expansion/TRIAL014/innovaTV301_Vergote_2024_NEJM_appendix.pdf",
    "FDA_ADC009_MDR_761158_ORIG1": ROOT / "data/raw/drugs_fda/review_documents/ADC009/761158Orig1s000MultidisciplineR.pdf",
    "FDA_ADC006_MDR_761137_ORIG1": ROOT / "data/raw/drugs_fda/review_documents/ADC006/761137Orig1s000MultidisciplineR.pdf",
    "FDA_ADC008_MDR_761115_ORIG1": ROOT / "data/raw/drugs_fda/review_documents/ADC008/761115Orig1s000MultidisciplineR.pdf",
    "FDA_ADC007_MDR_761139_ORIG1": ROOT / "data/raw/drugs_fda/review_documents/ADC007/761139Orig1s000MultidisciplineR.pdf",
    "CTGOV_NCT03219333": ROOT / "data/raw/clinicaltrials/NCT03219333.json",
    "CTGOV_NCT04697628": ROOT / "data/raw/clinicaltrials/NCT04697628.json",
    "CTGOV_NCT03525678": ROOT / "data/raw/clinicaltrials/NCT03525678.json",
}

FIELDS = [
    "comparison_id", "trial_id", "analysis_tier", "side", "source",
    "document_id", "local_path", "file_found", "locator", "term",
    "denominator", "percentage", "term_match", "value_match",
    "evidence_snippet", "auto_confirmation_status", "notes",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def normalize_text(text: str) -> str:
    text = text.replace("·", ".").replace("–", "-").replace("≥", ">=")
    text = re.sub(r"\s+", " ", text)
    return text.lower()


@lru_cache(maxsize=None)
def pdf_text(path: str) -> str:
    reader = PdfReader(path)
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return normalize_text("\n".join(parts))


@lru_cache(maxsize=None)
def file_text(path: str) -> str:
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        return pdf_text(path)
    if p.suffix.lower() == ".json":
        return normalize_text(p.read_text(encoding="utf-8"))
    return normalize_text(p.read_text(encoding="utf-8", errors="ignore"))


def significant_tokens(term: str) -> list[str]:
    stop = {
        "with", "and", "the", "due", "to", "any", "of", "by", "at", "least",
        "patients", "participants", "affected", "subjects", "event", "events",
        "adverse", "treatment", "emergent",
    }
    tokens = re.findall(r"[a-z0-9>=]+", normalize_text(term))
    return [token for token in tokens if len(token) >= 4 and token not in stop]


def term_matches(text: str, term: str) -> bool:
    tokens = significant_tokens(term)
    if not tokens:
        return True
    hits = sum(1 for token in tokens if token in text)
    return hits >= max(1, min(len(tokens), 2))


def pct_variants(value: str) -> list[str]:
    try:
        f = float(value)
    except ValueError:
        return []
    variants = {f"{f:.3f}", f"{f:.2f}", f"{f:.1f}", str(int(f)) if f.is_integer() else f"{f:g}"}
    return sorted(variants, key=len, reverse=True)


def value_matches_text(text: str, percentage: str, denominator: str) -> bool:
    for variant in pct_variants(percentage):
        escaped = re.escape(variant)
        if re.search(rf"(?<!\d){escaped}\s*%?", text):
            return True
    try:
        denom_int = int(float(denominator))
    except ValueError:
        return False
    return re.search(rf"\bn\s*=\s*{denom_int}\b|\(n\s*=\s*{denom_int}\)|\b{denom_int}\b", text) is not None


def evidence_snippet(text: str, term: str, percentage: str) -> str:
    needles = significant_tokens(term) + pct_variants(percentage)
    positions = [text.find(needle) for needle in needles if needle and text.find(needle) >= 0]
    if not positions:
        return ""
    pos = min(positions)
    snippet = text[max(0, pos - 180): pos + 300]
    return snippet.strip()


def ctgov_value_match(path: Path, percentage: str, denominator: str) -> bool:
    data = json.loads(path.read_text(encoding="utf-8"))
    ae = ((data.get("resultsSection") or {}).get("adverseEventsModule") or {})
    try:
        target_den = int(float(denominator))
        target_pct = float(percentage)
    except ValueError:
        return False
    for group in ae.get("eventGroups") or []:
        for affected_key, risk_key in [
            ("seriousNumAffected", "seriousNumAtRisk"),
            ("deathsNumAffected", "deathsNumAtRisk"),
            ("otherNumAffected", "otherNumAtRisk"),
        ]:
            try:
                affected = float(group.get(affected_key, ""))
                at_risk = int(float(group.get(risk_key, "")))
            except (TypeError, ValueError):
                continue
            if at_risk == target_den and abs((affected / at_risk * 100) - target_pct) < 0.01:
                return True
    return False


def check_side(row: dict[str, str], side: str) -> dict[str, str]:
    document_id = row[f"document_id_{side}"]
    path = DOC_PATHS.get(document_id)
    term = row[f"term_{side}"]
    percentage = row[f"percentage_{side}"]
    denominator = row[f"denominator_{side}"]
    source = row[f"source_{side}"]
    locator = row[f"locator_{side}"]

    out = {
        "comparison_id": row["comparison_id"],
        "trial_id": row["trial_id"],
        "analysis_tier": row["analysis_tier"],
        "side": side,
        "source": source,
        "document_id": document_id,
        "local_path": str(path) if path else "",
        "file_found": "yes" if path and path.exists() else "no",
        "locator": locator,
        "term": term,
        "denominator": denominator,
        "percentage": percentage,
        "term_match": "no",
        "value_match": "no",
        "evidence_snippet": "",
        "auto_confirmation_status": "needs_manual_source_confirmation",
        "notes": "",
    }
    if not path or not path.exists():
        out["notes"] = "No local file mapped for document_id."
        return out

    text = file_text(str(path))
    term_ok = term_matches(text, term)
    if path.suffix.lower() == ".json":
        value_ok = ctgov_value_match(path, percentage, denominator)
    else:
        value_ok = value_matches_text(text, percentage, denominator)
    out["term_match"] = "yes" if term_ok else "no"
    out["value_match"] = "yes" if value_ok else "no"
    out["evidence_snippet"] = evidence_snippet(text, term, percentage)

    if term_ok and value_ok:
        out["auto_confirmation_status"] = "auto_confirmed_text_value"
    elif value_ok:
        out["auto_confirmation_status"] = "auto_value_found_term_needs_review"
    elif term_ok:
        out["auto_confirmation_status"] = "auto_term_found_value_needs_review"
    else:
        out["auto_confirmation_status"] = "needs_manual_source_confirmation"
    if path.suffix.lower() == ".pdf" and len(text) < 1000:
        out["notes"] = "PDF text layer is sparse; visual/OCR confirmation may be needed."
    return out


def main() -> None:
    rows = read_csv(PACKET)
    out_rows = []
    for row in rows:
        out_rows.append(check_side(row, "1"))
        out_rows.append(check_side(row, "2"))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(out_rows)

    summary = {}
    for row in out_rows:
        key = row["auto_confirmation_status"]
        summary[key] = summary.get(key, 0) + 1
    summary_rows = [{"auto_confirmation_status": key, "source_side_count": str(value)} for key, value in sorted(summary.items())]
    with SUMMARY_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["auto_confirmation_status", "source_side_count"])
        writer.writeheader()
        writer.writerows(summary_rows)

    REPORT_OUT.write_text(
        "\n".join([
            "# Analysis-ready source auto-confirmation 报告",
            "",
            "日期：2026-06-19",
            "",
            "## 输出",
            "",
            "- `tables/analysis_ready_source_auto_confirmation.csv`",
            "- `tables/analysis_ready_source_auto_confirmation_summary.csv`",
            "",
            "## 自动核对结果",
            "",
            *[f"- {row['auto_confirmation_status']}: {row['source_side_count']} source-sides" for row in summary_rows],
            "",
            "## 说明",
            "",
            "该自动核对基于本地 PDF/JSON 文本层，标准偏保守。未自动确认不代表数值错误，只表示需要人工查看来源页或 OCR/视觉核对。",
        ]) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"Wrote {SUMMARY_OUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
