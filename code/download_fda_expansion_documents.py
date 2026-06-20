#!/usr/bin/env python3
"""Download FDA label, letter, TOC, and review documents for expansion candidates."""

from __future__ import annotations

import csv
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RAW_DIR = ROOT / "data" / "raw" / "drugs_fda" / "review_documents"
INVENTORY = PROCESSED / "fda_review_document_inventory.csv"
EXPANSION_APPROVALS = PROCESSED / "approval_event_expansion_candidates.csv"
MANIFEST = RAW_DIR / "expansion_document_download_manifest.tsv"

DIRECT_TOKENS = [
    "label",
    "lbl",
    "appletter",
    "approv",
    "sumr",
    "toc.html",
    "multidiscipline",
    "medr",
    "medical",
    "statr",
    "riskr",
]

LINK_TOKENS = [
    "review",
    "label",
    "lbl",
    "multidiscipline",
    "medical",
    "medr",
    "stat",
    "risk",
    "approv",
    "sumr",
]

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
    return cleaned.strip("_")[:180] or "document"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()


def candidate_drugs() -> set[str]:
    with EXPANSION_APPROVALS.open(newline="", encoding="utf-8") as f:
        return {row["drug_id"] for row in csv.DictReader(f)}


def should_download_url(url: str) -> bool:
    lower = url.lower()
    if not lower.endswith((".pdf", ".html", ".htm")):
        return False
    return any(token in lower for token in DIRECT_TOKENS)


def pdf_names_from_toc(text: str) -> set[str]:
    names = set(re.findall(r'"([^"]+\.pdf)"', text, flags=re.IGNORECASE))
    base = re.search(r'var\s+pdfBaseName\s*=\s*"([^"]+)"', text)
    if base:
        for suffix in FALLBACK_SUFFIXES:
            names.add(base.group(1) + suffix)
    return names


def write_manifest_row(row: list[str]) -> None:
    with MANIFEST.open("a", encoding="utf-8") as f:
        f.write("\t".join(row) + "\n")


def save_document(drug_id: str, url: str, reason: str) -> tuple[str, str]:
    drug_dir = RAW_DIR / drug_id
    drug_dir.mkdir(parents=True, exist_ok=True)
    name = slug(urllib.parse.urlparse(url).path.split("/")[-1])
    out = drug_dir / name
    if out.exists():
        return str(out), "already_exists"
    try:
        data = fetch(url)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        return "", f"error:{type(exc).__name__}:{exc}"
    out.write_bytes(data)
    lower = url.lower()
    if lower.endswith(".pdf") and not data.startswith(b"%PDF"):
        return str(out), f"saved_non_pdf_{len(data)}_bytes"
    return str(out), f"downloaded_{reason}_{len(data)}_bytes"


def linked_urls_from_toc(toc_url: str, toc_file: Path) -> list[str]:
    text = toc_file.read_text(encoding="utf-8", errors="ignore")
    urls = []
    parser = LinkParser()
    parser.feed(text)
    for href in parser.links:
        full = urllib.parse.urljoin(toc_url, href)
        lower = full.lower()
        if lower.endswith((".pdf", ".html", ".htm")) and any(token in lower for token in LINK_TOKENS):
            urls.append(full)
    base_url = toc_url.rsplit("/", 1)[0] + "/"
    for pdf_name in pdf_names_from_toc(text):
        lower = pdf_name.lower()
        if any(token in lower for token in LINK_TOKENS):
            urls.append(urllib.parse.urljoin(base_url, pdf_name))
    return sorted(set(urls))


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text("drug_id\tsource_url\tlocal_file\tstatus\treason\n", encoding="utf-8")
    drugs = candidate_drugs()
    inventory = list(csv.DictReader(INVENTORY.open(newline="", encoding="utf-8")))

    downloaded_primary = 0
    linked_attempts = 0
    for row in inventory:
        drug_id = row.get("drug_id", "")
        if drug_id not in drugs:
            continue
        url = row.get("url_or_local_path", "")
        if not should_download_url(url):
            continue
        local, status = save_document(drug_id, url, "inventory")
        write_manifest_row([drug_id, url, local, status, row.get("notes", "")])
        downloaded_primary += 1
        if local and url.lower().endswith(("toc.html", ".htm", ".html")):
            toc_file = Path(local)
            if toc_file.exists():
                for linked in linked_urls_from_toc(url, toc_file):
                    linked_local, linked_status = save_document(drug_id, linked, "toc_link")
                    write_manifest_row([drug_id, linked, linked_local, linked_status, f"linked from {url}"])
                    linked_attempts += 1
                    time.sleep(0.05)
        time.sleep(0.05)

    print(f"Processed {downloaded_primary} inventory document candidates.")
    print(f"Processed {linked_attempts} TOC-linked document candidates.")
    print(f"Wrote {MANIFEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
