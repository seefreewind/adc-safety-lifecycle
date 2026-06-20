#!/usr/bin/env python3
"""Download generated PDF filenames from FDA approval-package TOC pages."""

from __future__ import annotations

import re
import time
import csv
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "drugs_fda" / "review_documents"
INVENTORY = ROOT / "data" / "processed" / "fda_review_document_inventory.csv"

FALLBACK_SUFFIXES = [
    "Approv.pdf",
    "Lbl.pdf",
    "lbl.pdf",
    "MultidisciplineR.pdf",
    "MedR.pdf",
    "StatR.pdf",
    "RiskR.pdf",
    "ChemR.pdf",
    "ClinPharmR.pdf",
    "SumR.pdf",
]


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as response:
        return response.read()


def pdf_names_from_toc(text: str) -> set[str]:
    names = set(re.findall(r'"([^"]+\.pdf)"', text, flags=re.IGNORECASE))
    base = re.search(r'var\s+pdfBaseName\s*=\s*"([^"]+)"', text)
    if base:
        for suffix in FALLBACK_SUFFIXES:
            names.add(base.group(1) + suffix)
    return names


def main() -> None:
    toc_urls = {}
    with INVENTORY.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            url = row["url_or_local_path"]
            if url.lower().endswith("toc.html"):
                toc_urls[url.split("/")[-1]] = url

    manifest = []
    manifest_path = RAW_DIR / "generated_pdf_download_manifest.tsv"
    manifest_path.write_text("drug_id\turl\tlocal_file\tstatus\n", encoding="utf-8")
    for toc in sorted(RAW_DIR.glob("ADC*/*TOC.html")):
        drug_id = toc.parent.name
        text = toc.read_text(encoding="utf-8", errors="ignore")
        toc_url = toc_urls.get(toc.name)
        if not toc_url:
            manifest.append([drug_id, str(toc), "", "missing_original_toc_url"])
            continue
        base_url = toc_url.rsplit("/", 1)[0] + "/"
        for name in sorted(pdf_names_from_toc(text)):
            lower = name.lower()
            if not any(token in lower for token in ["approv", "lbl", "multidiscipline", "medr", "statr", "riskr", "chemr", "clinpharmr", "sumr"]):
                continue
            url = urllib.parse.urljoin(base_url, name)
            out = toc.parent / name
            if out.exists():
                manifest.append([drug_id, url, str(out), "already_exists"])
                continue
            try:
                data = fetch(url)
                if not data.startswith(b"%PDF"):
                    manifest.append([drug_id, url, "", f"not_pdf_{len(data)}_bytes"])
                    continue
                out.write_bytes(data)
                manifest.append([drug_id, url, str(out), f"downloaded_{len(data)}_bytes"])
                time.sleep(0.1)
            except Exception as exc:
                manifest.append([drug_id, url, "", f"error: {exc!r}"])
            with manifest_path.open("a", encoding="utf-8") as f:
                f.write("\t".join(manifest[-1]) + "\n")

    print(f"Wrote {len(manifest)} generated-PDF manifest rows.")


if __name__ == "__main__":
    main()
