import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go

st.set_page_config(
    page_title="SOXL Quant Pro",
    layout="wide"
)

# -----------------------------
# SETTINGS
# -----------------------------

TICKERS = [
    "SOXL",
    "SOXX",
    "NVDA",
    "AMD",
    "QQQ",
    "^VIX"
]

# -----------------------------
# DATA
# -----------------------------

@st.cache_data(ttl=3600)
def load_data():

    return yf.download(
        TICKERS,
        period="3y",
        auto_adjust=True,
        progress=False,
        group_by="ticker"
    )

def get_close(data, ticker):

    try:
        return data[ticker]["Close"].dropna()
    except:
        return pd.Series(dtype=float)

# -----------------------------
# INDICATORS
# -----------------------------

def build_indicators(close):

    if len(close) < 250:
        return None

    df = pd.DataFrame(index=close.index)

    df["Close"] = close

    df["SMA20"] = ta.trend.sma_indicator(close, 20)
    df["SMA50"] = ta.trend.sma_indicator(close, 50)
    df["SMA200"] = ta.trend.sma_indicator(close, 200)

    df["RSI"] = ta.momentum.rsi(close, 14)

    macd = ta.trend.MACD(close)

    df["MACD"] = macd.macd()
    df["SIGNAL"] = macd.macd_signal()

    return df.dropna()

# -----------------------------
# HEIKIN ASHI
# -----------------------------

@st.cache_data(ttl=1800)
def get_heikin_signal():

    try:

        df = yf.download(
            "SOXL",
            period="60d",
            interval="1h",
            auto_adjust=True,
            progress=False
        )

        if len(df) < 50:
            return "N/A", "N/A"

        ha = pd.DataFrame(index=df.index)

        ha["HA_Close"] = (
            df["Open"] +
            df["High"] +
            df["Low"] +
            df["Close"]
        ) / 4

        ha_open = []

        for i in range(len(df)):

            if i == 0:

                ha_open.append(
                    (df["Open"].iloc[0] +
                     df["Close"].iloc[0]) / 2
                )

            else:

                ha_open.append(
                    (ha_open[i - 1] +
                     ha["HA_Close"].iloc[i - 1]) / 2
                )

        ha["HA_Open"] = ha_open

        ha["EMA9"] = ta.trend.ema_indicator(
            df["Close"],
            9
        )

        ha["EMA21"] = ta.trend.ema_indicator(
            df["Close"],
            21
        )

        last = ha.iloc[-1]

        bullish_ha = (
            last["HA_Close"] >
            last["HA_Open"]
        )

        bullish_ema = (
            last["EMA9"] >
            last["EMA21"]
        )

        if bullish_ha and bullish_ema:

            return "🟢 BULLISH", "BUY"

        elif (not bullish_ha) and (not bullish_ema):

            return "🔴 BEARISH", "SELL"

        else:

            return "🟡 MIXED", "WAIT"

    except:

        return "N/A", "N/A"

# -----------------------------
# LOAD
# -----------------------------

data = load_data()

soxl_close = get_close(data, "SOXL")
soxx_close = get_close(data, "SOXX")
nvda_close = get_close(data, "NVDA")
amd_close = get_close(data, "AMD")
qqq_close = get_close(data, "QQQ")
vix_close = get_close(data, "^VIX")

soxl = build_indicators(soxl_close)
soxx = build_indicators(soxx_close)
nvda = build_indicators(nvda_close)
amd = build_indicators(amd_close)
qqq = build_indicators(qqq_close)

score = 0
reasons = []

# -----------------------------
# SCORE
# -----------------------------

if soxl is not None:

    s = soxl.iloc[-1]

    if s["Close"] > s["SMA20"]:
        score += 5
        reasons.append("✅ SOXL > SMA20")

    if s["SMA20"] > s["SMA50"]:
        score += 5
        reasons.append("✅ SOXL 상승 추세")

    if 50 < s["RSI"] < 70:
        score += 5
        reasons.append("✅ RSI 건강")

    if s["MACD"] > s["SIGNAL"]:
        score += 5
        reasons.append("✅ MACD 상승")

if soxx is not None:

    x = soxx.iloc[-1]

    if x["Close"] > x["SMA200"]:
        score += 20
        reasons.append("✅ 반도체 업사이클")

if nvda is not None:

    n = nvda.iloc[-1]

    if n["Close"] > n["SMA50"]:
        score += 10
        reasons.append("✅ NVDA 강세")

if amd is not None:

    a = amd.iloc[-1]

    if a["Close"] > a["SMA50"]:
        score += 10
        reasons.append("✅ AMD 강세")

if qqq is not None:

    q = qqq.iloc[-1]

    if q["Close"] > q["SMA200"]:
        score += 20
        reasons.append("✅ 나스닥 강세")

vix = float(vix_close.iloc[-1])

if vix < 18:

    score += 20
    reasons.append("✅ VIX 안정")

elif vix < 25:

    score += 10
    reasons.append("⚠️ VIX 보통")

else:

    reasons.append("❌ VIX 위험")

# -----------------------------
# SIGNAL
# -----------------------------

if score >= 85:
    signal = "🚀 STRONG BUY"
elif score >= 70:
    signal = "🟢 BUY"
elif score >= 50:
    signal = "🟡 HOLD"
elif score >= 30:
    signal = "🟠 SELL"
else:
    signal = "🔴 STRONG SELL"

if score >= 90:
    position = "100%"
elif score >= 80:
    position = "75%"
elif score >= 70:
    position = "50%"
elif score >= 60:
    position = "25%"
else:
    position = "0%"

# -----------------------------
# HEIKIN ASHI
# -----------------------------

ha_trend, scalp_signal = get_heikin_signal()

# -----------------------------
# UI
# -----------------------------

st.title("🚀 SOXL Quant Pro Dashboard")

c1, c2, c3 = st.columns(3)

c1.metric("Score", score)
c2.metric("Signal", signal)
c3.metric("Position", position)

# Gauge

gauge = go.Figure(
    go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": "Market Score"},
        gauge={
            "axis": {"range": [0, 100]}
        }
    )
)

st.plotly_chart(
    gauge,
    use_container_width=True
)

# Heikin Ashi

st.subheader("Heikin Ashi Swing")

h1, h2 = st.columns(2)

h1.metric(
    "Trend",
    ha_trend
)

h2.metric(
    "Signal",
    scalp_signal
)

# Market Overview

st.subheader("Market Overview")

status = pd.DataFrame({

    "Asset": [
        "SOXL",
        "SOXX",
        "NVDA",
        "AMD",
        "QQQ",
        "VIX"
    ],

    "Price": [

        round(float(soxl_close.iloc[-1]), 2),
        round(float(soxx_close.iloc[-1]), 2),
        round(float(nvda_close.iloc[-1]), 2),
        round(float(amd_close.iloc[-1]), 2),
        round(float(qqq_close.iloc[-1]), 2),
        round(float(vix), 2)
    ]
})

st.dataframe(
    status,
    use_container_width=True
)

# Reasons

st.subheader("Signal Reasons")

for r in reasons:
    st.write(r)

# Chart

st.subheader("SOXL Price")

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=soxl_close.index,
        y=soxl_close.values,
        mode="lines",
        name="SOXL"
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.caption("Updated automatically every hour")
