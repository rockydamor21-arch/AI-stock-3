import streamlit as st
import akshare as ak
import pandas as pd
import pandas_ta as ta
from openai import OpenAI
import time
from datetime import datetime

# --- 1. 配置与初始化 ---
st.set_page_config(page_title="AI量化决策终端", layout="wide")

# 安全获取 API Key
DEEPSEEK_KEY = st.sidebar.text_input("输入 DeepSeek API Key", type="password")
client = None
if DEEPSEEK_KEY:
    client = OpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com")

# --- 2. 核心分析函数 ---

def analyze_k_and_backtest(code, days=5):
    """K线分析模块：识别趋势与计算回测收益"""
    try:
        # 统一代码格式
        symbol = code.replace("sh", "").replace("sz", "")
        hist = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq").tail(60)
        
        if hist.empty or len(hist) < 20:
            return "数据不足", 50, 0.0
        
        # 计算技术指标
        hist['SMA_5'] = ta.sma(hist['收盘'], length=5)
        hist['SMA_20'] = ta.sma(hist['收盘'], length=20)
        
        last = hist.iloc[-1]
        prev = hist.iloc[-2]
        
        # 趋势判定
        pattern = "震荡"
        k_score = 50
        if prev['SMA_5'] < prev['SMA_20'] and last['SMA_5'] > last['SMA_20']:
            pattern = "🚀 均线金叉"
            k_score = 90
        elif last['SMA_5'] > last['SMA_20']:
            pattern = "📈 上升趋势"
            k_score = 75
        elif last['SMA_5'] < last['SMA_20']:
            pattern = "📉 下跌趋势"
            k_score = 30
            
        # 简易回测：计算过去N日收益
        price_past = hist.iloc[-(days+1)]['收盘']
        price_now = last['收盘']
        yield_rate = round(((price_now - price_past) / price_past) * 100, 2)
        
        return pattern, k_score, yield_rate
    except Exception as e:
        return f"分析出错", 50, 0.0

def get_ai_opinion(name, news_list):
    """DeepSeek AI 诊断模块"""
    if not client:
        return "未配置AI Key", 50
    if not news_list:
        return "暂无新闻", 50
    
    prompt = f"分析股票 {name} 的新闻并判断明天表现。新闻：{str(news_list[:3])}。只输出：[利好/利空/中性] + 理由(15字内)"
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        res = response.choices[0].message.content
        score = 80 if "利好" in res else (40 if "利空" in res else 50)
        return res, score
    except:
        return "AI连接超时", 50

# --- 3. Streamlit 界面 ---
st.title("🛡️ A股智能量化预测终端")
st.caption("集成：资金流向 + K线形态识别 + DeepSeek 语义分析 + 收益回测")

target_n = st.sidebar.slider("扫描资金流入前 N 名", 5, 30, 10)

if st.button("🔥 执行全自动决策扫描"):
    if not DEEPSEEK_KEY:
        st.error("请先在侧边栏输入 DeepSeek API Key")
        st.stop()

    with st.spinner("正在穿透市场数据并调用 DeepSeek AI..."):
        # --- 第一层：资金面数据获取 (带容错) ---
        try:
            df_funds = ak.stock_individual_fund_flow_rank(symbol="今日")
            if df_funds is None or df_funds.empty:
                st.warning("⚠️ 今日资金流接口无数据，切换至实时行情榜单...")
                df_funds = ak.stock_zh_a_spot_em().sort_values(
