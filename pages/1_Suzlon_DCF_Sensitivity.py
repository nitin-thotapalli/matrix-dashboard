"""Generated custom investigation view: Suzlon DCF sensitivity laboratory.

This page is intentionally distinct from the reusable company template in app.py.
It demonstrates code-generated dashboard layouts deployed through GitHub.
"""
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Suzlon | DCF Sensitivity", page_icon="🔬", layout="wide")
DATA = json.loads((Path(__file__).resolve().parents[1] / "dashboards" / "suzlon-energy.json").read_text(encoding="utf-8"))
DEFAULTS = DATA["dcf"]


def dcf_value(wacc_pct, terminal_growth_pct, margin_pct, initial_growth_pct, nwc_pct):
    revenue = float(DEFAULTS["starting_revenue_cr"])
    wacc = wacc_pct / 100
    terminal = terminal_growth_pct / 100
    if wacc <= terminal:
        return None, None
    tax = float(DEFAULTS["cash_tax_pct"]) / 100
    depreciation_pct = float(DEFAULTS["da_pct_revenue"]) / 100
    capex_pct = float(DEFAULTS["capex_pct_revenue"]) / 100
    growth_decay = float(DEFAULTS["annual_growth_decay_pp"])
    pv_cashflows = 0.0
    projections = []
    previous = revenue
    for year in range(1, 6):
        growth = (initial_growth_pct - growth_decay * (year - 1)) / 100
        revenue = previous * (1 + growth)
        depreciation = revenue * depreciation_pct
        ebit = revenue * margin_pct / 100 - depreciation
        cash_tax = max(ebit, 0) * tax
        capex = revenue * capex_pct
        change_nwc = (revenue - previous) * nwc_pct / 100
        fcff = ebit - cash_tax + depreciation - capex - change_nwc
        pv_cashflows += fcff / (1 + wacc) ** year
        projections.append({"Year": f"FY+{year}", "Revenue": revenue, "EBIT": ebit, "Cash tax": cash_tax,
                            "Capex": capex, "Δ NWC": change_nwc, "FCFF": fcff})
        previous = revenue
    terminal_value = projections[-1]["FCFF"] * (1 + terminal) / (wacc - terminal)
    pv_terminal = terminal_value / (1 + wacc) ** 5
    ev = pv_cashflows + pv_terminal
    equity = ev + float(DEFAULTS["net_cash_cr"])
    shares = float(DEFAULTS["shares_cr"])
    return equity / shares, {"Enterprise value": ev, "Equity value": equity,
                              "PV terminal value": pv_terminal, "PV explicit FCFF": pv_cashflows,
                              "Projections": projections}


st.title("MATRIX / Suzlon DCF Sensitivity")
st.caption("Custom generated research dashboard · ₹ per share · Five-year FCFF model")
st.write("Explore how Suzlon's intrinsic valuation responds to financing costs, long-run growth, margins and working-capital intensity. All forward estimates are scenario assumptions.")
with st.sidebar:
    st.header("Model controls")
    margin = st.slider("EBITDA margin (%)", 8.0, 28.0, float(DEFAULTS["ebitda_margin_pct"]), 0.5)
    growth = st.slider("Initial revenue growth (%)", 0.0, 40.0, float(DEFAULTS["initial_growth_pct"]), 1.0)
    nwc = st.slider("Incremental working capital (%)", 0.0, 50.0, float(DEFAULTS["incremental_nwc_pct"]), 1.0)
    wacc = st.slider("WACC (%)", 8.0, 20.0, float(DEFAULTS["wacc_pct"]), 0.5)
    terminal = st.slider("Terminal growth (%)", 1.0, 6.0, float(DEFAULTS["terminal_growth_pct"]), 0.25)
    reference_price = st.number_input("Reference share price (₹)", min_value=0.01, value=35.86, step=0.5)
    st.caption("Reference price is an editable historical example, not a live stock quote.")

value, details = dcf_value(wacc, terminal, margin, growth, nwc)
a, b, c, d = st.columns(4)
a.metric("Intrinsic value", f"₹{value:,.2f}" if value is not None else "—")
b.metric("Reference market price", f"₹{reference_price:,.2f}")
c.metric("Implied upside / downside", f"{(value / reference_price - 1) * 100:+.1f}%" if value is not None else "—")
d.metric("Terminal contribution to EV", f"{details['PV terminal value']/details['Enterprise value']*100:.1f}%" if details and details["Enterprise value"] else "—")

st.subheader("WACC × terminal growth sensitivity")
wacc_values = [round(max(7.0, wacc + (i - 4) * 0.75), 2) for i in range(9)]
growth_values = [round(max(0.0, terminal + (j - 4) * 0.35), 2) for j in range(9)]
grid = []
for tg in growth_values:
    row = []
    for wa in wacc_values:
        result, _ = dcf_value(wa, tg, margin, growth, nwc)
        row.append(round(result, 2) if result is not None else None)
    grid.append(row)
fig = go.Figure(go.Heatmap(
    z=grid, x=[f"{x:.2f}%" for x in wacc_values], y=[f"{y:.2f}%" for y in growth_values],
    colorscale="RdYlGn", colorbar={"title": "₹/share"}, texttemplate="%{z:.1f}", hoverongaps=False))
fig.update_layout(xaxis_title="WACC", yaxis_title="Terminal growth", height=470, margin=dict(l=30, r=30, t=20, b=30))
st.plotly_chart(fig, use_container_width=True)
st.caption("Higher terminal growth and lower WACC raise the valuation. Cells where terminal growth is not below WACC are excluded.")

left, right = st.columns(2)
with left:
    st.subheader("Margin sensitivity")
    margins = [round(max(0.0, margin + i), 1) for i in range(-5, 6)]
    points = [dcf_value(wacc, terminal, m, growth, nwc)[0] for m in margins]
    fig_m = go.Figure(go.Scatter(x=margins, y=points, mode="lines+markers"))
    fig_m.add_hline(y=reference_price, line_dash="dash", annotation_text="Reference price")
    fig_m.update_layout(xaxis_title="EBITDA margin (%)", yaxis_title="DCF value (₹/share)", height=330)
    st.plotly_chart(fig_m, use_container_width=True)
with right:
    st.subheader("Working-capital sensitivity")
    nwcs = [round(max(0.0, nwc + 3 * i), 1) for i in range(-5, 6)]
    values = [dcf_value(wacc, terminal, margin, growth, x)[0] for x in nwcs]
    fig_n = go.Figure(go.Scatter(x=nwcs, y=values, mode="lines+markers"))
    fig_n.add_hline(y=reference_price, line_dash="dash", annotation_text="Reference price")
    fig_n.update_layout(xaxis_title="Incremental working capital (%)", yaxis_title="DCF value (₹/share)", height=330)
    st.plotly_chart(fig_n, use_container_width=True)

st.subheader("Projected cash flow bridge")
if details:
    df = pd.DataFrame(details["Projections"])
    st.dataframe(df.style.format({col: "{:,.1f}" for col in df.columns if col != "Year"}), use_container_width=True, hide_index=True)
    st.download_button("Download forecast CSV", data=df.to_csv(index=False), file_name="suzlon_dcf_forecast.csv", mime="text/csv")
    st.write(f"Present value of explicit FCFF: ₹{details['PV explicit FCFF']:,.0f} Cr · PV of terminal value: ₹{details['PV terminal value']:,.0f} Cr · Equity value: ₹{details['Equity value']:,.0f} Cr")

with st.expander("Sources, assumptions and limitations"):
    st.markdown("""
- Historical revenue base and selected financial figures: [Suzlon research spreadsheet](https://docs.google.com/spreadsheets/d/1VtG-lAKhk7RrZwC5NK6ja12ZxHiCGgWoCF9ZOBvF8Cw/edit).
- Official disclosures for validation: [Suzlon Investor Relations](https://www.suzlon.com/in-en/investors).
- Starting assumptions: FY2026 revenue ₹16,731.84 Cr; net cash ₹2,048 Cr; diluted share count assumed at 1,374 Cr.
- Depreciation: 2% of revenue; capex: 3.5%; cash tax: 25%; growth rate declines 2 percentage points annually.
- Working-capital investment: a percentage of incremental revenue. Terminal FCFF is projected from year-five FCFF.
- The reference market price is **not live**. The model excludes segment-specific economics, minority interests, leases and other adjustments.
- This dashboard is an educational financial modeling experiment, not a verified price target.
""")
