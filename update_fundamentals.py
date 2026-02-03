import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# ===============================
# Какие поля обновляем из API
# ===============================

FIELDS = {
    "PE": ("trailingPE", float),
    "ForwardPE": ("forwardPE", float),
    "PEG": ("pegRatio", float),
    "EV_EBITDA": ("enterpriseToEbitda", float),
    "MarketCap_B": ("marketCap", lambda x: float(x) / 1e9),
    "Debt_to_Equity": ("debtToEquity", float),
    "ROE_Pct": (None, None),   # отдельный расчёт
    "ProfitMargin_Pct": ("profitMargins", lambda x: float(x) * 100),
    "EPS_Growth_5Y": (None, None),  # отдельный расчёт
    "AnalystRating": ("recommendationMean", float),
}

# ===============================
# Функция обновления
# ===============================

def update_fundamentals(csv_path="data/fundamentals.csv"):
    df = pd.read_csv(csv_path)

    # обязательно тикеры как index
    if "Ticker" not in df.columns:
        raise ValueError("Файл должен содержать колонку Ticker")

    df = df.set_index("Ticker")

    tickers = df.index.tolist()
    print(f"Найдено {len(tickers)} тикеров для обновления")

    for ticker in tickers:
        print(f"\n=== {ticker} ===")
        try:
            stock = yf.Ticker(ticker)
        except Exception as e:
            print("Ошибка загрузки через yfinance:", e)
            continue

        # ---------- FAST INFO ----------
        try:
            fast = stock.fast_info
        except Exception:
            fast = {}

        # ---------- ANALYSTS ----------
        try:
            analysis = stock.get_analysis()
        except Exception:
            analysis = None

        # ---------- FINANCIALS ----------
        try:
            financials = stock.get_financials()
        except Exception:
            financials = None

        # ---------- BALANCE SHEET ----------
        try:
            bs = stock.get_balance_sheet()
        except Exception:
            bs = None

        # ---------- INCOME STATEMENT ----------
        try:
            income = stock.get_income_stmt()
        except Exception:
            income = None

        # --------------------------------------
        # ОБНОВЛЕНИЕ ДАННЫХ
        # --------------------------------------
        for col, (yf_key, conv) in FIELDS.items():

            # если поле уже заполнено → НЕ трогаем
            if pd.notna(df.at[ticker, col]):
                continue

            value = None

            # ====== 1. ДАННЫЕ ИЗ FAST_INFO ======
            if yf_key and yf_key in fast:
                try:
                    raw = fast[yf_key]
                    value = conv(raw) if conv else raw
                except Exception:
                    pass

            # ====== 2. СЛОЖНЫЕ ПОЛЯ (ROE, EPS growth) ======
            if col == "ROE_Pct" and value is None:
                # ROE = NetIncome / Equity
                try:
                    if bs is not None and income is not None:
                        equity = bs.loc["StockholdersEquity"].iloc[0]
                        net = income.loc["NetIncome"].iloc[0]
                        value = float(net / equity * 100)
                except Exception:
                    pass

            if col == "EPS_Growth_5Y" and value is None:
                try:
                    hist = stock.get_earnings()
                    if hist is not None and len(hist) >= 5:
                        eps = hist["Earnings"].values
                        if len(eps) >= 5 and eps[0] > 0:
                            g = (eps[-1] / eps[0]) ** (1/5) - 1
                            value = float(g * 100)
                except Exception:
                    pass

            # ====== 3. ЗАПИСЬ, ЕСЛИ НАШЛИ ЗНАЧЕНИЕ ======
            if value is not None and np.isfinite(value):
                df.at[ticker, col] = value
                print(f"  {col}: обновлено → {value:.3f}")
            else:
                print(f"  {col}: нет свежих данных (оставляем старое)")

    # сохраняем
    df = df.reset_index()
    df.to_csv(csv_path, index=False)
    print("\nГотово! Фундаментальные данные обновлены.")

    return df


# ================================================
# Запуск из командной строки
# ================================================
if __name__ == "__main__":
    print("Обновление фундаментальных данных…")
    update_fundamentals()
