import pandas as pd


# -----------------------------------------------------
# Load company statistics
# -----------------------------------------------------

def load_company_stats(path):

    df = pd.read_csv(path)

    df.columns = [c.strip() for c in df.columns]

    return df


# -----------------------------------------------------
# Load bubble label offsets
# -----------------------------------------------------

def load_label_offsets(path):

    df = pd.read_csv(path)

    df.columns = [c.strip() for c in df.columns]

    return df


# -----------------------------------------------------
# Load line label offsets
# -----------------------------------------------------

def load_line_label_offsets(path):

    df = pd.read_csv(path)

    df.columns = [c.strip() for c in df.columns]

    return df


# -----------------------------------------------------
# Load fundamentals
# -----------------------------------------------------

def load_fundamentals(path):

    try:
        df = pd.read_csv(path)

        df.columns = [c.strip() for c in df.columns]

        return df

    except FileNotFoundError:

        return pd.DataFrame()


# -----------------------------------------------------
# Calculate Sharpe ratio
# -----------------------------------------------------

def calculate_sharpe(df, risk_free_rate=4.0):

    df = df.copy()

    if "Total Return (%)" in df.columns and "Volatility (%)" in df.columns:

        df["Sharpe"] = (
            (df["Total Return (%)"] - risk_free_rate)
            / df["Volatility (%)"]
        )

    else:

        df["Sharpe"] = None

    return df


# -----------------------------------------------------
# Update bubble label offset
# -----------------------------------------------------

def update_offset(
    df,
    ticker,
    offset_x,
    offset_y,
    color
):

    df = df.copy()

    mask = df["Ticker"] == ticker

    if mask.any():

        df.loc[mask, "Offset_X"] = offset_x
        df.loc[mask, "Offset_Y"] = offset_y
        df.loc[mask, "Color"] = color

    else:

        new_row = pd.DataFrame(
            {
                "Ticker": [ticker],
                "Offset_X": [offset_x],
                "Offset_Y": [offset_y],
                "Color": [color],
            }
        )

        df = pd.concat([df, new_row], ignore_index=True)

    return df


# -----------------------------------------------------
# Update line label offset
# -----------------------------------------------------

def update_line_offset(
    df,
    line_type,
    level,
    offset_x,
    offset_y,
    rotation_factor
):

    df = df.copy()

    mask = (
        (df["Type"] == line_type)
        &
        (df["Level"] == level)
    )

    if mask.any():

        df.loc[mask, "Offset_X"] = offset_x
        df.loc[mask, "Offset_Y"] = offset_y
        df.loc[mask, "RotationFactor"] = rotation_factor

    else:

        new_row = pd.DataFrame(
            {
                "Type": [line_type],
                "Level": [level],
                "Offset_X": [offset_x],
                "Offset_Y": [offset_y],
                "RotationFactor": [rotation_factor],
            }
        )

        df = pd.concat([df, new_row], ignore_index=True)

    return df