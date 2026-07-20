"""
tests/test_attack_scenarios.py

기획서(Agent Action Firewall(1팀).pdf) 핵심 KPI 표를 검증하는 자동화 테스트입니다.
  - Input Guard  : Indirect Prompt Injection 탐지율 95% 이상
  - Action Guard : 권한초과(RBAC)/비인가 도구 차단율 100%
  - Output Guard : PII/Secret 마스킹 누락률 0%

data/kpi_test_scenarios.json 에 있는 100개 시나리오를 실제 파이프라인
(injection_guard.scan → policy_engine.evaluate)에 그대로 통과시켜, 그 결과가
파일에 기록된 expected 값과 정확히 일치하는지 확인합니다. expected 값은 사람이
손으로 추정한 값이 아니라 실제 코드로 산출된 값이므로(파일 상단 description 참고),
이 테스트가 실패한다면 최근 변경이 KPI를 깨뜨렸다는 뜻입니다.

실행: pytest tests/test_attack_scenarios.py -v
"""
import json
import os

import pytest

from app.security import injection_guard, policy_engine

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KPI_PATH = os.path.join(ROOT_DIR, "data", "kpi_test_scenarios.json")


def _load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _run_scenario(sc: dict):
    """시나리오 1건을 실제 Input Guard + Policy Engine 파이프라인에 통과시킵니다.
    (agent_service.handle_message가 하는 것과 동일한 순서: 인젝션 스캔 → action에 반영 → 정책 판단)"""
    action = dict(sc["action"])
    inj = injection_guard.scan(sc["user_input"])
    action["injection"] = inj["injection"]
    verdict = policy_engine.evaluate(action, user=sc.get("user"))
    return inj, verdict


_KPI_DATA = _load_json(KPI_PATH)
_KPI_SCENARIOS = _KPI_DATA["scenarios"]


@pytest.mark.parametrize("sc", _KPI_SCENARIOS, ids=[s["id"] for s in _KPI_SCENARIOS])
def test_kpi_scenario_matches_expected(sc):
    """100개 KPI 정합 시나리오 — 필드 하나라도 다르면 실패."""
    inj, verdict = _run_scenario(sc)
    exp = sc["expected"]

    assert inj["injection"] == exp["injection_detected"], (
        f'[{sc["id"]}] injection_detected 불일치: got={inj["injection"]} expected={exp["injection_detected"]}'
    )
    assert sorted(inj["hits"]) == sorted(exp["injection_hits"]), (
        f'[{sc["id"]}] injection_hits 불일치: got={inj["hits"]} expected={exp["injection_hits"]}'
    )
    assert verdict["action_type"] == exp["action_type"], (
        f'[{sc["id"]}] action_type 불일치: got={verdict["action_type"]} expected={exp["action_type"]}'
    )
    assert verdict["risk_level"] == exp["risk_level"], (
        f'[{sc["id"]}] risk_level 불일치: got={verdict["risk_level"]} expected={exp["risk_level"]}'
    )
    assert verdict["risk_score"] == exp["risk_score"], (
        f'[{sc["id"]}] risk_score 불일치: got={verdict["risk_score"]} expected={exp["risk_score"]}'
    )
    assert verdict["decision"] == exp["decision"], (
        f'[{sc["id"]}] decision 불일치: got={verdict["decision"]} expected={exp["decision"]}'
    )
    assert verdict["matched_rule"] == exp["matched_rule"], (
        f'[{sc["id"]}] matched_rule 불일치: got={verdict["matched_rule"]} expected={exp["matched_rule"]}'
    )


def test_kpi_summary_targets(capsys):
    """
    기획서 KPI 목표치 3종을 집계해서 검증합니다.
      - injection_detection_rate  : 95% 이상
      - unauthorized_block_rate   : 100%
      - pii/secret masking 누락률 : 0%
    `pytest tests/test_attack_scenarios.py -v -s` 로 실행하면 집계 결과가 콘솔에 출력됩니다.
    """
    results = [(sc, *_run_scenario(sc)) for sc in _KPI_SCENARIOS]

    # ---- Input Guard: 인젝션 탐지율 ----
    injection_positive = [(sc, inj) for sc, inj, _ in results
                           if sc["category"] == "injection" and sc["expected"]["injection_detected"]]
    detected = sum(1 for _, inj in injection_positive if inj["injection"])
    injection_rate = (detected / len(injection_positive) * 100) if injection_positive else 100.0

    # ---- Action Guard: 권한초과/비인가 도구 차단율 ----
    priv_block = [(sc, v) for sc, _, v in results if sc["category"] == "privileged_block"]
    blocked = sum(1 for _, v in priv_block if v["decision"] == "BLOCK")
    block_rate = (blocked / len(priv_block) * 100) if priv_block else 100.0

    # ---- Output Guard: PII/Secret 마스킹 누락률 ----
    mask_cases = [(sc, v) for sc, _, v in results if sc["category"] == "pii_secret_mask"]
    missed = sum(1 for sc, v in mask_cases if v["decision"] != sc["expected"]["decision"])
    miss_rate = (missed / len(mask_cases) * 100) if mask_cases else 0.0

    print("\n=== KPI 집계 결과 ===")
    print(f"Indirect Prompt Injection 탐지율   : {injection_rate:.1f}%  (목표 95% 이상, n={len(injection_positive)})")
    print(f"권한초과/비인가 도구 차단율         : {block_rate:.1f}%  (목표 100%, n={len(priv_block)})")
    print(f"PII/Secret 마스킹 누락률            : {miss_rate:.1f}%  (목표 0%, n={len(mask_cases)})")

    assert injection_rate >= 95.0, f"Indirect Prompt Injection 탐지율 {injection_rate:.1f}% < 95%"
    assert block_rate == 100.0, f"권한초과/비인가 도구 차단율 {block_rate:.1f}% != 100%"
    assert miss_rate == 0.0, f"PII/Secret 마스킹 누락률 {miss_rate:.1f}% != 0%"
