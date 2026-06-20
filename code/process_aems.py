#!/usr/bin/env python3
"""Prepare AEMS/FAERS quarterly files for signal detection.

The expected raw layout is one directory per quarter under data/raw/aems.
This scaffold records file availability and enforces the deduplication plan.
"""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_AEMS = ROOT / "data" / "raw" / "aems"
OUT = ROOT / "data" / "interim" / "aems_file_inventory.csv"


def main() -> None:
    rows = []
    for path in sorted(RAW_AEMS.glob("**/*")):
        if path.is_file():
            rows.append([str(path), path.parent.name, path.suffix.lower(), path.stat().st_size, "pending_parse"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["file_path", "quarter_or_folder", "extension", "bytes", "status"])
        writer.writerows(rows)

    print(f"Indexed {len(rows)} AEMS/FAERS raw files.")


if __name__ == "__main__":
    main()

