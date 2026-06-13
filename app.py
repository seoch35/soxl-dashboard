
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import plotly.graph_objects as go

st.set_page_config(page_title="SOXL Quant Pro V5", layout="wide")

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

def get_series(data,ticker,col):
    return data[ticker][col].dropna()

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

    out["MFI"]=ta.volume.money_flow_index(
        high,low,close,volume,window=14
    )

    out["VOL20"]=volume.rolling(20).mean()

    ichi=ta.trend.IchimokuIndicator(high,low)

    out["SPAN_A"]=ichi.ichimoku_a()
    out["SPAN_B"]=ichi.ichimoku_b()

    return out.dropna()

def score_to_position(score):
    if score >= 90:
        return 1.00,"100%"
    elif score >= 80:
        return 0.75,"75%"
    elif score >= 70:
        return 0.50,"50%"
    elif score >= 60:
        return 0.25,"25%"
    return 0.0,"0%"

def score_to_signal(score):
    if score >= 85:
        return "🚀 STRONG BUY"
    elif score >= 70:
        return "🟢 BUY"
    elif score >= 50:
        return "🟡 HOLD"
    elif score >= 30:
        return "🟠 SELL"
    return "🔴 STRONG SELL"

data=load_data()

soxl_raw=data["SOXL"]
soxx_raw=data["SOXX"]
nvda_raw=data["NVDA"]
amd_raw=data["AMD"]
qqq_raw=data["QQQ"]

soxl=build_indicators(soxl_raw)
soxx=build_indicators(soxx_raw)
nvda=build_indicators(nvda_raw)
amd=build_indicators(amd_raw)
qqq=build_indicators(qqq_raw)

s=soxl.iloc[-1]
x=soxx.iloc[-1]
n=nvda.iloc[-1]
a=amd.iloc[-1]
q=qqq.iloc[-1]

vix=float(get_series(data,"^VIX","Close").iloc[-1])
tnx=float(get_series(data,"^TNX","Close").iloc[-1])

score=0
reasons=[]

if s["Close"] > s["SMA20"]:
    score += 5
    reasons.append("SOXL > SMA20")

if s["SMA20"] > s["SMA50"]:
    score += 5
    reasons.append("SMA20 > SMA50")

if 50 < s["RSI"] < 70:
    score += 5
    reasons.append("RSI healthy")

if s["MACD"] > s["MACD_SIGNAL"]:
    score += 5
    reasons.append("MACD bullish")

if x["Close"] > x["SMA200"]:
    score += 15
    reasons.append("Semiconductor cycle bullish")

if n["Close"] > n["SMA50"]:
    score += 10
    reasons.append("NVDA bullish")

if a["Close"] > a["SMA50"]:
    score += 10
    reasons.append("AMD bullish")

if q["Close"] > q["SMA200"]:
    score += 15
    reasons.append("QQQ bullish")

if vix < 18:
    score += 15
    reasons.append("Low VIX")
elif vix < 25:
    score += 8

cloud_top=max(s["SPAN_A"],s["SPAN_B"])
if s["Close"] > cloud_top:
    score += 10
    reasons.append("Above Ichimoku Cloud")

if s["MFI"] > 50:
    score += 5
    reasons.append("Money inflow")

latest_vol=float(soxl_raw["Volume"].iloc[-1])
if latest_vol > s["VOL20"]:
    score += 5
    reasons.append("Volume expansion")

if tnx < 4.5:
    score += 10
    reasons.append("Rates supportive")
elif tnx > 4.8:
    score -= 10
    reasons.append("Rates restrictive")

score=max(0,min(score,100))

signal=score_to_signal(score)
alloc,position=score_to_position(score)

# Backtest
close=soxl_raw["Close"].dropna()
ret=close.pct_change().fillna(0)

rolling_score=pd.Series(index=close.index,dtype=float)

for dt in close.index:
    try:
        tmp=soxl.loc[:dt]
        row=tmp.iloc[-1]
        sc=0
        if row["Close"] > row["SMA20"]: sc+=5
        if row["SMA20"] > row["SMA50"]: sc+=5
        if 50 < row["RSI"] < 70: sc+=5
        if row["MACD"] > row["MACD_SIGNAL"]: sc+=5
        cloud=max(row["SPAN_A"],row["SPAN_B"])
        if row["Close"] > cloud: sc+=10
        if row["MFI"] > 50: sc+=5

        if sc >= 30:
            rolling_score.loc[dt]=90
        elif sc >= 20:
            rolling_score.loc[dt]=75
        elif sc >= 10:
            rolling_score.loc[dt]=60
        else:
            rolling_score.loc[dt]=0
    except:
        pass

weights=rolling_score.shift(1).fillna(0)

weights=weights.apply(
    lambda x: 1.0 if x>=90 else
    0.75 if x>=80 else
    0.50 if x>=70 else
    0.25 if x>=60 else
    0.0
)

strategy=(1+(ret*weights)).cumprod()
buyhold=(1+ret).cumprod()

strategy_return=(strategy.iloc[-1]-1)*100
buyhold_return=(buyhold.iloc[-1]-1)*100

roll_max=strategy.cummax()
drawdown=(strategy-roll_max)/roll_max
mdd=drawdown.min()*100

st.title("🚀 SOXL Quant Pro V5")

c1,c2,c3=st.columns(3)
c1.metric("Score",round(score,1))
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
    "Metric":["VIX","TNX","RSI","MFI"],
    "Value":[round(vix,2),round(tnx,2),
             round(float(s["RSI"]),2),
             round(float(s["MFI"]),2)]
})
st.dataframe(overview,use_container_width=True)

st.subheader("Signal Reasons")
for r in reasons:
    st.write("✅",r)

st.subheader("Backtest")

b1,b2,b3=st.columns(3)
b1.metric("Strategy Return %",round(strategy_return,2))
b2.metric("Buy & Hold %",round(buyhold_return,2))
b3.metric("Max Drawdown %",round(mdd,2))

bt=go.Figure()
bt.add_trace(go.Scatter(x=strategy.index,y=strategy,name="Strategy"))
bt.add_trace(go.Scatter(x=buyhold.index,y=buyhold,name="Buy & Hold"))
st.plotly_chart(bt,use_container_width=True)

st.subheader("SOXL Price")

fig=go.Figure()
fig.add_trace(go.Scatter(
    x=close.index,
    y=close.values,
    name="SOXL"
))
st.plotly_chart(fig,use_container_width=True)

st.caption("SOXL Quant Pro V5")
