"""
schemas.py   (담당: 조정우 / 공통 약속)

[이 파일이 하는 일]
API로 주고받는 데이터의 '모양(형식)'을 정합니다. (FastAPI가 이 모양으로 검사해줍니다)
이 파일이 곧 세 사람의 '인터페이스 약속서'예요. 여기 필드 이름을 바꾸면 서로 안 맞습니다.

pydantic 의 BaseModel = "이런 필드들이 이런 타입으로 있어야 해" 라고 정해두는 틀.
"""
from typing import List, Optional
from pydantic import BaseModel


class ActionPlan(BaseModel):
    """AI가 실행하려는 '행동 계획' 한 개."""
    tool: str                       # 예: "mock_db_tool"
    operation: str                  # 예: "delete_database"
    target: str = "none"            # 예: "prod_db" / "backup" / "customer_db"
    destination: str = "internal"   # "internal" 또는 "external"
    scope: str = "single"           # "single" 또는 "broadcast"
    payload_text: str = ""          # 비밀값/개인정보 검사용 본문


class AgentRequest(BaseModel):
    """사용자가 보내는 요청 1건."""
    user: str
    user_input: str
    action: ActionPlan


class AgentResponse(BaseModel):
    """보안 검사 후 돌려주는 결과."""
    request_id: str
    decision: str                   # ALLOW / MASK / BLOCK / NEED_APPROVAL
    risk_level: str
    risk_score: int
    action_type: str
    reasons: List[str]
    output: str


class ApprovalAction(BaseModel):
    """승인/거절 요청."""
    request_id: str


class MessageRequest(BaseModel):
    """자연어 요청 (올라마가 행동 계획을 만듦)."""
    user: str
    user_input: str


class FirewallState(BaseModel):
    """방화벽 켜기/끄기 (kill-switch)."""
    enabled: bool
