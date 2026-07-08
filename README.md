# Naqi: Data Quality & PDPL Compliance Health Dashboard

> A quality gate that inspects a dataset **before** it feeds decisions or AI
> training - scoring it across the six **NDMO Data Quality dimensions** and
> mapping every failure to the **Saudi PDPL** principle it breaches.

Built for the **Data Governance Challenge - (Data Quality)**.

---

## The problem

> Duplicate and outdated data produce wrong results in AI systems.

Under the PDPL bad data a **compliance problem**. The law's *Accuracy* principle requires personal data to be kept
correct and up to date, and *Storage Limitation* requires that data not be kept
longer than needed. Naqi treats data quality as the enforcement layer for both.

## What Naqi does

1. **Upload** a CSV or Excel file.
2. Naqi scores it across the six **NDMO Data Quality dimensions**:

   | Dimension | What it checks |
   |-----------|----------------|
   | Completeness | Missing / empty values per column |
   | Validity  | Format rules: E-mail, Phone, National ID/Iqama, IBAN |
   | Uniqueness | Exact duplicate rows |
   | Timeliness | Stale records vs. a configurable freshness threshold |
   | Consistency | Mixed casing, whitespace, and date formats |
   | Integrity | Duplicated values in key identifier columns |

3. It produces an **Overall Data Health Score (0–100)** with a red/amber/green grade.
4. It maps failures to **PDPL principles** (Accuracy, Storage Limitation,
   Integrity & Confidentiality, Accountability) and flags **sensitive data**
   columns for a Data Minimization review.
5. It **exports** a summary report (`.txt`) and dimension scores (`.csv`).

## Quick start

```bash
pip install -r requirements.txt
python generate_sample_data.py    
streamlit run app.py
```

Then open the local URL Streamlit prints. Tick **"Use built-in sample dataset"**
to see every check fire, or upload your own file.

## Project structure

```
naqi/
├── app.py                   # Streamlit dashboard (UI)
├── quality_engine.py        # The six NDMO dimension checks + scoring
├── pdpl_mapping.py          # NDMO → PDPL principle mapping
├── generate_sample_data.py  # Builds a synthetic messy demo dataset
├── sample_data.csv          # Generated demo data (fake, no real PII)
├── requirements.txt
├── README.md
└── docs/
    └── Naqi_Documentation_Report.docx
```

## How the score works

Each dimension returns a 0–100 sub-score. The overall score is a weighted
average (Completeness/Validity/Timeliness 20% each, Uniqueness/Consistency 15%,
Integrity 10%). Dimensions that can't be assessed (e.g. no date column for
Timeliness) are skipped and the weights re-normalised.

## Compliance framing

Naqi's dimensions come straight from the **NDMO Data Quality** standard, and the
compliance panel references SDAIA's *Guide to the Saudi Personal Data Protection
Law*. Naqi is **advisory**, it highlights risk; the PDPL and its Implementing
Regulations remain the binding reference.

## Notes & limitations

- All sample data is **synthetic** and randomly generated using generate_sample_data.py - no real personal data.
- Validity rules are tuned for Saudi formats (National ID/Iqama, `05xxxxxxxx`
  phones, `SA` IBANs); extend `quality_engine.py` for other schemas.
