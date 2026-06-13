
import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go

st.set_page_config(page_title="SOXL Quant Pro V8.1", layout="wide")

@st.cache_data(ttl=3600)
def load_data():
    df = yf.download(
        "SOXL",
        period="3y",
        auto_adjust=True,
        progress=False
    )

    # yfinance 반환형 정규화
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    return df.dropna()

def build_indicators(df):
    close = pd.Series(df["Close"]).astype(float)
    high = pd.Series(df["High"]).astype(float)
    low = pd.Series(df["Low"]).astype(float)
    volume = pd.Series(df["Volume"]).astype(float)

    out = pd.DataFrame(index=df.index)

    out["Close"] = close
    out["EMA20"] = ta.trend.ema_indicator(close, window=20)
    out["EMA60"] = ta.trend.ema_indicator(close, window=60)

    out["RSI"] = ta.momentum.rsi(close, window=14)

    macd = ta.trend.MACD(close)
    out["MACD"] = macd.macd()
    out["MACD_SIGNAL"] = macd.macd_signal()

    out["MFI"] = ta.volume.money_flow_index(
        high, low, close, volume, window=14
    )

    ichi = ta.trend.IchimokuIndicator(high=high, low=low)
    out["SPAN_A"] = ichi.ichimoku_a()
    out["SPAN_B"] = ichi.ichimoku_b()

    out["HIGH_20"] = close.rolling(20).max()
    out["LOW_20"] = close.rolling(20).min()

    return out.dropna()

data = load_data()
ind = build_indicators(data)

last = ind.iloc[-1]

conditions = []

ema_ok = last["EMA20"] > last["EMA60"]
conditions.append(("EMA20 > EMA60", ema_ok))

rsi_ok = 50 <= last["RSI"] <= 70
conditions.append(("RSI 50~70", rsi_ok))

macd_ok = last["MACD"] > last["MACD_SIGNAL"]
conditions.append(("MACD Bullish", macd_ok))

mfi_ok = last["MFI"] > 50
conditions.append(("MFI > 50", mfi_ok))

cloud_top = max(last["SPAN_A"], last["SPAN_B"])
cloud_ok = last["Close"] > cloud_top
conditions.append(("Above Ichimoku Cloud", cloud_ok))

breakout_ok = last["Close"] >= last["HIGH_20"] * 0.99
conditions.append(("20-Day Breakout", breakout_ok))

score = sum(1 for _, ok in conditions if ok)

if score >= 6:
    signal = "🚀 STRONG BUY"
    position = "100%"
elif score >= 5:
    signal = "🟢 BUY"
    position = "75%"
elif score >= 3:
    signal = "🟡 HOLD"
    position = "50%"
elif score >= 2:
    signal = "🟠 SELL"
    position = "25%"
else:
    signal = "🔴 STRONG SELL"
    position = "0%"

st.title("🚀 SOXL Technical Signal V8.1")

c1, c2, c3 = st.columns(3)
c1.metric("Technical Score", f"{score}/6")
c2.metric("Signal", signal)
c3.metric("Suggested Position", position)

st.subheader("Technical Conditions")

for name, ok in conditions:
    st.write(("✅ " if ok else "❌ ") + name)

st.subheader("Indicator Snapshot")

snap = pd.DataFrame({
    "Metric":[
        "Close","EMA20","EMA60","RSI","MFI"
    ],
    "Value":[
        round(float(last["Close"]),2),
        round(float(last["EMA20"]),2),
        round(float(last["EMA60"]),2),
        round(float(last["RSI"]),2),
        round(float(last["MFI"]),2)
    ]
})

st.dataframe(snap, use_container_width=True)

st.subheader("SOXL Price & Trend")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=data.index,
    y=data["Close"],
    mode="lines",
    name="SOXL"
))

fig.add_trace(go.Scatter(
    x=ind.index,
    y=ind["EMA20"],
    mode="lines",
    name="EMA20"
))

fig.add_trace(go.Scatter(
    x=ind.index,
    y=ind["EMA60"],
    mode="lines",
    name="EMA60"
))

st.plotly_chart(fig, use_container_width=True)

st.caption("SOXL Technical Trading Model V8.1")
