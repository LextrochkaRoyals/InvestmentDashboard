import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D


def make_bubble_chart(
    df: pd.DataFrame,
    label_offsets: pd.DataFrame,
    line_offsets: pd.DataFrame,
    risk_anchor: float = 25  # ← сохраняем старую логику
):

    fig, ax = plt.subplots(figsize=(14, 9))

    x_min = 0
    x_max = 80
    y_min = -10
    y_max = 100

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

    ax.set_xlabel("Volatility (%)", fontsize=12)
    ax.set_ylabel("Total Return (%)", fontsize=12)

    # ------------------------------------------------
    # Scatter points
    # ------------------------------------------------

    index_colors = {
        "QQQ": "#DD8452",
        "SPY": "#55A868",
        "DIA": "#C44E52",
    }

    for _, row in df.iterrows():

        ticker = str(row["Ticker"])
        x = float(row["Volatility (%)"])
        y = float(row["Total Return (%)"])

        label_row = label_offsets[
            label_offsets["Ticker"].astype(str) == ticker
        ]

        if not label_row.empty:
            dx = int(label_row["Offset_X"].iloc[0])
            dy = int(label_row["Offset_Y"].iloc[0])
        else:
            dx, dy = 0, 0

        color = index_colors.get(ticker, "#4c72b0")

        ax.scatter(
            x,
            y,
            s=140,
            color=color,
            alpha=0.9,
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

    # ------------------------------------------------
    # Risk boundary (DYNAMIC)
    # ------------------------------------------------

    ax.axvline(
        risk_anchor,
        linestyle="--",
        color="black",
        linewidth=1.5,
        alpha=0.8,
    )

    # ------------------------------------------------
    # Minimum acceptable return (DYNAMIC)
    # ------------------------------------------------

    min_return = risk_anchor * 0.5

    ax.axhline(
        min_return,
        linestyle="--",
        color="black",
        linewidth=1.5,
        alpha=0.8,
    )

    # ------------------------------------------------
    # Inflation line (UNCHANGED)
    # ------------------------------------------------

    inflation = 4

    ax.axhline(
        inflation,
        linestyle="--",
        color="gray",
        linewidth=1.2,
        alpha=0.7,
    )

    ax.text(
        x_max * 0.85,
        inflation + 1,
        "Inflation ~4%",
        fontsize=10,
        color="gray",
    )

    # ------------------------------------------------
    # Legend (UNCHANGED)
    # ------------------------------------------------

    legend_elements = [

        Line2D([0], [0], marker="o", color="w",
               label="Companies",
               markerfacecolor="#4c72b0",
               markersize=12),

        Line2D([0], [0], marker="o", color="w",
               label="QQQ (NASDAQ-100 ETF)",
               markerfacecolor="#DD8452",
               markersize=12),

        Line2D([0], [0], marker="o", color="w",
               label="SPY (S&P 500 ETF)",
               markerfacecolor="#55A868",
               markersize=12),

        Line2D([0], [0], marker="o", color="w",
               label="DIA (Dow Jones ETF)",
               markerfacecolor="#C44E52",
               markersize=12),

        Line2D([0], [0], linestyle="--",
               color="black",
               label="Risk boundary"),

        Line2D([0], [0], linestyle="--",
               color="gray",
               label="Inflation"),
    ]

    ax.legend(
        handles=legend_elements,
        loc="upper left",
        frameon=True,
        fontsize=12,
    )

    ax.grid(True, linestyle="--", alpha=0.25)

    plt.tight_layout()

    return fig