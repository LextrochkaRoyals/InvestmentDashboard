import pandas as pd


# -----------------------------------------------------
# Portfolio metrics
# -----------------------------------------------------

def calculate_portfolio_metrics(portfolio: pd.DataFrame):

    if portfolio.empty:
        return {
            "return": 0.0,
            "volatility": 0.0
        }

    total_shares = portfolio["Shares"].sum()

    if total_shares == 0:
        return {
            "return": 0.0,
            "volatility": 0.0
        }

    portfolio = portfolio.copy()

    portfolio["Weight"] = portfolio["Shares"] / total_shares

    portfolio_return = (
        portfolio["Weight"] * portfolio["Total Return (%)"]
    ).sum()

    portfolio_volatility = (
        portfolio["Weight"] * portfolio["Volatility (%)"]
    ).sum()

    return {
        "return": portfolio_return,
        "volatility": portfolio_volatility
    }


# -----------------------------------------------------
# Comparison table
# -----------------------------------------------------

def build_comparison_table(old_metrics, new_metrics):

    df = pd.DataFrame({
        "Metric": ["Return (%)", "Volatility (%)"],
        "Old": [
            old_metrics["return"],
            old_metrics["volatility"]
        ],
        "New": [
            new_metrics["return"],
            new_metrics["volatility"]
        ]
    })

    df["Change"] = df["New"] - df["Old"]

    return df


# -----------------------------------------------------
# Recommendation text
# -----------------------------------------------------

def generate_portfolio_comment(old_metrics, new_metrics):

    delta_return = new_metrics["return"] - old_metrics["return"]
    delta_vol = new_metrics["volatility"] - old_metrics["volatility"]

    # Return text
    if delta_return > 0:
        return_text = f"<span style='color:green'>+{delta_return:.2f}%</span>"
    elif delta_return < 0:
        return_text = f"<span style='color:red'>{delta_return:.2f}%</span>"
    else:
        return_text = "0.00%"

    # Volatility text
    if delta_vol > 0:
        vol_text = f"<span style='color:red'>+{delta_vol:.2f}%</span>"
    elif delta_vol < 0:
        vol_text = f"<span style='color:green'>{delta_vol:.2f}%</span>"
    else:
        vol_text = "0.00%"

    return f"""
**Portfolio update:**

- Return changed by {return_text}
- Volatility changed by {vol_text}

Consider risk vs reward before adjusting allocation.
"""


# -----------------------------------------------------
# Initial recommendation (TOP 3 assets)
# -----------------------------------------------------

def build_recommendation(
    target_amount,
    years,
    monthly_contribution,
    risk_profile,
    company_stats
):

    # Risk thresholds
    risk_map = {
        "conservative": 25,
        "moderate": 33,
        "aggressive": 50,
        "ultra_aggressive": 66
    }

    max_risk = risk_map[risk_profile]

    df = company_stats.copy()

    # Filter by risk
    df = df[df["Volatility (%)"] <= max_risk]

    if df.empty:
        return {
            "assets": [],
            "expected_return": 0,
            "future_value": 0,
            "achievable": False
        }

    # Sort by return
    df = df.sort_values("Total Return (%)", ascending=False)

    top_assets = df.head(3)

    expected_return = top_assets["Total Return (%)"].mean()

    # Simple FV
    fv = monthly_contribution * 12 * years * (1 + expected_return / 100)

    return {
        "assets": top_assets["Ticker"].tolist(),
        "expected_return": expected_return / 100,
        "future_value": fv,
        "achievable": fv >= target_amount
    }