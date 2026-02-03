import io
import streamlit as st
import pandas as pd

from utils import (
    load_company_stats,
    load_label_offsets,
    load_line_label_offsets,
    load_fundamentals,
    calculate_sharpe,
    update_offset,
    update_line_offset,
)

from plot import make_bubble_chart
from recommendations_engine import build_recommendation


# =========================================================
# Page configuration
# =========================================================

st.set_page_config(
    page_title="Interactive Risk / Return Visualization",
    layout="wide",
)

st.title("Interactive Risk / Return Visualization (NASDAQ-100 & Indices)")

st.markdown(
    """
This dashboard allows you to:

- adjust bubble label positions and colors,
- fine-tune Sharpe line labels,
- export publication-ready charts,
- explore company fundamentals,
- evaluate investment goal feasibility.
"""
)


# =========================================================
# Data loading
# =========================================================

company_stats = load_company_stats("data/company_stats.csv")
label_offsets_raw = load_label_offsets("data/label_offsets.csv")
line_offsets_raw = load_line_label_offsets("data/line_label_offsets.csv")
fundamentals = load_fundamentals("data/fundamentals.csv")

index_tickers = ["QQQ", "SPY", "DIA"]

# Ensure indices exist in label offsets
for ticker in index_tickers:
    if ticker not in label_offsets_raw["Ticker"].astype(str).values:
        label_offsets_raw.loc[len(label_offsets_raw)] = [
            ticker, 0, 0, "#4c72b0"
        ]

company_stats = calculate_sharpe(company_stats)


# =========================================================
# Sidebar — visualization controls
# =========================================================

st.sidebar.header("⚙️ Visualization settings")

# ---------------------------------------------------------
# Bubble labels
# ---------------------------------------------------------

st.sidebar.subheader("Bubble labels & colors")

tickers = (
    company_stats["Ticker"].astype(str).tolist()
    + index_tickers
)

selected_ticker = st.sidebar.selectbox(
    "Select asset",
    tickers
)

row = label_offsets_raw[
    label_offsets_raw["Ticker"].astype(str) == selected_ticker
]

if not row.empty:
    dx_current = int(row["Offset_X"].iloc[0])
    dy_current = int(row["Offset_Y"].iloc[0])
    color_current = str(row["Color"].iloc[0])
else:
    dx_current, dy_current = 0, 0
    color_current = "#4c72b0"

dx = st.sidebar.slider(
    "Label offset X (points)",
    -40, 40, dx_current
)
dy = st.sidebar.slider(
    "Label offset Y (points)",
    -40, 40, dy_current
)
color = st.sidebar.color_picker(
    "Bubble color",
    value=color_current
)

label_offsets_for_plot = update_offset(
    label_offsets_raw,
    selected_ticker,
    dx,
    dy,
    color
)

if st.sidebar.button("💾 Save bubble settings"):
    label_offsets_for_plot.to_csv(
        "data/label_offsets.csv",
        index=False
    )
    st.sidebar.success(f"Saved for {selected_ticker}")


# ---------------------------------------------------------
# Sharpe line labels (ONLY Sharpe)
# ---------------------------------------------------------

st.sidebar.markdown("---")
st.sidebar.subheader("Sharpe line labels")

sharpe_lines = line_offsets_raw[
    line_offsets_raw["Type"] == "Sharpe"
]

levels = sharpe_lines["Level"].astype(float).tolist()

selected_level = st.sidebar.selectbox(
    "Sharpe line",
    levels,
    format_func=lambda x: f"Sharpe {x}",
)

line_row = sharpe_lines[
    sharpe_lines["Level"] == selected_level
]

if not line_row.empty:
    ldx = float(line_row["Offset_X"].iloc[0])
    ldy = float(line_row["Offset_Y"].iloc[0])
    rot = float(line_row["RotationFactor"].iloc[0])
else:
    ldx, ldy, rot = 0.8, -0.1, 0.7

ldx_new = st.sidebar.slider(
    "Label X offset (width fraction)",
    0.5, 1.2, ldx, step=0.01
)
ldy_new = st.sidebar.slider(
    "Label Y offset (height fraction)",
    -0.5, 0.5, ldy, step=0.01
)
rot_new = st.sidebar.slider(
    "Rotation factor",
    0.3, 1.2, rot, step=0.01
)

# ⬅️ ВАЖНО: без line_type
line_offsets_for_plot = update_line_offset(
    line_offsets_raw,
    selected_level,
    ldx_new,
    ldy_new,
    rot_new
)

if st.sidebar.button("💾 Save line settings"):
    line_offsets_for_plot.to_csv(
        "data/line_label_offsets.csv",
        index=False
    )
    st.sidebar.success(f"Saved Sharpe {selected_level}")


# =========================================================
# Main chart
# =========================================================

fig = make_bubble_chart(
    company_stats,
    label_offsets_for_plot,
    line_offsets_for_plot
)

st.pyplot(fig, clear_figure=True)

buf = io.BytesIO()
fig.savefig(
    buf,
    format="png",
    dpi=250,
    bbox_inches="tight"
)

st.download_button(
    "📥 Download chart (PNG)",
    data=buf.getvalue(),
    file_name="risk_return_chart.png",
    mime="image/png",
)


# =========================================================
# Investment goal simulator
# =========================================================

st.markdown("---")
st.markdown("## 🎯 Investment Goal Simulator")

with st.form("investment_goal_form"):
    col1, col2 = st.columns(2)

    with col1:
        target_amount = st.number_input(
            "Target amount ($)",
            min_value=10_000,
            max_value=10_000_000,
            value=100_000,
            step=10_000,
        )

        years = st.slider(
            "Investment horizon (years)",
            min_value=1,
            max_value=40,
            value=10,
        )

    with col2:
        monthly_contribution = st.number_input(
            "Monthly contribution ($)",
            min_value=100,
            max_value=100_000,
            value=1_000,
            step=100,
        )

        risk_profile = st.selectbox(
            "Risk profile",
            options=[
                "conservative",
                "moderate",
                "aggressive",
                "ultra_aggressive",
            ],
        )

    submitted = st.form_submit_button("Run simulation")


if submitted:
    result = build_recommendation(
        target_amount=target_amount,
        years=years,
        monthly_contribution=monthly_contribution,
        risk_profile=risk_profile,
        company_stats=company_stats,
    )

    st.markdown("### 📊 Simulation Result")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Expected portfolio value",
        f"${result['future_value']:,.0f}",
        delta=f"{result['gap']:,.0f} $",
    )

    c2.metric(
        "Target",
        f"${target_amount:,.0f}",
    )

    c3.metric(
        "Implied annual return",
        f"{result['expected_return'] * 100:.1f}%",
    )

    if result["achievable"]:
        st.success("✅ Goal is achievable under selected assumptions.")
    else:
        st.warning("⚠️ Goal is NOT achievable under selected assumptions.")

        st.markdown(
            f"""
**What could be adjusted:**

- required annual return: **{result['required_return'] * 100:.1f}%**
- monthly contribution
- investment horizon
"""
        )

