const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType,
  TableOfContents, PageBreak, PositionalTab, PositionalTabAlignment,
  PositionalTabLeader,
} = require("docx");

const NAVY = "1F3A5F";
const TEAL = "1E8E7E";
const GREY = "5A5A5A";
const LIGHT = "EEF3F7";

const H = (text, level) => new Paragraph({
  heading: level,
  spacing: { before: 240, after: 120 },
  children: [new TextRun({ text, color: level === HeadingLevel.HEADING_1 ? NAVY : TEAL, bold: true })],
});

const P = (text, opts = {}) => new Paragraph({
  spacing: { after: 120, line: 276 },
  alignment: opts.align || AlignmentType.JUSTIFIED,
  children: [new TextRun({ text, size: 22, color: opts.color || "222222", bold: !!opts.bold, italics: !!opts.italics })],
});

const bullet = (text) => new Paragraph({
  bullet: { level: 0 },
  spacing: { after: 60 },
  children: [new TextRun({ text, size: 22 })],
});

function cell(text, { header = false, w, bg } = {}) {
  return new TableCell({
    width: { size: w, type: WidthType.DXA },
    shading: bg ? { type: ShadingType.CLEAR, fill: bg, color: "auto" } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({
      children: [new TextRun({ text, bold: header, size: 20, color: header ? "FFFFFF" : "222222" })],
    })],
  });
}

function table(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map((h, i) => cell(h, { header: true, w: widths[i], bg: NAVY })),
  });
  const bodyRows = rows.map((r, ri) => new TableRow({
    children: r.map((c, i) => cell(c, { w: widths[i], bg: ri % 2 ? LIGHT : "FFFFFF" })),
  }));
  return new Table({
    columnWidths: widths,
    width: { size: total, type: WidthType.DXA },
    rows: [headerRow, ...bodyRows],
  });
}

const rule = () => new Paragraph({
  spacing: { after: 120 },
  border: { bottom: { color: TEAL, space: 1, style: BorderStyle.SINGLE, size: 12 } },
  children: [],
});

// ---- Title page --------------------------------------------------------------
const titlePage = [
  new Paragraph({ spacing: { before: 2200 }, children: [] }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Naqi", bold: true, size: 72, color: NAVY })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 200 },
    children: [new TextRun({ text: "Data Quality & PDPL Compliance Health Dashboard", size: 30, color: TEAL, bold: true })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Documentation Report", size: 26, color: GREY })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 120 },
    children: [new TextRun({ text: "Data Governance Challenge — Data Quality", size: 22, italics: true, color: GREY })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 1600 },
    children: [new TextRun({ text: "Aligned to NDMO Data Quality dimensions & the Saudi PDPL", size: 20, color: GREY })],
  }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---- TOC ---------------------------------------------------------------------
const toc = [
  H("Table of Contents", HeadingLevel.HEADING_1),
  new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---- Body --------------------------------------------------------------------
const body = [
  H("1. Overview", HeadingLevel.HEADING_1),
  P("Naqi (Arabic: نقي, “pure”) is a data-quality and compliance health dashboard. It acts as a quality gate that inspects a dataset before that data is used to make decisions or to train AI models. Naqi scores any uploaded dataset across the six NDMO Data Quality dimensions and maps each weakness to the specific Saudi Personal Data Protection Law (PDPL) principle it puts at risk."),
  P("The tool is deliberately simple to operate: a user uploads a CSV or Excel file, and within seconds receives an overall Data Health Score, a per-dimension breakdown, a PDPL compliance-risk panel, and an exportable report.", {}),

  H("2. Problem Statement", HeadingLevel.HEADING_1),
  P("The Data Quality challenge identifies a concrete failure mode: the presence of duplicate or outdated data that leads to wrong outcomes in AI systems (وجود بيانات مكررة أو قديمة تؤدي لنتائج خاطئة في أنظمة الذكاء الاصطناعي)."),
  P("Crucially, poor data quality is not only an analytics issue: it is a regulatory one. The PDPL embeds an Accuracy principle (personal data must be kept correct and up to date) and a Storage Limitation principle (data must not be retained longer than necessary). Duplicate, stale, or malformed personal data therefore represents a direct compliance exposure, not merely a technical inconvenience. Naqi is built around this insight."),

  H("3. Solution Approach", HeadingLevel.HEADING_1),
  P("Naqi treats data quality as the enforcement layer for PDPL accuracy and retention obligations. It is organised in four layers:", { bold: true }),
  bullet("Input layer: accepts CSV/Excel uploads and auto-detects likely PII, sensitive-data, and date columns by name and content."),
  bullet("Quality engine: runs six independent checks, one per NDMO Data Quality dimension, each returning a 0–100 sub-score and an issue count."),
  bullet("Scoring layer: combines the sub-scores into a weighted overall Data Health Score with a red/amber/green grade."),
  bullet("Compliance layer: maps failing dimensions to PDPL principles and raises a Data Minimization advisory when sensitive-data columns are detected."),

  H("4. The Six NDMO Data Quality Dimensions", HeadingLevel.HEADING_1),
  P("Naqi's checks are framed directly as the NDMO Data Quality dimensions so that results are expressed in the vocabulary national data governance already uses:"),
  table(
    ["Dimension", "What Naqi measures", "Example issue caught"],
    [
      ["Completeness", "Missing or empty values per column", "Blank national ID or email"],
      ["Validity", "Conformity to format rules", "Invalid Saudi phone or IBAN"],
      ["Uniqueness", "Exact duplicate rows", "Same record inserted twice"],
      ["Timeliness", "Records fresh vs. a staleness threshold", "Account inactive since 2015"],
      ["Consistency", "Uniform casing, whitespace, date formats", "RIYADH vs riyadh vs Riyadh"],
      ["Integrity", "Duplicated values in key identifiers", "Two customers, one ID"],
    ],
    [1800, 4200, 3000]
  ),

  H("5. Mapping Quality to PDPL Principles", HeadingLevel.HEADING_1),
  P("Each PDPL principle inherits the status of the weakest quality dimension that supports it. This turns an abstract score into a concrete compliance signal."),
  table(
    ["PDPL Principle", "Driven by dimensions", "Why it matters"],
    [
      ["Accuracy", "Validity, Consistency, Completeness, Timeliness", "Data must be correct and up to date"],
      ["Storage Limitation", "Timeliness", "Stale data may need review or destruction"],
      ["Integrity & Confidentiality", "Uniqueness, Integrity", "Duplicates corrupt record reliability"],
      ["Accountability", "Completeness, Uniqueness, Integrity", "RoPA records must be accurate & complete"],
    ],
    [2600, 3400, 3000]
  ),
  P("In addition, when Naqi detects a column likely to hold PDPL sensitive data (e.g. health, biometric, religious, or criminal data), it raises a Data Minimization advisory, reminding the user that such data carries stricter obligations and cannot rely on legitimate interest as a legal basis."),

  H("6. How the Score Is Calculated", HeadingLevel.HEADING_1),
  P("Each dimension produces a 0–100 sub-score (100 = no issues). The overall Data Health Score is a weighted average:"),
  bullet("Completeness, Validity, Timeliness: 20% each"),
  bullet("Uniqueness, Consistency: 15% each"),
  bullet("Integrity: 10%"),
  P("Dimensions that cannot be assessed for a given dataset (for example, Timeliness when no date column exists) are skipped, and the remaining weights are re-normalised so the score stays fair."),

  H("7. Architecture & Tech Stack", HeadingLevel.HEADING_1),
  table(
    ["Component", "File", "Responsibility"],
    [
      ["Dashboard (UI)", "app.py", "Streamlit interface, tabs, upload, export"],
      ["Quality engine", "quality_engine.py", "Six dimension checks + weighted scoring"],
      ["Compliance map", "pdpl_mapping.py", "NDMO → PDPL principle mapping"],
      ["Sample data", "generate_sample_data.py", "Synthetic messy dataset for the demo"],
    ],
    [2400, 3000, 3600]
  ),
  P("The stack is intentionally lightweight: Python, Streamlit, and pandas. So the tools install in one step and runs locally with a single command. This keeps the barrier to adoption low for a governance team that simply wants to check a file."),

  H("8. Running Naqi", HeadingLevel.HEADING_1),
  P("pip install -r requirements.txt", { color: NAVY, bold: true }),
  P("python generate_sample_data.py", { color: NAVY, bold: true }),
  P("streamlit run app.py", { color: NAVY, bold: true }),
  P("The user then opens the local URL, ticks “Use built-in sample dataset” to see every check fire, or uploads their own CSV/Excel file. Results appear across four tabs: Quality Dimensions, PDPL Compliance, Data Preview, and Report."),

  H("9. Evaluation Fit", HeadingLevel.HEADING_1),
  P("The solution addresses the challenge's stated judging criteria:"),
  bullet("Relevance to the challenge: targets duplicate and stale data as a quality gate before AI use."),
  bullet("Feasibility & implementation: a working Streamlit app that runs on any CSV/Excel today."),
  bullet("Idea & innovation: reframes data quality as PDPL enforcement, using the NDMO dimensions as the backbone."),
  bullet("Quality of implementation & documentation: modular code, a synthetic demo dataset, and this report."),

  H("10. Limitations & Future Work", HeadingLevel.HEADING_1),
  bullet("Uniqueness currently detects exact duplicates; fuzzy/entity-resolution matching (catching spelling variants across Arabic and English) is a natural extension."),
  bullet("Validity rules are tuned for Saudi formats; a configurable rules editor would generalise the tool."),
  bullet("A live database connector would let Naqi monitor quality continuously rather than per upload."),
  bullet("Naqi is advisory. It highlights risk; the PDPL and its Implementing Regulations remain the binding reference."),

  rule(),
  P("All sample data used by Naqi is synthetic and randomly generated. No real personal data is processed. This report is provided for the Data Governance Challenge and does not constitute legal advice.", { italics: true, color: GREY }),
];

const doc = new Document({
  creator: "Naqi",
  title: "Naqi: Documentation Report",
  styles: {
    default: { document: { run: { font: "Calibri" } } },
  },
  sections: [{
    properties: { page: { margin: { top: 1200, bottom: 1200, left: 1200, right: 1200 } } },
    children: [...titlePage, ...toc, ...body],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("Naqi_Documentation_Report.docx", buf);
  console.log("Wrote Naqi_Documentation_Report.docx");
});
