"""
tool_runner.py   (담당: 조정우)   ★ 신규 (2026-07)

[이 파일이 하는 일]
'검사를 통과한 행동을 실제로 실행하는' 부분만 따로 뗀 파일입니다.
원래 이 코드는 agent_service.py 안에 있었는데, 이번에 "승인(NEED_APPROVAL) 후 실제로
실행되게" 만들면서 approval_service.py도 같은 실행 로직이 필요해졌습니다.

approval_service.py가 agent_service.py를 직접 import하면 순환 참조(agent_service →
approval_service → agent_service …)가 생기기 때문에, 실행 로직 자체를 이 파일로 분리해서
agent_service.py와 approval_service.py가 둘 다 여기서만 가져다 쓰도록 정리했습니다.
(동작은 이전과 100% 동일합니다 — 파일 위치만 옮겼습니다.)
"""
import re

from ..tools import mock_db_tool, mock_mail_tool, mock_file_tool, mock_aws_tool, mock_iam_tool

EXECUTORS = {
    ("mock_db_tool", "search_mail"):     mock_db_tool.search_mail,
    ("mock_db_tool", "list_subscriptions"): mock_db_tool.list_subscriptions,
    ("mock_db_tool", "read_contacts"):   mock_db_tool.read_contacts,
    ("mock_db_tool", "summarize_file"):  mock_db_tool.summarize_file,
    ("mock_db_tool", "read_secure_note"): mock_db_tool.read_secure_note,
    ("mock_db_tool", "add_calendar_event"): mock_db_tool.add_calendar_event,
    ("mock_db_tool", "read_orders"):     mock_db_tool.read_orders,
    ("mock_db_tool", "read_customers"):  mock_db_tool.read_customers,
    ("mock_db_tool", "count_customers"): mock_db_tool.count_customers,
    ("mock_db_tool", "delete_database"): mock_db_tool.delete_database,
    ("mock_db_tool", "delete_backup"):   mock_db_tool.delete_backup,
    # ★ 신규(2026-07) — 테스트 고객 DB 실제 삭제
    ("mock_db_tool", "delete_customer"): mock_db_tool.delete_customer,
    ("mock_mail_tool", "send_mail"):     mock_mail_tool.send_mail,
    ("mock_mail_tool", "send_all"):      mock_mail_tool.send_all,
    ("mock_file_tool", "read_file"):     mock_file_tool.read_file,
    ("mock_file_tool", "write_file"):    mock_file_tool.write_file,
    ("mock_file_tool", "delete_file"):   mock_file_tool.delete_file,
    ("mock_aws_tool", "get_secret"):     mock_aws_tool.get_secret,
    ("mock_aws_tool", "export_to_url"):  mock_aws_tool.export_to_url,
    ("mock_iam_tool", "put_user_policy"):    mock_iam_tool.put_user_policy,
    ("mock_iam_tool", "attach_user_policy"): mock_iam_tool.attach_user_policy,
}

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_URL_RE = re.compile(r"https?://\S+")


def extract_kwargs(action: dict) -> dict:
    """
    실행 직전, action(target/payload_text)에서 도구 함수가 실제로 받는 kwargs를 뽑아냅니다.
    schemas.py의 ActionPlan 모양 자체는 바꾸지 않습니다 — 이건 실행 직전 '어댑터'라서,
    백이담·김나형과 맞춘 인터페이스 약속(스키마)에는 영향이 없습니다.
    """
    tool = action.get("tool")
    op = action.get("operation")
    target = action.get("target", "none")
    target = target if target not in (None, "none", "") else ""
    text = action.get("payload_text", "") or ""

    if (tool, op) == ("mock_mail_tool", "send_mail"):
        m = _EMAIL_RE.search(text) or _EMAIL_RE.search(target)
        return {"to": m.group() if m else target, "body": text}
    if (tool, op) == ("mock_mail_tool", "send_all"):
        return {"body": text}
    if (tool, op) == ("mock_file_tool", "read_file"):
        return {"path": target or text}
    if (tool, op) == ("mock_file_tool", "write_file"):
        return {"path": target or text, "content": text}
    if (tool, op) == ("mock_file_tool", "delete_file"):
        return {"path": target or text}
    if (tool, op) == ("mock_aws_tool", "get_secret"):
        return {"name": target or "secret"}
    if (tool, op) == ("mock_aws_tool", "export_to_url"):
        m = _URL_RE.search(text)
        return {"url": m.group() if m else target, "data": text}
    if (tool, op) in (("mock_iam_tool", "put_user_policy"), ("mock_iam_tool", "attach_user_policy")):
        return {"user": target or "unknown_user", "policy": "AdministratorAccess"}
    if (tool, op) == ("mock_db_tool", "search_mail"):
        return {"query": text or target}
    if (tool, op) == ("mock_db_tool", "read_contacts"):
        return {"name": text if action.get("scope") != "broadcast" else ""}
    if (tool, op) == ("mock_db_tool", "summarize_file"):
        return {"query": text or target}
    if (tool, op) == ("mock_db_tool", "read_secure_note"):
        return {"query": text or target}
    if (tool, op) == ("mock_db_tool", "add_calendar_event"):
        return {"title": text or target, "when_text": ""}
    if (tool, op) == ("mock_db_tool", "delete_customer"):
        # ★ 신규(2026-07) — payload_text(원문 문장) 안에서 실제 존재하는 고객 이름/이메일을
        # customers_repository가 찾아서 지우므로, 여기서는 문장 전체를 그대로 넘깁니다.
        return {"name": text or target}
    if (tool, op) == ("mock_db_tool", "read_orders"):
        return {"customer_name": text or target}
    return {}  # mock_db_tool의 조회/운영DB/백업 계열은 원래도 파라미터가 없음


def run_tool(action: dict) -> str:
    """실행 전 보안 검사를 통과한 행동 1개를 실제로 실행합니다."""
    fn = EXECUTORS.get((action.get("tool"), action.get("operation")))
    if not fn:
        return "[도구 없음] 알 수 없는 도구입니다."
    return fn(**extract_kwargs(action))
