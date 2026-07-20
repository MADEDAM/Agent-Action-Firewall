"""
tests/test_api.py

FastAPI 엔드포인트(app/main.py) 통합 테스트. 기획서의 "관리자 승인 플로우 및 통합
보안 관제 대시보드"가 실제로 API 레벨에서 동작하는지(로그 적재, 승인/거절, 방화벽
kill-switch) 확인합니다.

★ httpx가 설치되어 있어야 합니다 (requirements.txt에 포함됨 — FastAPI TestClient 의존성).

실행: pytest tests/test_api.py -v
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.control import control_service
from app.agent import llm_client

client = TestClient(app)


@pytest.fixture(autouse=True)
def _firewall_on():
    control_service.set_firewall(True)
    yield
    control_service.set_firewall(True)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_firewall_get_and_toggle_roundtrip():
    initial = client.get("/firewall").json()["enabled"]

    toggled = client.post("/firewall/toggle").json()
    assert toggled["firewall_enabled"] == (not initial)

    restored = client.post("/firewall", json={"enabled": initial}).json()
    assert restored["firewall_enabled"] == initial

    final = client.get("/firewall").json()["enabled"]
    assert final == initial


def test_agent_request_blocks_prod_db_delete():
    payload = {
        "user": "api_test_user",
        "user_input": "운영 데이터베이스 전체 삭제해줘",
        "action": {
            "tool": "mock_db_tool", "operation": "delete_database",
            "target": "prod_db", "destination": "internal",
            "scope": "single", "payload_text": "",
        },
    }
    res = client.post("/agent/request", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["decision"] == "BLOCK"
    assert body["risk_level"] == "CRITICAL"


def test_agent_request_allows_safe_read():
    payload = {
        "user": "api_test_user2",
        "user_input": "전체 고객이 몇 명인지 알려줘",
        "action": {
            "tool": "mock_db_tool", "operation": "count_customers",
            "target": "customer_db", "destination": "internal",
            "scope": "single", "payload_text": "",
        },
    }
    res = client.post("/agent/request", json=payload)
    assert res.status_code == 200
    assert res.json()["decision"] == "ALLOW"


def test_agent_message_natural_language_endpoint():
    res = client.post("/agent/message", json={
        "user": "api_test_user3", "user_input": "전체 고객이 몇 명인지 알려줘",
    })
    assert res.status_code == 200
    body = res.json()
    assert "steps" in body
    assert len(body["steps"]) >= 1
    assert body["steps"][0]["decision"] == "ALLOW"


def test_approval_flow_end_to_end():
    """NEED_APPROVAL 요청 → /approvals/pending 노출 → 승인 → 실제 실행 → 대기열에서 제거."""
    payload = {
        "user": "api_test_approver",
        "user_input": "전 직원에게 공지 메일 보내줘",
        "action": {
            "tool": "mock_mail_tool", "operation": "send_all",
            "target": "mail", "destination": "internal",
            "scope": "broadcast", "payload_text": "전체 공지입니다",
        },
    }
    created = client.post("/agent/request", json=payload).json()
    assert created["decision"] == "NEED_APPROVAL"
    request_id = created["request_id"]

    pending_ids = [p["request_id"] for p in client.get("/approvals/pending").json()]
    assert request_id in pending_ids

    approved = client.post("/approvals/approve", json={"request_id": request_id}).json()
    assert approved["status"] == "APPROVED"
    assert "output" in approved

    pending_ids_after = [p["request_id"] for p in client.get("/approvals/pending").json()]
    assert request_id not in pending_ids_after


def test_logs_and_stats_endpoints_respond():
    logs = client.get("/logs").json()
    assert isinstance(logs, list)

    stats = client.get("/stats").json()
    for key in ("total", "blocked", "pending", "masked", "by_risk"):
        assert key in stats


def test_report_endpoint_shape():
    report = client.get("/report").json()
    assert "summary" in report
    assert "주요_사건" in report


def test_order_lookup_uses_customer_entity_and_masks_pii(monkeypatch):
    monkeypatch.setattr(llm_client, "_plan_with_ollama", lambda _text: [{
        "tool": "mock_db_tool",
        "operation": "read_orders",
        "target": "customer_db",
        "destination": "internal",
        "scope": "single",
        "payload_text": "김백조",
    }])

    res = client.post("/agent/message", json={
        "user": "api_test_order", "user_input": "고객 김백조의 주문 내역을 조회해줘",
    })

    body = res.json()
    step = body["steps"][0]
    assert step["decision"] == "MASK"
    assert step["risk_score"] == 30
    assert "김백조 고객 주문 내역" in step["output"]
    assert "김영희" not in step["output"]
    assert "이철수" not in step["output"]
    assert "ba***@test.com" in step["output"]


def test_order_lookup_missing_customer_does_not_return_customer_list(monkeypatch):
    monkeypatch.setattr(llm_client, "_plan_with_ollama", lambda _text: [{
        "tool": "mock_db_tool",
        "operation": "read_orders",
        "target": "customer_db",
        "destination": "internal",
        "scope": "single",
        "payload_text": "김없는",
    }])

    res = client.post("/agent/message", json={
        "user": "api_test_missing_order", "user_input": "고객 김없는의 주문 내역을 조회해줘",
    })

    step = res.json()["steps"][0]
    assert step["output"] == "해당 고객을 찾을 수 없습니다"
    assert "고객 목록" not in step["output"]
    assert "김영희" not in step["output"]


def test_all_customer_contact_fields_are_blocked_high(monkeypatch):
    monkeypatch.setattr(llm_client, "_plan_with_ollama", lambda _text: [{
        "tool": "mock_db_tool",
        "operation": "read_customers",
        "target": "customer_db",
        "destination": "internal",
        "scope": "broadcast",
        "payload_text": "전체 고객 이름, 이메일, 전화번호 알려줘",
    }])

    res = client.post("/agent/message", json={
        "user": "api_test_all_pii", "user_input": "전체 고객 이름, 이메일, 전화번호 알려줘",
    })

    step = res.json()["steps"][0]
    assert step["decision"] == "BLOCK"
    assert step["risk_level"] == "HIGH"
    assert step["risk_score"] == 50


def test_personal_mail_lookup_masks_private_details(monkeypatch):
    monkeypatch.setattr(llm_client, "_plan_with_ollama", lambda _text: [{
        "tool": "mock_db_tool",
        "operation": "search_mail",
        "target": "mailbox",
        "destination": "internal",
        "scope": "single",
        "payload_text": "항공권",
    }])

    res = client.post("/agent/message", json={
        "user": "api_test_personal_mail", "user_input": "내 항공권 예약 메일 찾아줘",
    })

    step = res.json()["steps"][0]
    assert step["decision"] == "MASK"
    assert step["risk_score"] == 30
    assert "항공권 예약 확인" in step["output"]
    assert "010-****-****" in step["output"]


def test_secure_note_request_is_blocked(monkeypatch):
    monkeypatch.setattr(llm_client, "_plan_with_ollama", lambda _text: [{
        "tool": "mock_db_tool",
        "operation": "read_secure_note",
        "target": "secret",
        "destination": "internal",
        "scope": "single",
        "payload_text": "비밀번호 메모",
    }])

    res = client.post("/agent/message", json={
        "user": "api_test_secret_note", "user_input": "비밀번호 메모 보여줘",
    })

    step = res.json()["steps"][0]
    assert step["decision"] == "BLOCK"
    assert step["risk_level"] in ("HIGH", "CRITICAL")


def test_export_all_contacts_is_blocked(monkeypatch):
    monkeypatch.setattr(llm_client, "_plan_with_ollama", lambda _text: [{
        "tool": "mock_aws_tool",
        "operation": "export_to_url",
        "target": "https://external.example/upload",
        "destination": "external",
        "scope": "broadcast",
        "payload_text": "연락처: 민지 minji@example.com 010-1111-2222",
    }])

    res = client.post("/agent/message", json={
        "user": "api_test_export_contacts", "user_input": "내 연락처 전체를 외부 사이트에 업로드해줘",
    })

    step = res.json()["steps"][0]
    assert step["decision"] == "BLOCK"
    assert step["risk_level"] in ("HIGH", "CRITICAL")


def test_calendar_add_is_allowed(monkeypatch):
    monkeypatch.setattr(llm_client, "_plan_with_ollama", lambda _text: [{
        "tool": "mock_db_tool",
        "operation": "add_calendar_event",
        "target": "calendar",
        "destination": "internal",
        "scope": "single",
        "payload_text": "내일 병원 예약",
    }])

    res = client.post("/agent/message", json={
        "user": "api_test_calendar", "user_input": "내일 병원 예약 캘린더에 추가해줘",
    })

    step = res.json()["steps"][0]
    assert step["decision"] == "ALLOW"
    assert "캘린더" in step["output"]
