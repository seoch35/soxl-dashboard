import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go

st.set_page_config(page_title="SOXL Quant Pro V7", layout="wide")

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

def build(df):
    c=df["Close"]
    h=df["High"]
    l=df["Low"]
    v=df["Volume"]

    x=pd.DataFrame(index=df.index)
    x["Close"]=c
    x["SMA20"]=ta.trend.sma_indicator(c,20)
    x["SMA50"]=ta.trend.sma_indicator(c,50)
    x["SMA200"]=ta.trend.sma_indicator(c,200)

    x["RSI"]=ta.momentum.rsi(c,14)

    macd=ta.trend.MACD(c)
    x["MACD"]=macd.macd()
    x["MACD_SIGNAL"]=macd.macd_signal()

    x["MFI"]=ta.volume.money_flow_index(h,l,c,v,14)
    x["VOL20"]=v.rolling(20).mean()

    ichi=ta.trend.IchimokuIndicator(h,l)
    x["SPAN_A"]=ichi.ichimoku_a()
    x["SPAN_B"]=ichi.ichimoku_b()

    return x.dropna()

def signal(score):
    if score >= 90:
        return "🚀 STRONG BUY"
    elif score >= 80:
        return "🟢 BUY"
    elif score >= 60:
        return "🟡 HOLD"
    elif score >= 40:
        return "🟠 SELL"
    else:
        return "🔴 STRONG SELL"

def position(score):
    if score >= 90:
        return "100%"
    elif score >= 80:
        return "75%"
    elif score >= 70:
        return "50%"
    elif score >= 60:
        return "25%"
    return "0%"

data=load_data()

soxl=build(data["SOXL"])
soxx=build(data["SOXX"])
nvda=build(data["NVDA"])
amd=build(data["AMD"])
qqq=build(data["QQQ"])

s=soxl.iloc[-1]
x=soxx.iloc[-1]
n=nvda.iloc[-1]
a=amd.iloc[-1]
q=qqq.iloc[-1]

vix=float(data["^VIX"]["Close"].dropna().iloc[-1])
tnx=float(data["^TNX"]["Close"].dropna().iloc[-1])

score=50
reasons=[]

# SOXL trend
if s["Close"] > s["SMA20"]:
    score += 5
    reasons.append("SOXL > SMA20")
else:
    score -= 5

if s["SMA20"] > s["SMA50"]:
    score += 5
    reasons.append("SMA20 > SMA50")
else:
    score -= 5

# RSI
if 50 <= s["RSI"] <= 70:
    score += 5
    reasons.append("Healthy RSI")
elif s["RSI"] > 75:
    score -= 8
    reasons.append("Overbought RSI")
elif s["RSI"] < 40:
    score -= 10
    reasons.append("Weak RSI")

# MACD
if s["MACD"] > s["MACD_SIGNAL"]:
    score += 5
    reasons.append("MACD Bullish")
else:
    score -= 5

# SOXX
if x["Close"] > x["SMA200"]:
    score += 8
    reasons.append("SOXX Bull Market")
else:
    score -= 8

# NVDA
if n["Close"] > n["SMA50"]:
    score += 5
else:
    score -= 5

# AMD
if a["Close"] > a["SMA50"]:
    score += 3
else:
    score -= 3

# QQQ
if q["Close"] > q["SMA200"]:
    score += 8
else:
    score -= 8

# VIX
if vix < 15:
    score -= 3
    reasons.append("Too much optimism")
elif vix < 18:
    score += 5
elif vix > 25:
    score -= 15
    reasons.append("High fear")

# TNX
if tnx < 4.2:
    score += 8
    reasons.append("Friendly rates")
elif tnx > 4.8:
    score -= 10
    reasons.append("High rates")

# Ichimoku
cloud=max(s["SPAN_A"],s["SPAN_B"])

if s["Close"] > cloud:
    score += 10
    reasons.append("Above Cloud")
else:
    score -= 10
    reasons.append("Below Cloud")

# MFI
if s["MFI"] > 60:
    score += 5
elif s["MFI"] < 40:
    score -= 5

# Volume
latest_vol=float(data["SOXL"]["Volume"].iloc[-1])

if latest_vol > s["VOL20"]:
    score += 3
    reasons.append("Volume Expansion")

score=max(0,min(score,100))

sig=signal(score)
pos=position(score)

st.title("🚀 SOXL Quant Pro V7")

c1,c2,c3=st.columns(3)
c1.metric("Score", round(score,1))
c2.metric("Signal", sig)
c3.metric("Position", pos)

gauge=go.Figure(go.Indicator(
    mode="gauge+number",
    value=score,
    title={"text":"Market Score"},
    gauge={"axis":{"range":[0,100]}}
))
st.plotly_chart(gauge,use_container_width=True)

overview=pd.DataFrame({
    "Metric":["SOXL","RSI","MFI","VIX","TNX"],
    "Value":[
        round(float(s["Close"]),2),
        round(float(s["RSI"]),2),
        round(float(s["MFI"]),2),
        round(vix,2),
        round(tnx,2)
    ]
})

st.subheader("Market Overview")
st.dataframe(overview,use_container_width=True)

st.subheader("Signal Reasons")
for r in reasons:
    st.write("✅",r)

fig=go.Figure()
fig.add_trace(go.Scatter(
    x=data["SOXL"]["Close"].index,
    y=data["SOXL"]["Close"].values,
    mode="lines",
    name="SOXL"
))

st.subheader("SOXL Price")
st.plotly_chart(fig,use_container_width=True)
