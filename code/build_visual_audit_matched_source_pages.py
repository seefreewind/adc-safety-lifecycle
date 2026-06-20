#!/usr/bin/env python3
"""Render source audit pages by matching terms and values in PDF text."""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path

import fitz
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "tables" / "analysis_ready_source_confirmation_packet_confirmed.csv"
FIGDIR = ROOT / "figures" / "source_audit_matched_pages"
TABLE_OUT = ROOT / "tables" / "visual_source_audit_matched_pages.csv"
REPORT_OUT = ROOT / "protocol" / "visual_source_audit_matched_pages_report.zh.md"

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
}

STOPWORDS = {
    "with", "and", "the", "due", "to", "any", "of", "by", "at", "least",
    "patients", "participants", "affected", "subjects", "event", "events",
    "adverse", "treatment", "emergent", "because", "leading", "associated",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def normalize_text(text: str) -> str:
    text = text.replace("·", ".").replace("–", "-").replace("≥", ">=")
    return re.sub(r"\s+", " ", text).lower()


def significant_tokens(term: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9>=]+", normalize_text(term))
    return [token for token in tokens if len(token) >= 4 and token not in STOPWORDS]


def pct_variants(value: str) -> list[str]:
    try:
        f = float(value)
    except ValueError:
        return []
    variants = {f"{f:.3f}", f"{f:.2f}", f"{f:.1f}", str(int(f)) if f.is_integer() else f"{f:g}"}
    return sorted(variants, key=len, reverse=True)


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")


def page_texts(path: Path) -> list[str]:
    reader = PdfReader(str(path))
    return [normalize_text(page.extract_text() or "") for page in reader.pages]


def score_page(text: str, terms: list[str], percentages: list[str], denominators: list[str]) -> int:
    score = 0
    for term in terms:
        for token in set(significant_tokens(term)):
            if token in text:
                score += 4
    for value in percentages:
        if any(re.search(rf"(?<!\d){re.escape(v)}\s*%?", text) for v in pct_variants(value)):
            score += 6
    for denom in denominators:
        try:
            denom_int = int(float(denom))
        except ValueError:
            continue
        if re.search(rf"\bn\s*=\s*{denom_int}\b|\(n\s*=\s*{denom_int}\)|\b{denom_int}\b", text):
            score += 2
    return score


def render_page(path: Path, page_index: int, out_path: Path) -> None:
    doc = fitz.open(str(path))
    page = doc.load_page(page_index)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    pix.save(str(out_path))
    doc.close()


def main() -> None:
    packet = read_csv(PACKET)
    groups: dict[tuple[str, str, str], dict[str, object]] = defaultdict(lambda: {
        "terms": set(),
        "percentages": set(),
        "denominators": set(),
        "trials": set(),
        "comparisons": set(),
    })
    for row in packet:
        for side in ["1", "2"]:
            document_id = row.get(f"document_id_{side}", "")
            if document_id not in DOC_PATHS:
                continue
            locator = row.get(f"locator_{side}", "")
            source = row.get(f"source_{side}", "")
            key = (document_id, locator, source)
            groups[key]["terms"].add(row.get(f"term_{side}", ""))
            groups[key]["percentages"].add(row.get(f"percentage_{side}", ""))
            groups[key]["denominators"].add(row.get(f"denominator_{side}", ""))
            groups[key]["trials"].add(row.get("trial_id", ""))
            groups[key]["comparisons"].add(row.get("comparison_id", ""))

    FIGDIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for (document_id, locator, source), info in sorted(groups.items()):
        path = DOC_PATHS[document_id]
        texts = page_texts(path)
        terms = sorted(t for t in info["terms"] if t)
        percentages = sorted(p for p in info["percentages"] if p)
        denominators = sorted(d for d in info["denominators"] if d)
        scored = [(score_page(text, terms, percentages, denominators), idx) for idx, text in enumerate(texts)]
        score, page_index = max(scored, key=lambda item: item[0])
        out_name = f"{safe_name(document_id)}_{safe_name(locator)[:40]}_matched_p{page_index + 1}.png"
        out_path = FIGDIR / out_name
        render_page(path, page_index, out_path)
        rows.append({
            "document_id": document_id,
            "source": source,
            "trial_ids": ";".join(sorted(info["trials"])),
            "comparison_ids": ";".join(sorted(info["comparisons"])),
            "locator": locator,
            "local_pdf": str(path),
            "matched_pdf_page": str(page_index + 1),
            "match_score": str(score),
            "terms": "; ".join(terms),
            "percentages": "; ".join(percentages),
            "denominators": "; ".join(denominators),
            "audit_image": str(out_path),
            "visual_audit_status": "matched_render_pending_visual_review",
        })

    with TABLE_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    REPORT_OUT.write_text(
        "\n".join([
            "# Visual source audit matched pages 报告",
            "",
            "日期：2026-06-19",
            "",
            "## 输出",
            "",
            "- `tables/visual_source_audit_matched_pages.csv`",
            "- `figures/source_audit_matched_pages/*.png`",
            "",
            "## 方法",
            "",
            "按 document_id 与 locator 分组，使用 analysis-ready confirmation packet 中的原始术语、百分比和分母在 PDF 文本层中打分定位最佳页面，再渲染对应页面。该方法避免 manuscript page number 与 PDF physical page 不一致导致的错页。",
            "",
            f"- 渲染页面数：{len(rows)}",
        ]) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {TABLE_OUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")
    print(f"Rendered {len(rows)} matched audit pages to {FIGDIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
