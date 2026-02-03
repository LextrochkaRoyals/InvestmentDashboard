import math
import pandas as pd
from typing import Dict, List


# =========================================================
# Financial math
# =========================================================

def future_value_monthly(
    monthly_contribution: float,
    annual_return: float,
    years: int
) -> float:
    """Future value with monthly contributions and annualized return."""
    r = annual_return / 12
    n = years * 12

    if r <= -1:
        return 0.0

    if r == 0:
        return monthly_contribution * n

    return monthly_contribution * ((1 + r) ** n - 1) / r


def required_annual_return(
    target_amount: float,
    monthly_contribution: float,
    years: int
) -> float:
    """Solve required CAGR using binary search."""
    low, high = 0.0, 0.5
    for _ in range(100):
        mid = (low + high) / 2
        fv = future_value_monthly(monthly_contribution, mid, years)
        if fv < target_amount:
            low = mid
        else:
            high = mid
    return mid


# =========================================================
# Strategy constraints
# =========================================================

STRATEGY_LIMITS = {
    "conservative": {
        "max_volatility": 0.15,
        "max_high_risk_weight": 0.10,
    },
    "moderate": {
        "max_volatility": 0.25,
        "max_high_risk_weight": 0.20,
    },
    "aggressive": {
        "max_volatility": 0.40,
        "max_high_risk_weight": 0.35,
    },
    "ultra_aggressive": {
        "max_volatility": 1.00,
        "max_high_risk_weight": 0.50,
    },
}


# =========================================================
# Core recommendation logic
# =========================================================

def build_recommendation(
    company_stats: pd.DataFrame,
    target_amount: float,
    years: int,
    monthly_contribution: float,
    risk_profile: str,
) -> Dict[str, object]:
    """
    Build investment recommendation based on concrete assets,
    not abstract distributions.
    """

    # -----------------------------------------------------
    # Step 1. Required return
    # -----------------------------------------------------
    required_return = required_annual_return(
        target_amount, monthly_contribution, years
    )

    # -----------------------------------------------------
    # Step 2. Filter valid assets
    # -----------------------------------------------------
    df = company_stats.copy()

    required_columns = {"Ticker", "AnnualizedReturn", "Volatility", "Sharpe"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Only assets that can theoretically meet the goal
    df = df[df["AnnualizedReturn"] >= required_return]

    if df.empty:
        return {
            "achievable": False,
            "reason": "No assets have sufficient historical return to meet the target.",
            "required_return": required_return,
        }

    # -----------------------------------------------------
    # Step 3. Split assets by role
    # -----------------------------------------------------
    base_assets = df[
        (df["Volatility"] <= STRATEGY_LIMITS[risk_profile]["max_volatility"])
    ]

    high_risk_assets = df[
        (df["Volatility"] > STRATEGY_LIMITS[risk_profile]["max_volatility"])
    ]

    if base_assets.empty and high_risk_assets.empty:
        return {
            "achievable": False,
            "reason": "No assets fit the selected risk constraints.",
            "required_return": required_return,
        }

    # -----------------------------------------------------
    # Step 4. Portfolio construction (simple heuristic)
    # -----------------------------------------------------
    portfolio = []

    # Start with best base asset (highest Sharpe)
    if not base_assets.empty:
        base = base_assets.sort_values("Sharpe", ascending=False).iloc[0]
        portfolio.append({
            "Ticker": base["Ticker"],
            "Weight": 1.0,
            "Return": base["AnnualizedReturn"],
            "Volatility": base["Volatility"],
        })

    # Try adding one high-risk asset if needed
    portfolio_return = sum(
        p["Weight"] * p["Return"] for p in portfolio
    )

    if portfolio_return < required_return and not high_risk_assets.empty:
        hr = high_risk_assets.sort_values(
            "AnnualizedReturn", ascending=False
        ).iloc[0]

        max_hr_weight = STRATEGY_LIMITS[risk_profile]["max_high_risk_weight"]

        # Compute minimal weight needed
        needed_weight = (
            required_return - portfolio_return
        ) / (hr["AnnualizedReturn"] - portfolio_return)

        hr_weight = min(max_hr_weight, max(0.0, needed_weight))

        # Adjust base weight
        portfolio[0]["Weight"] -= hr_weight

        portfolio.append({
            "Ticker": hr["Ticker"],
            "Weight": hr_weight,
            "Return": hr["AnnualizedReturn"],
            "Volatility": hr["Volatility"],
        })

        portfolio_return = sum(
            p["Weight"] * p["Return"] for p in portfolio
        )

    # -----------------------------------------------------
    # Step 5. Final feasibility check
    # -----------------------------------------------------
    if portfolio_return < required_return:
        return {
            "achievable": False,
            "reason": "Even with maximum allowed risk, the target return cannot be reached.",
            "required_return": required_return,
        }

    # -----------------------------------------------------
    # Step 6. Output
    # -----------------------------------------------------
    fv = future_value_monthly(
        monthly_contribution,
        portfolio_return,
        years
    )

    return {
        "achievable": True,
        "required_return": required_return,
        "expected_portfolio_return": portfolio_return,
        "future_value": fv,
        "gap": fv - target_amount,
        "portfolio": portfolio,
        "risk_profile": risk_profile,
        "notes": (
            "Portfolio constructed from individual assets based on historical "
            "annualized returns and volatility. This is not a guarantee of future performance."
        ),
    }
