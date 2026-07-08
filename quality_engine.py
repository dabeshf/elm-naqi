"""
quality_engine.py
-----------------
Naqi's data-quality engine. Each function measures one NDMO Data Quality
dimension and returns a structured result:

    {
      "dimension": str,      # NDMO dimension name
      "score": float,        # 0-100 (100 = perfect)
      "issues": int,         # count of problem cells/rows
      "total": int,          # denominator used for the score
      "detail": dict,        # per-column or per-check breakdown
      "message": str,        # human-readable summary
    }

It works on any uploaded CSV/Excel file.
"""

import re
import pandas as pd
from datetime import datetime

# ---- Column detection helpers ------------------------------------------------

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SAUDI_PHONE_RE = re.compile(r"^05\d{8}$")
SAUDI_ID_RE = re.compile(r"^[12]\d{9}$")
IBAN_SA_RE = re.compile(r"^SA\d{22}$")

PII_HINTS = ["name", "email", "phone", "mobile", "national", "iqama", "id",
             "iban", "address", "dob", "birth", "passport", "health"]
SENSITIVE_HINTS = ["health", "medical", "religion", "ethnic", "biometric",
                   "genetic", "criminal", "disability", "diagnosis"]
DATE_HINTS = ["date", "time", "created", "updated", "activity", "registration",
              "last_", "modified"]


def detect_pii_columns(df):
    return [c for c in df.columns if any(h in c.lower() for h in PII_HINTS)]


def detect_sensitive_columns(df):
    return [c for c in df.columns if any(h in c.lower() for h in SENSITIVE_HINTS)]


def detect_date_columns(df):
    found = []
    for c in df.columns:
        if any(h in c.lower() for h in DATE_HINTS):
            found.append(c)
    return found


def _try_parse_date(val):
    if pd.isna(val) or str(val).strip() == "":
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(val).strip(), fmt)
        except ValueError:
            continue
    return None


# ---- The six NDMO dimensions -------------------------------------------------

# NDMO: Completeness
def check_completeness(df):
    total = df.size
    missing = int(df.isna().sum().sum() +
                  (df.astype(str).apply(lambda s: s.str.strip() == "")).sum().sum())
    score = 100 * (1 - missing / total) if total else 100
    per_col = {}
    for c in df.columns:
        col = df[c].astype(str).str.strip()
        m = int((df[c].isna() | (col == "")).sum())
        per_col[c] = round(100 * (1 - m / len(df)), 1) if len(df) else 100.0
    return {
        "dimension": "Completeness",
        "score": round(score, 1),
        "issues": missing,
        "total": total,
        "detail": per_col,
        "message": f"{missing} missing values across {total} cells.",
    }

# NDMO: Uniqueness
def check_uniqueness(df):
    dupes = int(df.duplicated().sum())
    total = len(df)
    score = 100 * (1 - dupes / total) if total else 100
    return {
        "dimension": "Uniqueness",
        "score": round(score, 1),
        "issues": dupes,
        "total": total,
        "detail": {"duplicate_rows": dupes},
        "message": f"{dupes} exact duplicate rows found.",
    }

# NDMO: Validity 
def check_validity(df):
    checks = {}
    total_checked = 0
    total_invalid = 0
    for c in df.columns:
        lc = c.lower()
        rule = None
        if "email" in lc:
            rule = EMAIL_RE
        elif "phone" in lc or "mobile" in lc:
            rule = SAUDI_PHONE_RE
        elif "national" in lc or "iqama" in lc or lc == "id":
            rule = SAUDI_ID_RE
        elif "iban" in lc:
            rule = IBAN_SA_RE
        if rule is None:
            continue
        vals = df[c].astype(str).str.strip()
        non_empty = vals[vals != ""]
        invalid = int((~non_empty.apply(lambda x: bool(rule.match(str(x).strip())))).sum())
        checks[c] = {
            "checked": len(non_empty),
            "invalid": invalid,
            "score": round(100 * (1 - invalid / len(non_empty)), 1) if len(non_empty) else 100.0,
        }
        total_checked += len(non_empty)
        total_invalid += invalid
    score = 100 * (1 - total_invalid / total_checked) if total_checked else 100
    return {
        "dimension": "Validity",
        "score": round(score, 1),
        "issues": total_invalid,
        "total": total_checked,
        "detail": checks,
        "message": f"{total_invalid} values fail format rules "
                   f"(email / Saudi phone / National ID / IBAN).",
    }

# NDMO: Consistency
def check_consistency(df):
    issues = 0
    detail = {}
    for c in df.columns:
        vals = df[c].astype(str)
        # whitespace / casing inconsistency: collapse and compare distinct forms
        norm = vals.str.strip().str.lower()
        raw = vals.str.strip()
        variant_count = 0
        for key, group in raw.groupby(norm):
            if group.nunique() > 1:
                variant_count += group.nunique() - 1
        if variant_count:
            detail[c] = f"{variant_count} inconsistent variants (casing/whitespace)"
            issues += variant_count
    # mixed date formats
    for c in detect_date_columns(df):
        formats = set()
        for v in df[c].dropna().astype(str).head(200):
            v = v.strip()
            if re.match(r"^\d{4}-\d{2}-\d{2}$", v):
                formats.add("YYYY-MM-DD")
            elif re.match(r"^\d{2}/\d{2}/\d{4}$", v):
                formats.add("DD/MM/YYYY")
            elif re.match(r"^\d{4}/\d{2}/\d{2}$", v):
                formats.add("YYYY/MM/DD")
        if len(formats) > 1:
            detail[c] = f"mixed date formats: {', '.join(sorted(formats))}"
            issues += 1
    total = len(df.columns)
    score = max(0, 100 - (issues / total * 20)) if total else 100
    return {
        "dimension": "Consistency",
        "score": round(score, 1),
        "issues": issues,
        "total": total,
        "detail": detail,
        "message": f"{issues} consistency problems (mixed casing, whitespace, or date formats).",
    }

# NDMO: Timeliness
def check_timeliness(df, staleness_days=365):
    date_cols = detect_date_columns(df)
    # prefer an 'activity' / 'updated' style column for freshness
    freshness_col = None
    for c in date_cols:
        if any(k in c.lower() for k in ["activity", "updated", "modified", "last"]):
            freshness_col = c
            break
    if freshness_col is None and date_cols:
        freshness_col = date_cols[-1]
    if freshness_col is None:
        return {
            "dimension": "Timeliness",
            "score": None,
            "issues": 0,
            "total": 0,
            "detail": {"note": "No date column detected: timeliness not assessed."},
            "message": "No date column found to assess record freshness.",
        }
    now = datetime.now()
    stale = 0
    checked = 0
    for v in df[freshness_col]:
        d = _try_parse_date(v)
        if d is None:
            continue
        checked += 1
        if (now - d).days > staleness_days:
            stale += 1
    score = 100 * (1 - stale / checked) if checked else 100
    return {
        "dimension": "Timeliness",
        "score": round(score, 1),
        "issues": stale,
        "total": checked,
        "detail": {"column": freshness_col, "threshold_days": staleness_days,
                   "stale_records": stale},
        "message": f"{stale} of {checked} records older than {staleness_days} days "
                   f"(based on '{freshness_col}').",
    }

# NDMO: Integrity
def check_integrity(df):
    id_cols = [c for c in df.columns
               if any(k in c.lower() for k in ["_id", "id_", "email", "national", "iban"])
               or c.lower() == "id"]
    detail = {}
    issues = 0
    for c in id_cols:
        vals = df[c].astype(str).str.strip()
        non_empty = vals[vals != ""]
        dup = int(non_empty.duplicated().sum())
        if dup:
            detail[c] = f"{dup} duplicate values in identifier column"
            issues += dup
    total = sum(len(df[c].astype(str)[df[c].astype(str).str.strip() != ""]) for c in id_cols) or 1
    score = 100 * (1 - issues / total)
    return {
        "dimension": "Integrity",
        "score": round(score, 1),
        "issues": issues,
        "total": total,
        "detail": detail if detail else {"note": "No key-uniqueness violations found."},
        "message": f"{issues} duplicate values in columns that should be unique keys.",
    }


# ---- Orchestrator ------------------------------------------------------------

DIMENSION_WEIGHTS = {
    "Completeness": 0.20,
    "Validity": 0.20,
    "Uniqueness": 0.15,
    "Timeliness": 0.20,
    "Consistency": 0.15,
    "Integrity": 0.10,
}


def run_all_checks(df, staleness_days=365):
    results = [
        check_completeness(df),
        check_validity(df),
        check_uniqueness(df),
        check_timeliness(df, staleness_days),
        check_consistency(df),
        check_integrity(df),
    ]
    # weighted overall score, skipping dimensions that couldn't be assessed (score None)
    num, den = 0.0, 0.0
    for r in results:
        if r["score"] is None:
            continue
        w = DIMENSION_WEIGHTS.get(r["dimension"], 0)
        num += r["score"] * w
        den += w
    overall = round(num / den, 1) if den else 0.0
    return overall, results


def grade(score):
    if score is None:
        return "N/A", "gray"
    if score >= 90:
        return "Excellent", "green"
    if score >= 75:
        return "Good", "green"
    if score >= 60:
        return "Fair", "amber"
    return "Poor", "red"
