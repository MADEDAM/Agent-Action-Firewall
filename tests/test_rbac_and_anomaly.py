"""
tests/test_rbac_and_anomaly.py

기획서의 "RBAC 기반 사용자 권한 매핑"과 "고급 기능 — 이상행동 자동격리"를 검증합니다.
(둘 다 KPI 표에는 직접 없지만, 기획서 3)절 Action Guard / 백이담 담당 산출물에 해당하는
핵심 보안 기능이라 별도 테스트로 분리했습니다.)

실행: pytest tests/test_rbac_and_anomaly.py -v
"""
import pytest

from app.security import rbac, policy_engine, anomaly_guard


# ---------------- RBAC ----------------
def test_unknown_user_is_general_role():
    assert rbac.get_role("no_such_user_xyz") == "general"
    assert rbac.get_role(None) == "general"


def test_known_admin_user_has_admin_role():
    # data/rbac_roles.json 에 등록된 관리자 계정
    assert rbac.get_role("admin_user") == "admin"
    assert rbac.get_role("demo_admin") == "admin"


def test_general_user_secret_access_is_blocked():
    action = {"tool": "mock_aws_tool", "operation": "get_secret", "target": "secret",
              "destination": "internal", "scope": "single", "payload_text": ""}
    verdict = policy_engine.evaluate(action, user="general_user_xyz")
    assert verdict["decision"] == "BLOCK"
    assert verdict["matched_rule"] == "R2"
    assert verdict["role"] == "general"


def test_admin_user_secret_access_is_downgraded_to_need_approval():
    """RBAC 완화: 관리자 계정은 시크릿 조회 시 즉시 차단이 아니라 승인 대기로 바뀝니다."""
    action = {"tool": "mock_aws_tool", "operation": "get_secret", "target": "secret",
              "destination": "internal", "scope": "single", "payload_text": ""}
    verdict = policy_engine.evaluate(action, user="admin_user")
    assert verdict["decision"] == "NEED_APPROVAL"
    assert verdict["matched_rule"] == "R_ADMIN1"
    assert verdict["role"] == "admin"


def test_admin_user_prod_db_delete_is_downgraded_to_need_approval():
    action = {"tool": "mock_db_tool", "operation": "delete_database", "target": "prod_db",
              "destination": "internal", "scope": "single", "payload_text": ""}
    verdict_admin = policy_engine.evaluate(action, user="demo_admin")
    assert verdict_admin["decision"] == "NEED_APPROVAL"
    assert verdict_admin["matched_rule"] == "R_ADMIN2"

    verdict_general = policy_engine.evaluate(action, user="general_user_xyz")
    assert verdict_general["decision"] == "BLOCK"
    assert verdict_general["matched_rule"] == "R1"


# ---------------- 이상행동 자동격리 (anomaly_guard) ----------------
@pytest.fixture(autouse=True)
def _clean_anomaly_state():
    anomaly_guard.reset()
    yield
    anomaly_guard.reset()


def test_critical_risk_quarantines_immediately():
    user = "attacker_critical_test"
    assert anomaly_guard.is_quarantined(user) is False
    result = anomaly_guard.register_risky(user, risk_level="CRITICAL")
    assert result["quarantined"] is True
    assert anomaly_guard.is_quarantined(user) is True


def test_high_risk_needs_three_within_window_to_quarantine():
    user = "attacker_high_test"
    r1 = anomaly_guard.register_risky(user, risk_level="HIGH")
    assert r1["quarantined"] is False
    r2 = anomaly_guard.register_risky(user, risk_level="HIGH")
    assert r2["quarantined"] is False
    r3 = anomaly_guard.register_risky(user, risk_level="HIGH")
    assert r3["quarantined"] is True
    assert anomaly_guard.is_quarantined(user) is True


def test_manual_release_clears_quarantine():
    user = "attacker_release_test"
    anomaly_guard.register_risky(user, risk_level="CRITICAL")
    assert anomaly_guard.is_quarantined(user) is True
    anomaly_guard.release(user)
    assert anomaly_guard.is_quarantined(user) is False


def test_quarantine_status_lists_active_users():
    user = "attacker_status_test"
    anomaly_guard.register_risky(user, risk_level="CRITICAL")
    active = {row["user"] for row in anomaly_guard.status()}
    assert user in active
