import streamlit as st
import akshare as ak
import pandas as pd
import pandas_ta as ta
from openai import OpenAI
import time

# --- 1. 配置与初始化 ---
st.set_page_config(page_title="AI量化决策终端", layout="wide")
DEEPSEEK_KEY = "你的_DEEPSEEK_API_KEY" # 请替换为你的实际Key
client = OpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com")

# --- 2. 核心功能函数 ---

@st.cache_data(ttl=3600)
def fetch_base_data():
    """获取全市场行情快照"""
    df = ak.stock_zh_a_spot_em()
    return df

def analyze_k_and_backtest(code, days=5):
    """K线分析 + 简易回测"""
    try:
        # 获取历史K线
        hist = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq").tail(60)
        # 1. K线指标计算
        hist.ta.sma(length=5, append=True)
        hist.ta.sma(length=20, append=True)
        
        last = hist.iloc[-1]
        prev = hist.iloc[-2]
        
        # 形态判定
        pattern = "震荡"
        k_score = 50
        if prev['SMA_5'] < prev['SMA_20'] and last['SMA_5'] > last['SMA_20']:
            pattern = "金叉突破"
            k_score = 90
        elif last['SMA_5'] > last['SMA_20']:
            pattern = "上升趋势"
            k_score = 75
            
        # 2. 回测：计算过去5日收益
        price_past = hist.iloc[-(days+1)]['收盘']
        price_now = last['收盘']
        yield_rate = round(((price_now - price_past) / price_past) * 100, 2)
        
        return pattern, k_score, yield_rate
    except:
        return "数据不足", 50, 0.0

def get_ai_prediction(name, news_list):
    """DeepSeek 情感建模"""
    if not news_list: return "中性", 50
    prompt = f"分析股票 {name} 的新闻并判断明天表现。新闻：{str(news_list[:3])}。只输出：[利好/利空/中性] + 分数(0-100)"
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        res = response.choices[0].message.content
        return res, 80 if "利好" in res else 40
    except:
        return "AI连接超时", 50

# --- 3. Streamlit 界面 ---
st.title("🛡️ A股智能量化预测终端 (2026版)")
st.sidebar.header("参数配置")
target_n = st.sidebar.slider("扫描资金流入前 N 名", 5, 50, 10)

if st.button("🔥 执行全自动决策扫描"):
    with st.spinner("正在穿透市场数据并调用 DeepSeek AI..."):
        # 第一层：资金面初筛
        df_funds = ak.stock_individual_fund_flow_rank(symbol="今日").head(target_n)
        
        final_recommendations = []
        progress = st.progress(0)
        
        for i, row in df_funds.iterrows():
            code, name = row['代码'], row['名称']
            
            # 第二层：K线与回测
            k_pattern, k_score, history_yield = analyze_k_and_backtest(code)
            
            # 第三层：AI 新闻研判
            news_df = ak.stock_news_em(symbol=code)
            ai_opinion, ai_score = get_ai_opinion(name, news_df['新闻标题'].tolist())
            
            # 第四层：综合决策引擎 (预测逻辑)
            # 综合评分 = 资金强度 + K线分 + AI分
            fund_intensity = (row['主力净流入-净额'] / row['成交额']) * 100 if row['成交额'] > 0 else 0
            predict_score = (fund_intensity * 2) + (k_score * 0.4) + (ai_score * 0.4)
            
            final_recommendations.append({
                "股票": f"{name}({code})",
                "主力净流入": f"{row['主力净流入-净额']/10000:.0f}万",
                "K线形态": k_pattern,
                "近5日胜率(回测)": f"{history_yield}%",
                "AI 诊断": ai_opinion,
                "明日预测分": round(predict_score, 1)
            })
            progress.progress((i + 1) / target_n)
            time.sleep(0.5) # 频率限制
            
        # --- 展示预测结果 ---
        st.success("扫描完成！以下是基于多因子模型的明日买入潜力预测：")
        result_df = pd.DataFrame(final_recommendations).sort_values(by="明日预测分", ascending=False)
        
        # 结果高亮展示
        st.table(result_df)
        
        st.balloons()
