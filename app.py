
import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go

st.set_page_config(page_title="SOXL Quant Pro V8", layout="wide")

@st.cache_data(ttl=3600)
def load_data():
    return yf.download(
        "SOXL",
        period="3y",
        auto_adjust=True,
        progress=False
    )

def build_indicators(df):
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    out = pd.DataFrame(index=df.index)

    out["Close"] = close
    out["EMA20"] = ta.trend.ema_indicator(close, 20)
    out["EMA60"] = ta.trend.ema_indicator(close, 60)

    out["RSI"] = ta.momentum.rsi(close, 14)

    macd = ta.trend.MACD(close)
    out["MACD"] = macd.macd()
    out["MACD_SIGNAL"] = macd.macd_signal()

    out["MFI"] = ta.volume.money_flow_index(
        high, low, close, volume, window=14
    )

    ichi = ta.trend.IchimokuIndicator(high, low)
    out["SPAN_A"] = ichi.ichimoku_a()
    out["SPAN_B"] = ichi.ichimoku_b()

    return out.dropna()

data = load_data()
ind = build_indicators(data)
s = ind.iloc[-1]

checks = []
score = 0

# 1. EMA Trend
ema_ok = s["EMA20"] > s["EMA60"]
checks.append(("EMA20 > EMA60", ema_ok))
if ema_ok:
    score += 1

# 2. RSI
rsi_ok = 50 <= s["RSI"] <= 70
checks.append(("RSI 50~70", rsi_ok))
if rsi_ok:
    score += 1

# 3. MACD
macd_ok = s["MACD"] > s["MACD_SIGNAL"]
checks.append(("MACD Bullish", macd_ok))
if macd_ok:
    score += 1

# 4. MFI
mfi_ok = s["MFI"] > 50
checks.append(("MFI > 50", mfi_ok))
if mfi_ok:
    score += 1

# 5. Cloud
cloud_top = max(s["SPAN_A"], s["SPAN_B"])
cloud_ok = s["Close"] > cloud_top
checks.append(("Above Ichimoku Cloud", cloud_ok))
if cloud_ok:
    score += 1

if score == 5:
    signal = "🚀 STRONG BUY"
    position = "100%"
elif score == 4:
    signal = "🟢 BUY"
    position = "75%"
elif score == 3:
    signal = "🟡 HOLD"
    position = "50%"
elif score == 2:
    signal = "🟠 SELL"
    position = "25%"
else:
    signal = "🔴 STRONG SELL"
    position = "0%"

st.title("🚀 SOXL Technical Signal V8")

c1, c2, c3 = st.columns(3)
c1.metric("Conditions Met", f"{score}/5")
c2.metric("Signal", signal)
c3.metric("Position", position)

st.subheader("Technical Checklist")

for name, passed in checks:
    st.write(("✅ " if passed else "❌ ") + name)

st.subheader("Current Indicators")

overview = pd.DataFrame({
    "Indicator": ["Close","EMA20","EMA60","RSI","MFI"],
    "Value": [
        round(float(s["Close"]),2),
        round(float(s["EMA20"]),2),
        round(float(s["EMA60"]),2),
        round(float(s["RSI"]),2),
        round(float(s["MFI"]),2)
    ]
})

st.dataframe(overview, use_container_width=True)

st.subheader("SOXL Price")

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=data.index,
        y=data["Close"],
        mode="lines",
        name="SOXL"
    )
)

fig.add_trace(
    go.Scatter(
        x=ind.index,
        y=ind["EMA20"],
        mode="lines",
        name="EMA20"
    )
)

fig.add_trace(
    go.Scatter(
        x=ind.index,
        y=ind["EMA60"],
        mode="lines",
        name="EMA60"
    )
)

st.plotly_chart(fig, use_container_width=True)

st.caption("V8 focuses on SOXL technical signals only.")
