import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go

st.set_page_config(page_title="SOXL Quant Pro V6", layout="wide")

TICKERS = ["SOXL","SOXX","NVDA","AMD","QQQ","^VIX","^TNX"]

@st.cache_data(ttl=3600)
def load_data():
    return yf.download(
        TICKERS,
        period="3y",
        auto_adjust=True,
        progress=False,
        group_by="ticker"
    )

def build_indicators(df):
    close=df["Close"]
    high=df["High"]
    low=df["Low"]
    volume=df["Volume"]

    out=pd.DataFrame(index=df.index)
    out["Close"]=close
    out["SMA20"]=ta.trend.sma_indicator(close,20)
    out["SMA50"]=ta.trend.sma_indicator(close,50)
    out["SMA200"]=ta.trend.sma_indicator(close,200)
    out["RSI"]=ta.momentum.rsi(close,14)

    macd=ta.trend.MACD(close)
    out["MACD"]=macd.macd()
    out["MACD_SIGNAL"]=macd.macd_signal()

    out["MFI"]=ta.volume.money_flow_index(high,low,close,volume,window=14)
    out["VOL20"]=volume.rolling(20).mean()

    ichi=ta.trend.IchimokuIndicator(high,low)
    out["SPAN_A"]=ichi.ichimoku_a()
    out["SPAN_B"]=ichi.ichimoku_b()

    return out.dropna()

def signal_from_score(score):
    if score >= 85: return "🚀 STRONG BUY"
    if score >= 70: return "🟢 BUY"
    if score >= 50: return "🟡 HOLD"
    if score >= 30: return "🟠 SELL"
    return "🔴 STRONG SELL"

def position_from_score(score):
    if score >= 90: return "100%"
    if score >= 80: return "75%"
    if score >= 70: return "50%"
    if score >= 60: return "25%"
    return "0%"

data=load_data()

soxl=build_indicators(data["SOXL"])
soxx=build_indicators(data["SOXX"])
nvda=build_indicators(data["NVDA"])
amd=build_indicators(data["AMD"])
qqq=build_indicators(data["QQQ"])

s=soxl.iloc[-1]
x=soxx.iloc[-1]
n=nvda.iloc[-1]
a=amd.iloc[-1]
q=qqq.iloc[-1]

vix=float(data["^VIX"]["Close"].dropna().iloc[-1])
tnx=float(data["^TNX"]["Close"].dropna().iloc[-1])

raw_score=0
reasons=[]

if s["Close"] > s["SMA20"]:
    raw_score += 5
    reasons.append("SOXL > SMA20")

if s["SMA20"] > s["SMA50"]:
    raw_score += 5
    reasons.append("상승 추세")

if 50 < s["RSI"] < 70:
    raw_score += 5
    reasons.append("RSI 양호")

if s["MACD"] > s["MACD_SIGNAL"]:
    raw_score += 5
    reasons.append("MACD 상승")

if x["Close"] > x["SMA200"]:
    raw_score += 12
    reasons.append("반도체 업사이클")

if n["Close"] > n["SMA50"]:
    raw_score += 8
    reasons.append("NVDA 강세")

if a["Close"] > a["SMA50"]:
    raw_score += 5
    reasons.append("AMD 강세")

if q["Close"] > q["SMA200"]:
    raw_score += 12
    reasons.append("QQQ 강세")

if vix < 18:
    raw_score += 12
    reasons.append("VIX 안정")
elif vix < 25:
    raw_score += 6

cloud=max(s["SPAN_A"],s["SPAN_B"])
if s["Close"] > cloud:
    raw_score += 15
    reasons.append("구름대 상단")

if s["MFI"] > 50:
    raw_score += 6
    reasons.append("자금 유입")

if float(data["SOXL"]["Volume"].iloc[-1]) > s["VOL20"]:
    raw_score += 5
    reasons.append("거래량 증가")

if tnx < 4.5:
    raw_score += 10
    reasons.append("금리 우호")
elif tnx > 4.8:
    raw_score -= 10
    reasons.append("금리 부담")

# 내부 백테스트 검증 (간략)
close=data["SOXL"]["Close"].dropna()
bh=(close.iloc[-1]/close.iloc[0])-1

if bh > 0.5:
    raw_score += 5

MAX_SCORE=95
score=round(max(0,min((raw_score/MAX_SCORE)*100,100)),1)

signal=signal_from_score(score)
position=position_from_score(score)

st.title("🚀 SOXL Quant Pro V6")

c1,c2,c3=st.columns(3)
c1.metric("Score",score)
c2.metric("Signal",signal)
c3.metric("Position",position)

gauge=go.Figure(go.Indicator(
    mode="gauge+number",
    value=score,
    title={"text":"Market Score"},
    gauge={"axis":{"range":[0,100]}}
))
st.plotly_chart(gauge,use_container_width=True)

st.subheader("Market Overview")

overview=pd.DataFrame({
    "Metric":["SOXL","VIX","TNX","RSI","MFI"],
    "Value":[
        round(float(s["Close"]),2),
        round(vix,2),
        round(tnx,2),
        round(float(s["RSI"]),2),
        round(float(s["MFI"]),2)
    ]
})

st.dataframe(overview,use_container_width=True)

st.subheader("Signal Reasons")
for r in reasons:
    st.write("✅",r)

st.subheader("SOXL Price")

fig=go.Figure()
fig.add_trace(go.Scatter(
    x=close.index,
    y=close.values,
    mode="lines",
    name="SOXL"
))
st.plotly_chart(fig,use_container_width=True)

st.caption("SOXL Quant Pro V6")
