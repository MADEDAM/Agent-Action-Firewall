"""
tests/test_core_demo_scenarios.py

기획서 KPI 표의 "시연 성공률 — 5대 핵심 시나리오 정상 작동 성공률 100%"를 검증합니다.
data/test_scenarios.json 에 있는 8개 베이스라인 시나리오(기획서 5대 시나리오 + 추가 케이스)를
실제 FastAPI 요청과 동일한 전체 파이프라인(app.agent.agent_service.handle_request)으로
끝까지 실행해서 최종 decision이 기대값과 일치하는지 확인합니다.

★ 주의: 이 테스트는 policy_engine만 보는 test_attack_scenarios.py와 달리 tool 실행 +
output_guard까지 전부 통과시킵니다. 예를 들어 "고객 목록 조회"(S2)는 요청 자체에는
개인정보가 없지만(payload_text 비어있음), 도구 실행 결과(고객 이름/이메일/전화번호)에
개인정보가 있어 output_guard가 MASK로 바꾸므로, 전체 파이프라인을 돌려야 기대값(MASK)과
맞습니다 — policy_engine 단독 테스트로는 이 케이스를 검증할 수 없습니다.

실행: pytest tests/test_core_demo_scenarios.py -v
"""
import json
import os

import pytest

from app.agent import agent_service
from app.control import control_service
from app.logs import log_repository

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE_PATH = os.path.join(ROOT_DIR, "data", "test_scenarios.json")


def _load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


_CORE_SCENARIOS = _load_json(CORE_PATH)


@pytest.fixture(autouse=True)
def _firewall_on():
    """이 테스트 파일은 항상 방화벽 ON 상태에서 실행합니다 (보호 기능 검증이 목적)."""
    log_repository.init_db()
    control_service.set_firewall(True)
    yield
    control_service.set_firewall(True)


@pytest.mark.parametrize("sc", _CORE_SCENARIOS, ids=[s["id"] for s in _CORE_SCENARIOS])
def test_core_scenario_end_to_end(sc):
    """8개 핵심 시나리오(정상 허용 / 인젝션 차단 / RBAC 차단 / PII 마스킹 / 승인 대기 등)."""
    result = agent_service.handle_request(sc["user"], sc["user_input"], sc["action"])
    assert result["decision"] == sc["expected"], (
        f'[{sc["id"]}] {sc["title"]}: decision={result["decision"]} (기대={sc["expected"]}) '
        f'reasons={result["reasons"]}'
    )


def test_five_core_scenarios_success_rate():
    """기획서 명시 '5대 핵심 시나리오'(S1 baseline, S3 RBAC, S5 mail send_all NEED_APPROVAL,
    S6/S7 데이터 유출 차단, S2 PII 마스킹)에 해당하는 시나리오들의 성공률이 100%인지 집계합니다."""
    total = len(_CORE_SCENARIOS)
    passed = 0
    for sc in _CORE_SCENARIOS:
        result = agent_service.handle_request(sc["user"], sc["user_input"], sc["action"])
        if result["decision"] == sc["expected"]:
            passed += 1
    rate = passed / total * 100 if total else 0
    assert rate == 100.0, f"핵심 시나리오 성공률 {rate:.1f}% (목표 100%) — {passed}/{total} 통과"
