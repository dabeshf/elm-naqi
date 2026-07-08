"""
pdpl_mapping.py
---------------
Bridges Naqi's NDMO Data Quality dimensions to the PDPL principles they
support, so a quality failure is expressed as a concrete compliance risk.

References (from SDAIA's 'Guide to the Saudi Personal Data Protection Law'):
  - Accuracy:            personal data must be kept accurate and up to date.
  - Storage Limitation:  personal data must not be kept longer than needed.
  - Integrity & Conf.:   adequate controls against loss/corruption of data.
  - Data Minimization:   process only the personal data truly required.
  - Accountability:      maintain records (RoPA) demonstrating compliance.

This module is advisory. It does not constitute legal advice; the PDPL and its
Implementing Regulations remain the binding reference.
"""

# Which NDMO dimensions feed each PDPL principle
PRINCIPLE_MAP = {
    "Accuracy": {
        "dimensions": ["Validity", "Consistency", "Completeness", "Timeliness"],
        "why": "The PDPL requires personal data to be accurate and kept up to date. "
               "Invalid formats, inconsistent values, missing fields and stale records "
               "all undermine accuracy.",
    },
    "Storage Limitation": {
        "dimensions": ["Timeliness"],
        "why": "The PDPL requires that personal data not be retained longer than "
               "necessary. Stale records flagged by the Timeliness dimension may "
               "indicate data that should be reviewed, refreshed, or destroyed.",
    },
    "Integrity & Confidentiality": {
        "dimensions": ["Uniqueness", "Integrity"],
        "why": "Duplicate rows and duplicated key identifiers compromise the "
               "integrity of records and can lead to conflicting or unreliable "
               "personal data.",
    },
    "Accountability": {
        "dimensions": ["Completeness", "Uniqueness", "Integrity"],
        "why": "Maintaining an accurate, complete Record of Processing Activities "
               "(RoPA) is an explicit PDPL obligation. Incomplete or duplicated "
               "records weaken demonstrable accountability.",
    },
}

# Thresholds for a principle's status, driven by the worst contributing dimension
def _status(score):
    if score is None:
        return "Not assessed", "gray"
    if score >= 90:
        return "Compliant", "green"
    if score >= 70:
        return "Needs attention", "amber"
    return "At risk", "red"


def build_compliance_view(results):
    """
    results: list of dimension result dicts from quality_engine.run_all_checks
    returns: list of principle dicts for the compliance panel
    """
    by_dim = {r["dimension"]: r for r in results}
    view = []
    for principle, cfg in PRINCIPLE_MAP.items():
        scores = [by_dim[d]["score"] for d in cfg["dimensions"]
                  if d in by_dim and by_dim[d]["score"] is not None]
        worst = min(scores) if scores else None
        label, color = _status(worst)
        contributing = []
        for d in cfg["dimensions"]:
            if d in by_dim:
                contributing.append({
                    "dimension": d,
                    "score": by_dim[d]["score"],
                    "issues": by_dim[d]["issues"],
                })
        view.append({
            "principle": principle,
            "status": label,
            "color": color,
            "score": worst,
            "why": cfg["why"],
            "contributing": contributing,
        })
    return view


def sensitive_data_note(sensitive_cols):
    """Data Minimization / sensitivity advisory for detected sensitive columns."""
    if not sensitive_cols:
        return None
    return (
        f"Detected {len(sensitive_cols)} column(s) that may contain PDPL 'sensitive data' "
        f"({', '.join(sensitive_cols)}). Under the PDPL, sensitive data (e.g. health, "
        f"biometric, religious, criminal) carries stricter obligations and cannot rely on "
        f"'legitimate interest' as a legal basis. Confirm this processing is necessary "
        f"(Data Minimization) and adequately safeguarded."
    )
