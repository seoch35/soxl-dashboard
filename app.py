
# SOXL Quant Pro V13
# MTF + ATR + ADX + Ichimoku + Risk/Reward + MDD Backtest Summary

import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go

st.set_page_config(page_title="SOXL Quant Pro V13", layout="wide")

@st.cache_data(ttl=300)
def load(tf_period, interval=None):
    kwargs = dict(tickers="SOXL", period=tf_period, auto_adjust=True, progress=False)
    if interval:
        kwargs["interval"] = interval
    df = yf.download(**kwargs)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

def score_frame(df):
    c,h,l,v = df["Close"], df["High"], df["Low"], df["Volume"]

    ema20 = ta.trend.ema_indicator(c,20)
    ema50 = ta.trend.ema_indicator(c,50)
    rsi = ta.momentum.rsi(c,14)
    adx = ta.trend.adx(h,l,c,14)

    macd = ta.trend.MACD(c)
    ichi = ta.trend.IchimokuIndicator(h,l)

    score = 0
    if ema20.iloc[-1] > ema50.iloc[-1]: score += 2
    if macd.macd().iloc[-1] > macd.macd_signal().iloc[-1]: score += 2
    if rsi.iloc[-1] > 50: score += 1
    if adx.iloc[-1] > 25: score += 2

    cloud_top = max(ichi.ichimoku_a().iloc[-1], ichi.ichimoku_b().iloc[-1])
    if c.iloc[-1] > cloud_top: score += 2

    return score, float(rsi.iloc[-1]), float(adx.iloc[-1])

daily = load("3y")
hour = load("730d","1h")
m30 = load("60d","30m")

s_d,rsi_d,adx_d = score_frame(daily)
s_h,rsi_h,adx_h = score_frame(hour)
s_m,rsi_m,adx_m = score_frame(m30)

base = s_d+s_h+s_m

close = daily["Close"]
high = daily["High"]
low = daily["Low"]
volume = daily["Volume"]

ema20 = ta.trend.ema_indicator(close,20)
atr = ta.volatility.average_true_range(high,low,close,14)

current = float(close.iloc[-1])
entry = float(ema20.iloc[-1])

distance = ((current-entry)/entry)*100

penalty = 0
flags=[]

if rsi_d > 75:
    penalty += 2
    flags.append("RSI 과열")

if distance > 12:
    penalty += 2
    flags.append("EMA20 이격 과열")

if close.pct_change(5).iloc[-1]*100 > 15:
    penalty += 1
    flags.append("최근 5일 급등")

final_score = max(0, base-penalty)

if final_score >= 20:
    signal="🚀 STRONG BUY"; pos="100%"
elif final_score >= 15:
    signal="🟢 BUY"; pos="75%"
elif final_score >= 10:
    signal="🟡 HOLD"; pos="50%"
elif final_score >= 5:
    signal="🟠 SELL"; pos="25%"
else:
    signal="🔴 STRONG SELL"; pos="0%"

stop = round(current - 2*float(atr.iloc[-1]),2)
target = round(current + 4*float(atr.iloc[-1]),2)

# 간단 백테스트 성능 지표
ret = close.pct_change().dropna()
cum = (1+ret).cumprod()
mdd = ((cum/cum.cummax())-1).min()*100
cagr = ((cum.iloc[-1])**(252/len(ret))-1)*100

st.title("🚀 SOXL Quant Pro V13")

a,b,c = st.columns(3)
a.metric("Trend Score", f"{final_score}/21")
b.metric("Signal", signal)
c.metric("Position", pos)

st.subheader("Trading Plan")
x,y,z = st.columns(3)
x.metric("Preferred Entry", round(entry,2))
y.metric("Stop Loss", stop)
z.metric("Target", target)

st.subheader("MTF Analysis")
st.dataframe(pd.DataFrame({
    "Timeframe":["30m","1h","Daily"],
    "Score":[s_m,s_h,s_d],
    "RSI":[round(rsi_m,1),round(rsi_h,1),round(rsi_d,1)],
    "ADX":[round(adx_m,1),round(adx_h,1),round(adx_d,1)]
}), use_container_width=True)

st.subheader("Risk Filters")
if flags:
    for f in flags:
        st.write("⚠️", f)
else:
    st.write("✅ 과열 없음")

st.subheader("Backtest Summary")
k1,k2 = st.columns(2)
k1.metric("CAGR %", round(cagr,2))
k2.metric("Max Drawdown %", round(mdd,2))

fig = go.Figure()
fig.add_trace(go.Scatter(x=daily.index,y=close,name="SOXL"))
fig.add_trace(go.Scatter(x=daily.index,y=ema20,name="EMA20"))
st.plotly_chart(fig, use_container_width=True)
