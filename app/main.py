import io
import numpy_financial as npf
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils import (
    load_company_stats,
    load_label_offsets,
    load_line_label_offsets,
    load_fundamentals,
    calculate_sharpe,
    update_offset
)

from plot import make_bubble_chart

from recommendations_engine import (
    build_recommendation,
    calculate_portfolio_metrics,
    build_comparison_table,
    generate_portfolio_comment
)

st.set_page_config(
    page_title="Interactive Risk / Return Visualization",
    layout="wide"
)

st.title("Interactive Risk / Return Visualization")

st.markdown("""
Interactive dashboard for analysing asset risk/return
and constructing investment portfolios.
""")

company_stats = load_company_stats("data/company_stats.csv")
label_offsets = load_label_offsets("data/label_offsets.csv")
line_offsets = load_line_label_offsets("data/line_label_offsets.csv")
fundamentals = load_fundamentals("data/fundamentals.csv")

company_stats = calculate_sharpe(company_stats)

st.sidebar.header("Visualization settings")

tickers = company_stats["Ticker"].tolist()
selected = st.sidebar.selectbox("Asset", tickers)

row = label_offsets[label_offsets["Ticker"] == selected]

dx = int(row["Offset_X"].iloc[0]) if not row.empty else 0
dy = int(row["Offset_Y"].iloc[0]) if not row.empty else 0
color = str(row["Color"].iloc[0]) if not row.empty else "#4c72b0"

dx = st.sidebar.slider("Offset X", -40, 40, dx)
dy = st.sidebar.slider("Offset Y", -40, 40, dy)
color = st.sidebar.color_picker("Bubble color", color)

label_offsets = update_offset(label_offsets, selected, dx, dy, color)

if st.sidebar.button("Save bubble settings"):
    label_offsets.to_csv("data/label_offsets.csv", index=False)

risk_map = {
    "conservative": 25,
    "moderate": 33,
    "aggressive": 50,
    "ultra_aggressive": 66
}

current_risk = st.session_state.get("last_risk", "conservative")
risk_anchor = risk_map.get(current_risk, 25)

fig = make_bubble_chart(
    company_stats,
    label_offsets,
    line_offsets,
    risk_anchor=risk_anchor
)

st.pyplot(fig, use_container_width=True)

buf = io.BytesIO()
fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")

st.download_button(
    "Download chart (PNG)",
    buf.getvalue(),
    "chart.png"
)

st.markdown("---")
st.header("Investment Goal Simulator")

with st.form("sim"):

    col1, col2 = st.columns(2)

    with col1:
        target = st.number_input("Target", value=100000)
        years = st.slider("Years", 1, 40, 10)
        initial = st.number_input("Initial investment", value=0)

    with col2:
        monthly = st.number_input("Monthly investment", value=1000)
        risk = st.selectbox(
            "Risk profile",
            ["conservative", "moderate", "aggressive", "ultra_aggressive"]
        )

        growth_type = st.selectbox(
            "Contribution growth type",
            ["percent", "absolute"]
        )

        growth_value = st.number_input("Growth value", value=0.0)

    run = st.form_submit_button("Run simulation")

if run:
    st.session_state.last_risk = risk
    st.session_state.years = years
    st.session_state.monthly = monthly
    st.session_state.initial = initial
    st.session_state.growth_type = growth_type
    st.session_state.growth_value = growth_value
    st.session_state.show_details = False

if run:

    result = build_recommendation(
        target,
        years,
        monthly,
        risk,
        company_stats
    )

    st.subheader("Simulation Result")

    c1, c2, c3 = st.columns(3)

    c1.metric("Future value", f"${result['future_value']:,.0f}")
    c2.metric("Target", f"${target:,.0f}")
    c3.metric("Return", f"{result['expected_return']*100:.2f}%")

    if result["achievable"]:
        st.success("Goal achievable")
    else:
        st.warning("Goal NOT achievable")

    portfolio = company_stats[
        company_stats["Ticker"].isin(result["assets"])
    ].copy()

    portfolio["Shares"] = 1

    st.session_state.portfolio = portfolio
    st.session_state.base_portfolio = portfolio.copy()
    st.session_state.current_metrics = calculate_portfolio_metrics(portfolio)

if "portfolio" in st.session_state:

    st.markdown("---")
    st.header("Portfolio Builder")

    portfolio = st.session_state.portfolio

    h1, h2, h3, h4, h5 = st.columns([2,2,2,2,1])
    h1.markdown("**Asset**")
    h2.markdown("**Shares**")
    h3.markdown("**Return %**")
    h4.markdown("**Volatility %**")
    h5.markdown("")

    remove_idx = None

    for i, row in portfolio.iterrows():

        c1, c2, c3, c4, c5 = st.columns([2,2,2,2,1])

        c1.write(row["Ticker"])

        shares = c2.number_input(
            "Shares",
            1,
            value=int(row["Shares"]),
            key=f"s_{i}"
        )

        c3.write(f"{row['Total Return (%)']:.2f}%")
        c4.write(f"{row['Volatility (%)']:.2f}%")

        if c5.button("❌", key=f"r_{i}"):
            remove_idx = i

        portfolio.loc[i, "Shares"] = shares

    if remove_idx is not None:
        portfolio = portfolio.drop(remove_idx)
        st.session_state.portfolio = portfolio
        st.rerun()

    st.markdown("### Add asset")

    new_asset = st.selectbox("Asset", company_stats["Ticker"])
    new_shares = st.number_input("Shares", 1, value=1, key="new")

    if st.button("Add"):
        new_row = company_stats[
            company_stats["Ticker"] == new_asset
        ].copy()
        new_row["Shares"] = new_shares

        st.session_state.portfolio = pd.concat(
            [portfolio, new_row],
            ignore_index=True
        )
        st.rerun()

    if st.button("Recalculate"):

        old = calculate_portfolio_metrics(st.session_state.base_portfolio)
        new = calculate_portfolio_metrics(st.session_state.portfolio)

        st.subheader("Comparison")

        table = build_comparison_table(old, new)
        st.dataframe(table)

        st.markdown(generate_portfolio_comment(old, new), unsafe_allow_html=True)

        st.session_state.current_metrics = new
        st.session_state.show_details = False

    if st.button("View Portfolio Details"):
        st.session_state.show_details = True

if st.session_state.get("show_details", False):

    st.markdown("---")
    st.header("Portfolio Details")

    portfolio = st.session_state.portfolio

    metrics = st.session_state.get(
        "current_metrics",
        calculate_portfolio_metrics(portfolio)
    )

    years = st.session_state.get("years", 10)
    monthly_base = st.session_state.get("monthly", 1000)
    initial = st.session_state.get("initial", 0)
    growth_type = st.session_state.get("growth_type", "percent")
    growth_value = st.session_state.get("growth_value", 0)

    annual_return = metrics["return"] / 100
    monthly_rate = (1 + annual_return) ** (1/12) - 1

    balance = initial
    invested = initial

    monthly_current = monthly_base

    timeline = []
    cash_flows = [-initial]

    for y in range(1, years + 1):

        months = []
        yearly_interest = 0
        yearly_contribution = 0

        for m in range(1, 13):

            balance += monthly_current
            invested += monthly_current
            cash_flows.append(-monthly_current)

            start_balance = balance

            interest = balance * monthly_rate
            balance += interest

            yearly_interest += interest
            yearly_contribution += monthly_current

            months.append({
                "Month": m,
                "Start": start_balance,
                "Interest": interest,
                "Contribution": monthly_current,
                "End": balance
            })

        timeline.append({
            "Year": y,
            "Start": months[0]["Start"],
            "Interest": yearly_interest,
            "Contribution": yearly_contribution,
            "End": balance,
            "Months": months
        })

        if growth_type == "percent":
            monthly_current *= (1 + growth_value / 100)
        else:
            monthly_current += growth_value

    cash_flows.append(balance)

    irr = npf.irr(cash_flows)
    effective = (1 + irr) ** 12 - 1 if irr is not None else 0

    profit = balance - invested

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Invested", f"{invested:,.2f} €")
    c2.metric("Profit", f"{profit:,.2f} €")
    c3.metric("Total", f"{balance:,.2f} €")
    c4.metric("Effective annual return", f"{effective*100:.2f}%")

    pie = px.pie(
        pd.DataFrame({
            "Type": ["Initial", "Contributions", "Profit"],
            "Value": [initial, invested - initial, profit]
        }),
        names="Type",
        values="Value"
    )

    st.plotly_chart(pie, use_container_width=True)

    years_list = [x["Year"] for x in timeline]
    total = [x["End"] for x in timeline]
    invested_line = [
        initial + sum([timeline[i]["Contribution"] for i in range(j+1)])
        for j in range(len(timeline))
    ]
    profit_line = [total[i] - invested_line[i] for i in range(len(total))]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years_list, y=invested_line, name="Invested"))
    fig.add_trace(go.Scatter(x=years_list, y=profit_line, name="Profit"))
    fig.add_trace(go.Scatter(x=years_list, y=total, name="Total"))

    fig.update_layout(height=600)

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Detailed breakdown")

    header = st.columns([2,2,2,2,2])
    header[0].markdown("**Year**")
    header[1].markdown("**Start (€)**")
    header[2].markdown("**Interest (€)**")
    header[3].markdown("**Contribution (€)**")
    header[4].markdown("**End (€)**")

    for y in timeline:

        key = f"year_{y['Year']}"

        if key not in st.session_state:
            st.session_state[key] = False

        row = st.columns([2,2,2,2,2])

        if row[0].button(f"Year {y['Year']}", key=f"btn_{key}"):
            st.session_state[key] = not st.session_state[key]

        row[1].write(f"{y['Start']:,.2f}")
        row[2].write(f"{y['Interest']:,.2f}")
        row[3].write(f"{y['Contribution']:,.2f}")
        row[4].write(f"{y['End']:,.2f}")

        if st.session_state[key]:

            df_months = pd.DataFrame(y["Months"])

            df_months = df_months.rename(columns={
                "Month": "Month",
                "Start": "Start (€)",
                "Interest": "Interest (€)",
                "Contribution": "Contribution (€)",
                "End": "End (€)"
            })

            st.dataframe(
                df_months,
                use_container_width=True,
                hide_index=True
            )