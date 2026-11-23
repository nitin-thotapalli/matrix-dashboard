import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Matrix | Financial Intelligence", page_icon="📊", layout="wide")

DATA_DIR = Path(__file__).parent / "dashboards"

@st.cache_data
def load_dashboards():
    items = {}
    for path in sorted(DATA_DIR.glob("*.json")):
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(report, dict) and report.get("company"):
                items[path.stem] = report
        except (ValueError, OSError):
            continue
    return items


def money(value):
    if value is None:
        return "—"
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def show_dcf(report):
    dcf = report.get("dcf") or {}
    if not dcf:
        return
    st.subheader("DCF valuation laboratory")
    st.caption("Illustrative model assumptions, not a verified price target. Adjust inputs and independently verify source figures.")
    c1, c2, c3 = st.columns(3)
    revenue = c1.number_input("Starting annual revenue (₹ crore)", min_value=0.0, value=float(dcf.get("starting_revenue_cr", 0)), step=100.0)
    margin = c2.slider("EBITDA margin (%)", 0.0, 35.0, float(dcf.get("ebitda_margin_pct", 18.0)), 0.5)
    growth = c3.slider("Initial revenue growth (%)", -10.0, 50.0, float(dcf.get("initial_growth_pct", 20.0)), 1.0)
    c4, c5, c6 = st.columns(3)
    wacc = c4.slider("WACC (%)", 7.0, 22.0, float(dcf.get("wacc_pct", 12.0)), 0.5)
    terminal = c5.slider("Terminal growth (%)", 0.0, 6.0, float(dcf.get("terminal_growth_pct", 4.0)), 0.25)
    reinvest = c6.slider("Incremental working capital / revenue increase (%)", 0.0, 60.0, float(dcf.get("incremental_nwc_pct", 20.0)), 1.0)
    tax_rate = float(dcf.get("cash_tax_pct", 25)) / 100
    da = float(dcf.get("da_pct_revenue", 2)) / 100
    capex = float(dcf.get("capex_pct_revenue", 3.5)) / 100
    decay = float(dcf.get("annual_growth_decay_pp", 2))
    shares = float(dcf.get("shares_cr", 0))
    net_cash = float(dcf.get("net_cash_cr", 0))
    if terminal >= wacc:
        st.error("WACC must exceed terminal growth.")
        return
    prior, discount_sum, rows = revenue, 0.0, []
    for year in range(1, 6):
        g = (growth - decay * (year - 1)) / 100
        sales = prior * (1 + g)
        depreciation = sales * da
        ebit = sales * margin / 100 - depreciation
        cash_tax = max(ebit, 0) * tax_rate
        capital_spending = sales * capex
        incremental_nwc = (sales - prior) * reinvest / 100
        fcff = ebit - cash_tax + depreciation - capital_spending - incremental_nwc
        discount_sum += fcff / ((1 + wacc / 100) ** year)
        rows.append(dict(Year=f"FY+{year}", Revenue=sales, FCFF=fcff, Growth_pct=g*100))
        prior = sales
    terminal_value = rows[-1]["FCFF"] * (1 + terminal / 100) / ((wacc - terminal) / 100)
    terminal_pv = terminal_value / ((1 + wacc / 100) ** 5)
    ev = discount_sum + terminal_pv
    equity = ev + net_cash
    per_share = equity / shares if shares > 0 else None
    d1, d2, d3 = st.columns(3)
    d1.metric("DCF value / share", money(per_share))
    d2.metric("Enterprise value (₹ Cr)", f"{ev:,.0f}")
    d3.metric("Terminal value % of EV", f"{terminal_pv / ev * 100:.1f}%" if ev else "—")
    forecast = pd.DataFrame(rows)
    st.plotly_chart(px.bar(forecast, x="Year", y="FCFF", title="Projected annual free cash flow (₹ Cr)"), use_container_width=True)
    st.dataframe(forecast.style.format({"Revenue": "{:,.1f}", "FCFF": "{:,.1f}", "Growth_pct": "{:.1f}%"}), use_container_width=True, hide_index=True)
    st.caption("Method: five-year unlevered FCFF; EBIT(1−tax) + depreciation − capex − change in working capital. Terminal Gordon growth. Net cash added to EV.")
    st.caption("Sensitivity is illustrative and does not include a full segment model, lease liabilities, other claims, or independently verified WACC.")


st.title("MATRIX / Financial Intelligence")
st.caption("Evidence-first research workbench · Dynamically generated dashboards from structured Matrix research data")
reports = load_dashboards()
if not reports:
    st.warning("No reports found in dashboards/. Add a Matrix research JSON file to generate a company dashboard.")
    st.stop()

selected = st.selectbox("Research dashboard", list(reports), format_func=lambda key: reports[key].get("company", key))
report = reports[selected]
st.header(report["company"])
st.caption(f"Research date: {report.get('as_of', 'unknown')} · Data classification: {report.get('classification','unverified')}")

tabs = st.tabs(["Overview", "Financial history", "DCF model", "Events & intelligence", "Evidence"])
with tabs[0]:
    summary = report.get("summary", "")
    st.write(summary or "No research summary yet.")
    metrics = report.get("metrics", [])
    if metrics:
        cols = st.columns(min(len(metrics), 4))
        for idx, metric in enumerate(metrics):
            cols[idx % len(cols)].metric(metric.get("label", ""), str(metric.get("value", "—")))
    st.subheader("Research findings")
    for finding in report.get("findings", []):
        st.markdown(f"- {finding}")
with tabs[1]:
    history = report.get("financial_history", [])
    if history:
        df = pd.DataFrame(history)
        st.dataframe(df, use_container_width=True, hide_index=True)
        numeric = [c for c in df.select_dtypes(include="number").columns]
        if numeric:
            chart_cols = st.multiselect("Plot financial metrics", numeric, default=numeric[:2])
            if chart_cols:
                st.plotly_chart(px.line(df, x="period", y=chart_cols, markers=True, title="Historical financial trends"), use_container_width=True)
    else:
        st.info("No financial history included in this research package.")
with tabs[2]:
    show_dcf(report)
with tabs[3]:
    for item in report.get("events", []):
        st.markdown(f"**{item.get('date', 'Undated')} — {item.get('title','Event')}**")
        st.write(item.get("detail", ""))
        if item.get("source_url"):
            st.link_button("Source", item["source_url"])
        st.divider()
with tabs[4]:
    st.subheader("Evidence register")
    evidence = report.get("evidence", [])
    if evidence:
        st.dataframe(pd.DataFrame(evidence), use_container_width=True, hide_index=True)
    else:
        st.info("No source records provided.")
    st.caption("Evidence links indicate source documents, not independent audit verification.")
