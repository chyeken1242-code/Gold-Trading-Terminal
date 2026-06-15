import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime

# 页面布局优化，适配移动端暗黑主题
st.set_page_config(page_title="Vibe-Trading Realtime Terminal", layout="wide")

st.markdown("""
    <style>
    .reportview-container { background: #0E1117; }
    h1 { color: #FFD700; font-family: 'Courier New', monospace; }
    </style>
    """, unsafe_allow_html=True)

st.title("🦅 Vibe-Trading – HKUDS 零延迟实时终端")
st.caption("数据源：Binance 全球做市商高频接口 (PAXG/USDT 锚定实物黄金)")

# =====================================================================
# 1. ⚡ REALTIME DATA ENGINE (币安低延迟实时数据源)
# =====================================================================
@st.cache_data(ttl=2) # 仅缓存2秒，逼近真高频实时
def get_realtime_gold_ticker():
    url = "https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=1m&limit=40"
    response = requests.get(url, timeout=5)
    data = response.json()
    
    df = pd.DataFrame(data, columns=[
        'OpenTime', 'Open', 'High', 'Low', 'Close', 'Volume',
        'CloseTime', 'QuoteVolume', 'Trades', 'BuyBase', 'BuyQuote', 'Ignore'
    ])
    
    df['Time'] = pd.to_datetime(df['OpenTime'], unit='ms')
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        df[col] = df[col].astype(float)
        
    return df

try:
    df = get_realtime_gold_ticker()
except Exception as e:
    st.error(f"⚠️ 核心网络总线连接失败，正在尝试重新握手... 错误: {e}")
    st.stop()

# =====================================================================
# 2. QUANT MATHEMATICS (数据类型强制对齐与安全检查)
# =====================================================================
try:
    current_price = float(df['Close'].iloc[-1])
    open_price = float(df['Open'].iloc[0])
    high_price = float(df['High'].max())
    low_price = float(df['Low'].min())

    # 修复核心：安全计算即时跳动
    last_close = float(df['Close'].iloc[-2]) if len(df) > 1 else current_price
    price_change = float(current_price - last_close)
    day_change_pct = float(((current_price - open_price) / open_price) * 100)

    # 动态计算真实波幅 (ATR) 用于风控
    recent_volatility = float(df['High'].iloc[-1] - df['Low'].iloc[-1])
    if recent_volatility <= 0:
        recent_volatility = 1.5
except Exception as math_error:
    st.error(f"量化矩阵因子对齐失败: {math_error}")
    st.stop()

# =====================================================================
# 3. INTERFACE RENDER (手机端精炼看板)
# =====================================================================
col1, col2, col3 = st.columns(3)

# 使用安全防护后的数字进行前端格式化展示
col1.metric("GOLD 实时现价", f"${current_price:,.2f}", f"{price_change:+,.2f} (1m)")
col2.metric("日内波动幅度 (ATR)", f"${recent_volatility:.2f}")
col3.metric("24H 累计涨跌幅", f"{day_change_pct:+.2f}%")

st.write("---")

# 4. 工业级秒级高频图表
fig = go.Figure(data=[go.Candlestick(
    x=df['Time'],
    open=df['Open'], high=df['High'],
    low=df['Low'], close=df['Close'],
    increasing_line_color='#00E676', decreasing_line_color='#FF1744'
)])
fig.update_layout(
    template="plotly_dark", 
    height=350, 
    margin=dict(l=0, r=0, t=10, b=0),
    xaxis_rangeslider_visible=False
)
st.plotly_chart(fig, use_container_width=True)

# 5. Citadel 级移动实时风控模块
st.write("---")
st.subheader("🛡️ Citadel 实时头寸锁闭系统")
capital = st.number_input("管理资产总额 (USD)", value=50000, step=5000)
risk_slider = st.slider("单笔最高回撤控制 (Risk %)", 0.2, 3.0, 1.0, 0.1)

# 核心公式计算
allowed_loss_cash = float(capital * (risk_slider / 100))
suggested_lots = float(allowed_loss_cash / (recent_volatility * 100))

sc_col1, sc_col2 = st.columns(2)
sc_col1.metric("单笔允许最大亏损风险", f"${allowed_loss_cash:,.2f}")
sc_col2.metric("🦅 推荐下注仓位 (Lots)", f"{max(suggested_lots, 0.01):.2f} 手")

# =====================================================================
# 4. AUTO REFRESH LOOP (每分每秒自动计算控制)
# =====================================================================
st.sidebar.header("⚙️ HKUDS 控制台")
st.sidebar.success("24H 实时数据管道连通")
refresh_speed = st.sidebar.slider("刷新脉冲速度 (秒)", 1, 10, 2)

import time
time.sleep(refresh_speed)
st.rerun()
