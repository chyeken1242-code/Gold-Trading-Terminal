import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 页面布局优化，适配移动端
st.set_page_config(page_title="Vibe-Trading System", layout="wide")

st.title("🦅 Vibe-Trading 量化指挥终端")

# 1. 数据获取模块 (接入真实黄金期货数据)
@st.cache_data(ttl=60) # 每60秒缓存刷新一次
def get_gold_data():
    ticker = "GC=F" # 黄金期货代码
    data = yf.download(ticker, period="1d", interval="5m")
    return data

df = get_gold_data()

# 2. 核心计算 (波动率与风险指标)
current_price = df['Close'].iloc[-1]
price_change = current_price - df['Open'].iloc[0]
volatility = df['High'].iloc[-1] - df['Low'].iloc[-1]

# 3. 数据展示面板
col1, col2, col3 = st.columns(3)
col1.metric("XAUUSD 现价", f"${current_price:,.2f}", f"{price_change:,.2f}")
col2.metric("日内波动幅度", f"{volatility:.2f}")
col3.metric("市场信号", "NEUTRAL" if abs(price_change) < 5 else "TRENDING")

# 4. 图表可视化 (Plotly 渲染)
fig = go.Figure(data=[go.Candlestick(x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'])])
fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=30, b=0))
st.plotly_chart(fig, use_container_width=True)

# 5. 风控计算器
st.subheader("🛡️ Citadel 风控计算器")
capital = st.number_input("账户总资金 (USD)", value=10000)
risk = st.slider("单笔风险敞口 (%)", 0.1, 5.0, 1.0)
lots = (capital * (risk/100)) / (volatility * 100)
st.success(f"建议执行仓位: {lots:.2f} 手")
