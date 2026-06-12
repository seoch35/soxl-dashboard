import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go

st.set_page_config(
    page_title="SOXL Quant Pro",
    layout="wide"
)

# -----------------
# DATA
# -----------------

TICKERS = [
    "SOXL",
    "SOXX",
    "NVDA",
    "AMD",
    "QQQ",
    "^VIX"
]

@st.cache_data(ttl=3600)
def load_data():

    data = yf.download(
        TICKERS,
        period="3y",
        group_by="ticker",
        auto_adjust=True,
        progress=False
    )

    return data

# -----------------
# INDICATORS
# -----------------

def build_indicators(close):

    df = pd.DataFrame()

    df["Close"] = close

    df["SMA20"] = ta.trend.sma_indicator(close, 20)
    df["SMA50"] = ta.trend.sma_indicator(close, 50)
    df["SMA200"] = ta.trend.sma_indicator(close, 200)

    df["RSI"] = ta.momentum.rsi(close, 14)

    macd = ta.trend.MACD(close)

    df["MACD"] = macd.macd()
    df["SIGNAL"] = macd.macd_signal()

    return df

# -----------------
# SCORE
# -----------------

def score_system():

    data = load_data()

    soxl = build_indicators(data["SOXL"]["Close"])
    soxx = build_indicators(data["SOXX"]["Close"])
    nvda = build_indicators(data["NVDA"]["Close"])
    amd  = build_indicators(data["AMD"]["Close"])
    qqq  = build_indicators(data["QQQ"]["Close"])

    s = soxl.iloc[-1]
    x = soxx.iloc[-1]
    n = nvda.iloc[-1]
    a = amd.iloc[-1]
    q = qqq.iloc[-1]

    vix = float(data["^VIX"]["Close"].iloc[-1])

    score = 0

    reasons = []

    # SOXL

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

    # SOXX

    if x["Close"] > x["SMA200"]:
        score += 20
        reasons.append("✅ 반도체 업사이클")

    # NVDA

    if n["Close"] > n["SMA50"]:
        score += 10
        reasons.append("✅ NVDA 강세")

    # AMD

    if a["Close"] > a["SMA50"]:
        score += 10
        reasons.append("✅ AMD 강세")

    # QQQ

    if q["Close"] > q["SMA200"]:
        score += 20
        reasons.append("✅ 나스닥 강세")

    # VIX

    if vix < 18:
        score += 20
        reasons.append("✅ VIX 안정")

    elif vix < 25:
        score += 10
        reasons.append("⚠️ VIX 보통")

    else:
        reasons.append("❌ VIX 위험")

    # SIGNAL

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

    # POSITION

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

    return (
        data,
        score,
        signal,
        position,
        reasons,
        vix
    )

# -----------------
# RUN
# -----------------

data, score, signal, position, reasons, vix = score_system()
st.write("DEBUG COLUMNS")
st.write(data.columns)

st.title("🚀 SOXL Quant Pro Dashboard")

c1, c2, c3 = st.columns(3)

c1.metric("Score", score)
c2.metric("Signal", signal)
c3.metric("Position", position)

# -----------------
# Gauge
# -----------------

fig = go.Figure(
    go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": "Market Score"},
        gauge={
            "axis": {"range": [0,100]}
        }
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# -----------------
# Status
# -----------------

st.subheader("Market Overview")

status = pd.DataFrame({
    "Asset":[
        "SOXX",
        "NVDA",
        "AMD",
        "QQQ",
        "VIX"
    ],
    "Price":[
        round(float(data["SOXX"]["Close"].iloc[-1]),2),
        round(float(data["NVDA"]["Close"].iloc[-1]),2),
        round(float(data["AMD"]["Close"].iloc[-1]),2),
        round(float(data["QQQ"]["Close"].iloc[-1]),2),
        round(vix,2)
    ]
})

st.dataframe(
    status,
    use_container_width=True
)

# -----------------
# Reasons
# -----------------

st.subheader("Signal Reasons")

for r in reasons:
    st.write(r)

# -----------------
# Chart
# -----------------

st.subheader("SOXL Price")

price = pd.DataFrame({
    "Date": data["SOXL"]["Close"].index,
    "Close": data["SOXL"]["Close"].values
})

chart = go.Figure()

chart.add_trace(
    go.Scatter(
        x=price["Date"],
        y=price["Close"],
        mode="lines",
        name="SOXL"
    )
)

st.plotly_chart(
    chart,
    use_container_width=True
)

st.caption("Auto-updated every hour")
