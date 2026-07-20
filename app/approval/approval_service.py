"""
approval_service.py   (담당: 김나형)

[이 파일이 하는 일]
NEED_APPROVAL(관리자 승인 필요) 행동을 '승인 대기 목록'에 넣고,
관리자가 대시보드에서 승인/거절하면 상태를 바꿉니다.

[왜 필요한가]
전체 메일 발송처럼 '위험하진 않지만 영향이 큰' 행동은, 무조건 막기보다
사람이 한 번 확인하고 결정하게 만드는 게 안전합니다. 그 '확인 줄'이 승인 대기열이에요.

★ 병합 (2026-07) — "승인하면 진짜로 실행되게" 변경
지금까지는 approve()가 상태만 PENDING → APPROVED로 바꿀 뿐, 실제로 그 행동(이메일 발송,
고객 삭제 등)을 실행하는 코드가 어디에도 없었습니다. 즉 승인 버튼을 눌러도 겉보기만
바뀌고 실제로는 아무 일도 일어나지 않았습니다.

이제 create_request()가 실행에 필요한 action(행동 계획) 전체를 함께 저장해두고,
approve()가 그 action을 실제로 실행(app/agent/tool_runner.py)한 뒤 결과를 돌려줍니다.
agent_service.py를 직접 import하면 순환 참조가 생기므로, 실행 로직은 tool_runner.py
(agent_service와 approval_service가 공통으로 쓰는 파일)에서 가져옵니다.
"""
import json
from datetime import datetime

from ..logs import log_repository as repo
from ..logs import log_service
from ..agent import tool_runner
from ..security import output_guard


def create_request(request_id: str, user: str, action_type: str, summary: str,
                    action: dict = None, user_input: str = ""):
    """승인 대기 1건을 만든다. (조정우의 agent_service가 호출)
    ★ 병합(2026-07): action(실행할 행동 계획)도 함께 저장해서, 나중에 승인 시 실제로
    실행할 수 있게 합니다. action이 없으면(예: 옛날 호출부) 빈 값으로 저장됩니다."""
    repo.upsert_approval({
        "request_id": request_id,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user,
        "action_type": action_type,
        "summary": summary,
        "status": "PENDING",
        "action_json": json.dumps(action or {}, ensure_ascii=False),
        "user_input": user_input,
    })


def list_pending():
    """아직 결정 안 된 승인 대기 목록. (대시보드 승인 화면이 이걸 보여줌)"""
    return repo.fetch_approvals(status="PENDING")


def approve(request_id: str) -> dict:
    """
    관리자가 승인 → APPROVED로 바꾸고, 저장해둔 행동을 실제로 실행합니다.

    돌려주는 값: {"request_id":.., "status":"APPROVED", "output": "실제로 무슨 일이 일어났는지"}
    action이 비어있던 옛날 승인 건이라면 실행할 게 없으므로 그 사실을 그대로 알려줍니다.
    """
    row = repo.fetch_approval_one(request_id)
    repo.set_approval_status(request_id, "APPROVED")

    if not row or not row.get("action_json"):
        return {"request_id": request_id, "status": "APPROVED",
                "output": "(실행할 행동 정보가 저장되어 있지 않아 실제 실행은 건너뛰었습니다)"}

    try:
        action = json.loads(row["action_json"]) if row["action_json"] else {}
    except (json.JSONDecodeError, TypeError):
        action = {}

    if not action:
        return {"request_id": request_id, "status": "APPROVED",
                "output": "(실행할 행동 정보가 비어 있어 실제 실행은 건너뛰었습니다)"}

    # ★ 승인된 행동을 실제로 실행 (예: 이메일 실제 발송, 테스트 고객 DB 실제 삭제)
    raw = tool_runner.run_tool(action)
    guard = output_guard.guard_output(raw)
    output = guard["output"]

    # 실행 결과도 로그에 남겨서 대시보드 탐지 로그 표에서 확인할 수 있게 합니다.
    log_service.save_log({
        "request_id": request_id + "-approved",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": row.get("user", ""),
        "user_input": row.get("user_input", ""),
        "tool": f"{action.get('tool')}.{action.get('operation')}",
        "action_type": row.get("action_type", ""),
        "risk_level": "-",
        "risk_score": 0,
        "decision": "APPROVED_EXECUTED",
        "reasons": ["관리자가 승인하여 실제로 실행함"],
        "status": "DONE",
    })

    return {"request_id": request_id, "status": "APPROVED", "output": output}


def reject(request_id: str):
    """관리자가 거절 → REJECTED 로 변경. (거절된 행동은 절대 실행되지 않습니다)"""
    repo.set_approval_status(request_id, "REJECTED")
    return {"request_id": request_id, "status": "REJECTED"}
