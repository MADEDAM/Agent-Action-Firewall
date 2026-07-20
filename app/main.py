"""
main.py   (담당: 조정우)    ★ 서버의 '정문'

[이 파일이 하는 일]
FastAPI 웹 서버를 만들고, 주소(엔드포인트)를 열어줍니다.
- POST /agent/request    : 요청을 받아 보안 검사 후 처리
- POST /agent/message    : 자연어 → 올라마 → 멀티스텝 (★ 메인)
- GET  /logs             : 로그 목록 (대시보드가 사용)
- GET  /stats            : 통계 숫자
- GET  /approvals/pending: 승인 대기 목록
- POST /approvals/approve, /approvals/reject : 승인/거절
- GET/POST /firewall, POST /firewall/toggle  : 방화벽 상태/토글
- GET  /quarantine       : 이상행동 격리 현황
- GET  /report           : 사고 리포트
- GET  /health           : 서버 살아있는지 확인

[실행 방법]
  uvicorn app.main:app --reload --port 8000
그러면 http://127.0.0.1:8000/docs 에서 직접 눌러볼 수 있어요.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .schemas import (AgentRequest, AgentResponse, ApprovalAction,
                      MessageRequest, FirewallState)
from .agent import agent_service
from .security import anomaly_guard
from .control import control_service
from .logs import log_service, log_repository
from .approval import approval_service
from .reports import incident_report

app = FastAPI(title="Agent Action Firewall", version="1.0")

# ★ 신규 — 프론트엔드(React, frontend/ 폴더, 기본 http://localhost:5173)가 브라우저에서
# 이 API(기본 http://localhost:8000)를 직접 호출하려면 CORS 허용이 필요합니다.
# 개발 편의를 위해 localhost/127.0.0.1의 아무 포트나 허용합니다(사내 데모용 — 운영 배포 시에는
# allow_origins를 실제 프론트엔드 도메인으로 좁혀야 합니다).
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    """서버가 켜질 때 DB 테이블을 준비합니다."""
    log_repository.init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/agent/request", response_model=AgentResponse)
def agent_request(req: AgentRequest):
    """사용자 요청 1건을 보안 검사 후 처리하고 결과를 돌려줍니다.
    (★ 2026-07 패치: CRITICAL Slack 알림은 agent_service._process_action 안에서
     공통으로 발송되도록 옮겼습니다 — /agent/message 경로도 빠짐없이 알림이 가도록.)"""
    return agent_service.handle_request(req.user, req.user_input, req.action.dict())


@app.get("/logs")
def get_logs(decision: str = None, risk_level: str = None, action_type: str = None):
    """로그 목록 (필터 가능)."""
    return log_service.get_logs(decision, risk_level, action_type)


@app.get("/stats")
def get_stats():
    return log_service.get_stats()


@app.get("/approvals/pending")
def pending():
    return approval_service.list_pending()


@app.post("/approvals/approve")
def approve(a: ApprovalAction):
    return approval_service.approve(a.request_id)


@app.post("/approvals/reject")
def reject(a: ApprovalAction):
    return approval_service.reject(a.request_id)


@app.post("/agent/message")
def agent_message(req: MessageRequest):
    """자연어 요청 → 올라마 계획(멀티스텝) → 단계별 보안 검사. (★ 메인 입구)"""
    return agent_service.handle_message(req.user, req.user_input)


@app.get("/firewall")
def firewall_status():
    """방화벽 ON/OFF 상태."""
    return {"enabled": control_service.is_firewall_on()}


@app.post("/firewall")
def firewall_set(state: FirewallState):
    """방화벽 켜기/끄기 (kill-switch)."""
    return control_service.set_firewall(state.enabled)


@app.post("/firewall/toggle")
def firewall_toggle():
    """방화벽 상태를 반대로 뒤집기."""
    return control_service.toggle()


@app.get("/quarantine")
def quarantine():
    """현재 이상행동으로 격리된 사용자 목록."""
    return anomaly_guard.status()


@app.get("/report")
def report():
    return incident_report.build_report()
