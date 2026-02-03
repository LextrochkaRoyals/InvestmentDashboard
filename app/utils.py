import pandas as pd


# ======================================================
# LOADERS
# ======================================================

def load_company_stats(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    required = [
        "Ticker",
        "Volatility (%)",
        "Total Return (%)",
        "Years",
    ]

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"company_stats.csv is missing columns: {missing}")

    return df


def load_label_offsets(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    required = ["Ticker", "Offset_X", "Offset_Y", "Color"]
    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(f"label_offsets.csv is missing columns: {missing}")

    return df


def load_line_label_offsets(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    required = ["Type", "Level", "Offset_X", "Offset_Y", "RotationFactor"]
    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(f"line_label_offsets.csv is missing columns: {missing}")

    return df


def load_fundamentals(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


# ======================================================
# CALCULATIONS
# ======================================================

def calculate_sharpe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds Sharpe ratio based on annualized return / volatility.
    """
    df = df.copy()

    df["Annual Return (%)"] = (
        (1 + df["Total Return (%)"] / 100) ** (1 / df["Years"]) - 1
    ) * 100

    df["Sharpe"] = df["Annual Return (%)"] / df["Volatility (%)"]

    return df


# ======================================================
# UPDATERS
# ======================================================

def update_offset(
    df: pd.DataFrame,
    ticker: str,
    dx: float,
    dy: float,
    color: str,
) -> pd.DataFrame:
    df = df.copy()

    mask = df["Ticker"].astype(str) == str(ticker)

    if mask.any():
        df.loc[mask, ["Offset_X", "Offset_Y", "Color"]] = [dx, dy, color]
    else:
        df.loc[len(df)] = [ticker, dx, dy, color]

    return df


def update_line_offset(
    df: pd.DataFrame,
    level: float,
    offset_x: float,
    offset_y: float,
    rotation: float,
) -> pd.DataFrame:
    """
    Updates ONLY Sharpe line with given level.
    Inflation line is not editable via UI.
    """
    df = df.copy()

    mask = (df["Type"] == "Sharpe") & (df["Level"] == level)

    if not mask.any():
        raise ValueError(f"Sharpe line {level} not found")

    df.loc[mask, ["Offset_X", "Offset_Y", "Rotation"]] = [
        offset_x,
        offset_y,
        rotation,
    ]

    return df

