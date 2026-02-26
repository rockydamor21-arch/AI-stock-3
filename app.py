import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import anthropic
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="AI智能量化分析平台", page_icon="📈", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Serif SC', serif; background-color: #0a0e1a; color: #e0e6f0; }
.stApp { background-color: #0a0e1a; }
.score-high { color: #ff4d4d; font-weight: 700; font-size: 2.2em; }
.score-mid  { color: #ffd700; font-weight: 700; font-size: 2.2em; }
.score-low  { color: #4da6ff; font-weight: 700; font-size: 2.2em; }
.signal-bullish { background: rgba(255,77,77,0.15); border-left: 3px solid #ff4d4d; padding: 8px 12px; border-radius: 4px; margin: 4px 0; }
.signal-bearish { background: rgba(77,166,255,0.15); border-left: 3px solid #4da6ff; padding: 8px 12px; border-radius: 4px; margin: 4px 0; }
.signal-neutral { background: rgba(255,215,0,0.10); border-left: 3px solid #ffd700; padding: 8px 12px; border-radius: 4px; margin: 4px 0; }
.advice-box { background: linear-gradient(135deg,#0d1b2a,#0a1628); border: 1px solid #ffd700; border-radius: 12px; padding: 20px; margin: 10px 0; }
.ai-box { background: linear-gradient(135deg,#0d2a1b,#0a2010); border: 1px solid #00ff88; border-radius: 12px; padding: 20px; margin: 10px 0; line-height: 1.8; }
.pattern-box { background: rgba(255,215,0,0.08); border: 1px solid #ffd700; border-radius: 8px; padding: 10px 14px; margin: 4px 0; }
.stButton > button { background: linear-gradient(135deg,#c0392b,#e74c3c); color: white; border: none; border-radius: 8px; font-weight: 600; width: 100%; padding: 10px; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 📈 AI智能量化分析平台")
st.markdown("##### K线形态识别 · 技术指标 · 金叉死叉 · AI深度研判")
st.divider()

# ─── 预设股票 ──────────────────────────────────────────────
STOCKS = {
    "🇨🇳 贵州茅台": "600519.SS",
    "🇨🇳 平安银行": "000001.SZ",
    "🇨🇳 宁德时代": "300750.SZ",
    "🇨🇳 比亚迪":   "002594.SZ",
    "🇨🇳 招商银行": "600036.SS",
    "🇺🇸 英伟达":   "NVDA",
    "🇺🇸 苹果":     "AAPL",
    "🇺🇸 特斯拉":   "TSLA",
}

with st.sidebar:
    st.markdown("## ⚙️ 分析配置")
    st.markdown("**热门股票**")
    cols = st.columns(2)
    clicked_sym = None
    for i, (name, code) in enumerate(STOCKS.items()):
        if cols[i % 2].button(name, key=f"btn_{i}"):
            clicked_sym = code

    st.markdown("---")
    default = clicked_sym if clicked_sym else "NVDA"
    symbol_input = st.text_input("输入股票代码", value=default,
        help="美股：NVDA | 上证：600519.SS | 深证：000001.SZ")
    symbols = [s.strip().upper() for s in symbol_input.split(",") if s.strip()]

    period_map = {"近1月":"1mo","近3月":"3mo","近6月":"6mo"}
    period_label = st.selectbox("分析周期", list(period_map.keys()), index=1)
    period_str = period_map[period_label]

    invest_style = st.multiselect("投资风格", ["短线(1-5天)","中线(1-4周)"],
                                   default=["短线(1-5天)","中线(1-4周)"])

    api_key = st.text_input("Claude API Key（用于AI分析）", type="password",
        help="从 console.anthropic.com 获取，不填则跳过AI分析")

    run_btn = st.button("🚀 开始智能分析")

# ─── 数据获取 ─────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def get_data(symbol, period):
    try:
        t  = yf.Ticker(symbol)
        df = t.history(period=period, interval="1d", timeout=15)
        if df is None or len(df) < 5: return None, symbol
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        df = df[['Open','High','Low','Close','Volume']].copy()
        df.columns = ['open','high','low','close','volume']
        df = df.astype(float).dropna()
        try:
            info = t.info
            name = info.get('longName') or info.get('shortName') or symbol
        except:
            name = symbol
        return df, name
    except:
        return None, symbol

# ─── 技术指标 ─────────────────────────────────────────────────
def compute_indicators(df):
    c = df['close']; v = df['volume']; n = len(df)
    df['EMA5']  = ta.ema(c, length=min(5, n-1))
    df['EMA10'] = ta.ema(c, length=min(10,n-1))
    df['EMA20'] = ta.ema(c, length=min(20,n-1))
    df['EMA60'] = ta.ema(c, length=min(60,n-1))
    df['RSI']   = ta.rsi(c, length=min(14,n-1))
    if n >= 22:
        bb = ta.bbands(c, length=20, std=2)
        if bb is not None: df = pd.concat([df, bb], axis=1)
    if n >= 35:
        macd = ta.macd(c)
        if macd is not None: df = pd.concat([df, macd], axis=1)
    df['vol_ma5']  = v.rolling(min(5, n)).mean()
    df['vol_ma20'] = v.rolling(min(20,n)).mean()
    # KDJ
    if n >= 9:
        stoch = ta.stoch(df['high'], df['low'], c, k=9, d=3, smooth_k=3)
        if stoch is not None: df = pd.concat([df, stoch], axis=1)
    df.dropna(inplace=True)
    return df

# ─── K线形态识别 ──────────────────────────────────────────────
def detect_patterns(df):
    patterns = []
    if len(df) < 3: return patterns
    c = df['close'].values
    o = df['open'].values
    h = df['high'].values
    l = df['low'].values
    v = df['volume'].values
    vol_avg = df['volume'].tail(10).mean()

    # ── 均线金叉/死叉 ──
    if 'EMA5' in df.columns and 'EMA20' in df.columns:
        e5  = df['EMA5'].values
        e20 = df['EMA20'].values
        if len(e5) >= 2:
            if e5[-1] > e20[-1] and e5[-2] <= e20[-2]:
                patterns.append(("🌟 EMA5/20 金叉", "bullish", "短期均线上穿中期均线，买入信号"))
            elif e5[-1] < e20[-1] and e5[-2] >= e20[-2]:
                patterns.append(("💀 EMA5/20 死叉", "bearish", "短期均线下穿中期均线，卖出信号"))
            elif e5[-1] > e20[-1]:
                patterns.append(("✅ 均线多头", "bullish", "EMA5在EMA20上方，趋势偏多"))
            else:
                patterns.append(("⚠️ 均线空头", "bearish", "EMA5在EMA20下方，趋势偏空"))

    # ── MACD金叉/死叉 ──
    mh_c = [col for col in df.columns if 'MACDh' in col]
    ml_c = [col for col in df.columns if col.startswith('MACD_')]
    ms_c = [col for col in df.columns if col.startswith('MACDs')]
    if mh_c and ml_c and ms_c:
        macd_line = df[ml_c[0]].values
        signal    = df[ms_c[0]].values
        hist      = df[mh_c[0]].values
        if len(macd_line) >= 2:
            if macd_line[-1] > signal[-1] and macd_line[-2] <= signal[-2]:
                patterns.append(("🌟 MACD金叉", "bullish", "MACD线上穿信号线，强烈买入信号"))
            elif macd_line[-1] < signal[-1] and macd_line[-2] >= signal[-2]:
                patterns.append(("💀 MACD死叉", "bearish", "MACD线下穿信号线，强烈卖出信号"))
            if hist[-1] > 0 and hist[-1] > hist[-2]:
                patterns.append(("🔴 MACD红柱扩张", "bullish", "上涨动能持续增强"))
            elif hist[-1] < 0 and hist[-1] < hist[-2]:
                patterns.append(("🔵 MACD绿柱扩张", "bearish", "下跌动能持续增强"))

    # ── RSI背离 ──
    if 'RSI' in df.columns and len(df) >= 5:
        rsi_vals = df['RSI'].values
        rsi_now  = rsi_vals[-1]
        if rsi_now >= 70:
            patterns.append(("⚠️ RSI超买区", "neutral", f"RSI={rsi_now:.1f}，存在回调风险"))
        elif rsi_now <= 30:
            patterns.append(("🔥 RSI超卖区", "bullish", f"RSI={rsi_now:.1f}，超跌反弹机会"))

    # ── KDJ金叉/死叉 ──
    k_col = [col for col in df.columns if col.startswith('STOCHk')]
    d_col = [col for col in df.columns if col.startswith('STOCHd')]
    if k_col and d_col and len(df) >= 2:
        k = df[k_col[0]].values
        d = df[d_col[0]].values
        if k[-1] > d[-1] and k[-2] <= d[-2]:
            patterns.append(("🌟 KDJ金叉", "bullish", "K线上穿D线，短线买入信号"))
        elif k[-1] < d[-1] and k[-2] >= d[-2]:
            patterns.append(("💀 KDJ死叉", "bearish", "K线下穿D线，短线卖出信号"))
        if k[-1] < 20 and d[-1] < 20:
            patterns.append(("🔥 KDJ超卖", "bullish", f"K={k[-1]:.1f} D={d[-1]:.1f}，底部反弹信号"))
        elif k[-1] > 80 and d[-1] > 80:
            patterns.append(("⚠️ KDJ超买", "neutral", f"K={k[-1]:.1f} D={d[-1]:.1f}，高位注意风险"))

    # ── 量价形态 ──
    if v[-1] > vol_avg * 2:
        if c[-1] > c[-2]:
            patterns.append(("🚀 天量大阳线", "bullish", f"量比{v[-1]/vol_avg:.1f}x配合上涨，主力拉升"))
        else:
            patterns.append(("🚨 天量大阴线", "bearish", f"量比{v[-1]/vol_avg:.1f}x配合下跌，主力出货"))
    elif v[-1] < vol_avg * 0.5 and c[-1] > c[-2]:
        patterns.append(("🟡 缩量上涨", "neutral", "上涨缺乏量能支撑，谨慎追高"))

    # ── K线单根形态 ──
    body = abs(c[-1] - o[-1])
    total_range = h[-1] - l[-1]
    if total_range > 0:
        upper_shadow = h[-1] - max(c[-1], o[-1])
        lower_shadow = min(c[-1], o[-1]) - l[-1]
        # 十字星
        if body / total_range < 0.1:
            patterns.append(("✴️ 十字星", "neutral", "开收价接近，市场多空均衡，方向待定"))
        # 锤头线（下影线长）
        if lower_shadow > body * 2 and lower_shadow > upper_shadow * 2:
            patterns.append(("🔨 锤头线", "bullish", "长下影线显示下方有强支撑，可能反转向上"))
        # 射击之星（上影线长）
        if upper_shadow > body * 2 and upper_shadow > lower_shadow * 2:
            patterns.append(("⭐ 射击之星", "bearish", "长上影线显示上方压力强，可能转跌"))
        # 大阳线
        if c[-1] > o[-1] and body / total_range > 0.8:
            patterns.append(("🕯️ 大阳线", "bullish", "强势大阳，多方力量强劲"))
        # 大阴线
        if c[-1] < o[-1] and body / total_range > 0.8:
            patterns.append(("🕯️ 大阴线", "bearish", "强势大阴，空方占主导"))

    # ── 布林带突破 ──
    bbu_c = [col for col in df.columns if 'BBU' in col]
    bbl_c = [col for col in df.columns if 'BBL' in col]
    if bbu_c and bbl_c:
        bbu = df[bbu_c[0]].values[-1]
        bbl = df[bbl_c[0]].values[-1]
        if c[-1] > bbu:
            patterns.append(("🔴 突破布林上轨", "bullish", "强势突破，动能强劲，注意追高风险"))
        elif c[-1] < bbl:
            patterns.append(("🔵 跌破布林下轨", "bearish", "超卖区域，可能反弹但需确认"))

    # ── 头肩顶/底（简化识别） ──
    if len(df) >= 20:
        highs = df['high'].tail(20).values
        lows  = df['low'].tail(20).values
        mid   = len(highs) // 2
        # 头肩顶
        if highs[mid] > highs[:mid].max() and highs[mid] > highs[mid+1:].max():
            if abs(highs[:mid].max() - highs[mid+1:].max()) / highs[mid] < 0.05:
                patterns.append(("👑 疑似头肩顶", "bearish", "经典顶部形态，注意反转风险"))
        # 头肩底
        if lows[mid] < lows[:mid].min() and lows[mid] < lows[mid+1:].min():
            if abs(lows[:mid].min() - lows[mid+1:].min()) / max(abs(lows[mid]),0.01) < 0.05:
                patterns.append(("🏔️ 疑似头肩底", "bullish", "经典底部形态，可能反转向上"))

    return patterns

# ─── 综合评分 ─────────────────────────────────────────────────
def score_stock(df, patterns):
    if df is None or len(df) < 2: return None
    latest = df.iloc[-1]; prev = df.iloc[-2]
    close   = float(latest['close'])
    volume  = float(latest['volume'])
    vol_avg = float(df['volume'].tail(10).mean()) or 1
    score   = 50

    # 形态加分
    bullish_count = sum(1 for _, t, _ in patterns if t == 'bullish')
    bearish_count = sum(1 for _, t, _ in patterns if t == 'bearish')
    score += bullish_count * 5 - bearish_count * 5

    # 量能
    vr = volume / vol_avg
    if vr > 2:   score += 10
    elif vr > 1.5: score += 6
    elif vr < 0.6: score -= 3

    # RSI
    rsi = float(latest.get('RSI', 50))
    if 50 <= rsi < 70:   score += 5
    elif rsi >= 70:      score -= 5
    elif rsi <= 30:      score += 8

    pct = (close - float(prev['close'])) / float(prev['close']) * 100

    return {
        "score":      max(0, min(100, score)),
        "rsi":        rsi,
        "vol_ratio":  vr,
        "pct_change": pct,
        "close":      close,
        "df":         df,
    }

# ─── 投资建议 ─────────────────────────────────────────────────
def generate_advice(result, style):
    score = result['score']; close = result['close']; rsi = result['rsi']
    df    = result['df']
    sup   = round(float(df['low'].tail(20).min()) * 1.01, 2)
    advice = {}
    if "短线(1-5天)" in style:
        if score >= 68:
            advice['短线'] = {"操作":"🟢 积极做多","入场":f"现价{close:.2f}附近分2-3次建仓","目标":f"{round(close*1.05,2)} ~ {round(close*1.08,2)}","止损":f"跌破{round(close*0.96,2)}止损(-4%)","仓位":"30%~50%","理由":f"评分{score}分，多指标共振向上"}
        elif score >= 52:
            advice['短线'] = {"操作":"🟡 轻仓观察","入场":f"{round(close*0.98,2)}附近小仓试探","目标":f"{round(close*1.03,2)} ~ {round(close*1.05,2)}","止损":f"跌破{round(close*0.96,2)}止损","仓位":"10%~20%","理由":f"评分{score}分，等待更强确认"}
        else:
            advice['短线'] = {"操作":"🔴 回避观望","入场":"当前不建议买入","目标":"等待企稳信号","止损":f"持仓跌破{round(close*0.95,2)}止损","仓位":"0%","理由":f"评分{score}分，技术面偏弱"}
    if "中线(1-4周)" in style:
        if score >= 65 and rsi < 65:
            advice['中线'] = {"操作":"🟢 逢低布局","入场":f"{sup} ~ {close:.2f}分批建仓","目标":f"{round(close*1.10,2)} ~ {round(close*1.15,2)}","止损":f"跌破支撑{sup}止损","仓位":"20%~40%","理由":"趋势向上，RSI未超买"}
        elif score >= 50:
            advice['中线'] = {"操作":"🟡 持股观望","入场":"未持仓暂不追高","目标":f"{round(close*1.08,2)}","止损":f"跌破{sup}减仓","仓位":"维持现有","理由":"趋势中性，等待方向"}
        else:
            advice['中线'] = {"操作":"🔴 规避风险","入场":"不建议中线持有","目标":"等待底部确认","止损":f"持仓设{round(close*0.93,2)}止损","仓位":"0%~10%","理由":"中期趋势偏弱"}
    return advice

# ─── AI深度分析 ───────────────────────────────────────────────
def ai_analyze(api_key, sym, name, result, patterns, advice):
    try:
        client = anthropic.Anthropic(api_key=api_key)
        score    = result['score']
        rsi      = result['rsi']
        vr       = result['vol_ratio']
        pct      = result['pct_change']
        close    = result['close']
        df       = result['df']
        sup      = round(float(df['low'].tail(20).min()) * 1.01, 2)
        res_line = round(float(df['high'].tail(20).max()) * 0.99, 2)

        pattern_str = '\n'.join([f"- {p[0]}：{p[2]}" for p in patterns])
        advice_str  = '\n'.join([f"【{k}】{v['操作']} | 目标:{v['目标']} | 止损:{v['止损']}" for k,v in advice.items()])

        prompt = f"""你是一位拥有20年经验的专业股票分析师，请对以下股票进行全面深度分析，用中文输出专业报告。

## 股票信息
- 代码：{sym}
- 名称：{name}
- 当前价：{close:.2f}
- 今日涨跌：{pct:+.2f}%
- 量化评分：{score}/100
- RSI：{rsi:.1f}
- 量比：{vr:.2f}x
- 近期支撑位：{sup}
- 近期压力位：{res_line}

## 已识别技术形态
{pattern_str}

## 量化系统建议
{advice_str}

## 请输出以下内容（格式清晰，每部分加标题）：

### 一、综合研判
（2-3句话总结当前技术面状态，给出明确的多/空/中性判断）

### 二、短线操作策略（1-5天）
（具体入场价位区间、分批建仓策略、目标价位、止损位，以及操作的风险收益比）

### 三、中线趋势分析（1-4周）
（趋势方向判断、关键支撑压力位、持仓建议）

### 四、关键风险提示
（列出2-3个必须警惕的风险信号，触发哪些条件必须离场）

### 五、最终结论
（用一句话给出明确结论：强烈买入 / 买入 / 观望 / 减仓 / 卖出）"""

        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"AI分析失败：{str(e)}\n\n请检查API Key是否正确"

# ─── K线图绘制 ────────────────────────────────────────────────
def draw_kline(df, sym, name):
    has_macd = any('MACDh' in c for c in df.columns)
    has_kdj  = any('STOCHk' in c for c in df.columns)
    rows = 2 + (1 if has_macd else 0) + (1 if has_kdj else 0)
    heights = [0.5, 0.15] + ([0.18] if has_macd else []) + ([0.17] if has_kdj else [])

    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True,
                        vertical_spacing=0.02, row_heights=heights,
                        subplot_titles=["K线 + 均线 + 布林带", "成交量",
                                        *( ["MACD"] if has_macd else []),
                                        *( ["KDJ"]  if has_kdj  else [])])

    # K线
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'],
        increasing_line_color='#ff4d4d', decreasing_line_color='#4da6ff',
        increasing_fillcolor='#ff4d4d', decreasing_fillcolor='#4da6ff', name='K线'), row=1, col=1)

    # 均线
    for col, color, width in [('EMA5','#ffd700',1.5),('EMA10','#ff9500',1.2),('EMA20','#ff4dff',1.5),('EMA60','#4dffff',2)]:
        if col in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df[col], line=dict(color=color, width=width), name=col), row=1, col=1)

    # 布林带
    bbu_c = [c for c in df.columns if 'BBU' in c]
    bbl_c = [c for c in df.columns if 'BBL' in c]
    bbm_c = [c for c in df.columns if 'BBM' in c]
    if bbu_c and bbl_c:
        fig.add_trace(go.Scatter(x=df.index, y=df[bbu_c[0]], line=dict(color='rgba(200,200,255,0.4)', width=1, dash='dash'), name='布林上轨'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df[bbl_c[0]], line=dict(color='rgba(200,200,255,0.4)', width=1, dash='dash'), name='布林下轨', fill='tonexty', fillcolor='rgba(150,150,255,0.04)'), row=1, col=1)
        if bbm_c:
            fig.add_trace(go.Scatter(x=df.index, y=df[bbm_c[0]], line=dict(color='rgba(200,200,255,0.3)', width=1), name='布林中轨'), row=1, col=1)

    # 标注金叉死叉
    if 'EMA5' in df.columns and 'EMA20' in df.columns:
        for i in range(1, len(df)):
            e5_now  = df['EMA5'].iloc[i];  e5_prev  = df['EMA5'].iloc[i-1]
            e20_now = df['EMA20'].iloc[i]; e20_prev = df['EMA20'].iloc[i-1]
            if e5_prev <= e20_prev and e5_now > e20_now:
                fig.add_annotation(x=df.index[i], y=float(df['low'].iloc[i])*0.995,
                    text="金叉", showarrow=True, arrowhead=2, arrowcolor='#ffd700',
                    font=dict(color='#ffd700', size=11), ax=0, ay=20, row=1, col=1)
            elif e5_prev >= e20_prev and e5_now < e20_now:
                fig.add_annotation(x=df.index[i], y=float(df['high'].iloc[i])*1.005,
                    text="死叉", showarrow=True, arrowhead=2, arrowcolor='#4da6ff',
                    font=dict(color='#4da6ff', size=11), ax=0, ay=-20, row=1, col=1)

    # 成交量
    vc = ['#ff4d4d' if df['close'].iloc[i] >= df['open'].iloc[i] else '#4da6ff' for i in range(len(df))]
    fig.add_trace(go.Bar(x=df.index, y=df['volume'], marker_color=vc, name='成交量', opacity=0.7), row=2, col=1)
    if 'vol_ma5' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['vol_ma5'], line=dict(color='#ffd700', width=1.2), name='量5均'), row=2, col=1)
    if 'vol_ma20' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['vol_ma20'], line=dict(color='#ff9500', width=1.2), name='量20均'), row=2, col=1)

    row_idx = 3
    # MACD
    if has_macd:
        mh_c = [c for c in df.columns if 'MACDh' in c]
        ml_c = [c for c in df.columns if c.startswith('MACD_')]
        ms_c = [c for c in df.columns if c.startswith('MACDs')]
        mc   = ['#ff4d4d' if v >= 0 else '#4da6ff' for v in df[mh_c[0]]]
        fig.add_trace(go.Bar(x=df.index, y=df[mh_c[0]], marker_color=mc, name='MACD柱', opacity=0.8), row=row_idx, col=1)
        if ml_c: fig.add_trace(go.Scatter(x=df.index, y=df[ml_c[0]], line=dict(color='#ffd700', width=1.5), name='MACD'), row=row_idx, col=1)
        if ms_c: fig.add_trace(go.Scatter(x=df.index, y=df[ms_c[0]], line=dict(color='#ff9500', width=1.5), name='Signal'), row=row_idx, col=1)
        fig.add_hline(y=0, line_color='rgba(255,255,255,0.2)', line_width=1, row=row_idx, col=1)
        row_idx += 1

    # KDJ
    if has_kdj:
        k_c = [c for c in df.columns if 'STOCHk' in c]
        d_c = [c for c in df.columns if 'STOCHd' in c]
        if k_c: fig.add_trace(go.Scatter(x=df.index, y=df[k_c[0]], line=dict(color='#ffd700', width=1.5), name='K'), row=row_idx, col=1)
        if d_c: fig.add_trace(go.Scatter(x=df.index, y=df[d_c[0]], line=dict(color='#ff4dff', width=1.5), name='D'), row=row_idx, col=1)
        fig.add_hline(y=80, line_color='rgba(255,77,77,0.3)', line_width=1, row=row_idx, col=1)
        fig.add_hline(y=20, line_color='rgba(77,166,255,0.3)', line_width=1, row=row_idx, col=1)

    title_text = f"{name}（{sym}）" if name and name != sym else sym
    fig.update_layout(
        title=dict(text=title_text + " 技术分析图表", font=dict(size=16, color='#e0e6f0')),
        template="plotly_dark", paper_bgcolor='#0d1b2a', plot_bgcolor='#0a1020',
        xaxis_rangeslider_visible=False, height=750,
        legend=dict(orientation='h', y=1.02, font=dict(size=10)),
        margin=dict(l=50, r=20, t=80, b=20)
    )
    for i in range(1, rows+1):
        fig.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.04)', row=i, col=1)
        fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.04)', row=i, col=1)
    return fig

# ─── 主程序 ──────────────────────────────────────────────────
if run_btn:
    if not symbols:
        st.warning("请输入至少一个股票代码"); st.stop()

    # 多股榜单
    if len(symbols) > 1:
        st.markdown("## 📊 多股评分榜单")
        scan_results = []
        prog = st.progress(0, text="扫描中...")
        for i, sym in enumerate(symbols):
            prog.progress((i+1)/len(symbols), text=f"分析 {sym}...")
            df, name = get_data(sym, period_str)
            if df is not None and len(df) >= 5:
                df = compute_indicators(df)
                pts = detect_patterns(df)
                r   = score_stock(df, pts)
                if r:
                    adv = generate_advice(r, invest_style)
                    scan_results.append({
                        "代码": sym, "名称": (name[:12] if name and name != sym else sym),
                        "现价": round(r['close'], 2), "评分": r['score'],
                        "RSI": round(r['rsi'],1), "量比": f"{r['vol_ratio']:.2f}x",
                        "今日": f"{r['pct_change']:+.2f}%",
                        "形态": "、".join([p[0] for p in pts[:2]]) if pts else "-",
                        "建议": adv.get('短线',{}).get('操作','-')
                    })
        prog.empty()
        if scan_results:
            st.dataframe(pd.DataFrame(scan_results).sort_values("评分", ascending=False),
                         use_container_width=True, hide_index=True)

    # 逐股深度分析
    for sym in symbols:
        st.markdown("---")
        st.markdown(f"## 🔍 {sym} 完整分析报告")

        with st.spinner(f"获取 {sym} 数据中..."):
            df, name = get_data(sym, period_str)

        if df is None or len(df) < 5:
            st.error(f"**{sym}** 数据获取失败。美股直接用代码如 NVDA；A股上证用 600519.SS，深证用 000001.SZ")
            continue

        st.caption(f"✅ 获取 {len(df)} 条数据 | 最新：{df.index[-1].strftime('%Y-%m-%d')} | 收盘：{df['close'].iloc[-1]:.2f}")

        df       = compute_indicators(df)
        patterns = detect_patterns(df)
        result   = score_stock(df, patterns)

        if not result:
            st.error(f"{sym} 数据不足"); continue

        result['df'] = df
        advice = generate_advice(result, invest_style)
        score  = result['score']

        # 指标卡片
        c1,c2,c3,c4,c5 = st.columns(5)
        with c1: st.metric("股票", name[:10] if name and len(name)>2 else sym)
        with c2: st.metric("现价", f"{result['close']:.2f}", f"{result['pct_change']:+.2f}%")
        with c3:
            sc = "score-high" if score>=70 else "score-mid" if score>=50 else "score-low"
            st.markdown("**综合评分**")
            st.markdown(f"<span class='{sc}'>{score}</span>/100", unsafe_allow_html=True)
        with c4: st.metric("RSI", f"{result['rsi']:.1f}", "⚠️超买" if result['rsi']>70 else "🔥超卖" if result['rsi']<30 else "✅正常")
        with c5: st.metric("量比", f"{result['vol_ratio']:.2f}x", "🔴放量" if result['vol_ratio']>1.5 else "🔵缩量" if result['vol_ratio']<0.7 else "正常")

        # K线图
        st.plotly_chart(draw_kline(df, sym, name or sym), use_container_width=True)

        # 形态 + 建议 并排
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📡 K线形态识别")
            if patterns:
                for p_name, p_type, p_desc in patterns:
                    st.markdown(f"<div class='signal-{p_type}'><b>{p_name}</b><br><small>{p_desc}</small></div>", unsafe_allow_html=True)
            else:
                st.info("暂未识别到明显形态")

        with col2:
            st.markdown("### 💡 量化投资建议")
            for style_name, adv in advice.items():
                st.markdown(
                    f"<div class='advice-box'><b>【{style_name}】{adv['操作']}</b><br><br>"
                    f"📌 入场：{adv['入场']}<br>🎯 目标：{adv['目标']}<br>"
                    f"🛡️ 止损：{adv['止损']}<br>💼 仓位：{adv['仓位']}<br><br>"
                    f"<small>📝 {adv['理由']}</small></div>", unsafe_allow_html=True)

        # AI深度分析
        st.markdown("### 🤖 AI深度分析报告")
        if api_key:
            with st.spinner("Claude AI 正在深度分析中，请稍候..."):
                ai_result = ai_analyze(api_key, sym, name or sym, result, patterns, advice)
            st.markdown(f"<div class='ai-box'>{ai_result.replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='ai-box' style='border-color:#556677; color:#778899;'>
            🔑 <b>在左侧填入 Claude API Key 即可开启AI深度分析</b><br><br>
            AI将为你提供：<br>
            • 综合研判与多空判断<br>
            • 具体入场点位和仓位策略<br>
            • 中线趋势分析<br>
            • 关键风险提示<br>
            • 明确的最终结论<br><br>
            <small>API Key 获取：<a href="https://console.anthropic.com" target="_blank" style="color:#4dffaa">console.anthropic.com</a></small>
            </div>
            """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div style='text-align:center; padding:60px 20px;'>
        <h2 style='color:#ffd700'>欢迎使用 AI智能量化分析平台</h2>
        <p style='color:#8899aa; font-size:16px'>点击左侧热门股票，或输入代码开始分析</p><br>
        <table style='margin:auto; color:#aabbcc; border-collapse:collapse;'>
            <tr><td style='padding:12px 24px;border:1px solid #2a3f6f'>📊 K线形态识别</td><td style='padding:12px 24px;border:1px solid #2a3f6f'>金叉·死叉·头肩·锤头·十字星</td></tr>
            <tr><td style='padding:12px 24px;border:1px solid #2a3f6f'>📈 多维技术指标</td><td style='padding:12px 24px;border:1px solid #2a3f6f'>均线·MACD·RSI·KDJ·布林带</td></tr>
            <tr><td style='padding:12px 24px;border:1px solid #2a3f6f'>💡 量化投资建议</td><td style='padding:12px 24px;border:1px solid #2a3f6f'>短线+中线双维度策略</td></tr>
            <tr><td style='padding:12px 24px;border:1px solid #2a3f6f'>🤖 Claude AI研判</td><td style='padding:12px 24px;border:1px solid #2a3f6f'>专业级深度分析报告</td></tr>
        </table>
        <br><p style='color:#556677;font-size:13px'>⚠️ 仅供学习研究，不构成投资建议</p>
    </div>
    """, unsafe_allow_html=True)
