import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.express as px

st.set_page_config(
    page_title="SOXL Dashboard",
    layout="wide"
)

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
        period="2y",
        auto_adjust=True,
        progress=False
    )

    return data


def indicators(close):

    df = pd.DataFrame()
    df["Close"] = close

    df["SMA20"] = ta.trend.sma_indicator(close, 20)
    df["SMA50"] = ta.trend.sma_indicator(close, 50)
    df["SMA200"] = ta.trend.sma_indicator(close, 200)

    df["RSI"] = ta.momentum.rsi(close, 14)

    macd = ta.trend.MACD(close)

    df["MACD"] = macd.macd()
    df["MACD_SIGNAL"] = macd.macd_signal()

    return df


data = load_data()

soxl = indicators(data["Close"]["SOXL"])
soxx = indicators(data["Close"]["SOXX"])
nvda = indicators(data["Close"]["NVDA"])
amd = indicators(data["Close"]["AMD"])
qqq = indicators(data["Close"]["QQQ"])

score = 0

s = soxl.iloc[-1]
x = soxx.iloc[-1]
n = nvda.iloc[-1]
a = amd.iloc[-1]
q = qqq.iloc[-1]

if s["Close"] > s["SMA20"]:
    score += 5

if s["SMA20"] > s["SMA50"]:
    score += 5

if 50 < s["RSI"] < 70:
    score += 5

if s["MACD"] > s["MACD_SIGNAL"]:
    score += 5

if x["Close"] > x["SMA200"]:
    score += 20

if n["Close"] > n["SMA50"]:
    score += 10

if a["Close"] > a["SMA50"]:
    score += 10

if q["Close"] > q["SMA200"]:
    score += 20

vix = float(data["Close"]["^VIX"].iloc[-1])

if vix < 18:
    score += 20

elif vix < 25:
    score += 10

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

st.title("SOXL Quant Dashboard")

col1, col2, col3 = st.columns(3)

col1.metric("Score", score)
col2.metric("Signal", signal)
col3.metric("Position", position)

st.subheader("Market Status")

status = pd.DataFrame({
    "Asset": [
        "SOXX",
        "NVDA",
        "AMD",
        "QQQ",
        "VIX"
    ],
    "Value": [
        round(x["Close"],2),
        round(n["Close"],2),
        round(a["Close"],2),
        round(q["Close"],2),
        round(vix,2)
    ]
})

st.dataframe(
    status,
    use_container_width=True
)

st.subheader("SOXL Price")

price = pd.DataFrame({
    "Date": data["Close"]["SOXL"].index,
    "Close": data["Close"]["SOXL"].values
})

fig = px.line(
    price,
    x="Date",
    y="Close"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.caption("Updated automatically from Yahoo Finance")
