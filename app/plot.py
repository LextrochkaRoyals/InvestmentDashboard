import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# =========================================================
# Main bubble chart
# =========================================================

def make_bubble_chart(
    df: pd.DataFrame,
    label_offsets: pd.DataFrame,
    line_offsets: pd.DataFrame,
):
    """
    Risk / Return bubble chart with:
    - fixed analytical axis scaling
    - Sharpe ratio lines
    - inflation line
    - movable labels (from CSV)
    """

    # -----------------------------------------------------
    # Validate required columns
    # -----------------------------------------------------

    required_cols = [
        "Ticker",
        "Volatility (%)",
        "Annual Return (%)",
    ]

    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing column in company_stats: {col}")

    # Drop invalid rows explicitly
    df = df.dropna(subset=["Volatility (%)", "Annual Return (%)"]).copy()

    if df.empty:
        raise ValueError("No valid data to plot after cleaning.")

    # -----------------------------------------------------
    # Figure
    # -----------------------------------------------------

    fig, ax = plt.subplots(figsize=(14, 9))

    # -----------------------------------------------------
    # Fixed analytical axis scale (CRITICAL FIX)
    # -----------------------------------------------------

    x_max = max(30.0, df["Volatility (%)"].max() * 1.2)
    y_max = max(50.0, df["Annual Return (%)"].max() * 1.2)

    ax.set_xlim(0, x_max)
    ax.set_ylim(-20, y_max)

    ax.set_xlabel("Volatility (%)", fontsize=12)
    ax.set_ylabel("Annual Return (%)", fontsize=12)

    # -----------------------------------------------------
    # Scatter points
    # -----------------------------------------------------

    for _, row in df.iterrows():
        ticker = str(row["Ticker"])
        x = float(row["Volatility (%)"])
        y = float(row["Annual Return (%)"])

        label_row = label_offsets[
            label_offsets["Ticker"].astype(str) == ticker
        ]

        if not label_row.empty:
            dx = int(label_row["Offset_X"].iloc[0])
            dy = int(label_row["Offset_Y"].iloc[0])
            color = str(label_row["Color"].iloc[0])
        else:
            dx, dy = 0, 0
            color = "#4c72b0"

        ax.scatter(
            x,
            y,
            s=140,
            color=color,
            alpha=0.85,
            edgecolors="white",
            linewidth=0.8,
            zorder=3,
        )

        ax.annotate(
            ticker,
            (x, y),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=10,
            ha="center",
            va="center",
            zorder=4,
        )

    # -----------------------------------------------------
    # Sharpe ratio lines
    # -----------------------------------------------------

    sharpe_lines = line_offsets[line_offsets["Type"] == "Sharpe"]

    for _, row in sharpe_lines.iterrows():
        sharpe = float(row["Level"])
        ox = float(row["Offset_X"])
        oy = float(row["Offset_Y"])
        rot = float(row["RotationFactor"])

        xs = np.linspace(0.01, x_max, 200)
        ys = sharpe * xs

        ax.plot(
            xs,
            ys,
            linestyle="--",
            linewidth=1.5,
            alpha=0.7,
            zorder=1,
        )

        label_x = x_max * ox
        label_y = sharpe * label_x + oy * y_max

        ax.text(
            label_x,
            label_y,
            f"Sharpe {sharpe}",
            rotation=np.degrees(np.arctan(rot)),
            fontsize=10,
            alpha=0.9,
            ha="left",
            va="center",
        )

    # -----------------------------------------------------
    # Inflation line
    # -----------------------------------------------------

    inflation_row = line_offsets[line_offsets["Type"] == "Inflation"]

    if not inflation_row.empty:
        infl = float(inflation_row["Level"].iloc[0])
        ox = float(inflation_row["Offset_X"].iloc[0])
        oy = float(inflation_row["Offset_Y"].iloc[0])

        ax.axhline(
            infl,
            linestyle="--",
            linewidth=1.5,
            alpha=0.7,
            zorder=1,
        )

        ax.text(
            x_max * ox,
            infl + oy * y_max,
            f"Inflation ~{infl}%",
            fontsize=10,
            ha="left",
            va="center",
            alpha=0.9,
        )

    # -----------------------------------------------------
    # Grid & layout
    # -----------------------------------------------------

    ax.grid(True, linestyle="--", alpha=0.25)
    plt.tight_layout()

    return fig
