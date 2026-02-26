import streamlit as st
import akshare as ak
import pandas as pd
import pandas_ta as ta
from openai import OpenAI
import time

# --- 1. 页面配置 ---
st.set_page_config(page_title="AI量化决策终端", layout="wide")

# 侧边栏配置 API Key
st.sidebar.header("🔑 接口配置")
DEEPSEEK_KEY = st.sidebar.text_input("DeepSeek API Key", type="password")

client = None
if DEEPSEEK_KEY:
    client = OpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com")

# --- 2. 核心分析函数 ---

def analyze_k_and_backtest(code, days=5):
    """K线技术分析与回测收益"""
    try:
        # 统一代码格式，去掉可能存在的后缀
        symbol = "".join(filter(str.isdigit, code))
        hist = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq").tail(60)
        
        if hist.empty or len(hist) < 20:
            return "数据不足", 50, 0.0
        
        # 计算技术指标 (使用 pandas_ta)
        hist['SMA_5'] = ta.sma(hist['收盘'], length=5)
        hist['SMA_20'] = ta.sma(hist['收盘'], length=20)
        
        last = hist.iloc[-1]
        prev = hist.iloc[-2]
        
        # 趋势判定逻辑
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
            
        # 简易回测收益计算
        price_past = hist.iloc[-(days+1)]['收盘']
        price_now = last['收盘']
        yield_rate = round(((price_now - price_past) / price_past) * 100, 2)
        
        return pattern, k_score, yield_rate
    except Exception:
        return "分析失败", 50, 0.0

def get_ai_opinion(name, news_list):
    """DeepSeek AI 语义研判"""
    if not client:
        return "未配置AI Key", 50
    if not news_list:
        return "暂无相关新闻", 50
    
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
    except Exception:
        return "AI调用异常", 50

# --- 3. 主界面显示 ---
st.title("🛡️ A股智能量化预测终端")
st.info("数据分析流程：资金流初筛 -> K线形态确认 -> AI情绪诊断 -> 收益回测验证")

target_n = st.sidebar.slider("初筛股票数量", 5, 30, 10)

if st.button("🔥 开始全自动策略扫描"):
    if not DEEPSEEK_KEY:
        st.error("❌
