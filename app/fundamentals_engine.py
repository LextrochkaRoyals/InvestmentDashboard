import pandas as pd
import numpy as np


# ============================================================
# Загрузка и предобработка fundamentals.csv
# ============================================================

def load_fundamentals(path: str = "data/fundamentals.csv") -> pd.DataFrame:
    """
    Загружает fundamentals.csv, приводит ключевые метрики к числовому виду.
    
    Требует как минимум колонку 'Ticker'.
    Остальные метрики обрабатываются по принципу "что есть — то и используем".
    """
    df = pd.read_csv(path)

    if "Ticker" not in df.columns:
        raise ValueError("В fundamentals.csv должна быть колонка 'Ticker'.")

    # Убираем возможные пробелы и приводим тикеры к строке
    df["Ticker"] = df["Ticker"].astype(str).str.strip()

    # Список метрик, которые ПЫТАЕМСЯ привести к числу, если они есть
    numeric_cols = [
        "marketCap",
        "trailingPE",
        "forwardPE",
        "pegRatio",
        "dividendYield",
        "payoutRatio",
        "profitMargins",
        "operatingMargins",
        "returnOnEquity",
        "returnOnAssets",
        "grossMargins",
        "ebitdaMargins",
        "revenueGrowth",
        "earningsGrowth",
        "debtToEquity",
        "currentRatio",
        "quickRatio",
        "beta",
        "freeCashflow",
        "totalDebt",
        "totalCash",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


# ============================================================
# Вспомогательные функции
# ============================================================

def _val(row: pd.Series, col: str, default=np.nan):
    """Безопасно достаём числовое значение метрики."""
    if col not in row.index:
        return default
    try:
        return float(row[col])
    except Exception:
        return default


def _bucket(value, bounds, labels, higher_is_better=True):
    """
    Универсальный разбиратор на "низкий / норм / высокий" и т.п.
    
    value: число или NaN
    bounds: [b1, b2, ...]
    labels: [label1, label2, label3, ...] на 1 больше, чем границ
    higher_is_better: если False — инвертируем интерпретацию (чем ниже, тем лучше)
    """
    if value is None or np.isnan(value):
        return "н/д"

    if not higher_is_better:
        # инверсия: например, для долга/волатильности — меньше = лучше
        value = -value
        bounds = [-b for b in bounds]
        bounds = sorted(bounds)

    for b, lab in zip(bounds, labels):
        if value < b:
            return lab
    return labels[-1]


# ============================================================
# Классификация компании по фундаменталу
# ============================================================

def classify_company(row: pd.Series) -> dict:
    """
    Возвращает словарь с короткими тегами по основным осям:
    - valuation (оценка)
    - growth (рост)
    - quality (качество бизнеса)
    - leverage (долговая нагрузка)
    - dividend (дивиденды)
    - risk (общий риск)
    """
    pe = _val(row, "trailingPE")
    fwd_pe = _val(row, "forwardPE")
    peg = _val(row, "pegRatio")
    dy = _val(row, "dividendYield")  # обычно в долях (0.02 = 2%)
    pm = _val(row, "profitMargins")
    roe = _val(row, "returnOnEquity")
    rg = _val(row, "revenueGrowth")
    eg = _val(row, "earningsGrowth")
    dte = _val(row, "debtToEquity")
    beta = _val(row, "beta")

    # --- Valuation (оценка) ---
    # если есть PEG — используем его в первую очередь
    if not np.isnan(peg):
        valuation = _bucket(
            peg,
            bounds=[0.8, 1.2, 2.0],
            labels=["потенциально недооценена", "близка к справедливой оценке", "дорогая", "очень дорогая"],
            higher_is_better=False,
        )
    else:
        valuation = _bucket(
            pe,
            bounds=[15, 25, 40],
            labels=["дешёвая", "умеренно оценённая", "дорогая", "супердорогая"],
            higher_is_better=False,
        )

    # --- Growth (рост бизнеса) ---
    # revenueGrowth / earningsGrowth обычно как доли (0.15 = +15%)
    growth_score = 0
    growth_tags = []

    if not np.isnan(rg):
        if rg > 0.20:
            growth_tags.append("сильный рост выручки")
            growth_score += 2
        elif rg > 0.05:
            growth_tags.append("умеренный рост выручки")
            growth_score += 1
        elif rg < 0:
            growth_tags.append("падение выручки")
            growth_score -= 1

    if not np.isnan(eg):
        if eg > 0.20:
            growth_tags.append("сильный рост прибыли")
            growth_score += 2
        elif eg > 0.05:
            growth_tags.append("умеренный рост прибыли")
            growth_score += 1
        elif eg < 0:
            growth_tags.append("падение прибыли")
            growth_score -= 1

    if growth_score >= 3:
        growth = "агрессивный рост"
    elif growth_score >= 1:
        growth = "умеренный рост"
    elif growth_score <= -1:
        growth = "замедление / снижение"
    else:
        growth = "стабильная динамика"

    # --- Quality (качество бизнеса) ---
    quality_score = 0
    if not np.isnan(pm):
        if pm > 0.25:
            quality_score += 2
        elif pm > 0.10:
            quality_score += 1
        elif pm < 0:
            quality_score -= 1

    if not np.isnan(roe):
        if roe > 0.25:
            quality_score += 2
        elif roe > 0.10:
            quality_score += 1
        elif roe < 0:
            quality_score -= 1

    if quality_score >= 3:
        quality = "высокая рентабельность"
    elif quality_score >= 1:
        quality = "здоровая рентабельность"
    elif quality_score <= -1:
        quality = "есть вопросы к эффективности"
    else:
        quality = "среднее качество бизнеса"

    # --- Leverage (долговая нагрузка) ---
    leverage = _bucket(
        dte,
        bounds=[50, 150, 300],
        labels=["низкий долг", "умеренный долг", "повышенная долговая нагрузка", "очень высокий долг"],
        higher_is_better=False,
    )

    # --- Dividend (дивидендная политика) ---
    if np.isnan(dy) or dy == 0:
        dividend = "дивиденды не выплачиваются"
    elif dy < 0.02:
        dividend = "низкая дивидендная доходность"
    elif dy < 0.05:
        dividend = "умеренные дивиденды"
    else:
        dividend = "высокая дивидендная доходность"

    # --- Risk (суммарный риск) ---
    risk_score = 0

    # Высокий долг = плюс к риску
    if not np.isnan(dte):
        if dte > 200:
            risk_score += 2
        elif dte > 100:
            risk_score += 1

    # Высокий beta = волатильность
    if not np.isnan(beta):
        if beta > 1.5:
            risk_score += 2
        elif beta > 1.0:
            risk_score += 1
        elif beta < 0.7:
            risk_score -= 1  # защитная бумага

    # Отрицательный рост/маржа = доп. риск
    if growth_score <= -1:
        risk_score += 1
    if quality_score <= -1:
        risk_score += 1

    if risk_score >= 4:
        risk = "очень высокий риск"
    elif risk_score >= 2:
        risk = "повышенный риск"
    elif risk_score <= 0:
        risk = "умеренный или низкий риск"
    else:
        risk = "средний риск"

    return {
        "valuation": valuation,
        "growth": growth,
        "growth_details": ", ".join(growth_tags) if growth_tags else "динамика без ярко выраженных трендов",
        "quality": quality,
        "leverage": leverage,
        "dividend": dividend,
        "risk": risk,
    }


# ============================================================
# Генерация текстового описания компании
# ============================================================

def generate_text_summary(row: pd.Series) -> str:
    """
    Создаёт компактное текстовое описание компании на основе фундаментальных метрик.
    Предполагается для отображения в Streamlit под выбором тикера.
    """
    ticker = str(row.get("Ticker", "N/A"))

    cls = classify_company(row)

    pe = _val(row, "trailingPE")
    dy = _val(row, "dividendYield")
    rg = _val(row, "revenueGrowth")
    eg = _val(row, "earningsGrowth")
    dte = _val(row, "debtToEquity")
    beta = _val(row, "beta")
    pm = _val(row, "profitMargins")
    roe = _val(row, "returnOnEquity")

    lines = []

    # --- Заголовок ---
    lines.append(f"**{ticker} — краткий фундаментальный профиль**")

    # --- Оценка и рост ---
    lines.append(
        f"- Оценка: {cls['valuation']}. Динамика роста: {cls['growth']} "
        f"({cls['growth_details']})."
    )

    # --- Рентабельность ---
    prof_bits = []
    if not np.isnan(pm):
        prof_bits.append(f"маржа прибыли ≈ {pm*100:.1f}%")
    if not np.isnan(roe):
        prof_bits.append(f"ROE ≈ {roe*100:.1f}%")

    if prof_bits:
        lines.append(f"- Рентабельность: {cls['quality']} ({'; '.join(prof_bits)}).")
    else:
        lines.append(f"- Рентабельность: {cls['quality']}.")

    # --- Дивиденды ---
    if not np.isnan(dy) and dy > 0:
        lines.append(f"- Дивиденды: {cls['dividend']} (≈ {dy*100:.1f}% годовых).")
    else:
        lines.append(f"- Дивиденды: {cls['dividend']}.")

    # --- Долг и риск ---
    risk_bits = [cls["risk"], cls["leverage"]]

    if not np.isnan(dte):
        risk_bits.append(f"Debt/Equity ≈ {dte:.0f}%")
    if not np.isnan(beta):
        risk_bits.append(f"β ≈ {beta:.2f}")

    lines.append(f"- Риск-профиль: {', '.join(risk_bits)}.")

    # --- Рост выручки/прибыли — если есть ---
    rg_bits = []
    if not np.isnan(rg):
        rg_bits.append(f"выручка: {rg*100:.1f}% г/г")
    if not np.isnan(eg):
        rg_bits.append(f"прибыль: {eg*100:.1f}% г/г")
    if rg_bits:
        lines.append(f"- Рост показателей: {', '.join(rg_bits)}.")

    # --- Итоговая роль в портфеле (грубая эвристика) ---
    role = infer_portfolio_role(cls)
    lines.append(f"- **Роль в портфеле:** {role}.")

    return "\n".join(lines)


# ============================================================
# Определение роли в портфеле
# ============================================================

def infer_portfolio_role(classes: dict) -> str:
    """
    На основе классификатора возвращает текст:
    - агрессивный рост / high beta
    - дивидендное ядро
    - защитный компонент
    - сбалансированная история роста и качества
    и т.п.
    """
    growth = classes.get("growth", "")
    quality = classes.get("quality", "")
    dividend = classes.get("dividend", "")
    risk = classes.get("risk", "")

    # Агрессивный рост + высокий риск
    if "агрессивный" in growth and "высокий риск" in risk:
        return "агрессивный компонент для разгона доходности (высокая волатильность)"

    # Рост + качество, но риск не зашкаливает
    if ("агрессивный" in growth or "умеренный" in growth) and "высокая рентабельность" in quality:
        if "дивиденд" in dividend:
            return "ростовая история с качественным бизнесом и дивидендами"
        return "ростовой компонент с упором на качество бизнеса"

    # Защитная штука с дивидендами
    if "дивидендная доходность" in dividend and "низкий долг" in classes.get("leverage", ""):
        return "дивидендное ядро портфеля с умеренным риском"

    # Просто дивиденды
    if "дивидендная доходность" in dividend:
        return "дивидендный компонент для сглаживания колебаний доходности"

    # Если явно высокий риск без компенсации качеством
    if "очень высокий риск" in risk or "повышенный риск" in risk:
        return "спекулятивная позиция для небольшой доли портфеля"

    # По умолчанию — нейтральная история
    return "сбалансированная позиция с умеренным риском и нейтральными характеристиками"


# ============================================================
# Утилита для получения профиля по тикеру
# ============================================================

def get_company_profile(fundamentals_df: pd.DataFrame, ticker: str) -> dict:
    """
    Возвращает:
    {
      'row': Series,
      'classes': dict (classify_company),
      'summary': str (generate_text_summary)
    }
    или None, если тикера нет.
    """
    ticker = str(ticker).strip()
    sub = fundamentals_df[fundamentals_df["Ticker"].astype(str).str.strip() == ticker]

    if sub.empty:
        return None

    row = sub.iloc[0]
    classes = classify_company(row)
    summary = generate_text_summary(row)

    return {
        "row": row,
        "classes": classes,
        "summary": summary,
    }
