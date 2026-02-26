import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import anthropic
import random
import numpy as np
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="股票学院", page_icon="🌱", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap');

/* ── 全局重置 ── */
:root {
  --bg:    #111827;
  --bg2:   #1f2937;
  --bg3:   #374151;
  --gold:  #fbbf24;
  --green: #34d399;
  --red:   #f87171;
  --blue:  #60a5fa;
  --text:  #f3f4f6;
  --sub:   #d1d5db;
  --muted: #9ca3af;
  --border:#374151;
}
html, body, [class*="css"], .stApp {
  font-family: 'Noto Sans SC', sans-serif !important;
  background: var(--bg) !important;
  color: var(--text) !important;
}
.main .block-container { padding: 1.5rem 2rem; max-width: 1400px; }

/* ── 侧边栏 ── */
section[data-testid="stSidebar"] {
  background: var(--bg2) !important;
  border-right: 2px solid var(--border);
}
section[data-testid="stSidebar"] * { color: var(--text) !important; }

/* ── 按钮 ── */
.stButton > button {
  background: var(--bg2) !important;
  color: var(--text) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 8px !important;
  font-size: 0.88em !important;
  width: 100% !important;
  padding: 10px 8px !important;
  font-weight: 500 !important;
}
.stButton > button:hover {
  border-color: var(--gold) !important;
  color: var(--gold) !important;
  background: rgba(251,191,36,0.08) !important;
}

/* ── 输入框 ── */
.stTextInput input, .stNumberInput input {
  background: var(--bg2) !important;
  color: var(--text) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 8px !important;
}
.stSelectbox select, div[data-baseweb="select"] {
  background: var(--bg2) !important;
  color: var(--text) !important;
}

/* ── 标题 ── */
h1 { color: var(--text) !important; font-size: 1.8em !important; font-weight: 700 !important; }
h2 { color: var(--text) !important; font-size: 1.4em !important; }
h3 { color: var(--sub) !important; font-size: 1.15em !important; }
p, li, span { color: var(--sub) !important; }

/* ── 卡片 ── */
.card {
  background: var(--bg2);
  border: 1.5px solid var(--border);
  border-radius: 12px;
  padding: 18px 20px;
  margin: 8px 0;
}
.card-green { border-left: 4px solid var(--green) !important; }
.card-red   { border-left: 4px solid var(--red)   !important; }
.card-gold  { border-left: 4px solid var(--gold)  !important; }
.card-blue  { border-left: 4px solid var(--blue)  !important; }

/* ── 信号条 ── */
.sig-up {
  background: rgba(52,211,153,0.1);
  border-left: 4px solid var(--green);
  border-radius: 8px;
  padding: 12px 16px;
  margin: 6px 0;
}
.sig-down {
  background: rgba(248,113,113,0.1);
  border-left: 4px solid var(--red);
  border-radius: 8px;
  padding: 12px 16px;
  margin: 6px 0;
}
.sig-mid {
  background: rgba(251,191,36,0.08);
  border-left: 4px solid var(--gold);
  border-radius: 8px;
  padding: 12px 16px;
  margin: 6px 0;
}

/* ── 解释框 ── */
.explain {
  background: var(--bg3);
  border-radius: 8px;
  padding: 12px 14px;
  margin-top: 8px;
  font-size: 0.9em;
  line-height: 1.9;
  color: var(--sub) !important;
}
.explain b { color: var(--gold) !important; }

/* ── AI框 ── */
.ai-box {
  background: #0d2318;
  border: 2px solid #065f46;
  border-radius: 12px;
  padding: 20px 24px;
  line-height: 2;
  font-size: 0.93em;
  color: #d1fae5 !important;
}
.ai-box b { color: #34d399 !important; }

/* ── 警告框 ── */
.warn {
  background: rgba(248,113,113,0.1);
  border: 2px solid var(--red);
  border-radius: 12px;
  padding: 16px 20px;
  margin: 10px 0;
  color: var(--text) !important;
}
.warn b { color: var(--red) !important; }

/* ── 好消息框 ── */
.good {
  background: rgba(52,211,153,0.08);
  border: 2px solid var(--green);
  border-radius: 12px;
  padding: 16px 20px;
  margin: 10px 0;
  color: var(--text) !important;
}
.good b { color: var(--green) !important; }

/* ── 进度条 ── */
.prog-wrap { background: var(--bg3); border-radius: 20px; height: 8px; overflow: hidden; margin: 4px 0; }
.prog-fill { height: 100%; border-radius: 20px; background: linear-gradient(90deg, var(--green), var(--gold)); }

/* ── 指标卡片 ── */
.ind-card {
  background: var(--bg2);
  border: 1.5px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  margin: 10px 0;
}
.ind-title { color: var(--gold) !important; font-size: 1.1em; font-weight: 700; margin-bottom: 10px; }
.ind-body  { color: var(--sub) !important; font-size: 0.9em; line-height: 2; }
.ind-rule  {
  background: var(--bg3);
  border-radius: 8px;
  padding: 12px 16px;
  margin: 10px 0;
  font-size: 0.88em;
  color: var(--sub) !important;
}
.ind-rule b { color: var(--text) !important; }

/* ── 评分数字 ── */
.score-hi { color: #34d399; font-size: 2.2em; font-weight: 700; }
.score-md { color: #fbbf24; font-size: 2.2em; font-weight: 700; }
.score-lo { color: #f87171; font-size: 2.2em; font-weight: 700; }

/* ── metric文字覆盖 ── */
[data-testid="metric-container"] label { color: var(--muted) !important; font-size: 0.85em !important; }
[data-testid="metric-container"] [data-testid="metric-value"] { color: var(--text) !important; font-size: 1.6em !important; font-weight: 700 !important; }

/* ── expander ── */
.streamlit-expanderHeader { color: var(--text) !important; background: var(--bg2) !important; border-radius: 8px !important; }
details { background: var(--bg2) !important; border: 1.5px solid var(--border) !important; border-radius: 10px !important; }

/* ── table ── */
table { width:100%; border-collapse:collapse; }
th { background:var(--bg3); color:var(--gold)!important; padding:10px; text-align:left; }
td { padding:9px 10px; border-bottom:1px solid var(--border); color:var(--sub)!important; }
tr:hover td { background:var(--bg3); }

/* ── 标签 ── */
.tag-green { display:inline-block; background:rgba(52,211,153,0.15); color:#34d399!important; border:1px solid #34d399; border-radius:20px; padding:2px 10px; font-size:0.78em; margin:2px; }
.tag-gold  { display:inline-block; background:rgba(251,191,36,0.15);  color:#fbbf24!important; border:1px solid #fbbf24; border-radius:20px; padding:2px 10px; font-size:0.78em; margin:2px; }
.tag-red   { display:inline-block; background:rgba(248,113,113,0.15); color:#f87171!important; border:1px solid #f87171; border-radius:20px; padding:2px 10px; font-size:0.78em; margin:2px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# Session State
# ══════════════════════════════════════════════
for k, v in {
    "page": "home", "xp": 0, "level": 1,
    "learned": [], "quiz_score": 0, "quiz_total": 0,
    "api_key": "", "holding": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

def add_xp(n):
    st.session_state.xp += n
    needed = st.session_state.level * 100
    if st.session_state.xp >= needed:
        st.session_state.xp -= needed
        st.session_state.level += 1
        st.toast(f"🎉 升级！现在是 Lv.{st.session_state.level}", icon="🏆")

# ══════════════════════════════════════════════
# 侧边栏
# ══════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🌱 股票学院")
    lv = st.session_state.level
    xp = st.session_state.xp
    needed = lv * 100
    st.markdown(f"<b style='color:#f3f4f6'>Lv.{lv} 新手投资者</b> <span style='color:#9ca3af'>{xp}/{needed} XP</span>", unsafe_allow_html=True)
    st.markdown(f"<div class='prog-wrap'><div class='prog-fill' style='width:{int(xp/needed*100)}%'></div></div>", unsafe_allow_html=True)
    st.divider()
    for icon, key, label in [
        ("🏠", "home",     "首页总览"),
        ("📚", "learn",    "K线课堂"),
        ("📊", "indicator","指标详解"),
        ("🔍", "scout",    "AI选股推荐"),
        ("🛡️", "hold",     "持仓守护"),
        ("🧩", "quiz",     "闯关练习"),
    ]:
        if st.button(f"{icon}  {label}", key=f"nav_{key}"):
            st.session_state.page = key
    st.divider()
    st.session_state.api_key = st.text_input(
        "🔑 Claude API Key（选填）",
        value=st.session_state.api_key,
        type="password",
        help="填入后开启AI分析功能"
    )
    st.caption("[获取免费Key →](https://console.anthropic.com)")

# ══════════════════════════════════════════════
# AI调用
# ══════════════════════════════════════════════
def call_ai(prompt, system="你是专门教股票小白的老师，语言亲切通俗，善用生活比喻，用中文回答，绝不使用晦涩专业术语。"):
    if not st.session_state.api_key:
        return None
    try:
        client = anthropic.Anthropic(api_key=st.session_state.api_key)
        msg = client.messages.create(
            model="claude-opus-4-6", max_tokens=1500,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text
    except Exception as e:
        return f"AI暂时无法回应：{e}"

# ══════════════════════════════════════════════
# 数据获取（双重尝试，提高A股成功率）
# ══════════════════════════════════════════════
@st.cache_data(ttl=300, show_spinner=False)
def get_data(symbol, period="3mo"):
    tries = [symbol]
    # A股自动补全后缀
    if "." not in symbol and len(symbol) == 6:
        if symbol.startswith("6") or symbol.startswith("5"):
            tries = [symbol + ".SS", symbol]
        else:
            tries = [symbol + ".SZ", symbol]

    for sym in tries:
        try:
            t = yf.Ticker(sym)
            df = t.history(period=period, interval="1d", timeout=20)
            if df is None or len(df) < 5:
                continue
            df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            df.columns = ['open', 'high', 'low', 'close', 'volume']
            df = df.astype(float).dropna()
            if len(df) < 5:
                continue
            try:
                info = t.info
                name = info.get('longName') or info.get('shortName') or sym
            except:
                name = sym
            return df, name, sym
        except:
            continue
    return None, symbol, symbol

# ══════════════════════════════════════════════
# 技术指标计算
# ══════════════════════════════════════════════
def compute_tech(df):
    c = df['close']; v = df['volume']; n = len(df)
    df['EMA5']  = ta.ema(c, length=min(5,  n-2))
    df['EMA20'] = ta.ema(c, length=min(20, n-2))
    df['EMA60'] = ta.ema(c, length=min(60, n-2))
    df['RSI']   = ta.rsi(c, length=min(14, n-2))
    if n >= 22:
        bb = ta.bbands(c, length=20, std=2)
        if bb is not None: df = pd.concat([df, bb], axis=1)
    if n >= 35:
        macd = ta.macd(c)
        if macd is not None: df = pd.concat([df, macd], axis=1)
    df['vol_ma10'] = v.rolling(min(10, n)).mean()
    df.dropna(inplace=True)
    return df

# ══════════════════════════════════════════════
# 完整K线图（日K + 成交量 + MACD）
# ══════════════════════════════════════════════
def draw_full_chart(df, sym, name, cost=None):
    has_macd = any('MACDh' in c for c in df.columns)
    rows    = 3 if has_macd else 2
    heights = [0.58, 0.18, 0.24] if has_macd else [0.70, 0.30]
    row_titles = ["K线 · 均线 · 布林带", "成交量"] + (["MACD"] if has_macd else [])

    fig = make_subplots(
        rows=rows, cols=1, shared_xaxes=True,
        vertical_spacing=0.04, row_heights=heights,
        subplot_titles=row_titles
    )

    # ── 日K线 ──
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['open'], high=df['high'],
        low=df['low'],   close=df['close'],
        increasing=dict(line=dict(color='#f87171', width=1), fillcolor='#f87171'),
        decreasing=dict(line=dict(color='#34d399', width=1), fillcolor='#34d399'),
        name='日K线',
        hoverlabel=dict(bgcolor='#1f2937')
    ), row=1, col=1)

    # ── 均线 ──
    ema_cfg = [('EMA5','#fbbf24',1.8,'5日均线'),('EMA20','#60a5fa',1.8,'20日均线'),('EMA60','#c084fc',1.5,'60日均线')]
    for col_n, color, w, label in ema_cfg:
        if col_n in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[col_n],
                line=dict(color=color, width=w),
                name=label, opacity=0.9
            ), row=1, col=1)

    # ── 布林带 ──
    bbu_c = [c for c in df.columns if 'BBU' in c]
    bbl_c = [c for c in df.columns if 'BBL' in c]
    bbm_c = [c for c in df.columns if 'BBM' in c]
    if bbu_c and bbl_c:
        fig.add_trace(go.Scatter(
            x=df.index, y=df[bbu_c[0]],
            line=dict(color='rgba(148,163,184,0.5)', width=1, dash='dot'),
            name='布林上轨', showlegend=True
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df[bbl_c[0]],
            line=dict(color='rgba(148,163,184,0.5)', width=1, dash='dot'),
            name='布林下轨', fill='tonexty',
            fillcolor='rgba(148,163,184,0.06)', showlegend=True
        ), row=1, col=1)
        if bbm_c:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[bbm_c[0]],
                line=dict(color='rgba(148,163,184,0.3)', width=1),
                name='布林中轨', showlegend=False
            ), row=1, col=1)

    # ── 金叉死叉标注 ──
    if 'EMA5' in df.columns and 'EMA20' in df.columns:
        for i in range(1, len(df)):
            e5n = df['EMA5'].iloc[i];  e5p  = df['EMA5'].iloc[i-1]
            e20n= df['EMA20'].iloc[i]; e20p = df['EMA20'].iloc[i-1]
            if e5p <= e20p and e5n > e20n:
                fig.add_annotation(
                    x=df.index[i], y=float(df['low'].iloc[i]) * 0.993,
                    text="▲金叉", showarrow=False,
                    font=dict(color='#fbbf24', size=11, family='Noto Sans SC'),
                    bgcolor='rgba(251,191,36,0.15)', bordercolor='#fbbf24',
                    borderwidth=1, borderpad=3, row=1, col=1
                )
            elif e5p >= e20p and e5n < e20n:
                fig.add_annotation(
                    x=df.index[i], y=float(df['high'].iloc[i]) * 1.007,
                    text="▼死叉", showarrow=False,
                    font=dict(color='#f87171', size=11, family='Noto Sans SC'),
                    bgcolor='rgba(248,113,113,0.15)', bordercolor='#f87171',
                    borderwidth=1, borderpad=3, row=1, col=1
                )

    # ── 成本线 ──
    if cost:
        fig.add_hline(
            y=cost, line_color='#fbbf24', line_width=2, line_dash='dash',
            annotation_text=f"  我的成本 ¥{cost}",
            annotation_font=dict(color='#fbbf24', size=12),
            row=1, col=1
        )

    # ── 成交量 ──
    vol_colors = ['#f87171' if df['close'].iloc[i] >= df['open'].iloc[i]
                  else '#34d399' for i in range(len(df))]
    fig.add_trace(go.Bar(
        x=df.index, y=df['volume'],
        marker_color=vol_colors, opacity=0.75, name='成交量'
    ), row=2, col=1)
    if 'vol_ma10' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['vol_ma10'],
            line=dict(color='#fbbf24', width=1.5),
            name='量10均线'
        ), row=2, col=1)

    # ── MACD ──
    if has_macd:
        mh_c = [c for c in df.columns if 'MACDh' in c]
        ml_c = [c for c in df.columns if c.startswith('MACD_')]
        ms_c = [c for c in df.columns if c.startswith('MACDs')]
        if mh_c:
            mc = ['#f87171' if v >= 0 else '#34d399' for v in df[mh_c[0]]]
            fig.add_trace(go.Bar(
                x=df.index, y=df[mh_c[0]],
                marker_color=mc, name='MACD柱', opacity=0.8
            ), row=3, col=1)
        if ml_c:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[ml_c[0]],
                line=dict(color='#fbbf24', width=2),
                name='MACD线'
            ), row=3, col=1)
        if ms_c:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[ms_c[0]],
                line=dict(color='#60a5fa', width=1.5),
                name='信号线'
            ), row=3, col=1)
        fig.add_hline(y=0, line_color='rgba(255,255,255,0.2)', line_width=1, row=3, col=1)

    # ── 布局 ──
    title = f"{name}（{sym}）完整日K分析图"
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color='#f3f4f6', family='Noto Sans SC')),
        template="plotly_dark",
        paper_bgcolor='#1f2937',
        plot_bgcolor='#111827',
        height=680,
        xaxis_rangeslider_visible=False,
        legend=dict(
            orientation='h', y=1.04, x=0,
            font=dict(size=11, color='#d1d5db'),
            bgcolor='rgba(31,41,55,0.8)',
            bordercolor='#374151'
        ),
        margin=dict(l=50, r=30, t=80, b=20),
        hoverlabel=dict(bgcolor='#1f2937', font_size=12)
    )
    for i in range(1, rows + 1):
        fig.update_xaxes(
            showgrid=True, gridcolor='rgba(255,255,255,0.06)',
            tickfont=dict(color='#9ca3af', size=11),
            row=i, col=1
        )
        fig.update_yaxes(
            showgrid=True, gridcolor='rgba(255,255,255,0.06)',
            tickfont=dict(color='#9ca3af', size=11),
            row=i, col=1
        )
    # subplot标题颜色
    for ann in fig.layout.annotations:
        ann.font.color = '#9ca3af'
        ann.font.size  = 11

    return fig

# ══════════════════════════════════════════════
# 信号分析
# ══════════════════════════════════════════════
def analyze_signals(df, cost=None):
    if df is None or len(df) < 2:
        return [], 50
    latest  = df.iloc[-1]; prev = df.iloc[-2]
    close   = float(latest['close'])
    vol_avg = float(latest.get('vol_ma10', latest['volume']))
    vr      = float(latest['volume']) / max(vol_avg, 1)
    rsi     = float(latest.get('RSI', 50))
    pct     = (close - float(prev['close'])) / float(prev['close']) * 100
    signals = []; score = 50

    e5  = float(latest.get('EMA5',  close))
    e20 = float(latest.get('EMA20', close))
    e60 = float(latest.get('EMA60', close))

    # 均线排列
    if close > e5 > e20:
        score += 10
        signals.append(("✅ 均线多头排列", "up",
            f"现价 {close:.2f}  >  5日线 {e5:.2f}  >  20日线 {e20:.2f}",
            "就像爬楼梯，每层都比上一层高。短期走势强于中期，是健康的上涨形态。",
            "可以持股或小仓位买入，趋势向上。"))
    elif close < e5 < e20:
        score -= 10
        signals.append(("⚠️ 均线空头排列", "down",
            f"现价 {close:.2f}  <  5日线 {e5:.2f}  <  20日线 {e20:.2f}",
            "就像下楼梯，每层都比上一层低。短期和中期都在下跌通道里。",
            "建议观望，不要抄底，等出现金叉再考虑。"))

    if close > e60:
        score += 5
        signals.append(("✅ 站稳60日长期均线", "up",
            f"现价 {close:.2f} 高于60日均线 {e60:.2f}",
            "长期持仓者的平均成本在你下方，大方向向上。",
            "中线持股信心增强。"))
    else:
        score -= 5
        signals.append(("⚠️ 跌破60日长期均线", "down",
            f"现价 {close:.2f} 低于60日均线 {e60:.2f}",
            "大多数长期持仓者处于亏损状态，随时可能卖出。",
            "中线要谨慎，减少持仓。"))

    # 金叉/死叉
    for i in range(len(df)-1, max(len(df)-15, 0), -1):
        e5n = df['EMA5'].iloc[i]; e5p = df['EMA5'].iloc[i-1]
        e20n= df['EMA20'].iloc[i]; e20p= df['EMA20'].iloc[i-1]
        if e5p <= e20p and e5n > e20n:
            d = len(df) - 1 - i
            score += 8
            signals.append((f"🌟 {'今日' if d==0 else f'{d}天前'}出现金叉", "up",
                "5日均线从下穿越20日均线向上",
                "金叉 = 短期动能超过中期，是经典买入信号。就像绿灯亮起，可以出发了。",
                "金叉后通常有一段上涨行情，适合轻仓介入。"))
            break
        elif e5p >= e20p and e5n < e20n:
            d = len(df) - 1 - i
            score -= 8
            signals.append((f"💀 {'今日' if d==0 else f'{d}天前'}出现死叉", "down",
                "5日均线从上穿越20日均线向下",
                "死叉 = 短期动能弱于中期，是经典卖出信号。就像红灯亮起，先停下来。",
                "死叉后注意止损，不要硬撑。"))
            break

    # 成交量
    if vr > 2.0:
        s_type = "up" if pct > 0 else "down"
        score += 8 if pct > 0 else -8
        signals.append((
            f"🚀 超级放量{'上涨' if pct>0 else '下跌'}", s_type,
            f"今日成交量是近10日均量的 {vr:.1f} 倍",
            f"{'成交量暴增+上涨 = 大量资金涌入买入，是强势信号！' if pct>0 else '成交量暴增+下跌 = 有人在大量抛售出逃，危险！'}",
            "放量上涨可跟进；放量下跌要止损。"))
    elif vr > 1.5:
        s_type = "up" if pct > 0 else "mid"
        score += 5 if pct > 0 else 0
        signals.append((f"📈 明显放量({'上涨' if pct>0 else '下跌'})", s_type,
            f"今日成交量是均量的 {vr:.1f} 倍",
            "成交活跃度提升，市场开始关注这只股票。",
            "结合涨跌方向判断。"))
    elif vr < 0.6:
        signals.append(("😴 明显缩量", "mid",
            f"今日成交量仅为均量的 {vr:.1f} 倍",
            "大家都在观望，没人交易，市场对这只股票不感兴趣。",
            "缩量时不宜追涨，等量能恢复再动。"))

    # RSI
    if rsi >= 75:
        score -= 10
        signals.append(("🔴 RSI严重超买", "down",
            f"RSI = {rsi:.1f}（警戒线：75以上）",
            f"RSI={rsi:.0f}，就像运动员跑到快虚脱了，股价可能要大幅回调。",
            "高位持仓者建议止盈，新入场者一定不要追高。"))
    elif rsi >= 70:
        score -= 5
        signals.append(("⚠️ RSI进入超买区", "mid",
            f"RSI = {rsi:.1f}（超买线：70）",
            "涨势偏猛，注意短期回调风险，但强势股可以在超买区持续一段时间。",
            "已持仓可以设好止盈单，等待出场机会。"))
    elif rsi <= 25:
        score += 10
        signals.append(("🔥 RSI严重超卖", "up",
            f"RSI = {rsi:.1f}（超卖线：30以下）",
            f"RSI={rsi:.0f}，股价跌得很惨，就像弹簧压到极限，反弹力量正在积累。",
            "小仓试探，但等K线出现止跌（如出现阳线）再加仓，别硬接飞刀。"))
    elif rsi <= 30:
        score += 5
        signals.append(("📉 RSI超卖区", "up",
            f"RSI = {rsi:.1f}（超卖线：30）",
            "跌势偏猛，可能有反弹机会，但要等企稳信号。",
            "等K线出现止跌迹象再入场。"))
    else:
        tag = "偏强" if rsi > 55 else "偏弱" if rsi < 45 else "中性"
        s   = "up" if rsi > 55 else "down" if rsi < 45 else "mid"
        score += 3 if rsi > 55 else -3 if rsi < 45 else 0
        signals.append((f"✅ RSI运行正常（{tag}）", s,
            f"RSI = {rsi:.1f}，处于30~70正常区间",
            f"RSI在健康区间内，{'偏向强势' if rsi>55 else '偏向弱势' if rsi<45 else '多空均衡'}。",
            "结合均线和MACD方向判断操作。"))

    # 布林带
    bbu_c = [c for c in df.columns if 'BBU' in c]
    bbl_c = [c for c in df.columns if 'BBL' in c]
    if bbu_c and bbl_c:
        bbu = float(latest[bbu_c[0]]); bbl = float(latest[bbl_c[0]])
        if close > bbu:
            score += 6
            signals.append(("🔴 强势突破布林上轨", "up",
                f"现价 {close:.2f} 突破布林上轨 {bbu:.2f}",
                "价格冲出了「正常波动范围」，说明这次上涨非常强劲，超出了日常波动。",
                "强势信号可跟进，但布林带外不可持续太久，设好止盈。"))
        elif close < bbl:
            score -= 6
            signals.append(("🔵 跌破布林下轨", "down",
                f"现价 {close:.2f} 跌破布林下轨 {bbl:.2f}",
                "价格跌出了「正常波动范围」，跌势非常猛烈。",
                "虽然超卖可能反弹，但先别急着抄底，等跌势止住再说。"))

    # MACD柱
    mh_c = [c for c in df.columns if 'MACDh' in c]
    if mh_c and len(df) >= 2:
        h = float(latest[mh_c[0]]); hp = float(prev[mh_c[0]])
        if h > 0 and h > hp:
            score += 6
            signals.append(("🔴 MACD红柱扩大", "up",
                f"MACD柱：{hp:.4f} → {h:.4f}（红柱变长）",
                "上涨的力量越来越大，就像顺风骑车风越来越大，越骑越快。",
                "动能增强，可以持股。"))
        elif h > 0 and h < hp:
            score -= 3
            signals.append(("🟡 MACD红柱收缩", "mid",
                f"MACD柱：{hp:.4f} → {h:.4f}（红柱变短）",
                "上涨动力开始减弱，就像顺风变成了微风，速度慢下来了。",
                "注意高位风险，考虑部分止盈。"))
        elif h < 0 and h < hp:
            score -= 6
            signals.append(("🔵 MACD绿柱扩大", "down",
                f"MACD柱：{hp:.4f} → {h:.4f}（绿柱变长）",
                "下跌的力量越来越大，就像逆风骑车风越来越大，越来越累。",
                "不宜入场，耐心等绿柱缩短。"))
        elif h < 0 and h > hp:
            score += 4
            signals.append(("🟡 MACD绿柱收缩", "mid",
                f"MACD柱：{hp:.4f} → {h:.4f}（绿柱变短）",
                "下跌动力开始减弱，可能快要止跌了。",
                "可以开始关注，等出现阳线确认后再入场。"))

    # 持仓成本
    if cost:
        pnl = (close - cost) / cost * 100
        if pnl >= 10:
            signals.append((f"💰 浮盈 {pnl:.1f}%", "up",
                f"成本 {cost}，现价 {close:.2f}，已盈利 {pnl:.1f}%",
                f"恭喜！已经盈利{pnl:.1f}%，可以考虑卖出一部分锁定利润。",
                "建议先卖出1/3止盈，剩余继续持有。"))
        elif pnl <= -5:
            signals.append((f"🚨 亏损 {abs(pnl):.1f}%", "down",
                f"成本 {cost}，现价 {close:.2f}，亏损 {abs(pnl):.1f}%",
                f"已亏损{abs(pnl):.1f}%，到了需要认真考虑止损的时候了。",
                "建议重新评估持仓逻辑，考虑止损离场。"))

    return signals, max(0, min(100, score))

# ══════════════════════════════════════════════
# 页面：首页
# ══════════════════════════════════════════════
def page_home():
    st.title("🌱 股票学院 · 新手成长营")
    st.markdown("<p>从零开始，边学边用，逐步掌握选股能力</p>", unsafe_allow_html=True)
    st.divider()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("当前等级", f"Lv.{st.session_state.level}")
    c2.metric("经验值", f"{st.session_state.xp} XP")
    c3.metric("完成课程", f"{len(st.session_state.learned)}/6")
    c4.metric("练习正确率", f"{int(st.session_state.quiz_score/max(st.session_state.quiz_total,1)*100)}%")

    st.divider()
    st.markdown("### 📌 新手三条铁律")
    st.markdown("""
    <div class='warn'>
    <b>🛡️ 第一条：买入前先设止损</b><br>
    亏损超过5%就卖，不犹豫不等待。保住本金才有下次机会。<br><br>
    <b>📦 第二条：单只股票不超过总资金1/3</b><br>
    鸡蛋不放一个篮子，一只股票出问题不至于全军覆没。<br><br>
    <b>🚫 第三条：说不出"为什么涨"就不买</b><br>
    别人推荐的股票，先问自己：这只股票涨的逻辑是什么？说不清楚就不买。
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🚀 快速开始")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""<div class='card card-blue'>
        <p style='color:#60a5fa;font-weight:700;font-size:1.05em'>📚 K线课堂</p>
        <p>6节系统课，每节5分钟<br>从K线到止损全覆盖</p>
        </div>""", unsafe_allow_html=True)
        if st.button("开始学习 →", key="h1"): st.session_state.page = "learn"
    with col2:
        st.markdown("""<div class='card card-gold'>
        <p style='color:#fbbf24;font-weight:700;font-size:1.05em'>🔍 AI选股推荐</p>
        <p>输入股票或说出你的想法<br>AI推荐+解释每个信号</p>
        </div>""", unsafe_allow_html=True)
        if st.button("AI帮我选 →", key="h2"): st.session_state.page = "scout"
    with col3:
        st.markdown("""<div class='card card-red'>
        <p style='color:#f87171;font-weight:700;font-size:1.05em'>🛡️ 持仓守护</p>
        <p>输入你的持仓和成本<br>AI告诉你该持有还是止损</p>
        </div>""", unsafe_allow_html=True)
        if st.button("分析持仓 →", key="h3"): st.session_state.page = "hold"

    st.divider()
    st.markdown("### 🗺️ 成长路线图")
    steps = [
        ("Lv.1", "🌱 K线入门",  "认识涨跌红绿", 1),
        ("Lv.2", "📊 指标理解", "RSI/MACD/均线", 2),
        ("Lv.3", "🔍 形态识别", "金叉死叉头肩", 3),
        ("Lv.4", "🎯 选股逻辑", "量价配合",     4),
        ("Lv.5", "💼 实战策略", "止损止盈仓位", 5),
    ]
    cols = st.columns(5)
    for i, (lv_tag, title, desc, req) in enumerate(steps):
        with cols[i]:
            unlocked = st.session_state.level >= req
            color = "#34d399" if unlocked else "#374151"
            st.markdown(f"""<div class='card' style='text-align:center;border-top:3px solid {color}'>
            <p style='color:{color};font-size:1.3em;margin:0'>{"✅" if unlocked else "🔒"}</p>
            <p style='color:{color};font-weight:700;margin:4px 0'>{lv_tag}</p>
            <p style='font-size:0.9em;margin:2px 0'>{title}</p>
            <p style='color:#6b7280;font-size:0.8em'>{desc}</p>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# 页面：K线课堂
# ══════════════════════════════════════════════
LESSONS = [
    {"id":"kline","title":"🕯️ 第一课：读懂一根K线","xp":30,"content":"""
**K线记录4个关键价格：**

| 价格 | 含义 |
|------|------|
| **开盘价** | 这段时间的第一笔成交价 |
| **收盘价** | 这段时间的最后一笔成交价 |
| **最高价** | 期间涨到的最高点 |
| **最低价** | 期间跌到的最低点 |

🔴 **红色K线（阳线）**：收盘价 > 开盘价 → 这段时间**涨了**

🟢 **绿色K线（阴线）**：收盘价 < 开盘价 → 这段时间**跌了**

---

**K线的上下细线叫"影线"：**

- **上影线**：价格曾涨上去，但被卖方打下来 → **上方有抛压**
- **下影线**：价格曾跌下去，但被买方托回来 → **下方有支撑**

📌 **实战规则：**
- 上影线很长 = 高位有人大量卖出，短期看跌
- 下影线很长（锤头线）= 低位有人大量买入，可能反转向上
- 十字星（影线长实体小）= 多空均衡，方向不明，等待
""","points":["K线=开高低收4个价格","红涨绿跌","影线越长=该方向力量越强"]},

    {"id":"ma","title":"📈 第二课：均线和金叉死叉","xp":30,"content":"""
**均线 = 过去N天收盘价的平均值**

代表这段时间内所有投资者的**平均买入成本**。

| 均线 | 周期 | 用途 |
|------|------|------|
| **MA5** | 5日 | 短期趋势，最敏感 |
| **MA20** | 20日 | 中期趋势，月线参考 |
| **MA60** | 60日 | 长期趋势，最稳定 |

---

**怎么判断趋势？**

✅ 股价在均线**上方** = 大家都在盈利 = 趋势向好

⚠️ 股价在均线**下方** = 大家都在亏损 = 趋势偏弱

---

**🌟 金叉（买入信号）**

短期均线（5日）从下方穿越长期均线（20日）向上

记忆方法：两线交叉像X，金色=金叉=好消息=买

**💀 死叉（卖出信号）**

短期均线（5日）从上方穿越长期均线（20日）向下

记忆方法：死叉=死亡=坏消息=卖

📌 **图表上有▲金叉 ▼死叉的标注，帮你识别每次信号**
""","points":["均线=平均持仓成本","价格>均线=多头趋势","金叉买 死叉卖"]},

    {"id":"rsi","title":"⚡ 第三课：RSI——超买超卖","xp":40,"content":"""
**RSI（相对强弱指数）= 0到100之间的数字，衡量涨跌力道**

---

**三个关键区间：**

| RSI值 | 区域 | 含义 | 操作 |
|-------|------|------|------|
| **> 70** | 🔴 超买区 | 涨过头了，可能回调 | 考虑止盈 |
| **30~70** | ✅ 正常区 | 正常波动 | 看均线方向 |
| **< 30** | 🔵 超卖区 | 跌过头了，可能反弹 | 关注机会 |

---

**通俗比喻：**

> RSI就像运动员的**体力值**
> - RSI=80 → 体力快耗尽了，跑不动了（涨势可能要停）
> - RSI=20 → 在休息补充体力，准备重新出发（跌势可能要停）

---

**⚠️ 重要提醒：**

超买不等于立刻跌，强势股可以在超买区停留很长时间！

RSI只是**辅助判断**，必须结合均线、成交量一起看。

📌 **实战记忆：RSI>70注意止盈，RSI<30小仓关注**
""","points":["RSI 0-100衡量力道","超买>70 超卖<30","必须结合其他指标"]},

    {"id":"macd","title":"🌊 第四课：MACD——动能变化","xp":40,"content":"""
**MACD由三部分组成：**

| 组成 | 名称 | 作用 |
|------|------|------|
| 快线 | MACD线 | 对价格变化敏感 |
| 慢线 | 信号线 | 对价格变化迟钝 |
| 柱状图 | MACD柱 | 两线差值，正=红柱，负=绿柱 |

---

**🌟 金叉（买入信号）**
MACD线从下方穿越信号线向上

**💀 死叉（卖出信号）**
MACD线从上方穿越信号线向下

---

**MACD柱状图更直观：**

- 🔴 红柱越来越长 = 上涨动力越来越足，趋势加速
- 🔴 红柱开始缩短 = 上涨动力减弱，注意变盘！
- 🟢 绿柱越来越长 = 下跌动力越来越强，别轻易抄底
- 🟢 绿柱开始缩短 = 下跌动力减弱，可以开始关注

---

**通俗比喻：**

> MACD就像两辆车的速度对比
> - 快车追上慢车（金叉）= 行情加速向上，可以跟进
> - 快车又被慢车超过（死叉）= 行情开始减速，准备离场

📌 **记住最重要的：红柱缩短是提前警告信号，比死叉更早！**
""","points":["MACD金叉买 死叉卖","红柱扩大=动能强","红柱收缩=提前警告"]},

    {"id":"bollinger","title":"📐 第五课：布林带——价格通道","xp":40,"content":"""
**布林带由三条线组成：**

| 线名 | 含义 |
|------|------|
| **上轨** | 价格的上边界（压力位） |
| **中轨** | 20日均线 |
| **下轨** | 价格的下边界（支撑位） |

正常情况下，**95%的价格波动发生在上下轨之间**。

---

**四种常见情况：**

✅ **触碰下轨** → 可能遇到支撑，关注反弹机会

⚠️ **触碰上轨** → 可能遇到压力，注意回调风险

🚀 **突破上轨** → 强势突破！上涨动力超强（但不可持续太久）

⚡ **布林带收窄** → 蓄势中！即将有方向性大行情（涨或跌）

---

**通俗比喻：**

> 布林带就像一根**橡皮筋**
> - 价格通常在橡皮筋范围内波动
> - 偶尔被拉到边缘，容易弹回来
> - 橡皮筋收紧（带宽收窄）= 蓄势爆发，即将大行情

📌 **带宽收窄后，等待突破方向再操作，不要提前猜！**
""","points":["布林带=价格正常波动通道","触下轨关注反弹","带宽收窄=即将变盘"]},

    {"id":"stoploss","title":"🛡️ 第六课：止损止盈——最重要的一课","xp":50,"content":"""
**为什么止损是最重要的？**

> 亏损50% → 需要盈利**100%**才能回本！
>
> 亏损20% → 需要盈利**25%**才能回本
>
> 亏损5%  → 只需要盈利**5.3%**就能回本 ✅

**结论：小亏可以接受，大亏很难翻身。止损 = 保护本金。**

---

**止损怎么设？**

| 风格 | 止损比例 | 适合谁 |
|------|---------|--------|
| 保守型 | 亏3%就走 | 刚入门，风险承受低 |
| 普通型 | 亏5%就走 | **推荐新手使用** |
| 激进型 | 亏8%就走 | 有经验，仓位小 |

📌 **买入后立刻在股票app里设置「条件单」！**

---

**止盈怎么做？（分批卖，不要一次全卖）**

- 涨5% → 卖出1/3，锁定部分利润
- 涨10% → 再卖出1/3
- 剩余 → 移动止盈线，让利润继续跑

---

**仓位管理铁律：**

单只股票最多用**总资金的1/3**

> 例：你有2万元，单只股票最多买约6000元
>
> 这样即使这只股票跌50%，你总资金只损失8%，还能继续操作

📌 **宁可卖早了错过涨幅，也不要因舍不得被深套！**
""","points":["止损5%是红线","分批止盈锁利润","单股不超总资金1/3"]},
]

def page_learn():
    st.title("📚 K线课堂")
    st.markdown("<p>6节系统课程，从零开始打好基础，每学完一节获得经验值</p>", unsafe_allow_html=True)
    st.divider()
    for lesson in LESSONS:
        done = lesson['id'] in st.session_state.learned
        with st.expander(
            f"{'✅' if done else '📖'}  {lesson['title']}    +{lesson['xp']} XP",
            expanded=False
        ):
            st.markdown(lesson['content'])
            st.markdown("<br>**🔑 本课要点：**", unsafe_allow_html=True)
            for p in lesson['points']:
                st.markdown(f"<span class='tag-green'>✓ {p}</span>", unsafe_allow_html=True)
            st.markdown("")
            c1, c2 = st.columns([1, 2])
            with c1:
                if not done:
                    if st.button(f"✅ 学完了，+{lesson['xp']} XP", key=f"d_{lesson['id']}"):
                        st.session_state.learned.append(lesson['id'])
                        add_xp(lesson['xp'])
                        st.success("已完成！"); st.rerun()
                else:
                    st.success("已完成 ✅")
            with c2:
                if st.session_state.api_key:
                    if st.button("🤖 还是不懂？让AI用大白话解释", key=f"ai_{lesson['id']}"):
                        with st.spinner("AI解释中..."):
                            r = call_ai(f"用最简单的语言和生活比喻解释：{lesson['title']}，100字以内，完全不懂股票的人也能看懂。")
                        if r:
                            st.markdown(f"<div class='ai-box'>🤖 <b>AI老师说：</b><br><br>{r}</div>", unsafe_allow_html=True)
                            add_xp(5)

# ══════════════════════════════════════════════
# 页面：指标详解（新增！）
# ══════════════════════════════════════════════
def page_indicator():
    st.title("📊 技术指标详解")
    st.markdown("<p>每个指标都配有详细解释和实战规则，帮你真正看懂图表</p>", unsafe_allow_html=True)
    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 均线 & 金叉死叉", "⚡ RSI", "🌊 MACD", "📐 布林带", "📦 成交量"])

    with tab1:
        st.markdown("## 📈 均线（MA）& 金叉死叉")
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("""
            <div class='ind-card'>
            <div class='ind-title'>什么是均线？</div>
            <div class='ind-body'>
            均线 = 过去N天收盘价的<b style='color:#fbbf24'>平均值</b><br><br>
            它代表一段时间内所有持仓者的<b style='color:#fbbf24'>平均买入成本</b>。<br><br>
            • <b style='color:#fbbf24'>5日均线（黄色）</b>：最近一周均价，最敏感<br>
            • <b style='color:#60a5fa'>20日均线（蓝色）</b>：近一个月均价，中期参考<br>
            • <b style='color:#c084fc'>60日均线（紫色）</b>：近三个月均价，长期方向
            </div>
            <div class='ind-rule'>
            <b>📌 看图规则：</b><br>
            股价在均线上方 = 持仓者普遍盈利 = 趋势健康<br>
            股价在均线下方 = 持仓者普遍亏损 = 趋势偏弱<br>
            均线向上倾斜 = 趋势向上<br>
            均线向下倾斜 = 趋势向下
            </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class='ind-card'>
            <div class='ind-title'>🌟 金叉 & 💀 死叉</div>
            <div class='ind-body'>
            <b style='color:#fbbf24'>金叉</b> = 5日线从下穿越20日线向上<br>
            → 短期动能超过中期，<b style='color:#34d399'>买入信号</b><br><br>
            <b style='color:#f87171'>死叉</b> = 5日线从上穿越20日线向下<br>
            → 短期动能弱于中期，<b style='color:#f87171'>卖出信号</b>
            </div>
            <div class='ind-rule'>
            <b>📌 实战规则：</b><br>
            ✅ 金叉出现 + 成交量放大 = 强烈买入信号<br>
            ✅ 死叉出现 + 成交量放大 = 强烈卖出信号<br>
            ⚠️ 金叉出现但缩量 = 假突破，谨慎<br>
            ⚠️ 图表中已用▲▼标注每次金叉死叉位置
            </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div class='ind-card card-gold'>
        <div class='ind-title'>💡 真实案例理解</div>
        <div class='ind-body'>
        想象你买了一只股票，5日线是你最近5天的"心情"，20日线是你最近一个月的"情绪基准"。<br><br>
        当你最近5天的心情（5日线）开始比一个月以来的情绪（20日线）更好时，说明局势在好转——<b style='color:#fbbf24'>这就是金叉！</b><br><br>
        反之，当5天心情开始比月均情绪更差时，说明局势在恶化——<b style='color:#f87171'>这就是死叉！</b>
        </div>
        </div>
        """, unsafe_allow_html=True)

    with tab2:
        st.markdown("## ⚡ RSI（相对强弱指数）")
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("""
            <div class='ind-card'>
            <div class='ind-title'>RSI是什么？怎么计算？</div>
            <div class='ind-body'>
            RSI = 过去14天中，<b style='color:#34d399'>涨幅总和</b> ÷（涨幅总和 + 跌幅总和）× 100<br><br>
            <b>简单说：</b>过去14天涨的力量占总力量的比例<br><br>
            • RSI = 100：14天全涨，极度超买<br>
            • RSI = 50：涨跌力量均衡<br>
            • RSI = 0：14天全跌，极度超卖
            </div>
            <div class='ind-rule'>
            <b>📌 三个关键位置：</b><br>
            <b style='color:#f87171'>RSI > 70</b> = 超买区，注意回调<br>
            <b style='color:#9ca3af'>RSI 30~70</b> = 正常区，看其他指标<br>
            <b style='color:#34d399'>RSI < 30</b> = 超卖区，关注反弹
            </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class='ind-card'>
            <div class='ind-title'>常见误区和正确用法</div>
            <div class='ind-body'>
            <b style='color:#f87171'>❌ 错误用法：</b><br>
            "RSI>70就立刻卖出" → 强势股可以在超买区持续几周<br>
            "RSI<30就立刻买入" → 弱势股可以在超卖区继续下跌<br><br>
            <b style='color:#34d399'>✅ 正确用法：</b><br>
            RSI作为辅助判断，配合均线使用<br>
            RSI超买 + 死叉 = 较强卖出信号<br>
            RSI超卖 + 金叉 = 较强买入信号
            </div>
            <div class='ind-rule'>
            <b>💡 记忆方法：</b><br>
            RSI就像手机电量。<br>
            电量>90%（超买）→ 快充满了，用用就会掉<br>
            电量<10%（超卖）→ 快没电了，充一充就会涨
            </div>
            </div>
            """, unsafe_allow_html=True)

    with tab3:
        st.markdown("## 🌊 MACD（指数平滑移动均线）")
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("""
            <div class='ind-card'>
            <div class='ind-title'>MACD三个组成部分</div>
            <div class='ind-body'>
            <b style='color:#fbbf24'>① MACD线（快线/黄色）</b><br>
            对价格变化敏感，反应快<br><br>
            <b style='color:#60a5fa'>② 信号线（慢线/蓝色）</b><br>
            对价格变化迟钝，反应慢<br><br>
            <b style='color:#f3f4f6'>③ 柱状图（红/绿色柱）</b><br>
            = 快线 - 慢线的差值<br>
            正值=红柱（看涨），负值=绿柱（看跌）
            </div>
            <div class='ind-rule'>
            <b>📌 金叉死叉：</b><br>
            <b style='color:#fbbf24'>MACD金叉</b> = 快线从下穿越慢线 = 买入信号<br>
            <b style='color:#f87171'>MACD死叉</b> = 快线从上穿越慢线 = 卖出信号
            </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class='ind-card'>
            <div class='ind-title'>柱状图是最早的预警信号</div>
            <div class='ind-body'>
            柱状图的变化比金叉死叉<b style='color:#fbbf24'>更早出现</b>，是提前预警！<br><br>
            <b style='color:#f87171'>🔴 红柱变长</b> = 上涨动能增强，趋势加速<br>
            <b style='color:#fbbf24'>🟡 红柱缩短</b> = 上涨动能减弱，提前警告！<br>
            <b style='color:#34d399'>🟢 绿柱变长</b> = 下跌动能增强，别抄底<br>
            <b style='color:#fbbf24'>🟡 绿柱缩短</b> = 下跌动能减弱，可以关注
            </div>
            <div class='ind-rule'>
            <b>💡 实战技巧：</b><br>
            看到红柱开始缩短，就要提高警惕准备止盈<br>
            不要等到死叉出现才反应，那时往往已经跌了一段
            </div>
            </div>
            """, unsafe_allow_html=True)

    with tab4:
        st.markdown("## 📐 布林带（Bollinger Bands）")
        st.markdown("""
        <div class='ind-card'>
        <div class='ind-title'>布林带结构</div>
        <div class='ind-body'>
        布林带 = 中轨（20日均线）± 2倍标准差<br><br>
        • <b style='color:#94a3b8'>上轨</b> = 中轨 + 2倍标准差（价格的上边界）<br>
        • <b style='color:#94a3b8'>中轨</b> = 20日均线（趋势中心）<br>
        • <b style='color:#94a3b8'>下轨</b> = 中轨 - 2倍标准差（价格的下边界）<br><br>
        统计规律：价格有<b style='color:#fbbf24'>95%</b>的时间在上下轨之间运动
        </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class='ind-card card-green'>
            <div class='ind-title'>4种常见形态</div>
            <div class='ind-body'>
            <b style='color:#34d399'>① 触碰下轨</b> → 支撑区域，可能反弹<br><br>
            <b style='color:#f87171'>② 触碰上轨</b> → 压力区域，注意回调<br><br>
            <b style='color:#fbbf24'>③ 突破上轨</b> → 超强势突破，动能极强<br><br>
            <b style='color:#60a5fa'>④ 带宽收窄</b> → 蓄势待发，即将大行情
            </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class='ind-card card-gold'>
            <div class='ind-title'>💡 最重要的信号：带宽收窄</div>
            <div class='ind-body'>
            当布林带上下轨越来越靠近时，说明市场波动率极低，价格在横盘整理。<br><br>
            这就像压缩的弹簧——<br>
            压缩时间越长，爆发力越强！<br><br>
            收窄后往往跟随一波大涨或大跌，<br>
            方向不确定，等待突破再操作。
            </div>
            </div>
            """, unsafe_allow_html=True)

    with tab5:
        st.markdown("## 📦 成交量分析")
        st.markdown("""
        <div class='ind-card card-blue'>
        <div class='ind-title'>核心原则：价是方向，量是动力</div>
        <div class='ind-body'>
        成交量 = 这段时间买卖双方成交的股票数量<br><br>
        没有成交量支撑的涨跌，就像没有油的车，走不远！
        </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <table>
        <tr><th>成交量</th><th>股价方向</th><th>含义</th><th>操作建议</th></tr>
        <tr><td><b style='color:#f87171'>放量 >1.5x</b></td><td>📈 上涨</td><td>量价齐升，主力进场，最强信号</td><td>✅ 可以跟进买入</td></tr>
        <tr><td>缩量 &lt;0.7x</td><td>📈 上涨</td><td>无量上涨，缺乏动力，假突破风险</td><td>⚠️ 不要追高</td></tr>
        <tr><td><b style='color:#f87171'>放量 >1.5x</b></td><td>📉 下跌</td><td>主力出货，资金出逃，危险信号</td><td>🚨 考虑止损</td></tr>
        <tr><td>缩量 &lt;0.7x</td><td>📉 下跌</td><td>无量下跌，无人关注，观望</td><td>👀 等待企稳</td></tr>
        </table>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class='ind-card' style='margin-top:16px'>
        <div class='ind-title'>量比 = 今日量 ÷ 过去10日均量</div>
        <div class='ind-body'>
        <span class='tag-red'>量比 > 3</span> 超级放量，必有异动，重点关注<br>
        <span class='tag-gold'>量比 1.5~3</span> 明显放量，结合涨跌判断方向<br>
        <span class='tag-green'>量比 0.7~1.5</span> 正常波动，参考其他指标<br>
        <span class='tag-green'>量比 < 0.7</span> 明显缩量，市场冷清，等待
        </div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# 页面：AI选股推荐
# ══════════════════════════════════════════════
def page_scout():
    st.title("🔍 AI选股推荐")
    st.markdown("<p>输入股票代码，AI帮你分析并用大白话解释每个信号——教你看懂，不只给答案</p>", unsafe_allow_html=True)
    st.divider()

    POPULAR = {
        "英伟达": "NVDA", "苹果": "AAPL", "特斯拉": "TSLA",
        "贵州茅台": "600519.SS", "宁德时代": "300750.SZ",
        "比亚迪": "002594.SZ", "平安银行": "000001.SZ", "招商银行": "600036.SS",
    }
    st.markdown("**热门股票一键分析：**")
    cols = st.columns(8)
    for i, (label, code) in enumerate(POPULAR.items()):
        if cols[i].button(label, key=f"p_{i}"):
            st.session_state["scout_sym"] = code

    sym_in = st.text_input(
        "或手动输入代码",
        value=st.session_state.get("scout_sym", "NVDA"),
        help="美股：NVDA | 上证加.SS：600519.SS | 深证加.SZ：000001.SZ（或直接输入6位数字自动识别）"
    )
    period = st.selectbox("分析周期", ["1mo", "3mo", "6mo"], index=1,
                           format_func=lambda x: {"1mo":"近1个月","3mo":"近3个月","6mo":"近6个月"}[x])

    if st.button("🚀 开始分析", type="primary"):
        sym = sym_in.strip().upper()
        with st.spinner(f"正在获取 {sym} 数据..."):
            df, name, actual_sym = get_data(sym, period)

        if df is None or len(df) < 5:
            st.error(f"""
**{sym} 数据获取失败**

请检查格式：
- 美股直接输入代码：`NVDA` `AAPL` `TSLA`
- A股上交所（6开头）：`600519.SS`
- A股深交所（0/3开头）：`000001.SZ` `300750.SZ`
- 或直接输入6位数字，系统自动识别
            """)
            return

        df = compute_tech(df)
        signals, score = analyze_signals(df)
        latest = df.iloc[-1]; prev = df.iloc[-2]
        close = float(latest['close'])
        pct   = (close - float(prev['close'])) / float(prev['close']) * 100
        vr    = float(latest['volume']) / max(float(latest.get('vol_ma10', latest['volume'])), 1)
        rsi   = float(latest.get('RSI', 50))

        # 标题
        st.markdown(f"## {name}")
        st.caption(f"代码：{actual_sym} | 数据：{len(df)} 个交易日 | 最新：{df.index[-1].strftime('%Y-%m-%d')}")

        # 指标卡片
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("当前价格", f"{close:.2f}", f"{pct:+.2f}%")
        c2.metric("RSI强弱", f"{rsi:.1f}", "超买⚠️" if rsi>70 else "超卖🔥" if rsi<30 else "正常✅")
        c3.metric("量比", f"{vr:.2f}x", "放量🔴" if vr>1.5 else "缩量" if vr<0.7 else "正常")
        with c4:
            st.markdown("**综合评分**")
            color = "#34d399" if score>=65 else "#fbbf24" if score>=45 else "#f87171"
            cls   = "score-hi" if score>=65 else "score-md" if score>=45 else "score-lo"
            st.markdown(f"<span class='{cls}'>{score}</span><span style='color:#6b7280'>/100</span>", unsafe_allow_html=True)
        with c5:
            bull = sum(1 for _, t, *_ in signals if t == 'up')
            bear = sum(1 for _, t, *_ in signals if t == 'down')
            verdict = "看多" if bull > bear else "看空" if bear > bull else "中性"
            v_color = "#34d399" if bull>bear else "#f87171" if bear>bull else "#fbbf24"
            st.markdown("**综合倾向**")
            st.markdown(f"<span style='color:{v_color};font-size:1.4em;font-weight:700'>{verdict}</span>", unsafe_allow_html=True)

        # 完整K线图
        st.plotly_chart(draw_full_chart(df, actual_sym, name), use_container_width=True)

        # 信号解读
        st.markdown("### 🎓 信号逐一解读")
        st.markdown("<p>每个信号都告诉你：是什么 → 为什么 → 该怎么做</p>", unsafe_allow_html=True)

        for sig_name, sig_type, technical, plain, advice in signals:
            css = "sig-up" if sig_type=="up" else "sig-down" if sig_type=="down" else "sig-mid"
            st.markdown(f"""
            <div class='{css}'>
            <b style='color:#f3f4f6;font-size:1em'>{sig_name}</b>
            <div style='color:#9ca3af;font-size:0.82em;margin:4px 0'>{technical}</div>
            <div class='explain'>
            💬 <b>通俗理解：</b>{plain}<br>
            📌 <b>操作参考：</b>{advice}
            </div>
            </div>
            """, unsafe_allow_html=True)

        # AI综合点评
        if st.session_state.api_key:
            st.markdown("### 🤖 AI综合点评")
            with st.spinner("AI老师分析中..."):
                r = call_ai(f"""
股票：{name}（{actual_sym}）
现价：{close:.2f}，今日{pct:+.2f}%，RSI={rsi:.1f}，量比{vr:.2f}x
综合评分：{score}/100，看多{bull}个信号，看空{bear}个信号

请用以下结构点评（像朋友聊天，200字以内）：
1.【现在状态】一句话总结
2.【小白该怎么做】明确说买/观望/卖，说清理由
3.【最要注意】1-2个风险点
4.【学习收获】从这个案例学到什么
""")
            if r:
                st.markdown(f"<div class='ai-box'>🤖 <b>AI老师说：</b><br><br>{r.replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)
                add_xp(20)
        else:
            st.markdown("<div class='ind-card'><p>💡 填入左侧 Claude API Key，可获得AI老师的个性化点评和学习建议</p></div>", unsafe_allow_html=True)

        add_xp(10)

# ══════════════════════════════════════════════
# 页面：持仓守护
# ══════════════════════════════════════════════
def page_hold():
    st.title("🛡️ 持仓守护")
    st.markdown("<p>输入你的持仓信息，AI实时告诉你：该继续持有还是止损离场</p>", unsafe_allow_html=True)
    st.divider()

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        default_sym = st.session_state.holding.get('sym', '603993.SS') if st.session_state.holding else '603993.SS'
        sym = st.text_input("股票代码", value=default_sym, help="上证：600519.SS | 深证：000001.SZ | 美股：NVDA")
    with c2:
        default_cost = float(st.session_state.holding.get('cost', 23)) if st.session_state.holding else 23.0
        cost = st.number_input("买入成本（元）", min_value=0.01, value=default_cost, step=0.01)
    with c3:
        default_shares = int(st.session_state.holding.get('shares', 800)) if st.session_state.holding else 800
        shares = st.number_input("持仓数量（股）", min_value=1, value=default_shares, step=100)

    if st.button("🔍 分析我的持仓", type="primary"):
        st.session_state.holding = {'sym': sym.upper(), 'cost': cost, 'shares': shares}
        with st.spinner("分析中..."):
            df, name, actual_sym = get_data(sym.upper())

        if df is None or len(df) < 5:
            st.error("数据获取失败，请检查股票代码格式")
            return

        df = compute_tech(df)
        signals, score = analyze_signals(df, cost=cost)
        latest = df.iloc[-1]; prev = df.iloc[-2]
        close  = float(latest['close'])
        pct_td = (close - float(prev['close'])) / float(prev['close']) * 100
        profit = close - cost
        pnl_pct = profit / cost * 100
        total_pnl = profit * shares

        st.markdown(f"## {name}（{actual_sym}）")

        # 持仓卡片
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("我的成本", f"¥{cost:.2f}")
        c2.metric("当前价格", f"¥{close:.2f}", f"{pct_td:+.2f}%")
        c3.metric("浮动盈亏", f"¥{total_pnl:+.0f}", f"{pnl_pct:+.2f}%",
                  delta_color="normal" if total_pnl >= 0 else "inverse")
        c4.metric("持仓市值", f"¥{close*shares:,.0f}")
        with c5:
            st.markdown("**技术评分**")
            cls = "score-hi" if score>=65 else "score-md" if score>=45 else "score-lo"
            st.markdown(f"<span class='{cls}'>{score}</span><span style='color:#6b7280'>/100</span>", unsafe_allow_html=True)

        # 止损提醒
        sl5 = round(cost * 0.95, 2)
        sl8 = round(cost * 0.92, 2)

        if close <= sl5:
            st.markdown(f"""<div class='warn'>
            <b>🚨 止损警报！当前价格已触及5%止损线</b><br><br>
            现价 <b>{close:.2f}</b> 已跌破止损线 <b>{sl5}</b>（-5%）<br>
            <b>强烈建议：认真考虑止损离场，保住剩余本金。</b><br>
            <small style='color:#9ca3af'>继续等待可能面临更大损失。先出来观望，等技术好转再考虑重新入场。</small>
            </div>""", unsafe_allow_html=True)
        else:
            dist = ((close - sl5) / close * 100)
            st.markdown(f"""<div class='good'>
            <b>✅ 持仓安全区</b> — 距离止损线还有 {dist:.1f}%<br><br>
            🛡️ <b>保守止损线：¥{sl5}</b>（亏5%，约损失¥{(sl5-cost)*shares:,.0f}）<br>
            🛡️ <b>普通止损线：¥{sl8}</b>（亏8%，约损失¥{(sl8-cost)*shares:,.0f}）<br>
            <small style='color:#9ca3af'>建议现在就在股票App里设置条件单，到价自动卖出！</small>
            </div>""", unsafe_allow_html=True)

        # 完整K线图（带成本线）
        st.plotly_chart(draw_full_chart(df, actual_sym, name, cost=cost), use_container_width=True)

        # 持有 vs 卖出
        st.markdown("### 📊 该继续持有，还是止损离场？")
        bull_sigs = [(n,_,t,p,a) for n,s,t,p,a in signals if s=='up']
        bear_sigs = [(n,_,t,p,a) for n,s,t,p,a in signals if s=='down']

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**✅ 支持持有的信号**")
            if bull_sigs:
                for n,_,t,p,a in bull_sigs:
                    st.markdown(f"<div class='good' style='padding:10px 14px'><b>{n}</b><br><small style='color:#9ca3af'>{p}</small></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='ind-card'><p>暂无明显看多信号</p></div>", unsafe_allow_html=True)

        with col2:
            st.markdown("**⚠️ 需要警惕的信号**")
            if bear_sigs:
                for n,_,t,p,a in bear_sigs:
                    st.markdown(f"<div class='warn' style='padding:10px 14px'><b>{n}</b><br><small style='color:#9ca3af'>{p}</small></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='ind-card'><p>暂无明显看空信号</p></div>", unsafe_allow_html=True)

        # 综合判断
        bull_n = len(bull_sigs); bear_n = len(bear_sigs)
        if bear_n >= 3 or close <= sl5:
            verdict, vcolor, vbg = "⚠️ 建议考虑止损", "#f87171", "rgba(248,113,113,0.1)"
            reason  = f"看空信号{bear_n}个多于看多信号{bull_n}个，技术面偏弱。"
            action  = f"建议分批减仓，或价格跌破 ¥{sl5} 时果断止损。"
        elif bull_n >= 3 and score >= 60:
            verdict, vcolor, vbg = "✅ 可以继续持有", "#34d399", "rgba(52,211,153,0.08)"
            reason  = f"看多信号{bull_n}个，技术评分{score}分，趋势偏好。"
            action  = f"继续持有，同时严格执行止损 ¥{sl5}，不能因为涨了就忘记风险。"
        else:
            verdict, vcolor, vbg = "🟡 中性观望", "#fbbf24", "rgba(251,191,36,0.08)"
            reason  = f"多空信号均衡（看多{bull_n}个，看空{bear_n}个），方向不明。"
            action  = f"可以先持仓等待，但止损 ¥{sl5} 一旦触发必须执行，不能手软。"

        st.markdown(f"""
        <div style='background:{vbg};border:2px solid {vcolor};border-radius:14px;padding:24px;margin:16px 0;text-align:center'>
        <div style='color:{vcolor};font-size:1.6em;font-weight:700'>{verdict}</div>
        <p style='margin:12px 0'>{reason}</p>
        <div style='background:rgba(255,255,255,0.05);border-radius:8px;padding:14px;margin-top:8px'>
        <b style='color:#f3f4f6'>📌 建议操作：</b><span style='color:#d1d5db'>{action}</span>
        </div>
        </div>
        """, unsafe_allow_html=True)

        # AI持仓点评
        if st.session_state.api_key:
            st.markdown("### 🤖 AI老师持仓点评")
            with st.spinner("AI分析你的持仓..."):
                r = call_ai(f"""
股票小白的持仓：{name}（{actual_sym}）
成本：{cost}元，现价：{close:.2f}元，盈亏：{pnl_pct:+.2f}%（共{total_pnl:+.0f}元）
技术评分：{score}/100，看多{bull_n}个信号，看空{bear_n}个信号

请像朋友聊天一样给出建议（200字以内）：
1.【当前处境】一句话说清楚
2.【我的建议】明确：继续持有/减仓/止损，为什么
3.【止损红线】跌到多少必须离场
4.【止盈目标】如果涨，目标价多少
5.【给新手的话】一句鼓励或提醒
""")
            if r:
                st.markdown(f"<div class='ai-box'>🤖 <b>AI老师说：</b><br><br>{r.replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='ind-card'><p>💡 填入 Claude API Key，获得AI老师对你持仓的个性化建议</p></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# 页面：闯关练习
# ══════════════════════════════════════════════
QUIZZES = [
    {"q":"红色K线（阳线）代表什么？","opts":["A. 今天跌了","B. 今天涨了","C. 成交量很大","D. 要退市了"],"ans":"B","exp":"红色阳线=收盘价>开盘价=今天涨了。记忆：红色=喜庆=涨！"},
    {"q":"5日均线从下穿越20日均线向上，叫什么信号？","opts":["A. 死叉","B. 布林突破","C. 金叉","D. RSI超买"],"ans":"C","exp":"短期线上穿长期线=金叉=买入信号。金=金色=好事！"},
    {"q":"RSI值达到82，说明什么？","opts":["A. 股票很便宜可以买","B. 超卖区，反弹机会","C. 超买区，有回调风险","D. 成交量很小"],"ans":"C","exp":"RSI>70进入超买区，涨得太猛，就像跑步跑到快累倒，需要歇歇（回调）。"},
    {"q":"成交量是平时的3倍，同时股价大涨5%，这叫什么？","opts":["A. 缩量上涨","B. 量价齐升","C. RSI超卖反弹","D. 死叉信号"],"ans":"B","exp":"量价齐升=最健康的上涨！大量资金涌入+价格上涨，说明市场高度认可，是强烈买入信号。"},
    {"q":"MACD红色柱状图越来越长，代表什么？","opts":["A. 上涨动能减弱","B. 下跌动能增强","C. 上涨动能增强","D. 即将暴跌"],"ans":"C","exp":"MACD红柱变长=快线和慢线差距扩大=上涨动力越来越足。就像顺风越来越大，骑得越来越快。"},
    {"q":"买入股票后，最重要的第一步是什么？","opts":["A. 等涨到最高点","B. 告诉朋友","C. 立刻设好止损","D. 继续买更多"],"ans":"C","exp":"止损是保命的！买入后立刻在App里设好止损线（亏5%就走），是新手最重要的纪律。"},
    {"q":"K线上影线很长，说明什么？","opts":["A. 下方支撑强","B. 上方抛压重","C. 成交量放大","D. 股价要暴涨"],"ans":"B","exp":"上影线长=价格涨上去了但被卖方打下来=上方有大量人在卖=压力重。"},
    {"q":"布林带「收口」（上下轨靠近），预示什么？","opts":["A. 股票要退市","B. 即将有大行情","C. RSI超买","D. 成交量缩小"],"ans":"B","exp":"布林带收口=波动率低=蓄势。就像弹簧压缩，压得越久弹出越猛。收口后往往有方向性大行情。"},
    {"q":"单只股票最多用多少总资金买入？","opts":["A. 全部资金","B. 一半资金","C. 1/3资金","D. 随意"],"ans":"C","exp":"铁律：单只股票不超过总资金的1/3。这样即使这只股票大跌，你总资金损失有限，还能继续操作。"},
    {"q":"MACD红柱开始缩短，说明什么？","opts":["A. 继续大涨","B. 上涨动能在减弱，要注意","C. 立刻暴跌","D. 可以加仓"],"ans":"B","exp":"红柱缩短=上涨动力在减弱，这是比死叉更早出现的预警信号！看到红柱缩短就要提高警惕，考虑止盈。"},
]

def page_quiz():
    st.title("🧩 闯关练习")
    st.markdown("<p>检验学习成果，每题都有详细解析，答错了才学得最快！</p>", unsafe_allow_html=True)
    st.divider()

    c1, c2, c3 = st.columns(3)
    total   = st.session_state.quiz_total
    correct = st.session_state.quiz_score
    c1.metric("已答题数", f"{total} 题")
    c2.metric("答对题数", f"{correct} 题")
    c3.metric("正确率",   f"{int(correct/max(total,1)*100)}%")
    st.divider()

    if 'cur_q' not in st.session_state or st.session_state.get('q_done', False):
        if st.button("🎲 随机出一道题", type="primary"):
            st.session_state.cur_q  = random.choice(QUIZZES)
            st.session_state.q_done = False
            st.rerun()

    if 'cur_q' in st.session_state and not st.session_state.get('q_done', False):
        q = st.session_state.cur_q
        st.markdown(f"<div class='card'><b style='color:#f3f4f6;font-size:1.05em'>📝 {q['q']}</b></div>", unsafe_allow_html=True)
        choice = st.radio("选择你的答案：", q['opts'], key="qr")
        if st.button("✅ 提交答案"):
            st.session_state.quiz_total += 1
            if choice[0] == q['ans']:
                st.session_state.quiz_score += 1
                add_xp(15)
                st.success("🎉 回答正确！+15 XP")
            else:
                add_xp(5)
                st.error(f"❌ 答错了，正确答案是 {q['ans']}，不过答错了才会记住，+5 XP 鼓励！")
            st.markdown(f"<div class='explain'><b>📖 解析：</b>{q['exp']}</div>", unsafe_allow_html=True)
            st.session_state.q_done = True

# ══════════════════════════════════════════════
# 路由
# ══════════════════════════════════════════════
p = st.session_state.page
if   p == "home":      page_home()
elif p == "learn":     page_learn()
elif p == "indicator": page_indicator()
elif p == "scout":     page_scout()
elif p == "hold":      page_hold()
elif p == "quiz":      page_quiz()
