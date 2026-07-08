"""
Run:  streamlit run app.py after installing requirements
"""

import io
import pandas as pd
import streamlit as st

from quality_engine import (run_all_checks, grade, detect_pii_columns,
                            detect_sensitive_columns)
from pdpl_mapping import build_compliance_view, sensitive_data_note

st.set_page_config(page_title="Naqi: Data Quality & PDPL Health",
                   page_icon="💧", layout="wide")

COLOR_HEX = {"green": "#1e8e3e", "amber": "#f9a825", "red": "#d93025", "gray": "#9aa0a6"}


def color_badge(text, color):
    return (f"<span style='background:{COLOR_HEX[color]};color:white;"
            f"padding:3px 10px;border-radius:12px;font-size:0.85rem;'>{text}</span>")


# ---- Header ------------------------------------------------------------------
st.title("Naqi: Data Quality & PDPL Compliance Health Dashboard")
st.caption("Aligned to NDMO Data Quality dimensions and the Saudi PDPL")

with st.sidebar:
    st.header("1 · Upload data")
    uploaded = st.file_uploader("CSV or Excel file", type=["csv", "xlsx", "xls"])
    use_sample = st.checkbox("Use built-in sample dataset", value=not uploaded)
    st.header("2 · Settings")
    staleness = st.slider("Staleness threshold (days)", 90, 1825, 365, step=30,
                          help="Records with a last-activity date older than this "
                               "are flagged under Timeliness / Storage Limitation.")
    st.markdown("---")
    st.caption("Naqi is advisory and does not constitute legal advice. The PDPL and "
               "its Implementing Regulations remain the binding reference.")

# ---- Load --------------------------------------------------------------------
df = None
if uploaded is not None:
    try:
        if uploaded.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded, dtype=str, keep_default_na=False)
        else:
            df = pd.read_excel(uploaded, dtype=str)
            df = df.fillna("")
    except Exception as e:
        st.error(f"Could not read file: {e}")
elif use_sample:
    try:
        df = pd.read_csv("sample_data.csv", dtype=str, keep_default_na=False)
    except FileNotFoundError:
        st.warning("Sample file not found. Run `python generate_sample_data.py` first.")

if df is None:
    st.info("⬅️ Upload a CSV/Excel file or tick 'Use built-in sample dataset' to begin.")
    st.stop()

# ---- Run checks --------------------------------------------------------------
overall, results = run_all_checks(df, staleness_days=staleness)
g_label, g_color = grade(overall)
pii_cols = detect_pii_columns(df)
sensitive_cols = detect_sensitive_columns(df)
compliance = build_compliance_view(results)

# ---- Top summary -------------------------------------------------------------
c1, c2, c3, c4 = st.columns([1.3, 1, 1, 1])
with c1:
    st.metric("Overall Data Health", f"{overall}/100")
    st.markdown(color_badge(g_label, g_color), unsafe_allow_html=True)
with c2:
    st.metric("Rows", f"{len(df):,}")
with c3:
    st.metric("Columns", f"{df.shape[1]}")
with c4:
    st.metric("PII columns detected", f"{len(pii_cols)}")

st.progress(min(int(overall), 100) / 100)

tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Quality Dimensions", "⚖️ PDPL Compliance", "🔎 Data Preview", "📄 Report"])

# ---- Tab 1: Quality dimensions ----------------------------------------------
with tab1:
    st.subheader("NDMO Data Quality Dimensions")
    cols = st.columns(3)
    for i, r in enumerate(results):
        _, c = grade(r["score"])
        with cols[i % 3]:
            st.markdown(f"**{r['dimension']}**")
            st.markdown(
                f"<div style='font-size:1.8rem;font-weight:700;color:{COLOR_HEX[c]}'>"
                f"{'N/A' if r['score'] is None else r['score']}</div>",
                unsafe_allow_html=True)
            st.caption(r["message"])
            st.markdown("---")

    st.subheader("Per-column completeness")
    comp = next(r for r in results if r["dimension"] == "Completeness")
    comp_df = pd.DataFrame(
        [{"column": k, "completeness_%": v} for k, v in comp["detail"].items()]
    ).sort_values("completeness_%")
    st.dataframe(comp_df, use_container_width=True, hide_index=True)

    val = next(r for r in results if r["dimension"] == "Validity")
    if val["detail"]:
        st.subheader("Format validity by column")
        val_df = pd.DataFrame([
            {"column": k, "checked": v["checked"], "invalid": v["invalid"],
             "valid_%": v["score"]}
            for k, v in val["detail"].items()])
        st.dataframe(val_df, use_container_width=True, hide_index=True)

# ---- Tab 2: PDPL compliance --------------------------------------------------
with tab2:
    st.subheader("PDPL Principle Risk")
    st.caption("Each principle's status is driven by the weakest quality dimension "
               "that supports it.")
    for item in compliance:
        with st.container(border=True):
            top = st.columns([2, 1])
            with top[0]:
                st.markdown(f"### {item['principle']}")
            with top[1]:
                st.markdown(color_badge(item["status"], item["color"]),
                            unsafe_allow_html=True)
            st.write(item["why"])
            chips = "  ·  ".join(
                f"{c['dimension']}: {'N/A' if c['score'] is None else str(c['score'])+'%'}"
                f" ({c['issues']} issues)"
                for c in item["contributing"])
            st.caption("Contributing dimensions → " + chips)

    note = sensitive_data_note(sensitive_cols)
    if note:
        st.warning("**Sensitive data: Data Minimization check**\n\n" + note)

# ---- Tab 3: Data preview -----------------------------------------------------
with tab3:
    st.subheader("Data preview (first 100 rows)")
    st.dataframe(df.head(100), use_container_width=True)
    dupe_mask = df.duplicated(keep=False)
    if dupe_mask.any():
        st.subheader(f"Duplicate rows ({int(dupe_mask.sum())})")
        st.dataframe(df[dupe_mask].head(50), use_container_width=True)

# ---- Tab 4: Report -----------------------------------------------------------
with tab4:
    st.subheader("Exportable summary report")
    report_lines = [
        "NAQI: DATA QUALITY & PDPL COMPLIANCE REPORT",
        "=" * 48,
        f"Rows: {len(df)}   Columns: {df.shape[1]}",
        f"Overall Data Health Score: {overall}/100 ({g_label})",
        f"Staleness threshold: {staleness} days",
        "",
        "NDMO DATA QUALITY DIMENSIONS",
        "-" * 48,
    ]
    for r in results:
        report_lines.append(
            f"{r['dimension']:<14} {('N/A' if r['score'] is None else str(r['score'])+'/100'):>10}"
            f"   {r['message']}")
    report_lines += ["", "PDPL PRINCIPLE RISK", "-" * 48]
    for item in compliance:
        report_lines.append(f"{item['principle']:<28} {item['status']}")
    if note:
        report_lines += ["", "SENSITIVE DATA NOTE", "-" * 48, note]
    report_text = "\n".join(report_lines)

    st.code(report_text)
    st.download_button("⬇️ Download report (.txt)", report_text,
                       file_name="naqi_report.txt")

    # CSV of dimension scores
    dim_csv = pd.DataFrame([
        {"dimension": r["dimension"], "score": r["score"], "issues": r["issues"],
         "summary": r["message"]} for r in results])
    st.download_button("⬇️ Download dimension scores (.csv)",
                       dim_csv.to_csv(index=False), file_name="naqi_scores.csv")
