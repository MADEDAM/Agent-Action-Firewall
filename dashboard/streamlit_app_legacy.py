"""
streamlit_app.py  (담당: 김나형)  ★ 보안 관제 콘솔 — "Command Center" Edition

회전 네온 글로우 테두리 · 움직이는 사이버 그리드 · 위협 레벨 게이지 · 실시간 경보 티커.
이 파일 하나만 디자인 변경 → 팀원 함수는 호출만 그대로(인터페이스 변경 0).

실행:  streamlit run dashboard/streamlit_app.py
"""
import sys
import os
import html

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from app.logs import log_service, log_repository
from app.approval import approval_service
from app.reports import incident_report
from app.control import control_service
from app.security import anomaly_guard

log_repository.init_db()
st.set_page_config(page_title="Agent Action Firewall", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

@property --deg{ syntax:'<angle>'; initial-value:0deg; inherits:false; }

#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"]{ display:none !important; }
header[data-testid="stHeader"]{ background:transparent; height:0; }

:root{ --ink:#eef1fa; --muted:#8b93ad; --line:rgba(255,255,255,0.08); --card:rgba(255,255,255,0.04); }
html, body, .stApp{ background:#04060d; }
.stApp{ color:var(--ink); font-family:'Pretendard','Space Grotesk',sans-serif; }

/* 오로라 + 움직이는 사이버 그리드 + 비네트 */
.stApp::before{ content:""; position:fixed; inset:0; z-index:-2; pointer-events:none;
  background:
   radial-gradient(680px 420px at 8% -6%, rgba(99,102,241,0.32), transparent 60%),
   radial-gradient(760px 460px at 100% 2%, rgba(168,85,247,0.26), transparent 58%),
   radial-gradient(640px 540px at 60% 112%, rgba(34,211,238,0.18), transparent 55%),
   linear-gradient(165deg,#05070f,#0a0f22 52%,#05060e);
  animation:aurora 18s ease-in-out infinite alternate; }
.stApp::after{ content:""; position:fixed; inset:0; z-index:-1; pointer-events:none; opacity:.5;
  background-image:
    linear-gradient(rgba(120,140,255,0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(120,140,255,0.06) 1px, transparent 1px);
  background-size:46px 46px; mask:radial-gradient(circle at 50% 35%, #000 0%, transparent 78%);
  animation:grid 22s linear infinite; }
@keyframes aurora{ 0%{filter:hue-rotate(0) saturate(1);} 100%{filter:hue-rotate(26deg) saturate(1.18);} }
@keyframes grid{ from{background-position:0 0,0 0;} to{background-position:46px 920px,46px 920px;} }

.block-container{ padding-top:1.8rem; padding-bottom:4rem; max-width:1240px;
  animation:fadeUp .7s cubic-bezier(.2,.7,.2,1) both; }
@keyframes fadeUp{ from{opacity:0; transform:translateY(16px);} to{opacity:1; transform:none;} }
h1,h2,h3,h4,p,span,div,label{ font-family:'Pretendard','Space Grotesk',sans-serif; }
::-webkit-scrollbar{ width:10px; height:10px; }
::-webkit-scrollbar-thumb{ background:rgba(255,255,255,0.12); border-radius:10px; }

/* 회전 네온 글로우 테두리 (재사용) */
.glow{ position:relative; border-radius:22px; }
.glow::before{ content:""; position:absolute; inset:0; border-radius:22px; padding:1.6px;
  background:conic-gradient(from var(--deg), #6366f1,#a855f7,#ec4899,#22d3ee,#6366f1);
  -webkit-mask:linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite:xor; mask-composite:exclude;
  animation:spin 6s linear infinite; filter:drop-shadow(0 0 8px rgba(139,92,246,0.45)); }
@keyframes spin{ to{ --deg:360deg; } }

/* HERO */
.hero{ position:relative; display:flex; align-items:center; gap:18px; overflow:hidden;
  padding:26px 30px; border-radius:22px;
  background:linear-gradient(120deg, rgba(99,102,241,0.20), rgba(168,85,247,0.10) 45%, rgba(34,211,238,0.06));
  box-shadow:0 20px 60px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.06); }
.hero .mark{ width:54px; height:54px; flex:none; filter:drop-shadow(0 6px 20px rgba(139,92,246,0.6)); }
.hero h1{ margin:0; font-family:'Space Grotesk','Pretendard',sans-serif; font-size:31px; font-weight:700;
  letter-spacing:-0.5px; line-height:1.05;
  background:linear-gradient(92deg,#c7d2fe,#e9d5ff 30%,#fbcfe8 55%,#a5f3fc 80%,#c7d2fe);
  background-size:220% auto; -webkit-background-clip:text; background-clip:text;
  -webkit-text-fill-color:transparent; animation:shimmer 6s linear infinite; }
@keyframes shimmer{ to{ background-position:220% center; } }
.hero .sub{ font-size:12px; color:#aab2cc; margin-top:6px; letter-spacing:2px; text-transform:uppercase; }
.live{ margin-left:auto; display:flex; align-items:center; gap:9px; padding:9px 16px; border-radius:999px;
  font-size:12px; font-weight:700; letter-spacing:0.6px;
  background:rgba(52,211,153,0.10); border:1px solid rgba(52,211,153,0.35); color:#6ee7b7; }
.live.off{ background:rgba(248,113,113,0.12); border-color:rgba(248,113,113,0.4); color:#fca5a5; }
.ld{ width:9px; height:9px; border-radius:50%; background:#34d399; animation:beat 1.6s infinite; }
.live.off .ld{ background:#f87171; animation:none; box-shadow:0 0 10px rgba(248,113,113,0.8); }
@keyframes beat{ 0%{box-shadow:0 0 0 0 rgba(52,211,153,0.55);} 70%{box-shadow:0 0 0 9px rgba(52,211,153,0);} 100%{box-shadow:0 0 0 0 rgba(52,211,153,0);} }

/* 경보 티커 */
.ticker{ margin-top:12px; overflow:hidden; border:1px solid var(--line); border-radius:13px;
  background:rgba(255,255,255,0.025); padding:10px 0; -webkit-mask:linear-gradient(90deg,transparent,#000 6%,#000 94%,transparent); }
.ticker .track{ display:inline-block; white-space:nowrap; animation:marq 30s linear infinite; }
.ticker:hover .track{ animation-play-state:paused; }
.ticker .chip{ display:inline-flex; align-items:center; gap:8px; margin:0 24px; font-size:12px; color:#cdd3e6;
  font-family:'JetBrains Mono',monospace; }
@keyframes marq{ from{transform:translateX(0);} to{transform:translateX(-50%);} }

.sec{ font-size:11px; font-weight:700; color:#9aa3c4; letter-spacing:2.6px; text-transform:uppercase;
  margin:30px 0 14px; display:flex; align-items:center; gap:12px; }
.sec::after{ content:""; flex:1; height:1px; background:linear-gradient(90deg, rgba(255,255,255,0.14), transparent); }

/* KPI */
.kpis{ display:flex; gap:16px; }
.kpi{ flex:1; position:relative; padding:20px 22px; border-radius:18px; overflow:hidden;
  background:var(--card); border:1px solid var(--line);
  box-shadow:0 10px 34px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05);
  transition:transform .18s, border-color .18s; }
.kpi:hover{ transform:translateY(-5px); border-color:rgba(255,255,255,0.2); }
.kpi::after{ content:""; position:absolute; top:0; left:-60%; width:50%; height:100%;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,0.10),transparent); transform:skewX(-20deg); transition:.5s; }
.kpi:hover::after{ left:120%; }
.kpi .n{ font-family:'Space Grotesk',sans-serif; font-size:42px; font-weight:700; line-height:1; letter-spacing:-1.5px; }
.kpi .l{ font-size:12px; color:var(--muted); margin-top:10px; font-weight:600; }
.kpi .glow2{ position:absolute; right:-30px; top:-30px; width:120px; height:120px; border-radius:50%; filter:blur(36px); opacity:.5; }
.grad-i{background:linear-gradient(92deg,#a5b4fc,#c4b5fd);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;}
.grad-r{background:linear-gradient(92deg,#fca5a5,#f87171);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;}
.grad-v{background:linear-gradient(92deg,#c4b5fd,#a78bfa);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;}
.grad-w{background:linear-gradient(92deg,#fcd34d,#fbbf24);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;}

.panel{ background:rgba(10,14,30,0.66); border:1px solid var(--line); border-radius:22px; padding:24px 26px;
  box-shadow:0 10px 34px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.05); height:100%; }
.panel .ttl{ font-size:12.5px; font-weight:700; color:#c3c9de; margin-bottom:18px; letter-spacing:0.6px; }

/* 위협 게이지 */
.gaugewrap{ display:flex; align-items:center; gap:26px; }
.gauge{ position:relative; width:172px; height:172px; border-radius:50%; flex:none;
  box-shadow:0 8px 36px rgba(0,0,0,0.5); }
.gauge .hole{ position:absolute; inset:18px; background:radial-gradient(circle at 50% 40%, #121933, #0a0f20);
  border-radius:50%; display:flex; flex-direction:column; align-items:center; justify-content:center;
  border:1px solid rgba(255,255,255,0.07); }
.gauge .pct{ font-family:'Space Grotesk',sans-serif; font-size:40px; font-weight:700; line-height:1; }
.gauge .tl{ font-size:11px; font-weight:700; letter-spacing:2px; margin-top:6px; }
.gmeta b{ font-family:'Space Grotesk',sans-serif; font-size:15px; }
.gmeta .row{ display:flex; justify-content:space-between; gap:30px; padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.06); font-size:12.5px; color:#cdd3e6; }

/* DONUT */
.donutwrap{ display:flex; align-items:center; gap:24px; }
.donut{ position:relative; width:150px; height:150px; border-radius:50%; flex:none; box-shadow:0 8px 30px rgba(0,0,0,0.4); }
.donut .hole{ position:absolute; inset:21px; background:#0a0f20; border-radius:50%; display:flex; flex-direction:column;
  align-items:center; justify-content:center; border:1px solid rgba(255,255,255,0.06); }
.donut .big{ font-family:'Space Grotesk',sans-serif; font-size:28px; font-weight:700; }
.donut .cap{ font-size:10px; color:var(--muted); letter-spacing:1px; margin-top:2px; }
.legend{ display:flex; flex-direction:column; gap:9px; }
.lg{ display:flex; align-items:center; gap:9px; font-size:12.5px; color:#cdd3e6; }
.lg .d{ width:10px; height:10px; border-radius:3px; } .lg b{ margin-left:auto; color:#fff; font-family:'JetBrains Mono',monospace; }

/* RISK METER */
.meter{ display:flex; flex-direction:column; gap:15px; }
.mrow{ display:flex; align-items:center; gap:12px; }
.mrow .lab{ width:80px; font-size:12px; font-weight:600; color:#cdd3e6; }
.mrow .track{ flex:1; height:11px; border-radius:999px; background:rgba(255,255,255,0.06); overflow:hidden; }
.mrow .fill{ height:100%; border-radius:999px; box-shadow:0 0 16px var(--c); background:linear-gradient(90deg,var(--c),var(--c2)); }
.mrow .val{ width:34px; text-align:right; font-family:'JetBrains Mono',monospace; font-size:13px; color:#fff; }

/* BADGES */
.badge{ display:inline-block; padding:3px 11px; border-radius:999px; font-size:11px; font-weight:700; letter-spacing:0.4px;
  border:1px solid transparent; font-family:'Space Grotesk',sans-serif; }
.b-ok{background:rgba(52,211,153,0.14);color:#6ee7b7;border-color:rgba(52,211,153,0.3);}
.b-warn{background:rgba(251,191,36,0.14);color:#fcd34d;border-color:rgba(251,191,36,0.3);}
.b-orange{background:rgba(251,146,60,0.14);color:#fdba74;border-color:rgba(251,146,60,0.3);}
.b-bad{background:rgba(248,113,113,0.16);color:#fca5a5;border-color:rgba(248,113,113,0.35);}
.b-info{background:rgba(167,139,250,0.16);color:#c4b5fd;border-color:rgba(167,139,250,0.35);}
.b-neutral{background:rgba(148,163,184,0.14);color:#cbd5e1;border-color:rgba(148,163,184,0.3);}

/* LOG TABLE */
table.logt{ width:100%; border-collapse:separate; border-spacing:0; font-size:12.5px; }
table.logt th{ text-align:left; color:#7e87a3; font-weight:700; font-size:10.5px; text-transform:uppercase; letter-spacing:0.7px; padding:0 14px 12px; }
table.logt td{ padding:12px 14px; border-top:1px solid rgba(255,255,255,0.055); color:#d7dcec; }
table.logt tr:hover td{ background:rgba(99,102,241,0.08); }
table.logt td.mono{ font-family:'JetBrains Mono',monospace; font-size:11px; color:#9aa3bf; }
.sevdot{ width:7px; height:7px; border-radius:50%; display:inline-block; margin-right:8px; box-shadow:0 0 8px currentColor; }
.empty{ padding:30px; text-align:center; color:#7e87a3; font-size:13px; border:1px dashed rgba(255,255,255,0.12); border-radius:16px; background:rgba(255,255,255,0.02); }

.stButton button{ background:rgba(255,255,255,0.05); color:var(--ink); border:1px solid rgba(255,255,255,0.14);
  border-radius:11px; padding:7px 16px; font-weight:600; font-size:13px; transition:.15s; }
.stButton button:hover{ background:linear-gradient(92deg,rgba(99,102,241,0.35),rgba(168,85,247,0.3)); border-color:rgba(168,85,247,0.5); color:#fff; transform:translateY(-1px); }
div[data-baseweb="select"] > div{ background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.12); border-radius:11px; color:var(--ink); }
.stSelectbox label{ color:#8b93ad !important; font-size:11.5px !important; font-weight:600; }
[data-testid="stExpander"]{ border:1px solid var(--line); border-radius:14px; background:var(--card); }
.row-card{ padding:14px 18px; margin-bottom:10px; border-radius:14px; background:var(--card); border:1px solid var(--line); }
</style>
""", unsafe_allow_html=True)

SHIELD = """<svg class="mark" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="sg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#818cf8"/>
<stop offset=".5" stop-color="#a855f7"/><stop offset="1" stop-color="#ec4899"/></linearGradient></defs>
<path d="M12 2.4l8 3.2v5.5c0 4.9-3.4 8.9-8 10.5-4.6-1.6-8-5.6-8-10.5V5.6L12 2.4z" fill="url(#sg)" opacity="0.96"/>
<path d="M8.6 12.3l2.4 2.4 4.4-4.8" stroke="#0a0f20" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>"""

DEC = {"ALLOW":"b-ok","MASK":"b-warn","BLOCK":"b-bad","NEED_APPROVAL":"b-info","LOG_ONLY_KILLSWITCH":"b-neutral"}
RISK = {"LOW":"b-ok","MEDIUM":"b-warn","HIGH":"b-orange","CRITICAL":"b-bad","OFF":"b-neutral"}
SEV = {"LOW":"#34d399","MEDIUM":"#fbbf24","HIGH":"#fb923c","CRITICAL":"#f87171","OFF":"#94a3b8"}


def badge(t, c):
    return f'<span class="badge {c}">{html.escape(str(t))}</span>'


def donut(segs, total):
    if total <= 0:
        ring = "conic-gradient(rgba(255,255,255,0.10) 0deg 360deg)"
    else:
        acc, st_ = 0, []
        for color, val in segs:
            a = acc / total * 360; acc += val; b = acc / total * 360
            st_.append(f"{color} {a:.1f}deg {b:.1f}deg")
        ring = "conic-gradient(" + ",".join(st_) + ")"
    return (f'<div class="donut" style="background:{ring}"><div class="hole">'
            f'<div class="big">{total}</div><div class="cap">REQUESTS</div></div></div>')


# ---------- HERO + LIVE ----------
fw_on = control_service.is_firewall_on()
live = ('<div class="live"><span class="ld"></span>LIVE · 방화벽 ON</div>' if fw_on
        else '<div class="live off"><span class="ld"></span>방화벽 OFF</div>')
st.markdown(f'<div class="glow"><div class="hero">{SHIELD}<div><h1>Agent Action Firewall</h1>'
            f'<div class="sub">Security Operations Console</div></div>{live}</div></div>',
            unsafe_allow_html=True)

# ---------- ALERT TICKER ----------
recent = log_service.get_logs(limit=14)
if recent:
    chips = ""
    for x in recent:
        sev = SEV.get(x["risk_level"], "#94a3b8")
        chips += (f'<span class="chip"><span class="sevdot" style="color:{sev}"></span>'
                  f'{html.escape(x["user"])} · {html.escape(x["tool"])} '
                  f'{badge(x["decision"], DEC.get(x["decision"],"b-neutral"))}</span>')
    st.markdown(f'<div class="ticker"><div class="track">{chips}{chips}</div></div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="ticker"><div class="track">'
                '<span class="chip"><span class="sevdot" style="color:#34d399"></span>시스템 정상 가동 중 · 감지된 위협 없음</span>'
                '<span class="chip"><span class="sevdot" style="color:#34d399"></span>SYSTEM NOMINAL · NO ACTIVE THREATS</span>'
                '<span class="chip"><span class="sevdot" style="color:#34d399"></span>시스템 정상 가동 중 · 감지된 위협 없음</span>'
                '<span class="chip"><span class="sevdot" style="color:#34d399"></span>SYSTEM NOMINAL · NO ACTIVE THREATS</span>'
                '</div></div>', unsafe_allow_html=True)

# ---------- TOGGLE ----------
cs, ct = st.columns([4, 1])
with ct:
    new_state = st.toggle("방화벽 활성화", value=fw_on, key="fw_toggle")
    if new_state != fw_on:
        control_service.set_firewall(new_state); st.rerun()
with cs:
    if not fw_on:
        st.markdown('<div class="empty" style="border-color:rgba(248,113,113,0.4);color:#fca5a5;margin-top:4px">'
                    '⚠ 방화벽 OFF — 모든 AI 행동이 검사 없이 실행됩니다. 시연이 끝나면 다시 켜세요.</div>',
                    unsafe_allow_html=True)

# ---------- KPI ----------
s = log_service.get_stats()
allow_cnt = max(0, s["total"] - s["blocked"] - s["pending"] - s["masked"])
st.markdown('<div class="sec">Overview</div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="kpis">
  <div class="kpi"><div class="glow2" style="background:#6366f1"></div><div class="n grad-i">{s['total']}</div><div class="l">전체 요청 · TOTAL</div></div>
  <div class="kpi"><div class="glow2" style="background:#f87171"></div><div class="n grad-r">{s['blocked']}</div><div class="l">차단 · BLOCKED</div></div>
  <div class="kpi"><div class="glow2" style="background:#a855f7"></div><div class="n grad-v">{s['pending']}</div><div class="l">승인 대기 · PENDING</div></div>
  <div class="kpi"><div class="glow2" style="background:#fbbf24"></div><div class="n grad-w">{s['masked']}</div><div class="l">마스킹 · MASKED</div></div>
</div>
""", unsafe_allow_html=True)

# ---------- THREAT GAUGE + DONUT ----------
st.markdown('<div class="sec">Threat Analytics</div>', unsafe_allow_html=True)
by = s["by_risk"]
crit = by.get("CRITICAL", 0); high = by.get("HIGH", 0)
threat = min(100, s["blocked"] * 12 + crit * 18 + high * 8 + s["pending"] * 5)
if threat >= 80:   tlabel, tc = "CRITICAL", "#f87171"
elif threat >= 50: tlabel, tc = "ELEVATED", "#fb923c"
elif threat >= 20: tlabel, tc = "GUARDED", "#fbbf24"
else:              tlabel, tc = "SECURE", "#34d399"
deg = threat / 100 * 360
gring = f"conic-gradient({tc} 0deg {deg:.0f}deg, rgba(255,255,255,0.07) {deg:.0f}deg 360deg)"

cga, cgb = st.columns([1, 1])
with cga:
    st.markdown(f"""
<div class="glow"><div class="panel"><div class="ttl">위협 레벨 · Threat Level</div>
  <div class="gaugewrap">
    <div class="gauge" style="background:{gring}; box-shadow:0 0 40px {tc}55, 0 8px 36px rgba(0,0,0,0.5)">
      <div class="hole"><div class="pct" style="color:{tc}">{threat}</div>
        <div class="tl" style="color:{tc}">{tlabel}</div></div></div>
    <div class="gmeta" style="flex:1">
      <div class="row"><span>치명 (CRITICAL)</span><b style="color:#fca5a5">{crit}</b></div>
      <div class="row"><span>높음 (HIGH)</span><b style="color:#fdba74">{high}</b></div>
      <div class="row"><span>차단 (BLOCK)</span><b style="color:#fca5a5">{s['blocked']}</b></div>
      <div class="row" style="border:none"><span>승인대기</span><b style="color:#c4b5fd">{s['pending']}</b></div>
    </div></div></div></div>
""", unsafe_allow_html=True)

with cgb:
    segs = [("#34d399", allow_cnt), ("#fbbf24", s["masked"]), ("#a78bfa", s["pending"]), ("#f87171", s["blocked"])]
    legend = "".join(
        f'<div class="lg"><span class="d" style="background:{c}"></span>{n}<b>{v}</b></div>'
        for c, n, v in [("#34d399", "ALLOW", allow_cnt), ("#fbbf24", "MASK", s["masked"]),
                        ("#a78bfa", "NEED_APPROVAL", s["pending"]), ("#f87171", "BLOCK", s["blocked"])])
    st.markdown(f'<div class="panel"><div class="ttl">처리 결과 분포 · Decision Mix</div>'
                f'<div class="donutwrap">{donut(segs, s["total"])}<div class="legend">{legend}</div></div></div>',
                unsafe_allow_html=True)

# ---------- RISK METER ----------
st.markdown('<div class="sec">Risk Levels</div>', unsafe_allow_html=True)
levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
mx = max([by.get(l, 0) for l in levels] + [1])
g2 = {"LOW":"#6ee7b7","MEDIUM":"#fde68a","HIGH":"#fdba74","CRITICAL":"#fca5a5"}
rows = ""
for l in levels:
    c = by.get(l, 0); w = c / mx * 100
    rows += (f'<div class="mrow"><div class="lab">{l}</div><div class="track">'
             f'<div class="fill" style="width:{w:.0f}%;--c:{SEV[l]};--c2:{g2[l]}"></div></div>'
             f'<div class="val">{c}</div></div>')
st.markdown(f'<div class="panel"><div class="meter">{rows}</div></div>', unsafe_allow_html=True)

# ---------- DETECTION LOG ----------
st.markdown('<div class="sec">Detection Log</div>', unsafe_allow_html=True)
f1, f2, f3 = st.columns(3)
fd = f1.selectbox("처리 결과", ["전체", "ALLOW", "MASK", "BLOCK", "NEED_APPROVAL"])
fr = f2.selectbox("위험도", ["전체", "LOW", "MEDIUM", "HIGH", "CRITICAL"])
fa = f3.selectbox("행동 유형", ["전체", "READ", "WRITE", "DELETE", "SEND", "EXPORT", "SECRET_ACCESS"])
logs = log_service.get_logs(decision=None if fd == "전체" else fd,
                            risk_level=None if fr == "전체" else fr,
                            action_type=None if fa == "전체" else fa)
if logs:
    head = ("<table class='logt'><tr><th>시각</th><th>사용자</th><th>요청</th><th>도구</th>"
            "<th>행동</th><th>위험도</th><th>점수</th><th>판정</th></tr>")
    body = ""
    for x in logs:
        sev = SEV.get(x["risk_level"], "#94a3b8")
        body += (f"<tr><td class='mono'>{html.escape(x['created_at'])}</td><td>{html.escape(x['user'])}</td>"
                 f"<td>{html.escape((x['user_input'] or '')[:42])}</td><td class='mono'>{html.escape(x['tool'])}</td>"
                 f"<td>{badge(x['action_type'],'b-neutral')}</td>"
                 f"<td><span class='sevdot' style='color:{sev}'></span>{badge(x['risk_level'],RISK.get(x['risk_level'],'b-neutral'))}</td>"
                 f"<td style='font-family:JetBrains Mono,monospace'>{x['risk_score']}</td>"
                 f"<td>{badge(x['decision'],DEC.get(x['decision'],'b-neutral'))}</td></tr>")
    st.markdown(f"<div class='panel' style='padding:18px 16px'>{head}{body}</table></div>", unsafe_allow_html=True)
else:
    st.markdown('<div class="empty">아직 로그가 없습니다. API로 요청을 보내면 여기에 실시간으로 쌓입니다.</div>', unsafe_allow_html=True)

# ---------- APPROVALS + QUARANTINE ----------
ca, cb = st.columns(2)
with ca:
    st.markdown('<div class="sec">Pending Approvals</div>', unsafe_allow_html=True)
    # ★ 병합(2026-07) — approve()가 실제로 행동을 실행한 직후의 결과(예: 실제 이메일 발송,
    # 테스트 고객 DB 실제 삭제)를 다음 화면 새로고침 때 한 번 보여줍니다. 승인 목록이 비게
    # 되더라도(마지막 대기 건이었어도) 이 배너는 그대로 보이도록 목록 위에 둡니다.
    if st.session_state.get("last_approval_output"):
        st.success(f"✅ 실행 결과: {st.session_state.pop('last_approval_output')}")
    pend = approval_service.list_pending()
    if pend:
        for item in pend:
            col = st.columns([4, 1, 1])
            col[0].markdown(f"<div class='row-card'>{badge('NEED_APPROVAL','b-info')} <b>{html.escape(item['summary'])}</b><br>"
                            f"<span style='color:#8b93ad;font-size:11.5px'>{html.escape(item['user'])} · {html.escape(item['created_at'])}</span></div>",
                            unsafe_allow_html=True)
            if col[1].button("승인", key="ap_" + item["request_id"]):
                result = approval_service.approve(item["request_id"])
                st.session_state["last_approval_output"] = result.get("output", "")
                st.rerun()
            if col[2].button("거절", key="rj_" + item["request_id"]):
                approval_service.reject(item["request_id"]); st.rerun()
    else:
        st.markdown('<div class="empty">승인 대기 요청이 없습니다.</div>', unsafe_allow_html=True)
with cb:
    st.markdown('<div class="sec">Quarantine</div>', unsafe_allow_html=True)
    q = anomaly_guard.status()
    if q:
        for item in q:
            col = st.columns([4, 1])
            col[0].markdown(f"<div class='row-card'>{badge('QUARANTINED','b-bad')} <b>{html.escape(item['user'])}</b> "
                            f"<span style='color:#8b93ad;font-size:11.5px'>· 남은 {item['남은초']}초</span></div>", unsafe_allow_html=True)
            if col[1].button("해제", key="rel_" + item["user"]):
                anomaly_guard.release(item["user"]); st.rerun()
    else:
        st.markdown('<div class="empty">격리된 사용자가 없습니다.</div>', unsafe_allow_html=True)

# ---------- REPORT ----------
st.markdown('<div class="sec">Incident Report</div>', unsafe_allow_html=True)
with st.expander("리포트 펼치기 · Expand full report"):
    st.json(incident_report.build_report())
