#!/usr/bin/env python3
"""Fetch openFDA drug label snapshots for the ADC cohort."""

from __future__ import annotations

import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRUG_MASTER = ROOT / "data" / "processed" / "drug_master.csv"
RAW_DIR = ROOT / "data" / "raw" / "labels" / "openfda"
OUT = ROOT / "data" / "interim" / "openfda_label_fetch_manifest.csv"


def query_openfda(term: str) -> dict:
    search = f'openfda.brand_name:"{term}" OR openfda.generic_name:"{term}"'
    params = urllib.parse.urlencode({"search": search, "limit": 10})
    url = f"https://api.fda.gov/drug/label.json?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=8) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    drugs = list(csv.DictReader(DRUG_MASTER.open(newline="", encoding="utf-8")))
    manifest = []
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("drug_id,query_term,local_file,result_count,status\n", encoding="utf-8")

    def record(row: list) -> None:
        manifest.append(row)
        with OUT.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(row)

    for drug in drugs:
        candidates = [drug["brand_name"], drug["generic_name"]]
        success = False
        for term in candidates:
            if not term:
                continue
            out = RAW_DIR / f"{drug['drug_id']}_{term.replace(' ', '_').replace('/', '_')}.json"
            try:
                data = query_openfda(term)
                out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
                record([drug["drug_id"], term, str(out), len(data.get("results", [])), "downloaded"])
                success = True
                break
            except Exception as exc:
                record([drug["drug_id"], term, "", 0, f"error: {exc!r}"])
                time.sleep(0.2)
        if not success:
            record([drug["drug_id"], "", "", 0, "no_openfda_label_found"])
        time.sleep(0.2)

    print(f"Wrote {len(manifest)} openFDA label manifest rows.")


if __name__ == "__main__":
    main()
