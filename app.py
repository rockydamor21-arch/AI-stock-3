import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import anthropic
import random
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="股票学院", page_icon="🌱", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=ZCOOL+XiaoWei&family=Noto+Sans+SC:wght@300;400;500;700&display=swap');
:root {
  --bg:#0f1923; --bg2:#162030; --bg3:#1e2d40;
  --gold:#f0b429; --green:#38ef7d; --red:#ff6b6b; --blue:#4ecdc4;
  --text:#d4e0ee; --muted:#6b8299;
}
html,body,[class*="css"]{font-family:'Noto Sans SC',sans-serif;background:var(--bg)!important;color:var(--text);}
.stApp{background:var(--bg)!important;}
.main .block-container{padding:1.5rem 2rem;max-width:1400px;}
section[data-testid="stSidebar"]{background:var(--bg2)!important;border-right:1px solid #1e3050;}
.hero{font-family:'ZCOOL XiaoWei',serif;font-size:2.2em;background:linear-gradient(135deg,var(--gold),var(--green));-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.stButton>button{background:var(--bg3);color:var(--text);border:1px solid #2a3f55;border-radius:10px;padding:10px 6px;font-size:0.85em;width:100%;transition:all 0.2s;}
.stButton>button:hover{border-color:var(--gold);color:var(--gold);}
.card{background:var(--bg2);border:1px solid #1e3050;border-radius:14px;padding:20px 22px;margin:10px 0;}
.card-green{border-left:4px solid var(--green);}
.card-red{border-left:4px solid var(--red);}
.card-gold{border-left:4px solid var(--gold);}
.card-blue{border-left:4px solid var(--blue);}
.signal-bullish{background:rgba(56,239,125,0.08);border-left:3px solid var(--green);padding:10px 14px;border-radius:6px;margin:6px 0;}
.signal-bearish{background:rgba(255,107,107,0.08);border-left:3px solid var(--red);padding:10px 14px;border-radius:6px;margin:6px 0;}
.signal-neutral{background:rgba(240,180,41,0.08);border-left:3px solid var(--gold);padding:10px 14px;border-radius:6px;margin:6px 0;}
.ai-box{background:linear-gradient(135deg,#0d2a1b,#0f2035);border:1px solid #00d4aa55;border-radius:14px;padding:22px;line-height:2;font-size:0.93em;}
.explain{background:rgba(78,205,196,0.06);border:1px solid #4ecdc433;border-radius:8px;padding:12px;margin:6px 0;font-size:0.88em;line-height:1.9;}
.warn-box{background:rgba(255,107,107,0.08);border:2px solid var(--red);border-radius:12px;padding:18px;margin:10px 0;}
.progress-wrap{background:var(--bg3);border-radius:20px;height:8px;overflow:hidden;margin:4px 0;}
.progress-fill{height:100%;border-radius:20px;background:linear-gradient(90deg,var(--green),var(--gold));}
.badge{display:inline-block;background:var(--bg3);border:1px solid var(--gold);border-radius:10px;padding:6px 12px;margin:4px;font-size:0.82em;}
.sell-signal{background:rgba(255,107,107,0.12);border:2px solid var(--red);border-radius:10px;padding:14px;margin:8px 0;}
.hold-signal{background:rgba(56,239,125,0.08);border:2px solid var(--green);border-radius:10px;padding:14px;margin:8px 0;}
</style>
""", unsafe_allow_html=True)

# ── Session State ────────────────────────────────────────────
for k,v in {"page":"home","xp":0,"level":1,"learned":[],"quiz_score":0,
            "quiz_total":0,"api_key":"","holding":None,"diary":[]}.items():
    if k not in st.session_state: st.session_state[k]=v

def add_xp(n):
    st.session_state.xp += n
    needed = st.session_state.level * 100
    if st.session_state.xp >= needed:
        st.session_state.xp -= needed
        st.session_state.level += 1
        st.toast(f"🎉 升级！Lv.{st.session_state.level}", icon="🏆")

# ── 侧边栏 ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌱 股票学院")
    lv=st.session_state.level; xp=st.session_state.xp; needed=lv*100
    st.markdown(f"**Lv.{lv}** · {xp}/{needed} XP")
    st.markdown(f"<div class='progress-wrap'><div class='progress-fill' style='width:{int(xp/needed*100)}%'></div></div>",unsafe_allow_html=True)
    st.divider()
    for icon,key,label in [("🏠","home","首页"),("📚","learn","K线课堂"),
                            ("🔍","scout","AI选股"),("🛡️","hold","持仓守护"),
                            ("🧩","quiz","闯关练习"),("🗂️","glossary","术语速查")]:
        if st.button(f"{icon} {label}",key=f"nav_{key}"): st.session_state.page=key
    st.divider()
    st.session_state.api_key = st.text_input("Claude API Key",value=st.session_state.api_key,type="password",help="填入后开启AI功能")
    st.caption("[获取Key](https://console.anthropic.com)")

# ── AI调用 ───────────────────────────────────────────────────
def call_ai(prompt, system="你是专门教股票小白的老师，语言亲切通俗，善用生活比喻，用中文回答。"):
    if not st.session_state.api_key: return None
    try:
        client = anthropic.Anthropic(api_key=st.session_state.api_key)
        msg = client.messages.create(model="claude-opus-4-6",max_tokens=1500,
            system=system,messages=[{"role":"user","content":prompt}])
        return msg.content[0].text
    except Exception as e:
        return f"AI暂时无法回应：{e}"

# ── 数据获取 ─────────────────────────────────────────────────
@st.cache_data(ttl=300,show_spinner=False)
def get_data(symbol,period="3mo"):
    try:
        t=yf.Ticker(symbol)
        df=t.history(period=period,interval="1d",timeout=15)
        if df is None or len(df)<5: return None,symbol
        df.columns=[c[0] if isinstance(c,tuple) else c for c in df.columns]
        df=df[['Open','High','Low','Close','Volume']].copy()
        df.columns=['open','high','low','close','volume']
        df=df.astype(float).dropna()
        try: info=t.info; name=info.get('longName') or info.get('shortName') or symbol
        except: name=symbol
        return df,name
    except: return None,symbol

def compute_tech(df):
    c=df['close']; v=df['volume']; n=len(df)
    df['EMA5'] =ta.ema(c,length=min(5,n-1))
    df['EMA20']=ta.ema(c,length=min(20,n-1))
    df['EMA60']=ta.ema(c,length=min(60,n-1))
    df['RSI']  =ta.rsi(c,length=min(14,n-1))
    if n>=22:
        bb=ta.bbands(c,length=20,std=2)
        if bb is not None: df=pd.concat([df,bb],axis=1)
    if n>=35:
        macd=ta.macd(c)
        if macd is not None: df=pd.concat([df,macd],axis=1)
    df['vol_ma10']=v.rolling(min(10,n)).mean()
    df.dropna(inplace=True)
    return df

def analyze_signals(df, cost=None):
    """分析技术信号，返回信号列表和综合评分"""
    if df is None or len(df)<2: return [],50
    latest=df.iloc[-1]; prev=df.iloc[-2]
    close=float(latest['close']); vol_avg=float(latest.get('vol_ma10',latest['volume']))
    vr=float(latest['volume'])/max(vol_avg,1)
    rsi=float(latest.get('RSI',50))
    pct=(close-float(prev['close']))/float(prev['close'])*100
    signals=[]; score=50

    # 均线
    e5=float(latest.get('EMA5',close)); e20=float(latest.get('EMA20',close))
    e60=float(latest.get('EMA60',close))
    if close>e5>e20:
        score+=10; signals.append(("✅ 均线多头排列","bullish",
            f"价格({close:.2f}) > 5日线({e5:.2f}) > 20日线({e20:.2f})",
            "就像爬楼梯，每一层都比上一层高，趋势向上是健康的。","可以持股或轻仓买入"))
    elif close<e5<e20:
        score-=10; signals.append(("⚠️ 均线空头排列","bearish",
            f"价格({close:.2f}) < 5日线({e5:.2f}) < 20日线({e20:.2f})",
            "就像下楼梯，趋势向下，不宜持仓。","建议观望或考虑止损"))
    if close>e60:
        score+=5; signals.append(("✅ 站稳长期均线","bullish",
            f"价格高于60日均线({e60:.2f})","中长期趋势健康，大方向向上。","中线持股信心增加"))
    else:
        score-=5; signals.append(("⚠️ 跌破长期均线","bearish",
            f"价格低于60日均线({e60:.2f})","中长期趋势偏弱。","中线要谨慎"))

    # 金叉死叉检测
    if len(df)>=2:
        for i in range(len(df)-1, max(len(df)-15,0),-1):
            e5n=df['EMA5'].iloc[i]; e5p=df['EMA5'].iloc[i-1]
            e20n=df['EMA20'].iloc[i]; e20p=df['EMA20'].iloc[i-1]
            if e5p<=e20p and e5n>e20n:
                days_ago=len(df)-1-i
                score+=8; signals.append((f"🌟 {'今日' if days_ago==0 else f'{days_ago}天前'}出现金叉","bullish",
                    "5日均线从下方穿越20日均线","金叉是经典买入信号，就像绿灯亮了可以出发。","金叉后通常有一段上涨行情"))
                break
            elif e5p>=e20p and e5n<e20n:
                days_ago=len(df)-1-i
                score-=8; signals.append((f"💀 {'今日' if days_ago==0 else f'{days_ago}天前'}出现死叉","bearish",
                    "5日均线从上方穿越20日均线","死叉是卖出信号，就像红灯亮了要停车。","死叉后注意止损"))
                break

    # 量能
    if vr>2:
        sig_type="bullish" if pct>0 else "bearish"
        score+=(8 if pct>0 else -8)
        signals.append((f"{'🚀 放量大涨' if pct>0 else '🚨 放量下跌'}",sig_type,
            f"成交量是平时的{vr:.1f}倍",
            f"{'成交量大+上涨=主力在买入，信号强烈！' if pct>0 else '成交量大+下跌=有人在大量抛售，危险信号！'}",
            "放量上涨可跟进" if pct>0 else "放量下跌要止损"))
    elif vr<0.6:
        signals.append(("😴 成交缩量","neutral",f"成交量只有平时的{vr:.1f}倍",
            "交易冷清，大家都在观望，行情缺乏动力。","等量能放出来再判断方向"))

    # RSI
    if rsi>=70:
        score-=8; signals.append(("⚠️ RSI超买区","bearish",f"RSI={rsi:.1f}（超过70进入超买区）",
            "就像弹簧拉得太紧，容易回弹。涨得太猛，注意回调。","考虑部分止盈，新入场者别追高"))
    elif rsi<=30:
        score+=8; signals.append(("🔥 RSI超卖区","bullish",f"RSI={rsi:.1f}（低于30进入超卖区）",
            "就像弹簧压得太低，可能要弹起来。跌得太猛，可能反弹。","小仓试探，等止跌信号确认"))
    else:
        tag="偏强" if rsi>55 else "偏弱" if rsi<45 else "中性"
        signals.append((f"✅ RSI{tag}({rsi:.1f})","bullish" if rsi>55 else "bearish" if rsi<45 else "neutral",
            f"RSI={rsi:.1f}，处于正常区间","RSI运行正常，不存在极端超买超卖。","结合均线判断方向"))

    # 布林带
    bbu_c=[c for c in df.columns if 'BBU' in c]
    bbl_c=[c for c in df.columns if 'BBL' in c]
    if bbu_c and bbl_c:
        bbu=float(latest[bbu_c[0]]); bbl=float(latest[bbl_c[0]])
        if close>bbu:
            score+=6; signals.append(("🔴 突破布林上轨","bullish",f"价格{close:.2f}冲出上轨{bbu:.2f}",
                "价格冲出了正常波动范围，说明这次上涨非常强势。","强势信号，但注意高位风险"))
        elif close<bbl:
            score-=6; signals.append(("🔵 跌破布林下轨","bearish",f"价格{close:.2f}跌破下轨{bbl:.2f}",
                "价格跌出了正常范围，说明下跌很猛烈。","超卖可能反弹，但先别急着买"))

    # MACD
    mh_c=[c for c in df.columns if 'MACDh' in c]
    if mh_c and len(df)>=2:
        h=float(latest[mh_c[0]]); hp=float(prev[mh_c[0]])
        if h>0 and h>hp:
            score+=6; signals.append(("🔴 MACD红柱扩大","bullish",f"MACD柱从{hp:.3f}增大到{h:.3f}",
                "上涨动力越来越强，就像顺风骑车越来越快。","趋势向好，持股"))
        elif h<0 and h<hp:
            score-=6; signals.append(("🔵 MACD绿柱扩大","bearish",f"MACD柱从{hp:.3f}减小到{h:.3f}",
                "下跌动力越来越强，就像逆风骑车越来越累。","不宜入场"))
        elif h>0 and h<hp:
            score-=2; signals.append(("🟡 MACD红柱收缩","neutral",f"上涨动能开始减弱",
                "就像顺风骑车但风速在减小，要注意变盘。","高位注意止盈"))

    # 持仓成本分析
    if cost:
        profit_pct=(close-cost)/cost*100
        if profit_pct>=8:
            signals.append((f"💰 浮盈{profit_pct:.1f}%","bullish",f"成本{cost}，现价{close:.2f}，浮盈{profit_pct:.1f}%",
                f"已经赚了{profit_pct:.1f}%，可以考虑部分止盈锁定利润。","建议卖出1/3锁定利润"))
        elif profit_pct<=-5:
            signals.append((f"🚨 亏损{abs(profit_pct):.1f}%","bearish",f"成本{cost}，现价{close:.2f}，亏损{abs(profit_pct):.1f}%",
                "已触及警戒线，需要认真考虑是否止损。","建议重新评估持仓逻辑"))

    return signals, max(0,min(100,score))

# ── K线图 ────────────────────────────────────────────────────
def draw_chart(df, sym, name, cost=None):
    has_macd=any('MACDh' in c for c in df.columns)
    rows=3 if has_macd else 2
    heights=[0.6,0.2,0.2] if has_macd else [0.7,0.3]
    fig=make_subplots(rows=rows,cols=1,shared_xaxes=True,vertical_spacing=0.03,row_heights=heights)
    fig.add_trace(go.Candlestick(x=df.index,open=df['open'],high=df['high'],
        low=df['low'],close=df['close'],
        increasing_line_color='#ff6b6b',decreasing_line_color='#4ecdc4',name='K线'),row=1,col=1)
    for col_n,color,w in [('EMA5','#f0b429',1.5),('EMA20','#4ecdc4',1.5),('EMA60','#a78bfa',1.5)]:
        if col_n in df.columns:
            fig.add_trace(go.Scatter(x=df.index,y=df[col_n],line=dict(color=color,width=w),name=col_n),row=1,col=1)
    bbu_c=[c for c in df.columns if 'BBU' in c]; bbl_c=[c for c in df.columns if 'BBL' in c]
    if bbu_c and bbl_c:
        fig.add_trace(go.Scatter(x=df.index,y=df[bbu_c[0]],line=dict(color='rgba(200,200,255,0.3)',width=1,dash='dash'),name='布林上轨'),row=1,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df[bbl_c[0]],line=dict(color='rgba(200,200,255,0.3)',width=1,dash='dash'),name='布林下轨',fill='tonexty',fillcolor='rgba(150,150,255,0.03)'),row=1,col=1)
    # 金叉死叉标注
    if 'EMA5' in df.columns and 'EMA20' in df.columns:
        for i in range(1,len(df)):
            e5n=df['EMA5'].iloc[i]; e5p=df['EMA5'].iloc[i-1]
            e20n=df['EMA20'].iloc[i]; e20p=df['EMA20'].iloc[i-1]
            if e5p<=e20p and e5n>e20n:
                fig.add_annotation(x=df.index[i],y=float(df['low'].iloc[i])*0.995,
                    text="金叉",showarrow=True,arrowhead=2,arrowcolor='#f0b429',
                    font=dict(color='#f0b429',size=10),ax=0,ay=20,row=1,col=1)
            elif e5p>=e20p and e5n<e20n:
                fig.add_annotation(x=df.index[i],y=float(df['high'].iloc[i])*1.005,
                    text="死叉",showarrow=True,arrowhead=2,arrowcolor='#ff6b6b',
                    font=dict(color='#ff6b6b',size=10),ax=0,ay=-20,row=1,col=1)
    # 成本线
    if cost:
        fig.add_hline(y=cost,line_color='#ffd700',line_width=1.5,line_dash='dash',
            annotation_text=f"成本线 {cost}",annotation_position="right",row=1,col=1)
    # 成交量
    vc=['#ff6b6b' if df['close'].iloc[i]>=df['open'].iloc[i] else '#4ecdc4' for i in range(len(df))]
    fig.add_trace(go.Bar(x=df.index,y=df['volume'],marker_color=vc,opacity=0.6,name='成交量'),row=2,col=1)
    if 'vol_ma10' in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df['vol_ma10'],line=dict(color='#f0b429',width=1),name='量10均'),row=2,col=1)
    # MACD
    if has_macd:
        mh_c=[c for c in df.columns if 'MACDh' in c]
        ml_c=[c for c in df.columns if c.startswith('MACD_')]
        ms_c=[c for c in df.columns if c.startswith('MACDs')]
        mc=['#ff6b6b' if v>=0 else '#4ecdc4' for v in df[mh_c[0]]]
        fig.add_trace(go.Bar(x=df.index,y=df[mh_c[0]],marker_color=mc,name='MACD柱',opacity=0.8),row=3,col=1)
        if ml_c: fig.add_trace(go.Scatter(x=df.index,y=df[ml_c[0]],line=dict(color='#f0b429',width=1.5),name='MACD'),row=3,col=1)
        if ms_c: fig.add_trace(go.Scatter(x=df.index,y=df[ms_c[0]],line=dict(color='#a78bfa',width=1.5),name='Signal'),row=3,col=1)
        fig.add_hline(y=0,line_color='rgba(255,255,255,0.15)',row=3,col=1)
    fig.update_layout(template="plotly_dark",paper_bgcolor='#162030',plot_bgcolor='#0f1923',
        height=620,xaxis_rangeslider_visible=False,
        title=dict(text=f"{name}（{sym}）技术分析图",font=dict(size=15,color='#d4e0ee')),
        legend=dict(orientation='h',y=1.02,font=dict(size=10)),
        margin=dict(l=40,r=20,t=60,b=20))
    for i in range(1,rows+1):
        fig.update_xaxes(showgrid=True,gridcolor='rgba(255,255,255,0.04)',row=i,col=1)
        fig.update_yaxes(showgrid=True,gridcolor='rgba(255,255,255,0.04)',row=i,col=1)
    return fig

# ════════════════════════════════════════════════════════════
# 页面：首页
# ════════════════════════════════════════════════════════════
def page_home():
    st.markdown("<div class='hero'>🌱 股票学院 · 新手成长营</div>",unsafe_allow_html=True)
    st.markdown("<span style='color:#6b8299'>从零开始，边学边用，逐步掌握选股能力</span>",unsafe_allow_html=True)
    st.divider()
    c1,c2,c3,c4=st.columns(4)
    c1.metric("当前等级",f"Lv.{st.session_state.level}")
    c2.metric("经验值",f"{st.session_state.xp} XP")
    c3.metric("已学课程",f"{len(st.session_state.learned)}/6 节")
    c4.metric("闯关正确率",f"{int(st.session_state.quiz_score/max(st.session_state.quiz_total,1)*100)}%")
    st.divider()

    # 新手必看
    st.markdown("### 📌 新手必看：3条铁律")
    st.markdown("""
    <div class='warn-box'>
    <b>🛡️ 第一条：先设止损，再谈赚钱</b><br>
    买入前就决定好：跌多少我一定卖。推荐亏损不超过<b>5%</b>就止损离场。保住本金，才有下次机会。<br><br>
    <b>📦 第二条：仓位不超过三分之一</b><br>
    单只股票最多用总资金的1/3。鸡蛋不放一个篮子，避免一次被套就全军覆没。<br><br>
    <b>🚫 第三条：别人推荐的股，先问自己"为什么涨"</b><br>
    说不出理由就不买。不懂的股票，再便宜也是陷阱。
    </div>
    """,unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🗺️ 你的成长路线")
    steps=[("Lv.1","🌱 K线入门","认识涨跌红绿",1),("Lv.2","📊 指标理解","RSI/MACD/均线",2),
           ("Lv.3","🔍 形态识别","金叉死叉头肩",3),("Lv.4","🎯 选股逻辑","量价配合",4),
           ("Lv.5","💼 实战策略","止损止盈仓位",5)]
    cols=st.columns(5)
    for i,(lv_tag,title,desc,req) in enumerate(steps):
        with cols[i]:
            unlocked=st.session_state.level>=req
            color="#38ef7d" if unlocked else "#2a3f55"
            st.markdown(f"""<div class='card' style='text-align:center;border-top:3px solid {color};opacity:{"1" if unlocked else "0.5"}'>
            <div style='color:{color};font-size:1.3em'>{"✅" if unlocked else "🔒"}</div>
            <b style='color:{color}'>{lv_tag}</b><br><span style='font-size:0.9em'>{title}</span><br>
            <small style='color:#6b8299'>{desc}</small></div>""",unsafe_allow_html=True)

    st.divider()
    col1,col2,col3=st.columns(3)
    with col1:
        st.markdown("<div class='card card-green'><b>📚 开始学习</b><br><br>6节系统课，每节5分钟<br>从K线到止损，全覆盖<br><br><small style='color:#6b8299'>完成全部课程解锁Lv.3</small></div>",unsafe_allow_html=True)
        if st.button("去学习 →",key="h_learn"): st.session_state.page="learn"
    with col2:
        st.markdown("<div class='card card-gold'><b>🔍 AI帮我选股</b><br><br>输入任意股票<br>AI用大白话解释每个信号<br>教你看懂，不只给答案<br><br><small style='color:#6b8299'>每次分析+20XP</small></div>",unsafe_allow_html=True)
        if st.button("去选股 →",key="h_scout"): st.session_state.page="scout"
    with col3:
        st.markdown("<div class='card card-red'><b>🛡️ 持仓守护</b><br><br>输入你持有的股票和成本<br>AI实时告诉你：该继续持有<br>还是该止损离场<br><br><small style='color:#6b8299'>最重要的功能</small></div>",unsafe_allow_html=True)
        if st.button("去守护 →",key="h_hold"): st.session_state.page="hold"

# ════════════════════════════════════════════════════════════
# 页面：K线课堂
# ════════════════════════════════════════════════════════════
LESSONS=[
    {"id":"kline","title":"🕯️ 第一课：读懂一根K线","xp":30,"content":"""
**K线记录4个价格：开盘价、收盘价、最高价、最低价**

🔴 **红色K线（阳线）** = 收盘价 > 开盘价 = 今天涨了

🟢 **绿色K线（阴线）** = 收盘价 < 开盘价 = 今天跌了

**上下的细线叫"影线"：**
- 上影线长 = 涨上去了但又被打下来 → 上方有卖压
- 下影线长 = 跌下去了但又被买回来 → 下方有支撑

**记住这句话：** 影线越长，说明那个方向的力量越强但没守住。
""","points":["K线=开高低收4价","红涨绿跌","上影线=上方压力，下影线=下方支撑"]},

    {"id":"ma","title":"📈 第二课：均线和金叉死叉","xp":30,"content":"""
**均线 = 过去N天的平均价格**

| 均线 | 含义 |
|------|------|
| 5日均线 | 最近一周平均成本 |
| 20日均线 | 最近一个月平均成本 |
| 60日均线 | 近三个月平均成本 |

**价格在均线上方** = 大家都赚钱 = 趋势向好

**价格在均线下方** = 大家都亏钱 = 趋势偏弱

🌟 **金叉 = 短期线穿越长期线向上** = 买入信号

💀 **死叉 = 短期线穿越长期线向下** = 卖出信号
""","points":["均线=平均持仓成本","价格>均线=多头","金叉买 死叉卖"]},

    {"id":"rsi","title":"⚡ 第三课：RSI超买超卖","xp":40,"content":"""
**RSI是0到100之间的数字，衡量涨跌力道**

| RSI | 含义 | 操作 |
|-----|------|------|
| >70 | 超买，涨过头了 | 考虑止盈 |
| 50-70 | 偏强，趋势向上 | 可以持股 |
| 30-50 | 偏弱，趋势向下 | 谨慎持仓 |
| <30 | 超卖，跌过头了 | 关注反弹 |

**通俗比喻：** RSI就像运动员的体力值。>70体力快耗尽（要休息=回调），<30体力恢复中（要出发=反弹）。

**注意：** RSI只是参考，不能单独使用！
""","points":["RSI 0-100","超买>70 超卖<30","单独使用不可靠"]},

    {"id":"macd","title":"🌊 第四课：MACD动能指标","xp":40,"content":"""
**MACD由三部分组成：**
- 快线（MACD线）：对价格变化敏感
- 慢线（Signal线）：对价格变化迟钝
- 柱状图：快线和慢线的差

**金叉：** 快线从下穿慢线 → 买入信号 🌟

**死叉：** 快线从上穿慢线 → 卖出信号 💀

**柱状图：**
- 红柱变长 = 上涨动能增强
- 红柱变短 = 上涨动能减弱，注意！
- 绿柱变长 = 下跌动能增强

**比喻：** MACD就像两辆车的速度差。快车追上慢车=加速向上（金叉）；快车又慢下来=开始减速（死叉）。
""","points":["MACD金叉=买 死叉=卖","红柱扩大=动能增强","结合均线一起看"]},

    {"id":"volume","title":"📦 第五课：成交量是主力的脚印","xp":40,"content":"""
**成交量 = 市场参与热度**

| 量 | 价 | 含义 | 操作 |
|----|----|------|------|
| 放量 | 上涨 | 主力进场，强烈信号 | 可跟进 |
| 缩量 | 上涨 | 缺乏支撑，谨慎 | 别追高 |
| 放量 | 下跌 | 主力出货，危险 | 考虑止损 |
| 缩量 | 下跌 | 无人关注，观望 | 等待 |

**量比 > 2 = 明显放量，值得关注**

**记住：价是方向，量是动力。没有量的涨跌都是虚的。**
""","points":["量价齐升=最强信号","放量下跌=危险","量比>2值得关注"]},

    {"id":"stop_loss","title":"🛡️ 第六课：止损止盈——最重要的一课","xp":50,"content":"""
**止损 = 亏到某个价格就卖，不犹豫**

为什么必须止损？
- 小亏可以再赚回来，大亏很难翻身
- 亏50%需要赚100%才能回本！

**新手止损参考：**
- 保守型：买入后跌3%就走
- 普通型：买入后跌5%就走
- 激进型：买入后跌8%就走

**止盈 = 赚到目标就卖，不贪**
- 建议分批止盈：涨5%卖1/3，涨10%卖1/3，剩余自由持有

**铁律：宁可卖早了错过后续上涨，也不要因为"舍不得"被套住。**

**仓位管理：单只股票不超过总资金的1/3！**
""","points":["止损=亏5%就走","分批止盈","单股不超1/3仓位"]},
]

def page_learn():
    st.markdown("# 📚 K线课堂")
    st.markdown("每学完一节获得经验值，打好基础才能真正看懂股票")
    st.divider()
    for lesson in LESSONS:
        learned=lesson['id'] in st.session_state.learned
        with st.expander(f"{'✅' if learned else '📖'} {lesson['title']}  ·  +{lesson['xp']}XP",expanded=False):
            st.markdown(lesson['content'])
            st.markdown("**🔑 本课要点：**")
            for p in lesson['points']:
                st.markdown(f"<span style='background:rgba(56,239,125,0.1);border:1px solid #38ef7d;border-radius:20px;padding:3px 10px;font-size:0.8em;margin:2px;display:inline-block'>✓ {p}</span>",unsafe_allow_html=True)
            st.markdown("")
            col1,col2=st.columns([1,2])
            with col1:
                if not learned:
                    if st.button(f"✅ 完成 +{lesson['xp']}XP",key=f"done_{lesson['id']}"):
                        st.session_state.learned.append(lesson['id'])
                        add_xp(lesson['xp']); st.success("已完成！"); st.rerun()
                else: st.success("已完成 ✅")
            with col2:
                if st.session_state.api_key:
                    if st.button("🤖 用大白话再解释一次",key=f"ai_{lesson['id']}"):
                        with st.spinner("AI老师解释中..."):
                            r=call_ai(f"用最简单的语言和生活比喻解释：{lesson['title']}，100字以内，适合完全不懂股票的新手。")
                        if r: st.markdown(f"<div class='ai-box'>🤖 {r}</div>",unsafe_allow_html=True); add_xp(5)

# ════════════════════════════════════════════════════════════
# 页面：AI选股助手
# ════════════════════════════════════════════════════════════
def page_scout():
    st.markdown("# 🔍 AI选股助手")
    st.markdown("输入股票代码，AI帮你分析并用大白话解释每个信号，教你看懂而不只给答案")
    st.divider()

    POPULAR={"英伟达":"NVDA","苹果":"AAPL","特斯拉":"TSLA","贵州茅台":"600519.SS",
             "宁德时代":"300750.SZ","比亚迪":"002594.SZ","平安银行":"000001.SZ","招商银行":"600036.SS"}
    st.markdown("**热门股票一键分析：**")
    cols=st.columns(8)
    for i,(label,code) in enumerate(POPULAR.items()):
        if cols[i%8].button(label,key=f"pop_{i}"): st.session_state["scout_sym"]=code

    sym=st.text_input("或手动输入代码",value=st.session_state.get("scout_sym","NVDA"),
        help="美股：NVDA | 上证加.SS：600519.SS | 深证加.SZ：000001.SZ")

    if st.button("🚀 开始分析",type="primary",key="scout_run"):
        sym=sym.strip().upper()
        with st.spinner(f"获取 {sym} 数据中..."):
            df,name=get_data(sym)
        if df is None or len(df)<5:
            st.error("数据获取失败，请检查代码格式\n- 美股直接输入：NVDA\n- 上交所：600519.SS\n- 深交所：000001.SZ")
            return
        df=compute_tech(df)
        signals,score=analyze_signals(df)
        latest=df.iloc[-1]; prev=df.iloc[-2]
        close=float(latest['close'])
        pct=(close-float(prev['close']))/float(prev['close'])*100
        vr=float(latest['volume'])/max(float(latest.get('vol_ma10',latest['volume'])),1)

        st.markdown(f"## {name}（{sym}）")
        c1,c2,c3,c4=st.columns(4)
        sc_color="score-high" if score>=70 else "score-mid" if score>=50 else "score-low"
        c1.metric("当前价格",f"{close:.2f}",f"{pct:+.2f}%")
        c2.metric("量比",f"{vr:.2f}x","放量🔴" if vr>1.5 else "缩量🔵" if vr<0.7 else "正常")
        c3.metric("RSI",f"{float(latest.get('RSI',50)):.1f}")
        with c4:
            st.markdown("**综合评分**")
            color="#ff6b6b" if score>=70 else "#f0b429" if score>=50 else "#4ecdc4"
            st.markdown(f"<span style='color:{color};font-weight:700;font-size:2em'>{score}</span>/100",unsafe_allow_html=True)

        st.plotly_chart(draw_chart(df,sym,name),use_container_width=True)

        st.markdown("### 🎓 信号解读（每一条都告诉你为什么）")
        for sig_name,sig_type,technical,plain,advice in signals:
            st.markdown(f"""
            <div class='signal-{sig_type}'>
            <b>{sig_name}</b>
            <div style='color:#6b8299;font-size:0.82em;margin:3px 0'>{technical}</div>
            <div class='explain'>
            💬 <b>通俗理解：</b>{plain}<br>
            📌 <b>操作参考：</b>{advice}
            </div></div>""",unsafe_allow_html=True)

        if st.session_state.api_key:
            st.markdown("### 🤖 AI老师综合点评")
            bullish=sum(1 for _,t,_,_,_ in signals if t=='bullish')
            bearish=sum(1 for _,t,_,_,_ in signals if t=='bearish')
            with st.spinner("AI分析中..."):
                r=call_ai(f"""
股票：{name}（{sym}）现价{close:.2f}，今日{pct:+.2f}%，RSI={float(latest.get('RSI',50)):.1f}，量比{vr:.2f}x
综合评分：{score}/100，看多信号{bullish}个，看空信号{bearish}个

请用以下格式，用大白话点评（像朋友聊天，不要太严肃）：
1. 【现在状态】一句话总结
2. 【小白该怎么做】给出明确建议：买/观望/卖，说理由
3. 【最要注意的事】1-2个风险点
4. 【学到了什么】从这个案例能学到什么技术知识

200字以内，通俗易懂。""")
            if r:
                st.markdown(f"<div class='ai-box'>🤖 <b>AI老师说：</b><br><br>{r.replace(chr(10),'<br>')}</div>",unsafe_allow_html=True)
                add_xp(20)
        else:
            st.info("💡 填入左侧API Key，可获得AI老师的个性化点评")
        add_xp(10)

# ════════════════════════════════════════════════════════════
# 页面：持仓守护（核心功能）
# ════════════════════════════════════════════════════════════
def page_hold():
    st.markdown("# 🛡️ 持仓守护")
    st.markdown("输入你持有的股票和成本，AI帮你判断：**该继续持有，还是该止损离场**")
    st.divider()

    col1,col2,col3=st.columns([2,1,1])
    with col1: sym=st.text_input("股票代码",value=st.session_state.holding.get('sym','603993.SS') if st.session_state.holding else "603993.SS",help="上证：600519.SS | 深证：000001.SZ | 美股：NVDA")
    with col2: cost=st.number_input("你的买入成本（元）",min_value=0.01,value=float(st.session_state.holding.get('cost',23)) if st.session_state.holding else 23.0,step=0.01)
    with col3: shares=st.number_input("持仓数量（股）",min_value=1,value=int(st.session_state.holding.get('shares',800)) if st.session_state.holding else 800,step=100)

    if st.button("🔍 分析我的持仓",type="primary"):
        st.session_state.holding={'sym':sym.upper(),'cost':cost,'shares':shares}
        with st.spinner("分析中..."):
            df,name=get_data(sym.upper())

        if df is None or len(df)<5:
            st.error("数据获取失败，请检查股票代码格式")
            return

        df=compute_tech(df)
        signals,score=analyze_signals(df,cost=cost)
        latest=df.iloc[-1]; prev=df.iloc[-2]
        close=float(latest['close'])
        pct_today=(close-float(prev['close']))/float(prev['close'])*100
        profit=close-cost; profit_pct=profit/cost*100
        total_profit=profit*shares

        # 持仓概况
        st.markdown(f"## {name}（{sym.upper()}）持仓分析")
        c1,c2,c3,c4,c5=st.columns(5)
        c1.metric("买入成本",f"¥{cost:.2f}")
        c2.metric("当前价格",f"¥{close:.2f}",f"{pct_today:+.2f}%")
        profit_color="normal"
        c3.metric("浮动盈亏",f"¥{total_profit:+.0f}",f"{profit_pct:+.2f}%",delta_color="normal" if total_profit>=0 else "inverse")
        c4.metric("持仓市值",f"¥{close*shares:,.0f}")
        score_color="#ff6b6b" if score>=70 else "#f0b429" if score>=50 else "#4ecdc4"
        with c5:
            st.markdown("**技术评分**")
            st.markdown(f"<span style='color:{score_color};font-weight:700;font-size:2em'>{score}</span>/100",unsafe_allow_html=True)

        # 止损提醒框
        stop_loss_5=round(cost*0.95,2); stop_loss_8=round(cost*0.92,2)
        if close<=stop_loss_5:
            st.markdown(f"""<div class='warn-box'>
            🚨 <b>止损警报！</b> 当前价格 {close:.2f} 已跌破5%止损线（{stop_loss_5}）<br>
            <b>建议：认真考虑止损离场，保住剩余本金。</b><br>
            <small>继续持有可能面临更大损失。先出来观望，等技术信号好转再考虑重新入场。</small>
            </div>""",unsafe_allow_html=True)
        else:
            st.markdown(f"""<div style='background:rgba(56,239,125,0.05);border:1px solid #38ef7d55;border-radius:10px;padding:14px;margin:10px 0'>
            🛡️ <b>止损线设置参考：</b><br>
            保守止损：<b>¥{stop_loss_5}</b>（亏5%，约亏¥{(stop_loss_5-cost)*shares:,.0f}）<br>
            普通止损：<b>¥{stop_loss_8}</b>（亏8%，约亏¥{(stop_loss_8-cost)*shares:,.0f}）<br>
            <small style='color:#6b8299'>建议现在就在你的股票app里设置条件单！</small>
            </div>""",unsafe_allow_html=True)

        # K线图（带成本线）
        st.plotly_chart(draw_chart(df,sym.upper(),name,cost=cost),use_container_width=True)

        # 持有 or 卖出 判断
        st.markdown("### 📊 该继续持有，还是止损离场？")

        bullish_count=sum(1 for _,t,_,_,_ in signals if t=='bullish')
        bearish_count=sum(1 for _,t,_,_,_ in signals if t=='bearish')

        col_hold,col_sell=st.columns(2)
        with col_hold:
            st.markdown("**✅ 支持继续持有的理由：**")
            hold_reasons=[s for s in signals if s[1]=='bullish']
            if hold_reasons:
                for sig_name,_,technical,plain,_ in hold_reasons:
                    st.markdown(f"<div class='hold-signal'><b>{sig_name}</b><br><small style='color:#6b8299'>{plain}</small></div>",unsafe_allow_html=True)
            else:
                st.markdown("<div class='hold-signal'><small>暂无明显看多信号</small></div>",unsafe_allow_html=True)

        with col_sell:
            st.markdown("**⚠️ 需要警惕的风险信号：**")
            sell_reasons=[s for s in signals if s[1]=='bearish']
            if sell_reasons:
                for sig_name,_,technical,plain,_ in sell_reasons:
                    st.markdown(f"<div class='sell-signal'><b>{sig_name}</b><br><small style='color:#6b8299'>{plain}</small></div>",unsafe_allow_html=True)
            else:
                st.markdown("<div class='sell-signal'><small>暂无明显看空信号</small></div>",unsafe_allow_html=True)

        # 综合判断
        st.markdown("### 🎯 综合判断")
        if bearish_count>=3 or (close<=stop_loss_5):
            verdict="⚠️ 建议考虑止损"; verdict_color="#ff6b6b"
            reason=f"看空信号{bearish_count}个，明显多于看多信号{bullish_count}个，技术面偏弱。"
            action=f"建议分批减仓，或在跌破 {stop_loss_5} 时果断止损。"
        elif bullish_count>=3 and score>=60:
            verdict="✅ 可以继续持有"; verdict_color="#38ef7d"
            reason=f"看多信号{bullish_count}个，技术评分{score}分，趋势偏向好转。"
            action=f"继续持有，但务必设好止损线 {stop_loss_5}，不要因为涨了就忘记风险。"
        else:
            verdict="🟡 中性观望"; verdict_color="#f0b429"
            reason=f"多空信号均衡（看多{bullish_count}个，看空{bearish_count}个），方向不明确。"
            action=f"可以先持仓观察，但严格执行止损 {stop_loss_5}，一旦触发立刻执行。"

        st.markdown(f"""<div class='card' style='border:2px solid {verdict_color};text-align:center;padding:24px'>
        <div style='font-size:1.5em;color:{verdict_color};font-weight:700'>{verdict}</div><br>
        <div>{reason}</div><br>
        <div style='background:rgba(255,255,255,0.05);border-radius:8px;padding:12px'><b>📌 建议操作：</b>{action}</div>
        </div>""",unsafe_allow_html=True)

        # AI持仓分析
        if st.session_state.api_key:
            st.markdown("### 🤖 AI老师持仓点评")
            with st.spinner("AI分析你的持仓..."):
                r=call_ai(f"""
一位股票小白的持仓情况：
- 股票：{name}（{sym}）
- 买入成本：{cost}元，现价：{close:.2f}元
- 浮动盈亏：{profit_pct:+.2f}%（共{total_profit:+.0f}元）
- 技术评分：{score}/100
- 看多信号：{bullish_count}个，看空信号：{bearish_count}个
- 当前技术状态：{"偏多" if bullish_count>bearish_count else "偏空" if bearish_count>bullish_count else "中性"}

请给出持仓建议，格式如下，语言要像朋友聊天：
1. 【当前处境】一句话说清楚他现在的状态
2. 【我的建议】明确说：继续持有/减仓/止损，理由是什么
3. 【止损红线】告诉他如果跌到多少必须走
4. 【止盈目标】如果技术好转，目标价位大概在哪里
5. 【给小白的话】一句鼓励或提醒

200字以内，不要太严肃。""")
            if r:
                st.markdown(f"<div class='ai-box'>🤖 <b>AI老师说：</b><br><br>{r.replace(chr(10),'<br>')}</div>",unsafe_allow_html=True)
        else:
            st.info("💡 填入Claude API Key，获得AI老师对你持仓的个性化建议")

# ════════════════════════════════════════════════════════════
# 页面：闯关练习
# ════════════════════════════════════════════════════════════
QUIZZES=[
    {"q":"红色K线（阳线）代表什么？","opts":["A. 今天跌了","B. 今天涨了","C. 成交量很大","D. 股票要退市"],"ans":"B","exp":"红色阳线=收盘价>开盘价=今天涨了。记忆方法：红色=喜庆=涨！"},
    {"q":"5日均线从下方穿越20日均线向上，叫做什么？","opts":["A. 死叉","B. 布林突破","C. 金叉","D. RSI超买"],"ans":"C","exp":"短期均线（5日）上穿长期均线（20日）=金叉=买入信号。金叉=金色=好事=涨！"},
    {"q":"RSI值达到78，说明什么？","opts":["A. 股票非常便宜","B. 处于超卖区，可以买","C. 处于超买区，有回调风险","D. 成交量很小"],"ans":"C","exp":"RSI>70进入超买区，说明短期涨太猛，像运动员跑太久快累了，可能需要休息（回调）。"},
    {"q":"放量上涨和缩量上涨，哪个更可靠？","opts":["A. 缩量上涨","B. 放量上涨","C. 一样可靠","D. 和成交量无关"],"ans":"B","exp":"放量上涨代表大量资金认可当前价格，是「量价齐升」，最健康的上涨形态。缩量上涨后劲不足。"},
    {"q":"MACD红色柱状图越来越长，代表什么？","opts":["A. 上涨动能减弱","B. 下跌动能增强","C. 上涨动能增强","D. 即将暴跌"],"ans":"C","exp":"MACD红柱变长=快线和慢线差距扩大=上涨动力越来越足。就像顺风骑车越来越快。"},
    {"q":"买入股票后，最重要的第一步是什么？","opts":["A. 等它涨到最高点","B. 告诉朋友","C. 设好止损价格","D. 继续买更多"],"ans":"C","exp":"止损是保命的！买入后立刻设好止损线（通常亏5%就走），是新手最重要的纪律。"},
    {"q":"K线上影线很长，说明什么？","opts":["A. 下方支撑强","B. 上方抛压重","C. 成交量放大","D. 股价要暴涨"],"ans":"B","exp":"上影线长=价格涨上去了但被卖方打下来=上方有很多人在卖=上方压力重。"},
    {"q":"布林带突然「收口」（上下轨靠近），预示什么？","opts":["A. 股票要退市","B. 即将有大行情","C. RSI超买","D. 成交量缩小"],"ans":"B","exp":"布林带收口=波动率低=蓄势中。就像弹簧压缩，压得越久弹出越猛。收口后往往有方向性大行情。"},
]

def page_quiz():
    st.markdown("# 🧩 闯关练习")
    st.markdown("检验学习成果，每题都有详细解析，答错了才学得最快！")
    st.divider()
    c1,c2,c3=st.columns(3)
    c1.metric("已答",f"{st.session_state.quiz_total}题")
    c2.metric("答对",f"{st.session_state.quiz_score}题")
    c3.metric("正确率",f"{int(st.session_state.quiz_score/max(st.session_state.quiz_total,1)*100)}%")
    st.divider()

    if 'cur_quiz' not in st.session_state or st.session_state.get('quiz_done',False):
        if st.button("🎲 出一道题",type="primary"):
            st.session_state.cur_quiz=random.choice(QUIZZES)
            st.session_state.quiz_done=False; st.rerun()
    if 'cur_quiz' in st.session_state and not st.session_state.get('quiz_done',False):
        q=st.session_state.cur_quiz
        st.markdown(f"<div class='card'><b>📝 {q['q']}</b></div>",unsafe_allow_html=True)
        choice=st.radio("选择答案：",q['opts'],key="qr")
        if st.button("✅ 提交"):
            st.session_state.quiz_total+=1
            if choice[0]==q['ans']:
                st.session_state.quiz_score+=1; add_xp(15); st.success("🎉 答对了！+15 XP")
            else:
                add_xp(5); st.error(f"❌ 答错了，正确是 {q['ans']}，但你也获得 +5 XP")
            st.markdown(f"<div class='explain'><b>📖 解析：</b>{q['exp']}</div>",unsafe_allow_html=True)
            st.session_state.quiz_done=True

# ════════════════════════════════════════════════════════════
# 页面：术语速查
# ════════════════════════════════════════════════════════════
GLOSSARY={
    "K线":"记录一段时间内开盘、收盘、最高、最低4个价格的图表。红（阳）=涨，绿（阴）=跌。",
    "均线(MA)":"过去N天收盘价的平均值，代表一段时间内的平均持仓成本。",
    "金叉":"短期均线从下穿越长期均线向上，买入信号。",
    "死叉":"短期均线从上穿越长期均线向下，卖出信号。",
    "RSI":"相对强弱指数0-100。>70超买（可能回调），<30超卖（可能反弹）。",
    "MACD":"动量指标，由快线、慢线、柱状图组成。金叉买，死叉卖。",
    "布林带":"三条线组成的价格通道。价格通常在通道内波动，带宽收窄意味着将有大行情。",
    "成交量":"买卖双方的交易数量。量是价格的「动力」，有量才有真行情。",
    "量比":"今日成交量÷过去5天均量。>1.5=放量，<0.7=缩量。",
    "止损":"提前设定的亏损上限，触发后必须卖出，是保护本金最重要的工具。",
    "止盈":"提前设定的盈利目标，达到后卖出锁定利润。",
    "仓位":"某只股票占你总资金的比例。单股不超过1/3是基本纪律。",
    "支撑位":"股价下跌时可能被托住的价格区域，常见于前期低点。",
    "压力位":"股价上涨时可能遇到阻力的价格区域，常见于前期高点。",
    "上影线":"K线上方的细线，代表价格涨上去但被打下来，上方有卖压。",
    "下影线":"K线下方的细线，代表价格跌下去但被买回来，下方有支撑。",
    "量价齐升":"成交量放大+股价上涨，最健康的上涨形态，说明资金认可。",
    "套牢":"买入后股价下跌，成本价高于现价，处于亏损状态。",
    "解套":"被套后等股价回到成本价再卖出。（注意：不是好策略，止损才是）",
    "大盘":"整体股票市场走势，常用上证指数或沪深300代表。",
}

def page_glossary():
    st.markdown("# 🗂️ 术语速查")
    st.markdown("遇到看不懂的词，在这里快速查")
    st.divider()
    search=st.text_input("🔍 搜索",placeholder="输入关键词...")
    filtered={k:v for k,v in GLOSSARY.items() if not search or search in k or search in v}
    cols=st.columns(2)
    for i,(term,desc) in enumerate(filtered.items()):
        with cols[i%2]:
            st.markdown(f"""<div class='card'>
            <div style='color:var(--gold);font-weight:700;margin-bottom:6px'>📌 {term}</div>
            <div style='font-size:0.88em;line-height:1.8'>{desc}</div>
            </div>""",unsafe_allow_html=True)
    if st.session_state.api_key and search and search not in GLOSSARY:
        if st.button(f"🤖 AI解释「{search}」"):
            with st.spinner("查询中..."):
                r=call_ai(f"用100字以内解释股票术语「{search}」，适合完全不懂股票的新手，要有举例。")
            if r: st.markdown(f"<div class='ai-box'>🤖 {r}</div>",unsafe_allow_html=True)

# ── 路由 ──────────────────────────────────────────────────────
p=st.session_state.page
if   p=="home":     page_home()
elif p=="learn":    page_learn()
elif p=="scout":    page_scout()
elif p=="hold":     page_hold()
elif p=="quiz":     page_quiz()
elif p=="glossary": page_glossary()
