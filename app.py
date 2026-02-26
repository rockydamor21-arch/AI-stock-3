import streamlit as st
import akshare as ak
import pandas as pd
import pandas_ta as ta
from openai import OpenAI
import time
import requests

# --- 1. 页面配置 ---
st.set_page_config(page_title="AI量化决策终端", layout="wide")

st.sidebar.header("🔑 接口配置")
DEEPSEEK_KEY = st.sidebar.text_input("DeepSeek API Key", type="password")

client = None
if DEEPSEEK_KEY:
    client = OpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com")

# --- 2. 核心分析函数 ---

def analyze_k_and_backtest(code, days=5):
    try:
        symbol = "".join(filter(str.isdigit, str(code)))
        # 增加容错：如果 hist 接口被封，这里会报错并返回
        hist = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq").tail(60)
        
        if hist.empty or len(hist) < 20:
            return "数据不足", 50, 0.0
        
        hist['SMA_5'] = ta.sma(hist['收盘'], length=5)
        hist['SMA_20'] = ta.sma(hist['收盘'], length=20)
        
        last = hist.iloc[-1]
        prev = hist.iloc[-2]
        
        pattern = "震荡"
        k_score = 50
        if prev['SMA_5'] < prev['SMA_20'] and last['SMA_5'] > last['SMA_20']:
            pattern = "🚀 均线金叉"
            k_score = 90
        elif last['SMA_5'] > last['SMA_20']:
            pattern = "📈 上升趋势"
            k_score = 75
            
        price_past = hist.iloc[-(days+1)]['收盘']
        price_now = last['收盘']
        yield_rate = round(((price_now - price_past) / price_past) * 100, 2)
        
        return pattern, k_score, yield_rate
    except:
        return "网络波动", 50, 0.0

def get_ai_opinion(name, news_list):
    if not client: return "未配置AI Key", 50
    if not news_list: return "暂无新闻", 50
    
    prompt = f"分析股票 {name} 的新闻。新闻：{str(news_list[:3])}。只输出：[利好/利空/中性] + 理由(15字内)"
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
        return "AI调用异常", 50

# --- 3. 主界面 ---
st.title("🛡️ A股智能量化预测终端")

target_n = st.sidebar.slider("初筛股票数量", 5, 20, 10)

if st.button("🔥 开始全自动策略扫描"):
    if not DEEPSEEK_KEY:
        st.error("❌ 请先输入 DeepSeek API Key")
    else:
        with st.spinner("🔍 正在穿透网络获取数据..."):
            try:
                # 针对 RemoteDisconnected 增加重试逻辑
                success = False
                retries = 3
                while retries > 0 and not success:
                    try:
                        df_funds = ak.stock_individual_fund_flow_rank()
                        if df_funds is not None: success = True
                    except:
                        retries -= 1
                        time.sleep(2) # 停顿2秒再试
                
                if not success:
                    st.error("🚫 数据源连接被切断。原因：您的服务器 IP 可能被封锁（常见于 Streamlit Cloud）。建议在本地运行此程序。")
                    st.stop()

                candidates = df_funds.head(target_n)
                final_list = []
                progress_bar = st.progress(0)
                
                for i, row in enumerate(candidates.to_dict('records')):
                    code, name = str(row.get('代码')), str(row.get('名称'))
                    
                    k_pattern, k_score, history_yield = analyze_k_and_backtest(code)
                    
                    try:
                        news_df = ak.stock_news_em(symbol=code)
                        news_titles = news_df['新闻标题'].tolist() if not news_df.empty else []
                    except:
                        news_titles = []
                    
                    ai_info, ai_score = get_ai_opinion(name, news_titles)
                    total_score = (k_score * 0.45) + (ai_score * 0.45) + 10 
                    
                    final_list.append({
                        "股票": f"{name} ({code})",
                        "K线形态": k_pattern,
                        "近5日收益率": f"{history_yield}%",
                        "AI 诊断结果": ai_info,
                        "明日预测分": round(total_score, 1)
                    })
                    progress_bar.progress((i + 1) / target_n)
                    time.sleep(0.5) # 增加延迟，降低封锁概率

                st.success("✅ 扫描完成！")
                result_df = pd.DataFrame(final_list).sort_values(by="明日预测分", ascending=False)
                st.dataframe(result_df, hide_index=True, use_container_width=True)

            except Exception as e:
                st.error(f"意外错误: {e}")

st.sidebar.markdown("---")
st.sidebar.caption("提示：如持续出现连接中断，请尝试在本地 Python 环境运行。")
