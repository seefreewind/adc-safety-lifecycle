import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const workbook = Workbook.create();

const sheets = [
  "README",
  "Source_Inventory",
  "AE_Extraction_Form",
  "Arm_Dictionary",
  "Safety_Concept_Dictionary",
  "Adjudication_Log",
  "QC_Rules",
  "Extraction_Progress",
  "Curated_Facts_Need_Review",
  "FDA_Table_Locator",
];

for (const name of sheets) {
  workbook.worksheets.add(name);
}

function writeRows(sheetName, startCell, rows) {
  const sheet = workbook.worksheets.getItem(sheetName);
  const rowCount = rows.length;
  const colCount = Math.max(...rows.map((row) => row.length));
  const startCol = startCell.match(/[A-Z]+/)[0];
  const startRow = Number(startCell.match(/\d+/)[0]);
  const endCol = String.fromCharCode(startCol.charCodeAt(0) + colCount - 1);
  sheet.getRange(`${startCell}:${endCol}${startRow + rowCount - 1}`).values = rows.map((row) => {
    const padded = [...row];
    while (padded.length < colCount) padded.push("");
    return padded;
  });
}

writeRows("README", "A1", [
  ["ADC Safety Lifecycle AE Numeric Extraction Workbook"],
  ["Purpose", "Structured extraction of adverse-event values from FDA reviews, ClinicalTrials.gov, publications, supplements, and labels."],
  ["Primary analysis", "A-grade comparable source pairs only."],
  ["Sensitivity analysis", "B-grade source pairs."],
  ["Descriptive only", "C-grade source pairs."],
  ["Do not overwrite raw source files.", "Each extracted value must include document ID, locator, denominator, data cutoff date, extractor, and review status."],
]);

writeRows("Source_Inventory", "A1", [[
  "document_id", "trial_id", "approval_id", "drug_id", "source_type", "document_title",
  "document_date", "data_cutoff_date", "url_or_local_path", "analysis_population",
  "version", "extraction_status", "reviewer_1", "reviewer_2", "notes"
]]);

writeRows("AE_Extraction_Form", "A1", [[
  "observation_id", "trial_id", "arm_id", "document_id", "source_type", "page_or_table_locator",
  "ae_original_term", "ae_standardized_term", "meddra_pt", "meddra_soc", "smq",
  "safety_concept", "grade_category", "seriousness", "causality", "number_events",
  "number_patients", "denominator", "percentage_reported", "percentage_calculated",
  "percent_delta", "reporting_threshold", "analysis_population", "data_cutoff_date",
  "extractor", "review_status", "qc_flag", "notes"
]]);

const extractionExamples = [
  ["EXAMPLE001", "TRIAL001", "ARM001", "DOC001", "FDA review", "Table 25", "Serious adverse events", "serious_adverse_event", "", "", "", "serious_adverse_event", "all grades", "serious", "all-cause", "", 12, 100, 12, "=IF(OR(Q2=\"\",R2=\"\"),\"\",Q2/R2*100)", "=IF(OR(S2=\"\",T2=\"\"),\"\",S2-T2)", "", "safety population", "", "reviewer_1", "example", "=IF(OR(R2=\"\",Q2=\"\"),\"missing numerator/denominator\",IF(ABS(U2)>0.2,\"check percent\",\"ok\"))", "Delete this example row before analysis."],
];
writeRows("AE_Extraction_Form", "A2", extractionExamples);

writeRows("Arm_Dictionary", "A1", [[
  "arm_id", "trial_id", "arm_name", "regimen", "dose", "schedule", "monotherapy_or_combination",
  "safety_population", "notes"
]]);

writeRows("Safety_Concept_Dictionary", "A1", [[
  "concept_id", "safety_concept", "display_name", "priority", "example_terms", "meddra_pt_or_smq_notes", "review_status"
],[
  "SC001", "interstitial_lung_disease_pneumonitis", "Interstitial lung disease/pneumonitis", "primary", "ILD; pneumonitis; organizing pneumonia", "Manual mapping required", "draft"
],[
  "SC002", "keratopathy_ocular_surface_toxicity", "Keratopathy/ocular surface toxicity", "primary", "keratopathy; keratitis; corneal epithelial changes", "Manual mapping required", "draft"
],[
  "SC017", "fatal_adverse_event", "Fatal adverse event", "core_outcome", "fatal AE; AE leading to death", "Outcome not PT-only", "draft"
],[
  "SC018", "adverse_event_discontinuation", "AE leading to discontinuation", "core_outcome", "AE leading to discontinuation", "Outcome not PT-only", "draft"
]]);

writeRows("Adjudication_Log", "A1", [[
  "adjudication_id", "observation_id", "field_name", "reviewer_1_value", "reviewer_2_value",
  "adjudicated_value", "adjudicator", "decision_date", "reason", "notes"
]]);

writeRows("QC_Rules", "A1", [
  ["rule_id", "field_or_condition", "rule", "severity"],
  ["QC001", "denominator", "Required when number_patients or percentage is reported.", "error"],
  ["QC002", "percentage_calculated", "number_patients / denominator * 100.", "check"],
  ["QC003", "percent_delta", "Flag if reported and calculated percentage differ by more than 0.2 percentage points.", "warning"],
  ["QC004", "source comparability", "Only A-grade rows enter primary analysis.", "error"],
  ["QC005", "AEMS/FAERS", "Do not report incidence or causal risk.", "error"],
]);

writeRows("Extraction_Progress", "A1", [[
  "drug_id", "drug_name", "trial_id", "fda_review_status", "ctgov_status", "publication_status",
  "supplement_status", "label_status", "aems_status", "blocker", "next_action"
]]);

writeRows("Curated_Facts_Need_Review", "A1", [[
  "fact_id", "drug_id", "topic", "draft_value", "source_url_or_file", "verification_status", "reviewer", "notes"
]]);

writeRows("FDA_Table_Locator", "A1", [[
  "locator_id", "document_id", "drug_id", "trial_id", "page", "section", "table_number",
  "table_title", "safety_topic", "priority", "extraction_status", "notes"
]]);

const outputDir = "adc_safety_lifecycle/templates";
await fs.mkdir(outputDir, { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(`${outputDir}/ae_numeric_extraction_workbook.xlsx`);

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 50 },
  summary: "formula error scan",
});
console.log(errors.ndjson);
console.log(`${outputDir}/ae_numeric_extraction_workbook.xlsx`);
