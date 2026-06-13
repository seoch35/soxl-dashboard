
import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go

st.set_page_config(page_title="SOXL Quant Pro V10", layout="wide")

@st.cache_data(ttl=300)
def load_tf(period, interval=None):
    kwargs = dict(tickers="SOXL", period=period, auto_adjust=True, progress=False)
    if interval:
        kwargs["interval"] = interval
    df = yf.download(**kwargs)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    return df.dropna()

def score_tf(df):
    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    vol = df["Volume"].astype(float)

    ema20 = ta.trend.ema_indicator(close, 20)
    ema60 = ta.trend.ema_indicator(close, 60)

    rsi = ta.momentum.rsi(close, 14)

    macd = ta.trend.MACD(close)
    macd_ok = macd.macd().iloc[-1] > macd.macd_signal().iloc[-1]

    mfi = ta.volume.money_flow_index(high, low, close, vol, window=14)

    ichi = ta.trend.IchimokuIndicator(high, low)
    cloud_ok = close.iloc[-1] > max(
        ichi.ichimoku_a().iloc[-1],
        ichi.ichimoku_b().iloc[-1]
    )

    score = 0

    if ema20.iloc[-1] > ema60.iloc[-1]:
        score += 2

    if macd_ok:
        score += 2

    if cloud_ok:
        score += 2

    if 50 <= rsi.iloc[-1] <= 75:
        score += 1

    if mfi.iloc[-1] > 50:
        score += 1

    return {
        "score": score,
        "close": float(close.iloc[-1]),
        "ema20": float(ema20.iloc[-1]),
        "rsi": float(rsi.iloc[-1]),
        "mfi": float(mfi.iloc[-1])
    }

daily_df = load_tf("3y")
hour_df = load_tf("730d", "1h")
m30_df = load_tf("60d", "30m")

daily = score_tf(daily_df)
hourly = score_tf(hour_df)
m30 = score_tf(m30_df)

base_score = daily["score"] + hourly["score"] + m30["score"]

# 과열 필터
penalty = 0
warnings = []

if daily["rsi"] > 75:
    penalty += 3
    warnings.append("RSI 과열")

if daily["mfi"] > 80:
    penalty += 2
    warnings.append("MFI 과열")

distance = ((daily["close"] - daily["ema20"]) / daily["ema20"]) * 100

if distance > 12:
    penalty += 3
    warnings.append("EMA20 대비 과도한 이격")

recent5 = daily_df["Close"].pct_change(5).iloc[-1] * 100

if recent5 > 15:
    penalty += 2
    warnings.append("최근 5일 급등")

final_score = max(0, base_score - penalty)

if final_score >= 16:
    signal = "🚀 STRONG BUY"
    position = "100%"
elif final_score >= 12:
    signal = "🟢 BUY"
    position = "75%"
elif final_score >= 8:
    signal = "🟡 HOLD"
    position = "50%"
elif final_score >= 4:
    signal = "🟠 SELL"
    position = "25%"
else:
    signal = "🔴 STRONG SELL"
    position = "0%"

st.title("🚀 SOXL Quant Pro V10")

c1, c2, c3 = st.columns(3)
c1.metric("Trend Score", f"{final_score}/18")
c2.metric("Signal", signal)
c3.metric("Position", position)

st.subheader("MTF Trend")

mtf = pd.DataFrame({
    "Timeframe":["30m","1h","Daily"],
    "Score":[m30["score"], hourly["score"], daily["score"]],
    "RSI":[round(m30["rsi"],1), round(hourly["rsi"],1), round(daily["rsi"],1)]
})

st.dataframe(mtf, use_container_width=True)

st.subheader("Overheat Filters")

if warnings:
    for w in warnings:
        st.write("⚠️", w)
else:
    st.write("✅ 과열 신호 없음")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=daily_df.index,
    y=daily_df["Close"],
    name="SOXL"
))

st.plotly_chart(fig, use_container_width=True)

st.caption("V10 | MTF + Overheat Filter")
