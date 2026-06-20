#!/usr/bin/env python3
"""Download FDA Drugs@FDA TOC pages and linked documents for selected drugs."""

from __future__ import annotations

import csv
import re
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "data" / "processed" / "fda_review_document_inventory.csv"
RAW_DIR = ROOT / "data" / "raw" / "drugs_fda" / "review_documents"

PILOT_DRUGS = {"ADC001", "ADC006", "ADC007", "ADC008", "ADC009"}


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.links.append(value)


def slug(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", text)
    return cleaned.strip("_")[:180]


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(INVENTORY.open(newline="", encoding="utf-8")))
    manifest = []

    for row in rows:
        drug_id = row["drug_id"]
        if drug_id not in PILOT_DRUGS:
            continue
        url = row["url_or_local_path"]
        if not url.lower().endswith("toc.html"):
            continue

        drug_dir = RAW_DIR / drug_id
        drug_dir.mkdir(exist_ok=True)
        toc_file = drug_dir / slug(url.split("/")[-1])
        try:
            toc_data = fetch(url)
            toc_file.write_bytes(toc_data)
            manifest.append([drug_id, url, str(toc_file), "downloaded_toc"])
        except Exception as exc:
            manifest.append([drug_id, url, "", f"toc_error: {exc!r}"])
            continue

        parser = LinkParser()
        parser.feed(toc_data.decode("utf-8", errors="ignore"))
        for href in parser.links:
            full = urllib.parse.urljoin(url, href)
            lower = full.lower()
            if not any(token in lower for token in ["review", "label", "multidiscipline", "medical", "statistical"]):
                continue
            if not lower.endswith((".pdf", ".html", ".htm")):
                continue
            out = drug_dir / slug(urllib.parse.urlparse(full).path.split("/")[-1])
            if out.exists():
                manifest.append([drug_id, full, str(out), "already_exists"])
                continue
            try:
                out.write_bytes(fetch(full))
                manifest.append([drug_id, full, str(out), "downloaded_linked_doc"])
                time.sleep(0.1)
            except Exception as exc:
                manifest.append([drug_id, full, "", f"linked_doc_error: {exc!r}"])

    with (RAW_DIR / "pilot_download_manifest.tsv").open("w", encoding="utf-8") as f:
        f.write("drug_id\turl\tlocal_file\tstatus\n")
        for item in manifest:
            f.write("\t".join(item) + "\n")

    print(f"Wrote {len(manifest)} download manifest rows.")


if __name__ == "__main__":
    main()

