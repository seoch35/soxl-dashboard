
import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go

st.set_page_config(page_title="SOXL Quant Pro V9 MTF", layout="wide")

# -----------------------------
# DATA
# -----------------------------

@st.cache_data(ttl=300)
def load_daily():
    df = yf.download("SOXL", period="3y", auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

@st.cache_data(ttl=300)
def load_hourly():
    df = yf.download("SOXL", period="730d", interval="1h", auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

@st.cache_data(ttl=300)
def load_30m():
    df = yf.download("SOXL", period="60d", interval="30m", auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

# -----------------------------
# INDICATORS
# -----------------------------

def analyze(df):

    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    volume = df["Volume"].astype(float)

    ema20 = ta.trend.ema_indicator(close, 20)
    ema60 = ta.trend.ema_indicator(close, 60)

    rsi = ta.momentum.rsi(close, 14)

    macd = ta.trend.MACD(close)

    mfi = ta.volume.money_flow_index(
        high, low, close, volume, window=14
    )

    ichi = ta.trend.IchimokuIndicator(high, low)

    span_a = ichi.ichimoku_a()
    span_b = ichi.ichimoku_b()

    last_close = float(close.iloc[-1])

    conditions = 0

    if ema20.iloc[-1] > ema60.iloc[-1]:
        conditions += 1

    if 50 <= rsi.iloc[-1] <= 75:
        conditions += 1

    if macd.macd().iloc[-1] > macd.macd_signal().iloc[-1]:
        conditions += 1

    if mfi.iloc[-1] > 50:
        conditions += 1

    if last_close > max(span_a.iloc[-1], span_b.iloc[-1]):
        conditions += 1

    return {
        "score": conditions,
        "close": round(last_close, 2),
        "rsi": round(float(rsi.iloc[-1]), 2)
    }

# -----------------------------
# LOAD
# -----------------------------

daily = analyze(load_daily())
hourly = analyze(load_hourly())
m30 = analyze(load_30m())

total_score = daily["score"] + hourly["score"] + m30["score"]

if total_score >= 13:
    signal = "🚀 STRONG BUY"
    position = "100%"
elif total_score >= 10:
    signal = "🟢 BUY"
    position = "75%"
elif total_score >= 7:
    signal = "🟡 HOLD"
    position = "50%"
elif total_score >= 4:
    signal = "🟠 SELL"
    position = "25%"
else:
    signal = "🔴 STRONG SELL"
    position = "0%"

# -----------------------------
# UI
# -----------------------------

st.title("🚀 SOXL Quant Pro V9 (MTF)")

c1, c2, c3 = st.columns(3)

c1.metric("MTF Score", f"{total_score}/15")
c2.metric("Signal", signal)
c3.metric("Position", position)

st.subheader("Multi Time Frame Analysis")

table = pd.DataFrame({
    "Timeframe": ["30 Minute", "1 Hour", "Daily"],
    "Score": [
        f'{m30["score"]}/5',
        f'{hourly["score"]}/5',
        f'{daily["score"]}/5'
    ],
    "RSI": [
        m30["rsi"],
        hourly["rsi"],
        daily["rsi"]
    ],
    "Close": [
        m30["close"],
        hourly["close"],
        daily["close"]
    ]
})

st.dataframe(table, use_container_width=True)

st.subheader("SOXL Daily Chart")

daily_df = load_daily()

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=daily_df.index,
    y=daily_df["Close"],
    mode="lines",
    name="SOXL"
))

st.plotly_chart(fig, use_container_width=True)

st.caption("V9 MTF Model | 30m + 1h + Daily | Refresh every 5 minutes")
