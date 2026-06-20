#!/usr/bin/env python3
"""Download focused FDA review PDFs referenced by locally available TOC pages."""

from __future__ import annotations

import csv
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import http.client
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "tables"
RAW_DIR = ROOT / "data" / "raw" / "drugs_fda" / "review_documents"
FDA_QUEUE = TABLES / "fda_expansion_priority_document_queue.csv"
MANIFEST = RAW_DIR / "toc_review_pdf_download_manifest.tsv"

REVIEW_KEY_RE = re.compile(
    r"(?:medr|medical|multidiscipline|sumr|summary|statr|statistical|riskr|clinical|clinpharmr|approv)",
    re.I,
)
PDF_RE = re.compile(r'"([^"]+\.pdf)"', re.I)
ASSIGNMENT_RE = re.compile(r"([A-Za-z0-9_]+)\s*:\s*\"([^\"]+\.pdf)\"", re.I)
BASE_NAME_RE = re.compile(r"pdfBaseName\s*=\s*\"([^\"]+)\"", re.I)
FALLBACK_SUFFIXES = [
    "MultidisciplineR.pdf",
    "MedR.pdf",
    "MedicalR.pdf",
    "SumR.pdf",
    "StatR.pdf",
    "RiskR.pdf",
    "ClinPharmR.pdf",
    "Approv.pdf",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=8) as response:
        return response.read()


def pdf_names_from_toc(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    names = set()
    for key, pdf_name in ASSIGNMENT_RE.findall(text):
        if ("+" not in pdf_name and " " not in pdf_name) and (REVIEW_KEY_RE.search(key) or REVIEW_KEY_RE.search(pdf_name)):
            names.add(pdf_name)
    for pdf_name in PDF_RE.findall(text):
        if ("+" not in pdf_name and " " not in pdf_name) and REVIEW_KEY_RE.search(pdf_name):
            names.add(pdf_name)
    base_match = BASE_NAME_RE.search(text)
    if base_match:
        for suffix in FALLBACK_SUFFIXES:
            names.add(base_match.group(1) + suffix)
    return names


def target_name(url: str) -> str:
    name = urllib.parse.urlparse(url).path.rsplit("/", 1)[-1]
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_") or "review.pdf"


def main() -> None:
    queue = read_csv(FDA_QUEUE)
    toc_rows = []
    for row in queue:
        if row["priority"] != "P1" or row["local_file_status"] != "present":
            continue
        local_file = Path(row["expected_local_file"])
        if local_file.suffix.lower() not in {".html", ".htm"} or not local_file.exists():
            continue
        toc_rows.append(row)

    targets: dict[tuple[str, str], dict[str, str]] = {}
    for row in toc_rows:
        toc_file = Path(row["expected_local_file"])
        base_url = row["url_or_local_path"].rsplit("/", 1)[0] + "/"
        for pdf_name in pdf_names_from_toc(toc_file):
            url = urllib.parse.urljoin(base_url, pdf_name)
            targets[(row["drug_id"], url)] = {
                "drug_id": row["drug_id"],
                "candidate_approval_ids": row["candidate_approval_ids"],
                "toc_file": str(toc_file),
                "toc_url": row["url_or_local_path"],
                "url": url,
            }

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = ["drug_id", "candidate_approval_ids", "toc_file", "source_url", "local_file", "status"]
    existing_status: dict[str, str] = {}
    if MANIFEST.exists():
        with MANIFEST.open(newline="", encoding="utf-8") as f:
            existing_status = {row["source_url"]: row["status"] for row in csv.DictReader(f)}

    rows = []
    with MANIFEST.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for target in sorted(targets.values(), key=lambda item: (item["drug_id"], item["url"])):
            drug_dir = RAW_DIR / target["drug_id"]
            drug_dir.mkdir(parents=True, exist_ok=True)
            out = drug_dir / target_name(target["url"])
            if out.exists() and out.stat().st_size > 0:
                status = "already_exists"
            elif existing_status.get(target["url"], "").startswith("error"):
                status = existing_status[target["url"]]
            else:
                try:
                    data = fetch(target["url"])
                    out.write_bytes(data)
                    status = f"downloaded_{len(data)}_bytes" if data.startswith(b"%PDF") else f"saved_non_pdf_{len(data)}_bytes"
                except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, http.client.InvalidURL, OSError) as exc:
                    status = f"error:{type(exc).__name__}:{exc}"
            manifest_row = {
                "drug_id": target["drug_id"],
                "candidate_approval_ids": target["candidate_approval_ids"],
                "toc_file": target["toc_file"],
                "source_url": target["url"],
                "local_file": str(out) if out.exists() else "",
                "status": status,
            }
            rows.append(manifest_row)
            writer.writerow(manifest_row)
            f.flush()
            time.sleep(0.03)

    ok = sum(1 for row in rows if row["status"].startswith(("downloaded", "already_exists")))
    print(f"TOC files scanned: {len(toc_rows)}")
    print(f"Review PDF targets: {len(rows)}")
    print(f"Available locally: {ok}")
    print(f"Wrote {MANIFEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
