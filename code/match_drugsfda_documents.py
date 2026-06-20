#!/usr/bin/env python3
"""Match working ADC cohort to Drugs@FDA product and document tables."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "drugs_fda" / "drugsatfda_data"
PROCESSED = ROOT / "data" / "processed"


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="latin-1") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def norm(text: str) -> str:
    return " ".join((text or "").lower().replace("-", " ").split())


def main() -> None:
    drugs = list(csv.DictReader((PROCESSED / "drug_master.csv").open(newline="", encoding="utf-8")))
    products = read_tsv(DATA / "Products.txt")
    apps = {row["ApplNo"]: row for row in read_tsv(DATA / "Applications.txt")}
    docs = read_tsv(DATA / "ApplicationDocs.txt")
    docs_by_appl: dict[str, list[dict[str, str]]] = {}
    for row in docs:
        docs_by_appl.setdefault(row["ApplNo"], []).append(row)

    product_rows = []
    doc_rows = []
    doc_seq = 1
    for drug in drugs:
        terms = {
            norm(drug["generic_name"]),
            norm(drug["brand_name"]),
        }
        for alias in [drug["generic_name"].replace("fam-", ""), drug["generic_name"].replace("ado-", "")]:
            terms.add(norm(alias))

        matched_products = []
        for product in products:
            hay = norm(product.get("DrugName", "") + " " + product.get("ActiveIngredient", ""))
            if any(term and term in hay for term in terms):
                matched_products.append(product)

        for product in matched_products:
            appl = product["ApplNo"]
            app = apps.get(appl, {})
            product_rows.append([
                drug["drug_id"], drug["generic_name"], drug["brand_name"], appl,
                app.get("ApplType", ""), app.get("SponsorName", ""),
                product.get("ProductNo", ""), product.get("DrugName", ""),
                product.get("ActiveIngredient", ""), product.get("Form", ""),
                product.get("Strength", ""),
            ])

            for doc in docs_by_appl.get(appl, []):
                title = doc.get("ApplicationDocsTitle", "")
                url = doc.get("ApplicationDocsURL", "")
                date = doc.get("ApplicationDocsDate", "").split(" ")[0]
                if not url:
                    continue
                doc_rows.append([
                    f"FDADOC{doc_seq:06d}", drug["drug_id"], "", "Drugs@FDA document",
                    title, date, url, "", "not_downloaded", "needs_triage",
                    f"ApplNo {appl}; Submission {doc.get('SubmissionType','').strip()} {doc.get('SubmissionNo','').strip()}",
                ])
                doc_seq += 1

    with (PROCESSED / "drugsfda_adc_product_matches.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "drug_id", "generic_name", "brand_name", "appl_no", "appl_type", "sponsor_name",
            "product_no", "drug_name", "active_ingredient", "form", "strength",
        ])
        writer.writerows(product_rows)

    with (PROCESSED / "fda_review_document_inventory.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "document_id", "drug_id", "approval_id", "document_type", "document_title",
            "document_date", "url_or_local_path", "local_file", "download_status",
            "extraction_status", "notes",
        ])
        writer.writerows(doc_rows)

    print(f"Matched {len(product_rows)} product rows and {len(doc_rows)} FDA document rows.")


if __name__ == "__main__":
    main()

