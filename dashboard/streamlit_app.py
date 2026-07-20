"""
streamlit_app.py — Agent Action Firewall SecOps Dashboard
Agent 실행 전 보안 통제 흐름이 한눈에 보이는 관제 대시보드입니다.

★ 2026-07 개편 (v2 — 실제 클릭 가능한 사이드바 내비게이션):
처음 버전은 사이드바 전체(브랜드/메뉴/방화벽 상태)를 하나의 raw HTML로 그려서 시각
디자인은 원본과 똑같았지만, 그 안의 메뉴(Overview/Approvals/Quarantine 등)는 그림일
뿐 실제로 클릭해도 아무 일도 일어나지 않았습니다. 이번 버전에서는 메뉴를 실제
Streamlit 버튼(st.button)으로 바꿔서, 클릭하면 진짜로 해당 화면(Approvals 승인/거절,
Quarantine 격리 해제, Audit Logs 필터링, Settings 방화벽 on/off 등)으로 전환되고
실제 동작(승인 실행, 격리 해제, 정책 조회 등)까지 이어지도록 했습니다.

실행: streamlit run dashboard/streamlit_app.py
"""
import os
import sys
import html
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd

from app.logs import log_repository, log_service
from app.control import control_service
from app.approval import approval_service
from app.security import anomaly_guard, policy_engine
from app.reports import incident_report

log_repository.init_db()
st.set_page_config(page_title="Agent Action Firewall Dashboard", page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed")

CSS = r"""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');
#MainMenu, footer, [data-testid="stDecoration"], header[data-testid="stHeader"], [data-testid="stSidebar"]{display:none!important}
:root{--bg:#020617;--panel:rgba(8,16,31,.72);--panel2:rgba(15,23,42,.66);--line:rgba(96,165,250,.18);--text:#f8fafc;--muted:#94a3b8;--blue:#3b82f6;--green:#22c55e;--red:#ef4444;--amber:#f59e0b;--violet:#8b5cf6;--cyan:#22d3ee}
html,body,.stApp{background:radial-gradient(circle at 12% 0%,rgba(37,99,235,.12),transparent 35%),radial-gradient(circle at 88% 90%,rgba(124,58,237,.12),transparent 35%),linear-gradient(135deg,#020617 0%,#04101f 55%,#050816 100%)!important;color:var(--text);font-family:Pretendard,Inter,system-ui,sans-serif!important}
.block-container{max-width:none!important;padding:20px 28px 40px!important}
[data-testid="column"]:first-of-type{border-right:1px solid rgba(96,165,250,.16);padding-right:16px!important}
.brand{display:flex;gap:12px;align-items:center;margin-bottom:20px}.brand-icon{width:42px;height:42px;border-radius:14px;display:grid;place-items:center;background:rgba(37,99,235,.18);border:1px solid rgba(96,165,250,.35);color:#60a5fa;font-size:24px}.brand-title{font-weight:950;line-height:1.1;text-transform:uppercase;font-size:15px}.brand-sub{font-size:12px;color:#94a3b8;margin-top:4px}
.badge{margin-left:auto;background:#2563eb;border-radius:999px;padding:3px 8px;font-size:11px}
.fwbox,.profile{border:1px solid rgba(96,165,250,.16);background:rgba(15,23,42,.55);border-radius:16px;padding:16px;margin-top:16px}.fw-title{font-size:12px;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em}.fw-state{font-size:20px;font-weight:950;margin:14px 0}.fw-state.on{color:#34d399}.fw-state.off{color:#fb7185}.status-dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#22c55e;box-shadow:0 0 0 6px rgba(34,197,94,.12);margin-right:8px}.status-dot.off{background:#ef4444;box-shadow:0 0 0 6px rgba(239,68,68,.12)}.profile{display:flex;gap:12px;align-items:center}.avatar{width:40px;height:40px;border-radius:50%;display:grid;place-items:center;background:linear-gradient(135deg,#1d4ed8,#7c3aed);font-weight:900}
.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}.search{width:430px;height:44px;border-radius:14px;border:1px solid rgba(96,165,250,.18);background:rgba(15,23,42,.55);display:flex;align-items:center;color:#64748b;padding:0 16px;font-size:13px}.sys{display:flex;align-items:center;gap:18px;color:#cbd5e1;font-size:13px}.bell{font-size:22px;position:relative}.hello{font-size:34px;font-weight:950}.sub{color:#a8b3cf;margin:8px 0 24px;font-size:15px;line-height:1.55}
.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:20px}.card{border:1px solid rgba(96,165,250,.15);background:linear-gradient(180deg,rgba(15,23,42,.68),rgba(3,7,18,.54));border-radius:16px;box-shadow:0 22px 56px rgba(0,0,0,.28),inset 0 1px 0 rgba(255,255,255,.04);overflow:hidden}.metric{padding:22px;min-height:118px;position:relative;overflow:hidden}.metric:after{content:"";position:absolute;right:10px;bottom:8px;width:120px;height:50px;background:linear-gradient(135deg,transparent,rgba(59,130,246,.12));clip-path:polygon(0 70%,15% 60%,28% 68%,40% 38%,56% 52%,70% 22%,88% 46%,100% 25%,100% 100%,0 100%)}.m-label{font-size:13px;color:#d6def2;text-transform:uppercase;font-weight:900;display:flex;gap:10px;align-items:center}.m-icon{width:38px;height:38px;border-radius:12px;display:grid;place-items:center;background:rgba(59,130,246,.15);color:#60a5fa}.m-val{font-size:40px;font-weight:900;margin-top:16px}.m-sub{font-size:13px;margin-top:8px;color:#a8b3cf;line-height:1.5}.up{color:#3b82f6}.bad{color:#ef4444}.good{color:#22c55e}.warn{color:#f59e0b}.violet{color:#a78bfa}.risk-ring{width:92px;height:92px;border-radius:50%;display:grid;place-items:center;margin:auto}.risk-inner{width:68px;height:68px;border-radius:50%;background:#06101f;display:grid;place-items:center}.risk-num{font-size:26px;font-weight:850}
.home-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:10px 0 22px}.home-card{min-height:152px;padding:22px;border:1px solid rgba(96,165,250,.18);border-radius:16px;background:linear-gradient(180deg,rgba(15,23,42,.72),rgba(6,12,25,.58));box-shadow:inset 0 1px 0 rgba(255,255,255,.04)}.home-ico{width:44px;height:44px;border-radius:14px;display:grid;place-items:center;background:rgba(59,130,246,.16);border:1px solid rgba(96,165,250,.25);font-size:22px;margin-bottom:18px}.home-title{font-size:18px;font-weight:950;margin-bottom:8px}.home-desc{font-size:14px;color:#a8b3cf;line-height:1.55;min-height:44px}.home-meta{font-size:12px;color:#60a5fa;font-weight:900;margin-top:12px;text-transform:uppercase}.console-note{padding:18px 20px;border:1px solid rgba(96,165,250,.16);border-radius:16px;background:rgba(15,23,42,.48);color:#cbd5e1;font-size:14px;line-height:1.65;margin-bottom:18px}
.grid2{display:grid;grid-template-columns:320px 1.45fr 360px;gap:14px;margin-bottom:14px}.grid3{display:grid;grid-template-columns:1fr 1.05fr 1.1fr;gap:14px;margin-bottom:14px}.panel{padding:22px}.panel-title{display:flex;justify-content:space-between;align-items:center;font-weight:950;text-transform:uppercase;font-size:16px;margin-bottom:18px}.view{color:#94a3b8;font-size:12px}
.agent{display:grid;grid-template-columns:42px 1fr 82px 56px;gap:10px;align-items:center;padding:13px 0;border-bottom:1px solid rgba(96,165,250,.09)}.agent:last-child{border-bottom:none}.agent-ico{width:36px;height:36px;border-radius:50%;display:grid;place-items:center;background:rgba(59,130,246,.13);border:1px solid rgba(96,165,250,.22)}.agent-name{font-weight:850;font-size:14.5px}.agent-meta{font-size:12.5px;color:#a8b3cf;margin-top:3px;line-height:1.5}
.tag{border-radius:7px;padding:5px 8px;text-align:center;font-size:10.5px;font-weight:900;white-space:nowrap;display:inline-block}.safe{background:rgba(34,197,94,.12);color:#34d399;border:1px solid rgba(34,197,94,.25)}.risk{background:rgba(245,158,11,.12);color:#fbbf24;border:1px solid rgba(245,158,11,.25)}.blocked{background:rgba(239,68,68,.12);color:#fb7185;border:1px solid rgba(239,68,68,.25)}.masked{background:rgba(139,92,246,.12);color:#c4b5fd;border:1px solid rgba(139,92,246,.25)}.idle{background:rgba(148,163,184,.1);color:#cbd5e1;border:1px solid rgba(148,163,184,.18)}
.pipe{padding:22px}.pipeline{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;position:relative;margin:20px 0}.pipeline:before{content:"";position:absolute;left:8%;right:8%;top:38px;height:2px;background:linear-gradient(90deg,#3b82f6,#22d3ee,#22c55e);box-shadow:0 0 16px rgba(34,211,238,.45)}.pstep{text-align:center;position:relative}.pnode{width:76px;height:76px;border-radius:50%;margin:0 auto 12px;display:grid;place-items:center;background:rgba(37,99,235,.14);border:1px solid rgba(96,165,250,.45);font-size:30px;box-shadow:0 0 25px rgba(37,99,235,.13)}.pnode.green{border-color:rgba(34,197,94,.45);color:#34d399}.pnode.amber{border-color:rgba(245,158,11,.5);color:#f59e0b}.pnode.red{border-color:rgba(239,68,68,.5);color:#ef4444}.ptitle{font-size:12px;font-weight:950;text-transform:uppercase}.psub{font-size:11px;color:#94a3b8;margin-top:10px;line-height:1.5}.current{border:1px solid rgba(96,165,250,.16);background:rgba(15,23,42,.54);border-radius:12px;padding:13px 16px;margin-top:18px;display:flex;justify-content:space-between;align-items:center;gap:14px;color:#cbd5e1;overflow:hidden}.current>span:first-child{flex:1 1 auto;min-width:0;overflow-wrap:break-word}.current .tag{flex-shrink:0}
.feed-item{display:grid;grid-template-columns:76px 34px 1fr 96px;gap:10px;padding:14px 0;border-bottom:1px solid rgba(96,165,250,.09);align-items:start}.feed-item:last-child{border-bottom:none}.time{color:#94a3b8;font-size:12.5px}.sev{width:30px;height:30px;border-radius:50%;display:grid;place-items:center}.sev.red{background:rgba(239,68,68,.14);color:#ef4444}.sev.amber{background:rgba(245,158,11,.14);color:#f59e0b}.sev.blue{background:rgba(59,130,246,.14);color:#3b82f6}.feed-body{min-width:0;overflow:hidden}.feed-title{font-weight:900;font-size:14.5px;overflow-wrap:anywhere;word-break:break-word}.feed-meta{font-size:13px;color:#a8b3cf;line-height:1.6;margin-top:5px;overflow-wrap:anywhere;word-break:break-word}
.tool-row,.policy-row,.approval-row{display:grid;grid-template-columns:130px 1fr 36px 36px 36px;gap:10px;align-items:center;padding:9px 0}.bar{height:7px;background:rgba(96,165,250,.13);border-radius:999px;overflow:hidden}.bar-in{height:100%;border-radius:999px;background:linear-gradient(90deg,#22c55e,#f59e0b,#ef4444,#8b5cf6)}.legend{display:flex;gap:18px;color:#94a3b8;font-size:12px;margin-top:10px}.legend span:before{content:"";display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px;background:#22c55e}.policy-row{grid-template-columns:42px 1fr 58px}.toggle-on{height:26px;border-radius:999px;background:rgba(34,197,94,.18);border:1px solid rgba(34,197,94,.25);display:flex;align-items:center;justify-content:center;color:#34d399;font-size:11px;font-weight:900}.approval-row{grid-template-columns:30px 1fr 116px}.btn-review{height:38px;border-radius:10px;background:linear-gradient(135deg,rgba(37,99,235,.28),rgba(15,23,42,.6));border:1px solid rgba(96,165,250,.2);display:grid;place-items:center;margin-top:12px;font-weight:850}
.trend{height:170px;position:relative;padding:12px 14px 4px}.trend svg{width:100%;height:138px}
.radar{height:150px;border-radius:50%;background:radial-gradient(circle,rgba(239,68,68,.16) 0 22%,transparent 22% 24%,rgba(59,130,246,.10) 24% 25%,transparent 25% 48%,rgba(59,130,246,.10) 48% 49%,transparent 49%),conic-gradient(from 0deg,rgba(239,68,68,.22),transparent 25%,rgba(37,99,235,.16),transparent 62%,rgba(239,68,68,.22));display:grid;place-items:center}.radar:before{content:"🛡";font-size:44px;color:#ef4444;filter:drop-shadow(0 0 20px rgba(239,68,68,.55))}
.level{display:grid;grid-template-columns:70px 1fr;gap:12px;align-items:center;margin:12px 0}.range{border-radius:7px;padding:6px 8px;text-align:center;font-size:12px}.r1{background:rgba(34,197,94,.12);color:#34d399;border:1px solid rgba(34,197,94,.25)}.r2{background:rgba(245,158,11,.12);color:#fbbf24;border:1px solid rgba(245,158,11,.25)}.r3{background:rgba(239,68,68,.12);color:#fb7185;border:1px solid rgba(239,68,68,.25)}
.sec{font-size:11px;font-weight:800;color:#9aa3c4;letter-spacing:2.6px;text-transform:uppercase;margin:6px 0 14px;display:flex;align-items:center;gap:12px}.sec::after{content:"";flex:1;height:1px;background:linear-gradient(90deg,rgba(255,255,255,.16),transparent)}
.row-card{padding:14px 18px;margin-bottom:10px;border-radius:14px;background:rgba(15,23,42,.55);border:1px solid rgba(96,165,250,.15)}
.empty-box{padding:24px;text-align:center;color:#94a3b8;font-size:13px;border:1px dashed rgba(96,165,250,.25);border-radius:14px;background:rgba(15,23,42,.35)}
.log-table-shell{border:1px solid rgba(96,165,250,.16);border-radius:14px;overflow:auto;background:linear-gradient(180deg,rgba(15,23,42,.68),rgba(3,7,18,.58));box-shadow:inset 0 1px 0 rgba(255,255,255,.04),0 18px 44px rgba(0,0,0,.28);max-height:560px}.log-table{width:100%;border-collapse:separate;border-spacing:0;color:#f8fafc;font-size:13.5px;line-height:1.45}.log-table thead th{position:sticky;top:0;z-index:1;background:#0b1524;color:#93c5fd;text-align:left;font-weight:900;padding:13px 14px;border-bottom:1px solid rgba(96,165,250,.3);white-space:nowrap}.log-table tbody td{padding:12px 14px;border-bottom:1px solid rgba(96,165,250,.1);vertical-align:top}.log-table tbody tr:nth-child(even){background:rgba(59,130,246,.03)}.log-table tbody tr:hover{background:rgba(59,130,246,.08)}.log-mono{font-family:Consolas,'SFMono-Regular',Menlo,monospace;color:#a8b3cf;white-space:nowrap}.log-request{color:#f8fafc;min-width:260px}.log-pill{display:inline-flex;align-items:center;border-radius:999px;padding:4px 9px;font-size:11px;font-weight:950;letter-spacing:.02em;white-space:nowrap}.pill-allow,.pill-low{background:rgba(34,197,94,.14);color:#86efac;border:1px solid rgba(34,197,94,.35)}.pill-mask,.pill-medium{background:rgba(20,184,166,.13);color:#67e8f9;border:1px solid rgba(20,184,166,.32)}.pill-block,.pill-high,.pill-critical{background:rgba(248,113,113,.13);color:#fca5a5;border:1px solid rgba(248,113,113,.34)}.pill-need_approval{background:rgba(245,158,11,.13);color:#fcd34d;border:1px solid rgba(245,158,11,.34)}
.navsec{font-size:11px;font-weight:950;color:#71809f;text-transform:uppercase;letter-spacing:1.8px;margin:18px 0 8px;padding-left:4px}.stButton button{background:rgba(255,255,255,.05);color:#f8fafc;border:1px solid rgba(96,165,250,.25);border-radius:12px;padding:12px 16px;font-weight:800;justify-content:flex-start;font-size:14px;min-height:44px}
.stButton button:hover{background:linear-gradient(92deg,rgba(37,99,235,.35),rgba(139,92,246,.3));border-color:rgba(139,92,246,.5);color:#fff}
.stButton button[kind="primary"]{background:linear-gradient(135deg,rgba(37,99,235,.55),rgba(124,58,237,.4))!important;border-color:rgba(96,165,250,.55)!important;color:#fff!important}
[data-testid="stExpander"]{border:1px solid rgba(96,165,250,.15);border-radius:14px;background:rgba(15,23,42,.4)}
div[data-baseweb="select"] > div{background:rgba(15,23,42,.55);border:1px solid rgba(96,165,250,.2);border-radius:10px;color:#f8fafc}
@media(max-width:1200px){.metrics,.home-grid{grid-template-columns:repeat(2,1fr)}.grid2,.grid3{grid-template-columns:1fr}.pipeline{grid-template-columns:repeat(3,1fr)}.pipeline:before{display:none}}
</style>
"""

# 도구 이름 → (아이콘, 사람이 읽기 좋은 "에이전트" 이름). 백엔드는 tool/operation만 알고
# '에이전트'라는 개념은 따로 없어서, 대시보드 표시용으로만 도구를 에이전트처럼 묶어 보여줍니다.
AGENT_MAP = {
    "mock_mail_tool": ("✉️", "Mail Assistant"),
    "mock_db_tool":   ("📊", "Personal Data Agent"),
    "mock_file_tool": ("📄", "File Assistant"),
    "mock_aws_tool":  ("☁️", "External Sharing Guard"),
    "mock_iam_tool":  ("🔐", "Permission Guard"),
}
DECISION_TAG = {
    "ALLOW": ("SAFE", "safe"), "BLOCK": ("BLOCKED", "blocked"),
    "MASK": ("MASKED", "masked"), "NEED_APPROVAL": ("RISK", "risk"),
}
DECISION_PRIORITY = {"BLOCK": 3, "NEED_APPROVAL": 2, "MASK": 1, "ALLOW": 0}
SEV_COLOR = {"CRITICAL": "red", "HIGH": "red", "MEDIUM": "amber", "LOW": "blue", "OFF": "blue"}

NAV_ITEMS = [
    ("▦", "Overview"), ("◎", "Agent Monitor"), ("⬢", "Action Requests"),
    ("◴", "Live Detection"), ("▣", "Policies"), ("▤", "Approvals"),
    ("▧", "Quarantine"), ("▥", "Reports"), ("☷", "Audit Logs"), ("⚙", "Settings"),
]
NAV_GROUPS = [
    ("Home", [("▦", "Overview")]),
    ("Monitor", [("◎", "Agent Monitor"), ("⬢", "Action Requests"), ("◴", "Live Detection")]),
    ("Governance", [("▣", "Policies"), ("▤", "Approvals"), ("▧", "Quarantine")]),
    ("Reports", [("▥", "Reports"), ("☷", "Audit Logs")]),
    ("System", [("⚙", "Settings")]),
]
PAGE_DESC = {
    "Overview": "필요한 영역으로 들어가는 콘솔 홈입니다. 전체 상황은 크게 보고, 세부 내용은 메뉴에서 확인하세요.",
    "Agent Monitor": "개인 AI 도구별 처리량과 차단/마스킹 현황을 확인합니다.",
    "Action Requests": "최근 사용자 요청과 실제 실행된 도구를 시간순으로 추적합니다.",
    "Live Detection": "방화벽이 감지한 이벤트를 실시간 피드로 확인합니다.",
    "Policies": "개인정보, 민감정보, 외부 공유 정책을 한곳에서 점검합니다.",
    "Approvals": "관리자 승인이 필요한 요청만 모아 처리합니다.",
    "Quarantine": "이상 행동으로 격리된 사용자를 확인하고 해제합니다.",
    "Reports": "현재 보안 이벤트를 보고서 형태로 요약합니다.",
    "Audit Logs": "조건별로 감사 로그를 검색하고 검토합니다.",
    "Settings": "방화벽 동작과 자동 새로고침을 설정합니다.",
}


def esc(v):
    return html.escape(str(v if v is not None else ""))


def pill_class(value):
    raw = str(value or "").lower()
    return "pill-" + raw.replace(" ", "_")


def render_log_table(records, columns, height=520):
    if not records:
        st.markdown('<div class="empty-box">표시할 데이터가 없습니다.</div>', unsafe_allow_html=True)
        return

    head = "".join(f"<th>{esc(label)}</th>" for key, label in columns)
    body = ""
    for record in records:
        cells = ""
        for key, label in columns:
            value = record.get(key, "")
            if label in ("판정", "위험도"):
                cells += f"<td><span class='log-pill {pill_class(value)}'>{esc(value)}</span></td>"
            elif label in ("시각", "도구", "행동", "사용자"):
                cells += f"<td class='log-mono'>{esc(value)}</td>"
            elif label == "요청":
                cells += f"<td class='log-request'>{esc(value)}</td>"
            else:
                cells += f"<td>{esc(value)}</td>"
        body += f"<tr>{cells}</tr>"

    st.markdown(
        f"<div class='log-table-shell' style='max-height:{height}px'>"
        f"<table class='log-table'><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>",
        unsafe_allow_html=True,
    )


def load_rows(limit=300):
    # ★ 수정(2026-07) — 예전에는 log_repository.fetch_logs()를 직접 불러서 항상 SQLite만
    # 읽었습니다. 그런데 LOG_BACKEND=dynamo로 운영 중일 때는 실제 로그가 DynamoDB에 있으므로,
    # log_service를 통해 불러야 현재 설정된 백엔드(SQLite/DynamoDB)를 그대로 따라갑니다.
    # (상단 통계 카드는 원래부터 log_service.get_stats()를 썼는데, Overview의 Running
    # Agents/Pipeline/Live Feed/Tool Calls만 이 버그 때문에 다른 백엔드를 보고 있었습니다.)
    try:
        return log_service.get_logs(limit=limit)
    except Exception:
        return []


def compute_risk_score(stats):
    """상단 Risk Score 링 카드용 점수(0~100). 실데이터가 없으면 0."""
    by_risk = stats.get("by_risk", {})
    crit, high = by_risk.get("CRITICAL", 0), by_risk.get("HIGH", 0)
    return min(100, stats["blocked"] * 12 + crit * 18 + high * 8 + stats["pending"] * 5)


# ============================== 읽기 전용 카드(HTML) — Overview/기타 화면에서 재사용 ==============================
def running_agents_html(rows, limit=5):
    if not rows:
        return ("<div class='card panel'><div class='panel-title'>Running Agents</div>"
                "<div class='empty-box'>아직 기록된 활동이 없습니다.<br>API/채팅으로 요청을 보내면 여기에 표시됩니다.</div></div>")
    by_agent = {}
    for r in rows:
        base = (r.get("tool") or "").split(".")[0]
        icon, name = AGENT_MAP.get(base, ("🤖", base or "Unknown Agent"))
        slot = by_agent.setdefault(base, {"icon": icon, "name": name, "count": 0, "worst": "ALLOW"})
        slot["count"] += 1
        if DECISION_PRIORITY.get(r["decision"], 0) > DECISION_PRIORITY.get(slot["worst"], 0):
            slot["worst"] = r["decision"]
    items = sorted(by_agent.values(), key=lambda a: -a["count"])[:limit]
    rows_html = "".join(
        f"<div class='agent'><div class='agent-ico'>{esc(a['icon'])}</div>"
        f"<div><div class='agent-name'>{esc(a['name'])}</div><div class='agent-meta'>오늘 {a['count']}건 처리</div></div>"
        f"<div class='tag {DECISION_TAG.get(a['worst'], ('IDLE','idle'))[1]}'>{DECISION_TAG.get(a['worst'], ('IDLE','idle'))[0]}</div>"
        f"<div style='color:#cbd5e1;text-align:right;font-size:12px'><span style='color:#94a3b8'>건수</span><br>{a['count']}</div></div>"
        for a in items
    )
    return f"<div class='card panel'><div class='panel-title'>Running Agents</div>{rows_html}</div>"


def pipeline_html(rows, fw_on):
    if not rows:
        steps = [("👤", "User Prompt", "대기 중", ""), ("🔍", "Prompt Scan", "대기 중", ""),
                 ("🛡", "Policy Engine", "대기 중", ""), ("🔒", "Permission Check", "대기 중", ""),
                 ("▷", "Execution", "대기 중", ""), ("🛡", "Decision", "대기 중", "")]
        items = "".join(f"<div class='pstep'><div class='pnode {c}'>{i}</div><div class='ptitle'>{t}</div><div class='psub'>{s}</div></div>" for i, t, s, c in steps)
        return f"<div class='card pipe'><div class='panel-title'>Agent Execution Pipeline <span style=\"color:#94a3b8\">● Idle</span></div><div class='pipeline'>{items}</div><div class='current'><span>아직 처리된 요청이 없습니다.</span></div></div>"

    latest = rows[0]
    decision = latest["decision"]
    tag_label, tag_cls = DECISION_TAG.get(decision, ("DONE", "safe"))
    color_cls = "green" if decision == "ALLOW" else "amber" if decision in ("MASK", "NEED_APPROVAL") else "red"
    steps = [
        ("👤", "User Prompt", f"접수됨<br>{esc(latest['created_at'][-8:])}", ""),
        ("🔍", "Prompt Scan", "검사 완료<br><span class='good'>OK</span>", "green"),
        ("🛡", "Policy Engine", f"판정: {esc(latest['risk_level'])}", color_cls if decision != "ALLOW" else "green"),
        ("🔒", "Permission Check", f"역할 확인<br><span class='good'>OK</span>", "green"),
        ("▷", "Execution", ("실행됨" if decision in ("ALLOW", "MASK") else "미실행"), "green" if decision in ("ALLOW", "MASK") else "red"),
        ("🛡", "Decision", f"<span class='tag {tag_cls}'>{tag_label}</span>", color_cls),
    ]
    items = "".join(f"<div class='pstep'><div class='pnode {c}'>{i}</div><div class='ptitle'>{t}</div><div class='psub'>{s}</div></div>" for i, t, s, c in steps)
    return (f"<div class='card pipe'><div class='panel-title'>Agent Execution Pipeline <span class='good'>● Live Flow</span></div><div class='pipeline'>{items}</div>"
            f"<div class='current'><span>Current Action: <b>{esc(latest['tool'])}</b><br>"
            f"<span style='color:#94a3b8'>User: {esc(latest['user'])} &nbsp;|&nbsp; Risk Score: {latest['risk_score']}/120</span></span>"
            f"<span class='tag {tag_cls}'>{esc(decision)}</span></div></div>")


def feed_html(rows, limit=6):
    if not rows:
        return ("<div class='card panel'><div class='panel-title'>Live Detection Feed</div>"
                "<div class='empty-box'>탐지된 이벤트가 없습니다.</div></div>")
    items = ""
    for r in rows[:limit]:
        sev = SEV_COLOR.get(r["risk_level"], "blue")
        tag_label, tag_cls = DECISION_TAG.get(r["decision"], (r["decision"], "idle"))
        reason = (r.get("reasons") or [""])[-1]
        items += (f"<div class='feed-item'><div class='time'>{esc(r['created_at'][-8:])}</div><div class='sev {sev}'>●</div>"
                  f"<div class='feed-body'><div class='feed-title'>{esc(r['tool'])}</div>"
                  f"<div class='feed-meta'>{esc(r['user'])} · {esc(reason)[:90]}</div></div>"
                  f"<div class='tag {tag_cls}'>{esc(tag_label)}</div></div>")
    return f"<div class='card panel'><div class='panel-title'>Live Detection Feed</div>{items}</div>"


def tool_calls_html(rows, limit=5):
    if not rows:
        return ("<div class='card panel'><div class='panel-title'>Tool Calls Today</div>"
                "<div class='empty-box'>아직 도구 호출 기록이 없습니다.</div></div>")
    agg = {}
    for r in rows:
        base = (r.get("tool") or "").split(".")[0] or "unknown"
        slot = agg.setdefault(base, {"count": 0, "blocked": 0, "masked": 0})
        slot["count"] += 1
        if r["decision"] == "BLOCK":
            slot["blocked"] += 1
        elif r["decision"] == "MASK":
            slot["masked"] += 1
    items = sorted(agg.items(), key=lambda kv: -kv[1]["count"])[:limit]
    mx = max(v["count"] for _, v in items) or 1
    rows_html = "".join(
        f"<div class='tool-row'><div>{esc(name)}</div><div class='bar'><div class='bar-in' style='width:{v['count']/mx*100:.0f}%'></div></div>"
        f"<div>{v['count']}</div><div>{v['blocked']}</div><div>{v['masked']}</div></div>"
        for name, v in items
    )
    return f"<div class='card panel'><div class='panel-title'>Tool Calls Today</div>{rows_html}<div class='legend'><span>COUNT</span><span style='color:#ef4444'>BLOCK</span><span style='color:#8b5cf6'>MASK</span></div></div>"


def policy_html(limit=6):
    icons = ["🛡", "🛡", "▧", "◇", "▣", "🔐", "◈"]
    rules = policy_engine.POLICY.get("rules", [])
    if limit:
        rules = rules[:limit]
    rows_html = "".join(
        f"<div class='policy-row'><div class='agent-ico'>{icons[i % len(icons)]}</div>"
        f"<div><b>{esc(r['id'])}</b><div class='agent-meta'>{esc(r.get('desc', r.get('reason','')))}</div></div>"
        f"<div class='toggle-on'>ON</div></div>"
        for i, r in enumerate(rules)
    )
    return f"<div class='card panel'><div class='panel-title'>Policy Engine Status</div>{rows_html}</div>"


def approvals_preview_html(pending):
    if not pending:
        return ("<div class='card panel'><div class='panel-title'>Pending Approvals</div>"
                "<div class='empty-box'>승인 대기 중인 요청이 없습니다.</div></div>")
    items = ""
    for p in pending[:3]:
        items += (f"<div class='approval-row'><div class='sev amber'>!</div>"
                  f"<div><b>{esc(p['summary'])}</b><div class='feed-meta'>{esc(p['user'])} · {esc(p['created_at'])}</div></div>"
                  f"<div class='tag risk'>NEED APPROVAL</div></div>")
    return (f"<div class='card panel'><div class='panel-title'>Pending Approvals</div>{items}"
            f"<div class='btn-review'>← 왼쪽 'Approvals' 메뉴에서 승인/거절 · 총 {len(pending)}건</div></div>")


def trend_html(rows):
    ordered = list(reversed(rows))[-14:]  # 오래된 → 최신 순
    if len(ordered) < 2:
        scores = [0] * 14
    else:
        scores = [int(r.get("risk_score") or 0) for r in ordered]
        while len(scores) < 14:
            scores.insert(0, scores[0])
    mx = max(max(scores), 20)
    xs = [20 + i * (715 / 13) for i in range(14)]
    ys = [140 - (s / mx) * 110 for s in scores]
    points = " ".join(f"{x:.0f},{y:.0f}" for x, y in zip(xs, ys))
    last_color = "#ef4444" if scores[-1] >= 80 else "#f59e0b" if scores[-1] >= 50 else "#3b82f6"
    svg = (f"<svg viewBox='0 0 760 150' preserveAspectRatio='none'><defs><linearGradient id='ta' x1='0' x2='0' y1='0' y2='1'>"
           f"<stop offset='0%' stop-color='#3b82f6' stop-opacity='.35'/><stop offset='100%' stop-color='#ef4444' stop-opacity='0'/></linearGradient></defs>"
           f"<line x1='20' y1='126' x2='740' y2='126' stroke='rgba(148,163,184,.15)'/><line x1='20' y1='86' x2='740' y2='86' stroke='rgba(148,163,184,.09)'/>"
           f"<line x1='20' y1='46' x2='740' y2='46' stroke='rgba(148,163,184,.09)'/>"
           f"<polygon points='20,140 {points} 735,140' fill='url(#ta)'/>"
           f"<polyline points='{points}' fill='none' stroke='#3b82f6' stroke-width='3' stroke-linecap='round'/>"
           f"<circle cx='{xs[-1]:.0f}' cy='{ys[-1]:.0f}' r='5' fill='{last_color}'/></svg>")
    return f"<div class='card panel'><div class='panel-title'>Risk Score Over Time</div><div class='trend'>{svg}</div></div>"


def risk_levels_html(stats):
    by = stats.get("by_risk", {})
    return f"""<div class="card panel"><div class="level"><div class="range r1">LOW</div><div><b>Low Risk</b><div class="agent-meta">{by.get('LOW',0)}건 · 정상 처리</div></div></div><div class="level"><div class="range r2">MEDIUM</div><div><b class="warn">Medium Risk</b><div class="agent-meta">{by.get('MEDIUM',0)}건 · 모니터링 필요</div></div></div><div class="level"><div class="range r3">HIGH+</div><div><b class="bad">High/Critical</b><div class="agent-meta">{by.get('HIGH',0)+by.get('CRITICAL',0)}건 · 즉시 확인 필요</div></div></div><div class="radar"></div></div>"""


def protection_layers_html(fw_on):
    state = "ON" if fw_on else "OFF"
    return (f"<div class='card panel'><div class='panel-title'>Protection Layers</div>"
            f"<div class='policy-row'><div class='agent-ico'>🛡</div><div><b>Input Guard</b><div class='agent-meta'>Active</div></div><div class='toggle-on'>{state}</div></div>"
            f"<div class='policy-row'><div class='agent-ico'>▤</div><div><b>Audit Logger</b><div class='agent-meta'>Active</div></div><div class='toggle-on'>ON</div></div>"
            f"<div class='policy-row'><div class='agent-ico'>◇</div><div><b>Output Filter</b><div class='agent-meta'>Active</div></div><div class='toggle-on'>{state}</div></div></div>")


def render_quarantine_rows(quarantined):
    """격리된 사용자 목록 + '격리 해제' 버튼. Overview(빠른 해제)와 Quarantine 페이지가 공통으로 씁니다."""
    if not quarantined:
        st.markdown('<div class="empty-box">현재 격리된 사용자가 없습니다.</div>', unsafe_allow_html=True)
        return
    for item in quarantined:
        c = st.columns([4, 1])
        c[0].markdown(
            f"<div class='row-card'><span class='tag blocked'>QUARANTINED</span> "
            f"<b>{esc(item['user'])}</b> <span style='color:#94a3b8;font-size:11.5px'>· 남은 {item['남은초']}초</span></div>",
            unsafe_allow_html=True,
        )
        if c[1].button("격리 해제", key="release_" + item["user"]):
            anomaly_guard.release(item["user"])
            st.rerun()


# ============================== 페이지(실제 클릭 시 전환되는 화면) ==============================
def open_page(label):
    st.session_state["page"] = label
    st.rerun()


def overview_card(icon, title, desc, meta, target):
    st.markdown(
        f"<div class='home-card'><div class='home-ico'>{esc(icon)}</div>"
        f"<div class='home-title'>{esc(title)}</div><div class='home-desc'>{esc(desc)}</div>"
        f"<div class='home-meta'>{esc(meta)}</div></div>",
        unsafe_allow_html=True,
    )
    if st.button(f"{title} 열기", key=f"open_{target}", use_container_width=True):
        open_page(target)


def page_overview(rows, stats, fw_on, pending, quarantined):
    total, blocked, need = stats["total"], stats["blocked"], stats["pending"]
    risk = compute_risk_score(stats)
    st.markdown(
        "<div class='console-note'>"
        "이 화면은 전체 관제 내용을 한 번에 펼치지 않고, AWS 콘솔처럼 필요한 영역으로 들어가는 홈입니다. "
        "상세 로그와 표는 왼쪽 메뉴나 아래 카드에서 단계적으로 확인할 수 있습니다."
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"""
    <section class="metrics">
      <div class="card metric"><div class="m-label"><span class="m-icon">▦</span>오늘 요청</div><div class="m-val">{total:,}</div><div class="m-sub">개인 AI 요청 처리 현황</div></div>
      <div class="card metric"><div class="m-label"><span class="m-icon" style="color:#ef4444;background:rgba(239,68,68,.13)">■</span>차단</div><div class="m-val">{blocked}</div><div class="m-sub">위험하거나 과도한 공유 요청</div></div>
      <div class="card metric"><div class="m-label"><span class="m-icon" style="color:#f59e0b;background:rgba(245,158,11,.13)">!</span>승인 대기</div><div class="m-val">{need}</div><div class="m-sub">확인이 필요한 민감 작업</div></div>
      <div class="card metric"><div class="m-label"><span class="m-icon" style="color:#a78bfa;background:rgba(139,92,246,.13)">●</span>위험 점수</div><div class="m-val">{risk}</div><div class="m-sub">{'높음' if risk>=70 else '중간' if risk>=30 else '낮음'} 단계로 모니터링 중</div></div>
    </section>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sec">Console Navigation</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        overview_card("◴", "실시간 탐지", "방금 들어온 요청과 방화벽 판단을 피드 형태로 확인합니다.", f"최근 {min(len(rows), 20)}건", "Live Detection")
    with c2:
        overview_card("◎", "도구 모니터", "메일, 파일, 개인 데이터, 외부 공유 도구별 처리 흐름을 봅니다.", "도구별 집계", "Agent Monitor")
    with c3:
        overview_card("▤", "승인함", "사용자에게 바로 실행하기 애매한 요청만 따로 검토합니다.", f"대기 {len(pending)}건", "Approvals")

    c4, c5, c6 = st.columns(3)
    with c4:
        overview_card("▣", "정책", "개인정보, 민감정보, 외부 공유 차단 기준을 확인합니다.", "정책 엔진", "Policies")
    with c5:
        overview_card("☷", "감사 로그", "조건을 걸어 요청, 도구, 판단 결과를 추적합니다.", "검색/필터", "Audit Logs")
    with c6:
        overview_card("⚙", "설정", "방화벽 ON/OFF와 대시보드 새로고침을 관리합니다.", "시스템 설정", "Settings")

    st.markdown('<div class="sec">Latest Snapshot</div>', unsafe_allow_html=True)
    st.markdown(
        f"<section class='grid3' style='grid-template-columns:1fr 1fr'>"
        f"{feed_html(rows, limit=3)}{approvals_preview_html(pending)}</section>",
        unsafe_allow_html=True,
    )


def page_agent_monitor(rows, fw_on):
    st.markdown('<div class="sec">최근 실행 파이프라인</div>', unsafe_allow_html=True)
    st.markdown(pipeline_html(rows, fw_on), unsafe_allow_html=True)

    st.markdown('<div class="sec">도구(에이전트)별 처리 현황</div>', unsafe_allow_html=True)
    if not rows:
        st.markdown('<div class="empty-box">아직 기록된 활동이 없습니다.</div>', unsafe_allow_html=True)
        return
    agg = {}
    for r in rows:
        base = (r.get("tool") or "").split(".")[0] or "unknown"
        _, name = AGENT_MAP.get(base, ("🤖", base))
        slot = agg.setdefault(base, {"name": name, "count": 0, "allow": 0, "block": 0, "mask": 0, "need_approval": 0})
        slot["count"] += 1
        key = {"ALLOW": "allow", "BLOCK": "block", "MASK": "mask", "NEED_APPROVAL": "need_approval"}.get(r["decision"])
        if key:
            slot[key] += 1
    records = [
        {"에이전트": v["name"], "도구": k, "총 처리": v["count"], "허용": v["allow"],
         "차단": v["block"], "마스킹": v["mask"], "승인대기": v["need_approval"]}
        for k, v in sorted(agg.items(), key=lambda kv: -kv[1]["count"])
    ]
    render_log_table(
        records,
        [("에이전트", "에이전트"), ("도구", "도구"), ("총 처리", "총 처리"), ("허용", "허용"),
         ("차단", "차단"), ("마스킹", "마스킹"), ("승인대기", "승인대기")],
        height=360,
    )


def page_action_requests(rows):
    st.markdown('<div class="sec">최근 처리된 Action Request</div>', unsafe_allow_html=True)
    if not rows:
        st.markdown('<div class="empty-box">아직 처리된 요청이 없습니다.</div>', unsafe_allow_html=True)
        return
    records = [
        {"시각": r["created_at"], "사용자": r["user"], "요청": (r["user_input"] or "")[:60],
         "도구": r["tool"], "행동": r["action_type"], "위험도": r["risk_level"],
         "점수": r["risk_score"], "판정": r["decision"]}
        for r in rows[:40]
    ]
    render_log_table(
        records,
        [("시각", "시각"), ("사용자", "사용자"), ("요청", "요청"), ("도구", "도구"),
         ("행동", "행동"), ("위험도", "위험도"), ("점수", "점수"), ("판정", "판정")],
        height=560,
    )


def page_live_detection(rows):
    st.markdown('<div class="sec">Live Detection Feed — 최근 20건</div>', unsafe_allow_html=True)
    st.markdown(feed_html(rows, limit=20), unsafe_allow_html=True)


def page_policies():
    st.markdown('<div class="sec">Policy Engine — 전체 규칙 (data/policies.json)</div>', unsafe_allow_html=True)
    st.markdown(policy_html(limit=None), unsafe_allow_html=True)


def page_approvals(pending):
    st.markdown('<div class="sec">Pending Approvals — 승인/거절</div>', unsafe_allow_html=True)
    if st.session_state.get("last_approval_output"):
        st.success(f"✅ 실행 결과: {st.session_state.pop('last_approval_output')}")
    if not pending:
        st.markdown('<div class="empty-box">승인 대기 요청이 없습니다.</div>', unsafe_allow_html=True)
        return
    for item in pending:
        c = st.columns([4, 1, 1])
        c[0].markdown(
            f"<div class='row-card'><span class='tag risk'>NEED APPROVAL</span> "
            f"<b>{esc(item['summary'])}</b><br>"
            f"<span style='color:#94a3b8;font-size:11.5px'>{esc(item['user'])} · {esc(item['created_at'])}</span></div>",
            unsafe_allow_html=True,
        )
        if c[1].button("승인", key="approve_" + item["request_id"]):
            result = approval_service.approve(item["request_id"])
            st.session_state["last_approval_output"] = result.get("output", "")
            st.rerun()
        if c[2].button("거절", key="reject_" + item["request_id"]):
            approval_service.reject(item["request_id"])
            st.rerun()


def page_quarantine(quarantined):
    st.markdown('<div class="sec">Quarantine — 이상행동 자동격리</div>', unsafe_allow_html=True)
    render_quarantine_rows(quarantined)


def page_reports():
    st.markdown('<div class="sec">Incident Report</div>', unsafe_allow_html=True)
    report = incident_report.build_report()
    s = report["summary"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 요청", s["총_요청"])
    c2.metric("차단", s["차단"])
    c3.metric("승인대기", s["승인대기"])
    c4.metric("마스킹", s["마스킹"])
    with st.expander("전체 리포트(JSON) 펼치기", expanded=False):
        st.json(report)


def page_audit_logs():
    st.markdown('<div class="sec">Audit Logs — 감사 로그 조회</div>', unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3)
    fd = f1.selectbox("처리 결과", ["전체", "ALLOW", "MASK", "BLOCK", "NEED_APPROVAL"], key="filter_decision")
    fr = f2.selectbox("위험도", ["전체", "LOW", "MEDIUM", "HIGH", "CRITICAL"], key="filter_risk")
    fa = f3.selectbox("행동 유형", ["전체", "READ", "WRITE", "DELETE", "SEND", "EXPORT", "SECRET_ACCESS", "PRIV_ESC"], key="filter_action")
    logs = log_service.get_logs(
        decision=None if fd == "전체" else fd,
        risk_level=None if fr == "전체" else fr,
        action_type=None if fa == "전체" else fa,
        limit=300,
    )
    if not logs:
        st.markdown('<div class="empty-box">조건에 맞는 로그가 없습니다. API/채팅으로 요청을 보내면 여기에 실시간으로 쌓입니다.</div>', unsafe_allow_html=True)
        return
    records = [{
        "시각": r["created_at"], "사용자": r["user"], "요청": (r["user_input"] or "")[:40],
        "도구": r["tool"], "행동": r["action_type"], "위험도": r["risk_level"],
        "점수": r["risk_score"], "판정": r["decision"],
    } for r in logs]
    render_log_table(
        records,
        [("시각", "시각"), ("사용자", "사용자"), ("요청", "요청"), ("도구", "도구"),
         ("행동", "행동"), ("위험도", "위험도"), ("점수", "점수"), ("판정", "판정")],
        height=500,
    )


def page_settings(fw_on):
    st.markdown('<div class="sec">Settings</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c2:
        new_state = st.toggle("방화벽 ON/OFF", value=fw_on, key="fw_toggle_settings")
        if new_state != fw_on:
            control_service.set_firewall(new_state)
            st.rerun()
    with c1:
        if fw_on:
            st.success("🛡 방화벽이 켜져 있습니다 — 모든 AI 행동이 실시간으로 검사됩니다.")
        else:
            st.error("⚠ 방화벽이 꺼져 있습니다 — AI 행동이 검사 없이 그대로 실행됩니다. 시연 비교용이 아니면 다시 켜세요.")

    st.markdown("<br>", unsafe_allow_html=True)
    auto = st.checkbox("🔄 5초마다 자동 새로고침", value=False, key="auto_refresh")
    if auto:
        st.markdown('<meta http-equiv="refresh" content="5">', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="sec">데이터 리셋</div>', unsafe_allow_html=True)
    st.caption(
        "Total Requests / Blocked Actions / Need Approval / Masked Actions 카드는 "
        "로그 기록 건수로 계산됩니다. 아래 리셋을 누르면 이 로그가 전부 삭제되어 "
        "카드가 0으로 돌아갑니다 (승인 대기 목록·격리 이력·방화벽 설정은 그대로 유지됩니다). "
        "되돌릴 수 없으니 시연/테스트 데이터를 정리할 때만 사용하세요."
    )
    confirm_reset = st.checkbox("로그 기록을 전부 삭제하는 데 동의합니다", key="confirm_reset_logs")
    if st.button("🗑 로그 리셋 (카드 값 0으로 초기화)", key="btn_reset_logs", disabled=not confirm_reset):
        log_service.reset_logs()
        st.session_state["confirm_reset_logs"] = False
        st.success("로그가 초기화되었습니다. 상단 카드가 0으로 표시됩니다.")
        st.rerun()


# ============================== 메인 — 사이드바 내비게이션 + 페이지 라우팅 ==============================
def main():
    rows = load_rows()
    stats = log_service.get_stats()
    fw_on = control_service.is_firewall_on()
    pending = approval_service.list_pending()
    quarantined = anomaly_guard.status()

    st.markdown(CSS, unsafe_allow_html=True)
    st.session_state.setdefault("page", "Overview")
    st.session_state.setdefault("sidebar_collapsed", False)
    collapsed = st.session_state["sidebar_collapsed"]

    if collapsed:
        st.markdown(
            "<style>"
            "[data-testid='column']:first-of-type{padding-right:6px!important;border-right:1px solid rgba(96,165,250,.10)!important}"
            "[data-testid='column']:first-of-type .stButton button{padding:8px 0!important;justify-content:center!important;font-size:15px!important}"
            "</style>",
            unsafe_allow_html=True,
        )

    col_side, col_main = st.columns([0.34, 4.9] if collapsed else [1, 3.6], gap="small" if collapsed else "medium")

    with col_side:
        # ★ 사용자 요청 — 사이드바 접기/펼치기
        toggle_icon = "»" if collapsed else "«  접기"
        if st.button(toggle_icon, key="nav_collapse_toggle", use_container_width=True):
            st.session_state["sidebar_collapsed"] = not collapsed
            st.rerun()

        if collapsed:
            st.markdown('<div class="brand-icon" style="margin-bottom:14px">🛡</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="brand"><div class="brand-icon">🛡</div><div>'
                '<div class="brand-title">Agent Action<br>Firewall</div>'
                '<div class="brand-sub">Personal AI Guard Console</div></div></div>',
                unsafe_allow_html=True,
            )

        badge_count = {"Approvals": len(pending), "Quarantine": len(quarantined)}
        for group, items in NAV_GROUPS:
            if not collapsed:
                st.markdown(f'<div class="navsec">{esc(group)}</div>', unsafe_allow_html=True)
            for icon, label in items:
                n = badge_count.get(label, 0)
                if collapsed:
                    btn_label = icon + (f"·{n}" if n else "")
                else:
                    btn_label = f"{icon}  {label}" + (f"  ({n})" if n else "")
                if st.button(btn_label, key=f"nav_{label}", use_container_width=True,
                             type="primary" if st.session_state["page"] == label else "secondary"):
                    st.session_state["page"] = label
                    st.rerun()

        if not collapsed:
            fw_state = "PROTECTION ON" if fw_on else "PROTECTION OFF"
            st.markdown(
                f'<div class="fwbox"><div class="fw-title">Firewall Status</div>'
                f'<div class="fw-state {"on" if fw_on else "off"}">{fw_state}</div>'
                f'<div><span class="status-dot {"" if fw_on else "off"}"></span>'
                f'{"System Healthy" if fw_on else "Protection Disabled"}</div>'
                f'<div style="color:#94a3b8;font-size:12px;margin-top:10px">Settings 메뉴에서 켜고 끌 수 있습니다</div></div>'
                '<div class="profile"><div class="avatar">ST</div><div><b>SecOps Team</b>'
                '<div style="color:#94a3b8;font-size:12px">Administrator</div></div></div>',
                unsafe_allow_html=True,
            )
        else:
            dot = "" if fw_on else "off"
            st.markdown(f'<div class="status-dot {dot}" style="margin:10px auto;display:block;width:10px;height:10px"></div>', unsafe_allow_html=True)

    with col_main:
        now = datetime.now().strftime("%Y-%m-%d   %H:%M:%S")
        st.markdown(
            f'<div class="top"><div class="search">⌕ Search events, users, threats...</div>'
            f'<div class="sys"><span><span class="status-dot {"" if fw_on else "off"}"></span>'
            f'{"System Healthy" if fw_on else "Protection Disabled"}</span>'
            f'<span>📅 {now} (UTC+09:00)</span><span class="bell">♧</span></div></div>',
            unsafe_allow_html=True,
        )
        page = st.session_state["page"]
        st.markdown(f'<div class="hello">{esc(page)}</div><div class="sub">{esc(PAGE_DESC.get(page, "개인 AI 방화벽 상태를 확인합니다."))}</div>', unsafe_allow_html=True)

        total, blocked, need, masked = stats["total"], stats["blocked"], stats["pending"], stats["masked"]
        risk = compute_risk_score(stats)
        if page != "Overview":
            st.markdown(f"""
            <section class="metrics">
              <div class="card metric"><div class="m-label"><span class="m-icon">▧</span>Total Requests</div><div class="m-val">{total:,}</div><div class="m-sub" style="color:#94a3b8">실시간 로그 기준(SQLite)</div></div>
              <div class="card metric"><div class="m-label"><span class="m-icon" style="color:#ef4444;background:rgba(239,68,68,.13)">🛡</span>Blocked Actions</div><div class="m-val">{blocked}</div><div class="m-sub" style="color:#94a3b8">Input/Action Guard 차단</div></div>
              <div class="card metric"><div class="m-label"><span class="m-icon" style="color:#f59e0b;background:rgba(245,158,11,.13)">◷</span>Need Approval</div><div class="m-val">{need}</div><div class="m-sub" style="color:#94a3b8">관리자 승인 대기 중</div></div>
              <div class="card metric"><div class="m-label"><span class="m-icon" style="color:#a78bfa;background:rgba(139,92,246,.13)">◈</span>Masked Actions</div><div class="m-val">{masked}</div><div class="m-sub" style="color:#94a3b8">Output Guard 마스킹</div></div>
            </section>
            """, unsafe_allow_html=True)

        if page == "Overview":
            page_overview(rows, stats, fw_on, pending, quarantined)
        elif page == "Agent Monitor":
            page_agent_monitor(rows, fw_on)
        elif page == "Action Requests":
            page_action_requests(rows)
        elif page == "Live Detection":
            page_live_detection(rows)
        elif page == "Policies":
            page_policies()
        elif page == "Approvals":
            page_approvals(pending)
        elif page == "Quarantine":
            page_quarantine(quarantined)
        elif page == "Reports":
            page_reports()
        elif page == "Audit Logs":
            page_audit_logs()
        elif page == "Settings":
            page_settings(fw_on)


main()
