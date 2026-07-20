"""
chat_app.py — Agent Action Firewall client AI chat UI
Premium dark AI client screen. 관제 대시보드와 분리된 사용자용 AI 채팅 화면입니다.
실행: streamlit run dashboard/chat_app.py --server.port 8502
"""
import os
import sys
import html

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from app.agent import agent_service, llm_client
from app.control import control_service
from app.logs import log_repository

log_repository.init_db()

st.set_page_config(
    page_title="Agent Action Firewall",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CSS = r"""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');
#MainMenu, footer, [data-testid="stDecoration"], header[data-testid="stHeader"]{display:none!important}
:root{--bg:#020617;--panel:rgba(8,16,31,.72);--panel2:rgba(15,23,42,.66);--line:rgba(96,165,250,.22);--line2:rgba(59,130,246,.46);--text:#f8fafc;--muted:#94a3b8;--blue:#2563eb;--cyan:#22d3ee;--violet:#7c3aed;--green:#22c55e;--red:#ef4444;--amber:#f59e0b}
html,body,.stApp{background:radial-gradient(circle at 48% 10%,rgba(37,99,235,.18),transparent 33%),radial-gradient(circle at 86% 32%,rgba(124,58,237,.18),transparent 35%),linear-gradient(135deg,#020617 0%,#04101f 42%,#080b1d 100%)!important;color:var(--text);font-family:Pretendard,Inter,system-ui,sans-serif!important}
.stApp:before{content:"";position:fixed;inset:0;pointer-events:none;background-image:linear-gradient(rgba(96,165,250,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(96,165,250,.035) 1px,transparent 1px);background-size:64px 64px;mask-image:radial-gradient(circle at 52% 44%,#000 0%,transparent 72%)}
.block-container{max-width:none!important;padding:0!important;position:relative;z-index:1}
.aaf-shell{min-height:100vh;display:grid;grid-template-columns:280px minmax(650px,1fr) 300px;gap:0}
.aaf-side{border-right:1px solid rgba(96,165,250,.18);background:linear-gradient(180deg,rgba(2,6,23,.95),rgba(8,13,29,.98));padding:22px 18px;display:flex;flex-direction:column;min-height:100vh;box-shadow:20px 0 70px rgba(0,0,0,.34)}
.brand{display:flex;align-items:center;gap:12px;margin-bottom:26px}.brand-logo{width:44px;height:44px;border-radius:15px;display:grid;place-items:center;color:#7dd3fc;background:linear-gradient(135deg,rgba(37,99,235,.28),rgba(124,58,237,.18));border:1px solid rgba(125,211,252,.34);box-shadow:0 0 32px rgba(59,130,246,.28)}.brand-logo:before{content:"🛡"}.brand-title{font-size:16px;font-weight:950;line-height:1.08;text-transform:uppercase}.brand-sub{font-size:11px;color:#67e8f9;letter-spacing:.12em;font-weight:900;margin-top:5px;text-transform:uppercase}
.new-chat{height:52px;border-radius:16px;background:linear-gradient(135deg,#2563eb,#4f46e5 58%,#7c3aed);display:flex;align-items:center;justify-content:center;color:white;font-size:16px;font-weight:900;box-shadow:0 18px 44px rgba(37,99,235,.28);margin-bottom:28px}.section-label{font-size:12px;color:#64748b;text-transform:uppercase;letter-spacing:.08em;font-weight:900;margin:0 0 12px}.history-item{height:50px;border-radius:14px;background:rgba(15,23,42,.58);border:1px solid rgba(96,165,250,.15);display:flex;align-items:center;justify-content:space-between;padding:0 14px;margin-bottom:10px;color:#dbeafe;font-size:13px;font-weight:750}.history-item.active{border-color:rgba(96,165,250,.46);background:linear-gradient(135deg,rgba(37,99,235,.24),rgba(15,23,42,.62))}.history-empty{height:54px;border-radius:16px;background:rgba(15,23,42,.5);border:1px solid rgba(96,165,250,.16);display:grid;place-items:center;color:#64748b;font-size:13px}.side-bottom{margin-top:auto}.fw-card,.profile-card{border:1px solid rgba(96,165,250,.16);background:rgba(15,23,42,.58);border-radius:18px;padding:18px;box-shadow:inset 0 1px 0 rgba(255,255,255,.05)}.fw-title{font-size:11px;color:#94a3b8;letter-spacing:.09em;text-transform:uppercase;font-weight:950}.fw-state{display:flex;gap:12px;align-items:center;margin:14px 0 10px;color:#34d399;font-size:19px;font-weight:950}.fw-icon{width:42px;height:42px;border-radius:14px;display:grid;place-items:center;background:rgba(16,185,129,.16);box-shadow:0 0 32px rgba(16,185,129,.22)}.fw-icon:before{content:"🛡"}.fw-desc{color:#94a3b8;font-size:12.5px;line-height:1.6}.fw-link{margin-top:14px;padding-top:13px;border-top:1px solid rgba(96,165,250,.12);display:flex;justify-content:space-between;color:#bfdbfe;font-size:13px}.profile-card{margin-top:18px;display:flex;align-items:center;gap:12px;padding:14px}.avatar{width:38px;height:38px;border-radius:50%;display:grid;place-items:center;background:linear-gradient(135deg,#1d4ed8,#7c3aed);font-weight:950}.profile-name{font-weight:900;font-size:14px}.profile-role{color:#94a3b8;font-size:12px;margin-top:2px}
.main{padding:26px 36px 32px;min-height:100vh}.right{padding:86px 22px 24px 0;min-height:100vh}.topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:28px}.gateway{display:inline-flex;align-items:center;gap:10px;border:1px solid rgba(96,165,250,.24);background:rgba(15,23,42,.58);border-radius:999px;padding:11px 17px;color:#dbeafe;font-size:11px;font-weight:950;letter-spacing:.08em}.dot{width:9px;height:9px;border-radius:50%;background:#10b981;box-shadow:0 0 0 6px rgba(16,185,129,.12),0 0 20px rgba(16,185,129,.72)}.top-actions{display:flex;align-items:center;gap:14px}.toggle-label{font-weight:900;color:#dbeafe}.fake-toggle{width:58px;height:30px;border-radius:999px;background:linear-gradient(135deg,#2563eb,#10b981);border:1px solid rgba(125,211,252,.35);position:relative;box-shadow:0 0 24px rgba(16,185,129,.22)}.fake-toggle:after{content:"";position:absolute;right:4px;top:4px;width:22px;height:22px;border-radius:50%;background:white}.deploy{padding:14px 24px;border-radius:16px;border:1px solid rgba(96,165,250,.26);background:rgba(15,23,42,.58);font-weight:950;color:#e0e7ff}.hero{text-align:center}.hello{font-size:44px;font-weight:950;letter-spacing:-1.5px;text-shadow:0 0 32px rgba(37,99,235,.18)}.hello span{background:linear-gradient(90deg,#22d3ee,#3b82f6,#8b5cf6);-webkit-background-clip:text;color:transparent}.subcopy{color:#cbd5e1;font-size:16px;font-weight:750;margin-top:12px}.holo{height:310px;position:relative;display:grid;place-items:center;margin:8px auto 0}.holo:before{content:"";position:absolute;left:50%;bottom:38px;transform:translateX(-50%);width:430px;height:110px;background:radial-gradient(ellipse,rgba(34,211,238,.44),rgba(37,99,235,.12) 42%,transparent 72%);filter:blur(16px)}.holo-grid{position:absolute;inset:90px 10% 20px;background-image:linear-gradient(rgba(59,130,246,.12) 1px,transparent 1px),linear-gradient(90deg,rgba(59,130,246,.12) 1px,transparent 1px);background-size:28px 28px;transform:rotateX(64deg);transform-origin:center bottom;mask-image:radial-gradient(ellipse,#000 0%,transparent 68%)}.ring{position:absolute;border:1px solid rgba(34,211,238,.52);border-radius:50%;width:330px;height:82px;transform:rotateX(66deg);box-shadow:0 0 26px rgba(34,211,238,.22);animation:spin 14s linear infinite}.ring.r2{width:250px;height:62px;border-color:rgba(124,58,237,.45);animation:spin 21s linear infinite reverse}.shield{position:relative;width:185px;height:224px;filter:drop-shadow(0 0 18px rgba(34,211,238,.85)) drop-shadow(0 0 62px rgba(59,130,246,.45));animation:float 5s ease-in-out infinite}.shield:before{content:"";position:absolute;inset:0;background:linear-gradient(150deg,rgba(34,211,238,.78),rgba(37,99,235,.28) 50%,rgba(124,58,237,.42));clip-path:polygon(50% 0,91% 20%,83% 72%,50% 100%,17% 72%,9% 20%)}.shield:after{content:"";position:absolute;inset:18px;background:linear-gradient(150deg,rgba(15,23,42,.08),rgba(15,23,42,.78));clip-path:polygon(50% 3%,86% 21%,78% 68%,50% 91%,22% 68%,14% 21%);border:1px solid rgba(191,219,254,.26)}.mark{position:absolute;inset:0;display:grid;place-items:center;color:#67e8f9;font-size:82px;font-weight:950;text-shadow:0 0 24px rgba(34,211,238,.85);z-index:2}.scanline{position:absolute;left:18px;right:18px;top:45%;height:2px;background:linear-gradient(90deg,transparent,#67e8f9,transparent);z-index:3;box-shadow:0 0 18px #22d3ee;animation:scan 2.8s ease-in-out infinite}.particle{position:absolute;width:5px;height:5px;border-radius:50%;background:#60a5fa;box-shadow:0 0 14px #60a5fa;animation:drift 5s infinite}.p1{left:25%;top:42%}.p2{right:25%;top:35%;animation-delay:.8s}.p3{left:34%;bottom:25%;animation-delay:1.5s}.p4{right:33%;bottom:21%;animation-delay:2.2s}.quick-actions{display:flex;justify-content:center;gap:12px;flex-wrap:wrap;margin:0 0 18px}.quick-chip{border:1px solid rgba(96,165,250,.22);background:rgba(15,23,42,.54);border-radius:14px;padding:12px 16px;color:#dbeafe;font-size:13px;font-weight:850}.prompt-card{max-width:720px;margin:0 auto 18px;border:1px solid rgba(59,130,246,.5);background:linear-gradient(180deg,rgba(15,23,42,.72),rgba(3,7,18,.55));border-radius:20px;padding:18px;box-shadow:0 0 44px rgba(37,99,235,.18)}.prompt-placeholder{height:58px;display:flex;align-items:center;justify-content:space-between;color:#94a3b8}.send-dot{width:44px;height:44px;border-radius:14px;background:linear-gradient(135deg,#2563eb,#7c3aed);display:grid;place-items:center;color:white;font-size:20px}.scan-panel{max-width:880px;margin:0 auto;border:1px solid rgba(96,165,250,.22);background:rgba(15,23,42,.55);border-radius:22px;padding:20px}.scan-title{font-weight:950;color:#e2e8f0;margin-bottom:18px}.flow{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;position:relative}.flow:before{content:"";position:absolute;left:9%;right:9%;top:28px;height:2px;background:linear-gradient(90deg,#3b82f6,#22d3ee,#22c55e);opacity:.75}.step{text-align:center;position:relative}.node{width:56px;height:56px;margin:0 auto 10px;border-radius:50%;display:grid;place-items:center;background:rgba(37,99,235,.18);border:1px solid rgba(96,165,250,.42);font-size:22px}.node.done{background:rgba(16,185,129,.18);border-color:rgba(16,185,129,.52)}.stitle{font-size:12px;font-weight:900}.ssub{font-size:11px;color:#94a3b8;margin-top:4px}.protect{border:1px solid rgba(96,165,250,.24);background:linear-gradient(180deg,rgba(15,23,42,.68),rgba(3,7,18,.58));border-radius:24px;padding:22px;box-shadow:0 24px 70px rgba(0,0,0,.32),0 0 48px rgba(37,99,235,.13);margin-bottom:14px}.protect-head{display:flex;gap:10px;align-items:center;font-size:18px;font-weight:950}.protect-visual{width:88px;height:88px;border-radius:28px;margin:22px auto;display:grid;place-items:center;background:radial-gradient(circle,rgba(34,197,94,.22),rgba(15,23,42,.2));font-size:42px;box-shadow:0 0 44px rgba(34,197,94,.24)}.protect-copy{text-align:center;color:#cbd5e1;font-size:13.5px;line-height:1.65}.check-row{display:flex;gap:10px;align-items:center;padding:9px 0;color:#dbeafe;font-weight:800;font-size:13.5px}.check{width:20px;height:20px;border-radius:50%;display:grid;place-items:center;color:#34d399;border:1px solid rgba(52,211,153,.55);font-size:12px}.policy-mini{border:1px solid rgba(96,165,250,.16);background:rgba(15,23,42,.52);border-radius:18px;padding:18px}.policy-title{display:flex;justify-content:space-between;font-weight:900;margin-bottom:14px}.policy-dots{display:flex;gap:10px;flex-wrap:wrap;color:#94a3b8;font-size:12px}.policy-dots span:before{content:"";display:inline-block;width:7px;height:7px;background:#22c55e;border-radius:50%;margin-right:6px}.chat-wrap{max-width:900px;margin:20px auto}.msg-user{margin-left:auto;max-width:68%;padding:14px 18px;border-radius:18px 18px 5px 18px;background:linear-gradient(135deg,rgba(37,99,235,.36),rgba(124,58,237,.28));border:1px solid rgba(96,165,250,.24);line-height:1.65}.msg-assistant{max-width:86%;padding:18px 20px;border-radius:18px;background:rgba(15,23,42,.65);border:1px solid rgba(96,165,250,.18);margin:18px 0;line-height:1.7}.pill{display:inline-flex;padding:6px 12px;border-radius:999px;font-size:12px;font-weight:950;margin-bottom:10px}.allow{background:rgba(16,185,129,.14);color:#34d399}.block{background:rgba(239,68,68,.14);color:#fb7185}.mask{background:rgba(124,58,237,.14);color:#c4b5fd}.wait{background:rgba(245,158,11,.14);color:#fbbf24}.stChatInput{max-width:900px;margin:auto}.stChatInput > div{background:rgba(15,23,42,.76)!important;border:1px solid rgba(96,165,250,.28)!important;border-radius:18px!important;box-shadow:0 18px 50px rgba(0,0,0,.32)}.stChatInput textarea{color:#fff!important}
[data-testid="stSidebar"]{display:none!important}
@keyframes float{0%,100%{transform:translateY(0) rotateY(-8deg)}50%{transform:translateY(-12px) rotateY(8deg)}}@keyframes spin{to{transform:rotateX(66deg) rotateZ(360deg)}}@keyframes scan{0%{transform:translateY(-56px);opacity:0}35%,65%{opacity:1}100%{transform:translateY(60px);opacity:0}}@keyframes drift{0%,100%{transform:translateY(18px);opacity:.25}45%{transform:translateY(-24px);opacity:1}}
@media(max-width:1100px){.aaf-shell{grid-template-columns:230px 1fr}.right{display:none}.hello{font-size:34px}.flow{grid-template-columns:repeat(3,1fr)}.flow:before{display:none}}@media(max-width:800px){.aaf-shell{display:block}.aaf-side{display:none}.main{padding:20px}.hello{font-size:30px}}
</style>
"""

DECISION_STYLE = {
    "ALLOW": ("allow", "ALLOW"),
    "BLOCK": ("block", "BLOCK"),
    "MASK": ("mask", "MASK"),
    "NEED_APPROVAL": ("wait", "NEED APPROVAL"),
}


def esc(v):
    return html.escape(str(v or ""))


def render_layout_start(fw_on: bool):
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="aaf-shell">
          <aside class="aaf-side">
            <div class="brand"><div class="brand-logo"></div><div><div class="brand-title">Agent Action<br>Firewall</div><div class="brand-sub">AI Security Chat</div></div></div>
            <div class="new-chat">＋ 새 채팅</div>
            <div class="section-label">최근 대화</div>
            <div class="history-item active"><span>💬 고객 주문 데이터 조회</span><span>14:35</span></div>
            <div class="history-item"><span>💬 주간 매출 보고서 생성</span><span>14:20</span></div>
            <div class="history-item"><span>💬 재고 현황 확인</span><span>13:48</span></div>
            <div class="history-item"><span>💬 반품 요청 처리</span><span>13:30</span></div>
            <div class="history-item"><span>💬 상품 정보 요약</span><span>12:15</span></div>
            <div class="side-bottom">
              <div class="fw-card"><div class="fw-title">Firewall Status</div><div class="fw-state"><span class="fw-icon"></span>PROTECTION {'ON' if fw_on else 'OFF'}</div><div class="fw-desc">모든 AI 에이전트 요청을 실시간으로 보호 중입니다.</div><div class="fw-link"><span>정책 설정</span><span>→</span></div></div>
              <div class="profile-card"><div class="avatar">김</div><div><div class="profile-name">김연세님</div><div class="profile-role">SecOps Team</div></div></div>
            </div>
          </aside>
          <main class="main">
            <div class="topbar"><div class="gateway"><span class="dot"></span>AGENT SECURITY GATEWAY · {'ON' if fw_on else 'OFF'}</div><div class="top-actions"><span class="toggle-label">Firewall</span><span class="fake-toggle"></span><span class="deploy">Deploy</span></div></div>
        """,
        unsafe_allow_html=True,
    )


def render_layout_end():
    st.markdown("</main><aside class='right'>" + protection_html() + policy_html() + "</aside></div>", unsafe_allow_html=True)


def hero_html(user_name: str) -> str:
    return f"""
      <section class="hero">
        <div class="hello">안녕하세요, <span>{esc(user_name)}</span>님</div>
        <div class="subcopy">AI Agent가 안전하게 도와드릴게요.</div>
        <div class="holo">
          <div class="holo-grid"></div><div class="ring"></div><div class="ring r2"></div>
          <div class="particle p1"></div><div class="particle p2"></div><div class="particle p3"></div><div class="particle p4"></div>
          <div class="shield"><div class="scanline"></div><div class="mark">✓</div></div>
        </div>
        <div class="quick-actions">
          <div class="quick-chip">💬 고객 주문 데이터 조회</div>
          <div class="quick-chip">📊 주간 매출 보고서 생성</div>
          <div class="quick-chip">📦 재고 현황 확인</div>
        </div>
        <div class="prompt-card"><div class="prompt-placeholder"><span>AI에게 요청하세요...</span><span class="send-dot">↗</span></div></div>
      </section>
    """


def scan_panel_html() -> str:
    steps = [
        ("🔍", "입력 프롬프트 검사", "위험 탐지", ""),
        ("🛡", "정책 및 권한 검토", "접근 제어", ""),
        ("⬢", "외부 도구 실행 통제", "도구 검증", ""),
        ("💬", "AI 응답 콘텐츠 검사", "응답 검증", ""),
        ("🔒", "안전한 응답 제공", "완료 대기", "done"),
    ]
    items = "".join(f"<div class='step'><div class='node {done}'>{icon}</div><div class='stitle'>{title}</div><div class='ssub'>{sub}</div></div>" for icon,title,sub,done in steps)
    return f"<div class='scan-panel'><div class='scan-title'>🛡 실시간 보안 검사 진행 중</div><div class='flow'>{items}</div></div>"


def protection_html() -> str:
    return """
    <div class="protect">
      <div class="protect-head"><span class="dot"></span>보안 보호 중</div>
      <div class="protect-visual">✓</div>
      <div class="protect-copy">Agent Action Firewall이 AI 에이전트의 모든 활동을 안전하게 보호하고 있습니다.</div>
      <div class="check-row"><span class="check">✓</span>입력 프롬프트 검사</div>
      <div class="check-row"><span class="check">✓</span>AI 응답 콘텐츠 검사</div>
      <div class="check-row"><span class="check">✓</span>외부 도구 실행 통제</div>
      <div class="check-row"><span class="check">✓</span>데이터 유출 방지</div>
    </div>
    """


def policy_html() -> str:
    return """
    <div class="policy-mini"><div class="policy-title"><span>정책 엔진 상태</span><span>모두 정상</span></div>
      <div class="policy-dots"><span>보안 정책</span><span>권한 정책</span><span>탐지 규칙</span><span>차단 규칙</span></div>
    </div>
    """


def render_result_card(step: dict, idx: int, total: int) -> str:
    decision = step.get("decision", "ALLOW")
    cls, label = DECISION_STYLE.get(decision, ("allow", decision or "DONE"))
    output = step.get("output") or "요청이 처리되었습니다."
    risk = f"{step.get('risk_level','LOW')} · {step.get('risk_score',0)}점"
    prefix = f"STEP {idx} · " if total > 1 else ""
    reasons = step.get("reasons") or []
    reason_html = f"<div style='color:#94a3b8;margin-top:8px;font-size:13px'>사유: {esc(', '.join(reasons))}</div>" if reasons else ""
    return f"<div class='msg-assistant'><span class='pill {cls}'>{prefix}{esc(label)}</span><span style='color:#94a3b8;margin-left:8px;font-size:12px'>{esc(risk)}</span><div>{esc(output)}</div>{reason_html}</div>"


def process(prompt: str):
    prompt = (prompt or "").strip()
    if not prompt:
        return
    st.session_state.chat_history.append({"role": "user", "content": esc(prompt)})
    with st.spinner("Agent Action Firewall 검사 중..."):
        result = agent_service.handle_message(st.session_state.chat_user, prompt)
    parts = []
    if result.get("injection"):
        parts.append("<div class='msg-assistant'><span class='pill block'>PROMPT INJECTION</span><div>프롬프트 인젝션 시도가 감지되어 보호 조치가 적용되었습니다.</div></div>")
    steps = result.get("steps", [])
    for i, step in enumerate(steps, 1):
        ds = dict(step)
        try:
            ds["output"] = llm_client.narrate_result(prompt, step.get("decision", ""), step.get("output", ""))
        except Exception:
            pass
        parts.append(render_result_card(ds, i, len(steps)))
    st.session_state.chat_history.append({"role": "assistant", "content": "".join(parts) or "<div class='msg-assistant'>처리 결과가 없습니다.</div>", "raw": result})
    st.rerun()


st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("chat_user", "김연세")
fw_on = control_service.is_firewall_on()

render_layout_start(fw_on)

if not st.session_state.chat_history:
    st.markdown(hero_html(st.session_state.chat_user), unsafe_allow_html=True)
    st.markdown(scan_panel_html(), unsafe_allow_html=True)
    prompt = st.chat_input("AI에게 요청하세요...")
    if prompt:
        process(prompt)
else:
    st.markdown("<div class='chat-wrap'>", unsafe_allow_html=True)
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"<div class='msg-user'>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(msg["content"], unsafe_allow_html=True)
            if msg.get("raw") is not None:
                with st.expander("원본 JSON 보기"):
                    st.json(msg["raw"])
    st.markdown("</div>", unsafe_allow_html=True)
    prompt = st.chat_input("Agent Action Firewall에게 요청해보세요")
    if prompt:
        process(prompt)

render_layout_end()
