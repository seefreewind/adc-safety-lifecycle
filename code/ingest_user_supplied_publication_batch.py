#!/usr/bin/env python3
"""Ingest user-supplied publication files into the expansion publication folder."""

from __future__ import annotations

import csv
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = Path("/Users/zy/gaofen")
DEST_DIR = ROOT / "data" / "raw" / "publications" / "expansion"
TABLES = ROOT / "tables"
PROTOCOL = ROOT / "protocol"


ROWS = [
    ["TRIAL001", "DESTINY-Breast01", "ADC007", "supplementary appendix", "nejmoa1914510_appendix.pdf", "DESTINYBreast01_Modi_2020_NEJM_appendix_usercopy.pdf", "duplicate_or_update", "Already available in pilot folder; retained as user-supplied duplicate."],
    ["TRIAL001", "DESTINY-Breast01", "ADC007", "protocol", "nejmoa1914510_protocol.pdf", "DESTINYBreast01_Modi_2020_NEJM_protocol.pdf", "new_useful", "Protocol/SAP for pilot trial."],
    ["TRIAL007", "SG035-0003", "ADC002", "main article", "/Users/zy/Downloads/P22454421_1397573_副本.pdf", "SG0350003_Younes_2012_JCO_PMID22454421.pdf", "new_useful", "Primary publication for brentuximab vedotin in relapsed/refractory Hodgkin lymphoma."],
    ["TRIAL008", "SG035-0004", "ADC002", "main article", "/Users/zy/Downloads/P22614995_1397574_副本.pdf", "SG0350004_Pro_2012_JCO_PMID22614995.pdf", "new_useful", "Primary publication for brentuximab vedotin in systemic ALCL."],
    ["TRIAL009", "EMILIA", "ADC003", "main article", "/Users/zy/Downloads/P23020162_1397575_副本.pdf", "EMILIA_Verma_2012_NEJM_PMID23020162.pdf", "new_useful", "Primary publication for T-DM1 EMILIA."],
    ["TRIAL009", "EMILIA", "ADC003", "supplementary appendix", "nejmoa1209124_appendix.pdf", "EMILIA_Verma_2012_NEJM_appendix.pdf", "new_useful", "Supplementary appendix for T-DM1 EMILIA."],
    ["TRIAL009", "EMILIA", "ADC003", "protocol", "nejmoa1209124_protocol.pdf", "EMILIA_Verma_2012_NEJM_protocol.pdf", "new_useful", "Protocol/SAP for T-DM1 EMILIA."],
    ["TRIAL010", "INO-VATE ALL", "ADC004", "main article", "P27292104_1397005_副本2.pdf", "INOVATEALL_Kantarjian_2016_NEJM_PMID27292104.pdf", "new_useful", "Primary publication for inotuzumab ozogamicin."],
    ["TRIAL010", "INO-VATE ALL", "ADC004", "supplementary appendix", "nejmoa1509277_appendix.pdf", "INOVATEALL_Kantarjian_2016_NEJM_appendix.pdf", "new_useful", "Supplementary appendix."],
    ["TRIAL010", "INO-VATE ALL", "ADC004", "protocol", "nejmoa1509277_protocol.pdf", "INOVATEALL_Kantarjian_2016_NEJM_protocol.pdf", "new_useful", "Protocol/SAP."],
    ["TRIAL011", "GO29365", "ADC005", "main article", "P31693429_1397016_副本2.pdf", "GO29365_Sehn_2019_JCO_PMID31693429.pdf", "new_useful", "Primary publication for polatuzumab vedotin plus BR."],
    ["TRIAL012", "LOTIS-2", "ADC010", "main article", "P33989558_1397019_副本2.pdf", "LOTIS2_Caimi_2021_LancetOncol_PMID33989558.pdf", "new_useful", "Primary publication for loncastuximab tesirine."],
    ["TRIAL012", "LOTIS-2", "ADC010", "supplementary appendix", "1-s2.0-S147020452100139X-mmc1.pdf", "LOTIS2_Caimi_2021_LancetOncol_appendix.pdf", "new_useful", "Supplementary appendix."],
    ["TRIAL013", "innovaTV 204", "ADC011", "main article", "P33845034_1397021_副本2.pdf", "innovaTV204_Coleman_2021_LancetOncol_PMID33845034.pdf", "new_useful", "Primary publication for tisotumab vedotin accelerated approval."],
    ["TRIAL013", "innovaTV 204", "ADC011", "supplementary appendix", "1-s2.0-S1470204521000565-mmc1.pdf", "innovaTV204_Coleman_2021_LancetOncol_appendix.pdf", "new_useful", "Supplementary appendix."],
    ["TRIAL014", "innovaTV 301", "ADC011", "main article", "P38959480_1397023_副本2.pdf", "innovaTV301_Vergote_2024_NEJM_PMID38959480.pdf", "new_useful", "Primary publication for tisotumab vedotin regular approval."],
    ["TRIAL014", "innovaTV 301", "ADC011", "supplementary appendix", "nejmoa2313811_appendix.pdf", "innovaTV301_Vergote_2024_NEJM_appendix.pdf", "new_useful", "Supplementary appendix."],
    ["TRIAL014", "innovaTV 301", "ADC011", "protocol", "nejmoa2313811_protocol.pdf", "innovaTV301_Vergote_2024_NEJM_protocol.pdf", "new_useful", "Protocol/SAP."],
    ["TRIAL015", "SORAYA", "ADC012", "main article", "P36716407_1397026_副本2.pdf", "SORAYA_Matulonis_2023_JCO_PMID36716407.pdf", "new_useful", "Primary publication for mirvetuximab accelerated approval."],
    ["TRIAL015", "SORAYA", "ADC012", "protocol", "protocol_jco.22.01900.pdf", "SORAYA_Matulonis_2023_JCO_protocol.pdf", "new_useful", "Protocol for SORAYA."],
    ["TRIAL016", "MIRASOL", "ADC012", "main article", "P38055253_1397027_副本2.pdf", "MIRASOL_Moore_2023_NEJM_PMID38055253.pdf", "new_useful", "Primary publication for mirvetuximab regular approval."],
    ["TRIAL016", "MIRASOL", "ADC012", "supplementary appendix", "nejmoa2309169_appendix.pdf", "MIRASOL_Moore_2023_NEJM_appendix.pdf", "new_useful", "Supplementary appendix."],
    ["TRIAL016", "MIRASOL", "ADC012", "protocol", "nejmoa2309169_protocol.pdf", "MIRASOL_Moore_2023_NEJM_protocol.pdf", "new_useful", "Protocol/SAP."],
    ["TRIAL017", "DREAMM-7", "ADC009", "main article", "P38828933_1397030_副本2.pdf", "DREAMM7_Mateos_2024_NEJM_PMID38828933.pdf", "new_useful", "Primary publication for belantamab reapproval evidence."],
    ["TRIAL018", "DREAMM-8", "ADC009", "main article", "P38828951_1397047_副本2.pdf", "DREAMM8_Dimopoulos_2024_NEJM_PMID38828951.pdf", "new_useful", "Primary publication for belantamab reapproval evidence."],
    ["TRIAL019", "TROPION-Breast01", "ADC013", "main article", "P39265124_1397048_副本2.pdf", "TROPIONBreast01_Bardia_2024_JCO_PMID39265124.pdf", "new_useful", "Primary publication for datopotamab deruxtecan breast cancer."],
    ["TRIAL019", "TROPION-Breast01", "ADC013", "publisher html", "Datopotamab Deruxtecan Versus Chemotherapy in Previously Treated Inoperable_Metastatic Hormone Receptor–Positive Human Epidermal Growth Factor Receptor 2–Negative Breast Cancer_ Primary Results From TROPION-Breast01 _ Journal of Clinical Oncology.html", "TROPIONBreast01_Bardia_2024_JCO.html", "new_useful", "Publisher HTML for table and figure extraction."],
    ["TRIAL019", "TROPION-Breast01", "ADC013", "publisher html files", "Datopotamab Deruxtecan Versus Chemotherapy in Previously Treated Inoperable_Metastatic Hormone Receptor–Positive Human Epidermal Growth Factor Receptor 2–Negative Breast Cancer_ Primary Results From TROPION-Breast01 _ Journal of Clinical Oncology_files", "TROPIONBreast01_Bardia_2024_JCO_files", "new_useful", "Publisher HTML asset folder."],
    ["TRIAL020", "TROPION-Lung05", "ADC013", "main article", "P39761483_1397051_副本2.pdf", "TROPIONLung05_Sands_2024_JCO_PMID39761483.pdf", "new_useful", "Primary publication for datopotamab deruxtecan NSCLC."],
    ["TRIAL020", "TROPION-Lung05", "ADC013", "data supplement", "ds_jco-24-01349.pdf", "TROPIONLung05_Sands_2024_JCO_data_supplement.pdf", "new_useful", "Data supplement."],
    ["TRIAL020", "TROPION-Lung05", "ADC013", "protocol", "protocol_jco-24-01349.pdf", "TROPIONLung05_Sands_2024_JCO_protocol.pdf", "new_useful", "Protocol."],
    ["TRIAL021", "LUMINOSITY", "ADC014", "main article", "P38843488_1397054_副本2.pdf", "LUMINOSITY_Camidge_2024_JCO_PMID38843488_accepted_manuscript.pdf", "new_useful", "Accepted manuscript for telisotuzumab vedotin."],
    ["TRIAL021", "LUMINOSITY", "ADC014", "publisher html", "Telisotuzumab Vedotin Monotherapy in Patients With Previously Treated c-Met Protein–Overexpressing Advanced Nonsquamous EGFR-Wildtype Non–Small Cell Lung Cancer in the Phase II LUMINOSITY Trial _ Journal of Clinical Oncology.html", "LUMINOSITY_Camidge_2024_JCO.html", "new_useful", "Publisher HTML for table and figure extraction."],
    ["TRIAL021", "LUMINOSITY", "ADC014", "publisher html files", "Telisotuzumab Vedotin Monotherapy in Patients With Previously Treated c-Met Protein–Overexpressing Advanced Nonsquamous EGFR-Wildtype Non–Small Cell Lung Cancer in the Phase II LUMINOSITY Trial _ Journal of Clinical Oncology_files", "LUMINOSITY_Camidge_2024_JCO_files", "new_useful", "Publisher HTML asset folder."],
    ["TRIAL021", "LUMINOSITY", "ADC014", "protocol", "protocol_jco.24.00720.pdf", "LUMINOSITY_Camidge_2024_JCO_protocol.pdf", "new_useful", "Protocol."],
    ["TRIAL022", "TROPION-Breast02", "ADC013", "main article", "/Users/zy/Downloads/P41937088_1397055 2_副本.pdf", "TROPIONBreast02_Dent_2026_AnnOncol_PMID41937088.pdf", "new_useful", "Primary publication for datopotamab deruxtecan in untreated advanced TNBC."],
    ["TRIAL023", "CADENZA", "ADC015", "main article", "P41671533_1397058_副本2.pdf", "CADENZA_Pemmaraju_2025_JCO_PMID41671533.pdf", "new_useful", "Primary publication for pivekimab sunirine."],
    ["TRIAL023", "CADENZA", "ADC015", "data supplement", "ds_jco-25-02083.pdf", "CADENZA_Pemmaraju_2025_JCO_data_supplement.pdf", "new_useful", "Data supplement."],
    ["TRIAL023", "CADENZA", "ADC015", "protocol", "protocol_jco-25-02083.pdf", "CADENZA_Pemmaraju_2025_JCO_protocol.pdf", "new_useful", "Protocol/SAP."],
]


def copy_item(src: Path, dst: Path) -> str:
    if not src.exists():
        return "source_missing"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)
    return "copied"


def main() -> None:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(exist_ok=True)
    out_rows = []
    for trial_id, acronym, drug_id, role, source_name, dest_name, use_status, notes in ROWS:
        source_path = Path(source_name)
        src = source_path if source_path.is_absolute() else SOURCE_DIR / source_name
        dst = DEST_DIR / trial_id / dest_name
        copy_status = copy_item(src, dst)
        out_rows.append({
            "trial_id": trial_id,
            "acronym": acronym,
            "drug_id": drug_id,
            "document_role": role,
            "source_file": str(src),
            "project_file": str(dst),
            "copy_status": copy_status,
            "use_status": use_status,
            "notes": notes,
        })

    inventory = TABLES / "user_supplied_publication_batch_inventory.csv"
    with inventory.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0]))
        writer.writeheader()
        writer.writerows(out_rows)

    by_trial: dict[str, list[dict[str, str]]] = {}
    for row in out_rows:
        by_trial.setdefault(row["trial_id"], []).append(row)

    lines = [
        "# 用户补充全文文件批次核对报告",
        "",
        "日期：2026-06-18",
        "",
        "## 输出",
        "",
        "- `data/raw/publications/expansion/`",
        "- `tables/user_supplied_publication_batch_inventory.csv`",
        "",
        "## 本批次可用文件",
        "",
    ]
    for trial_id in sorted(by_trial):
        rows = by_trial[trial_id]
        copied = sum(1 for row in rows if row["copy_status"] == "copied")
        roles = ", ".join(sorted({row["document_role"] for row in rows}))
        lines.append(f"- `{trial_id}` / {rows[0]['acronym']}：{copied}/{len(rows)} copied；{roles}")
    lines.extend([
        "",
        "## 仍需优先补齐",
        "",
        "- `TRIAL007` / SG035-0003：Adcetris Hodgkin lymphoma pivotal primary paper full text and supplement/protocol if available.",
        "- `TRIAL008` / SG035-0004：Adcetris systemic ALCL pivotal primary paper full text and supplement/protocol if available.",
        "- `TRIAL009` / EMILIA：main NEJM article PDF is still missing; appendix and protocol are now available.",
        "- `TRIAL017` / DREAMM-7：main article available; supplementary appendix/protocol not yet supplied.",
        "- `TRIAL018` / DREAMM-8：main article available; supplementary appendix/protocol not yet supplied.",
        "- `TRIAL019` / TROPION-Breast01：main article and HTML available; data supplement/protocol still need confirmation if separate files exist.",
        "- `TRIAL021` / LUMINOSITY：main/HTML/protocol available; data supplement still need confirmation if separate file exists.",
        "",
        "## 备注",
        "",
        "本报告只判断文件是否可用于 source locator 和后续安全数据抽取，不代表数值已经完成提取。下一步应把这些文件纳入 expansion publication locator，并继续按来源、分母、治疗臂、时间窗进行可比性分级。",
    ])
    (PROTOCOL / "user_supplied_publication_batch_check.zh.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {inventory.relative_to(ROOT)}")
    print("Wrote protocol/user_supplied_publication_batch_check.zh.md")
    print(f"Copied {sum(1 for row in out_rows if row['copy_status'] == 'copied')} of {len(out_rows)} mapped files/folders.")


if __name__ == "__main__":
    main()
