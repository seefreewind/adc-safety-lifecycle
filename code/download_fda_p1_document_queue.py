#!/usr/bin/env python3
"""Download missing P1 FDA expansion documents only."""

from __future__ import annotations

import csv
import re
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "tables" / "fda_expansion_priority_document_queue.csv"
RAW_DIR = ROOT / "data" / "raw" / "drugs_fda" / "review_documents"
MANIFEST = RAW_DIR / "p1_document_download_manifest.tsv"


def slug_from_url(url: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", url.split("/")[-1])
    return cleaned.strip("_")[:180] or "document"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return response.read()


def main() -> None:
    rows = list(csv.DictReader(QUEUE.open(newline="", encoding="utf-8")))
    targets = []
    seen = set()
    for row in rows:
        if row["priority"] != "P1" or row["local_file_status"] != "missing":
            continue
        key = (row["drug_id"], row["url_or_local_path"])
        if key in seen:
            continue
        seen.add(key)
        targets.append(row)

    MANIFEST.write_text("drug_id\turl\tlocal_file\tstatus\tnotes\n", encoding="utf-8")
    status_counts = {}
    for row in targets:
        drug_id = row["drug_id"]
        url = row["url_or_local_path"]
        drug_dir = RAW_DIR / drug_id
        drug_dir.mkdir(parents=True, exist_ok=True)
        out = drug_dir / slug_from_url(url)
        if out.exists():
            status = "already_present"
        else:
            try:
                data = fetch(url)
                out.write_bytes(data)
                if url.lower().endswith(".pdf") and not data.startswith(b"%PDF"):
                    status = f"saved_non_pdf_{len(data)}_bytes"
                else:
                    status = f"downloaded_{len(data)}_bytes"
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
                status = f"failed_{type(exc).__name__}:{exc}"
                out = Path("")
        status_counts[status.split("_")[0]] = status_counts.get(status.split("_")[0], 0) + 1
        with MANIFEST.open("a", encoding="utf-8") as f:
            f.write("\t".join([drug_id, url, str(out), status, row["priority_reason"]]) + "\n")
        time.sleep(0.05)

    print(f"Attempted {len(targets)} unique missing P1 FDA documents.")
    print(status_counts)
    print(f"Wrote {MANIFEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
