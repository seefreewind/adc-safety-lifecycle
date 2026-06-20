#!/usr/bin/env python3
"""Render representative source pages for final visual audit."""

from __future__ import annotations

import csv
import re
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
FIGDIR = ROOT / "figures" / "source_audit_pages"
TABLE_OUT = ROOT / "tables" / "visual_source_audit_sample_pages.csv"
REPORT_OUT = ROOT / "protocol" / "visual_source_audit_sample_pages_report.zh.md"

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

SAMPLES = [
    ("TRIAL002", "PUB_DREAMM_MAIN", "main article p6", 6, "DREAMM-2 publication AE overview"),
    ("TRIAL002", "PUB_DREAMM_MAIN", "main article p7", 7, "DREAMM-2 publication serious/fatal AE narrative"),
    ("TRIAL002", "FDA_ADC009_MDR_761158_ORIG1", "Table 27, FDA review p148", 148, "DREAMM-2 FDA Table 27"),
    ("TRIAL003", "PUB_EV201_MAIN", "Table A3/A4, PDF p17", 17, "EV-201 publication appendix safety table"),
    ("TRIAL003", "FDA_ADC006_MDR_761137_ORIG1", "Table 74, FDA review p184", 184, "EV-201 FDA Table 74 first page"),
    ("TRIAL003", "FDA_ADC006_MDR_761137_ORIG1", "Table 74, FDA review p185", 185, "EV-201 FDA Table 74 continuation"),
    ("TRIAL004", "PUB_IMMU_APP", "Supplementary Table S1, appendix p18", 18, "IMMU-132-01 publication supplement discontinuation"),
    ("TRIAL004", "FDA_ADC008_MDR_761115_ORIG1", "FDA review text p87", 87, "IMMU-132-01 FDA discontinuation text"),
    ("TRIAL014", "EXPUB_TRIAL014_0001", "Supplementary Table S7, appendix p36", 36, "innovaTV 301 serious AE supplement table"),
    ("TRIAL001", "PUB_DESTINY_APP", "Supplementary Table S3, appendix p11", 11, "DESTINY-Breast01 supplement safety table"),
    ("TRIAL001", "FDA_ADC007_MDR_761139_ORIG1", "Table 35, FDA review p174", 174, "DESTINY-Breast01 FDA serious TEAE"),
    ("TRIAL001", "FDA_ADC007_MDR_761139_ORIG1", "Table 38, FDA review p177", 177, "DESTINY-Breast01 FDA dose interruption"),
    ("TRIAL001", "FDA_ADC007_MDR_761139_ORIG1", "Table 41, FDA review p183", 183, "DESTINY-Breast01 FDA any TEAE"),
]


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")


def render_page(pdf_path: Path, page_number: int, out_path: Path) -> str:
    doc = fitz.open(str(pdf_path))
    index = max(0, min(page_number - 1, len(doc) - 1))
    page = doc.load_page(index)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    pix.save(str(out_path))
    doc.close()
    return str(index + 1)


def main() -> None:
    FIGDIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for trial_id, document_id, locator, page_number, rationale in SAMPLES:
        pdf_path = DOC_PATHS[document_id]
        out_name = f"{trial_id}_{safe_name(document_id)}_p{page_number}.png"
        out_path = FIGDIR / out_name
        rendered_page = render_page(pdf_path, page_number, out_path)
        rows.append({
            "trial_id": trial_id,
            "document_id": document_id,
            "local_pdf": str(pdf_path),
            "locator": locator,
            "requested_page": str(page_number),
            "rendered_pdf_page": rendered_page,
            "audit_image": str(out_path),
            "audit_rationale": rationale,
            "visual_audit_status": "rendered_pending_visual_review",
        })

    TABLE_OUT.parent.mkdir(parents=True, exist_ok=True)
    with TABLE_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    REPORT_OUT.write_text(
        "\n".join([
            "# Visual source audit sample pages 报告",
            "",
            "日期：2026-06-19",
            "",
            "## 输出",
            "",
            "- `tables/visual_source_audit_sample_pages.csv`",
            "- `figures/source_audit_pages/*.png`",
            "",
            "## 覆盖",
            "",
            f"- 渲染审计页：{len(rows)}",
            "- 覆盖 trial：TRIAL001, TRIAL002, TRIAL003, TRIAL004, TRIAL014",
            "",
            "## 说明",
            "",
            "这些页面用于正式稿前抽样视觉审计。数据层已自动确认；视觉审计主要用于确认 PDF 页面布局、表格位置和文本抽取未误读。",
        ]) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {TABLE_OUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")
    print(f"Rendered {len(rows)} audit pages to {FIGDIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
