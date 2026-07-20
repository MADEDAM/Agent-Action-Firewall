"""
agent_service.py   (담당: 조정우)    ★ 전체 흐름의 '지휘자'

[이 파일이 하는 일]
요청 1건을 받아 아래 순서로 처리합니다.
  0) 방화벽이 꺼져 있으면(kill-switch OFF) 보호 없이 그냥 실행 (발표 비교 시연용)
  1) 사용자가 '이상행동 격리' 상태면 즉시 차단
  2) (자연어 요청일 때) 프롬프트 인젝션 검사 + 올라마로 행동 계획 만들기(멀티스텝)
  3) 각 행동을 보안 엔진(policy_engine)으로 '실행 전 검사'
  4) ALLOW/MASK면 가짜 도구 실행 → output_guard로 '출구 검사'
  5) 위험(HIGH/CRITICAL)하면 이상행동 카운트 → 누적되면 자동 격리
  6) 모든 결과를 로그로 저장

[두 가지 입구]
  - handle_request(user, user_input, action) : 행동(action)이 정해진 1건 처리 (테스트·API용)
  - handle_message(user, user_input)         : 자연어 → 올라마 계획 → 멀티스텝 처리 (★ 메인)
"""
import uuid
from datetime import datetime

from ..security import policy_engine, output_guard, injection_guard, anomaly_guard
from ..control import control_service
from ..logs import log_service
from ..approval import approval_service
from ..alerts import alert_service
from . import llm_client
from . import tool_runner

# ★ 병합 (2026-07) — 도구 실행 로직(EXECUTORS/_extract_kwargs/_run_tool)은
# tool_runner.py로 옮겼습니다. approval_service.py도 "승인되면 실제로 실행"하려면
# 같은 실행 로직이 필요한데, approval_service가 agent_service를 직접 import하면
# 순환 참조가 생기기 때문입니다. 동작은 이전과 100% 동일합니다.
_run_tool = tool_runner.run_tool


def _process_action(user: str, user_input: str, action: dict, firewall_on: bool) -> dict:
    """행동 1개를 검사·실행·기록하고 결과를 돌려줍니다. (handle_request/handle_message가 공통으로 사용)"""
    request_id = "req-" + uuid.uuid4().hex[:8]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 0) 방화벽 OFF → 보호 없이 통과 (발표 비교용). 그래도 로그는 남김.
    if not firewall_on:
        raw = _run_tool(action)
        entry = _make_entry(request_id, now, user, user_input, action,
                            action_type="UNCHECKED", risk_level="OFF", risk_score=0,
                            decision="ALLOW", reasons=["방화벽 OFF — 보호 비활성 상태로 그냥 실행됨"],
                            status="DONE")
        log_service.save_log(entry)
        return _result(request_id, "ALLOW", "OFF", 0, "UNCHECKED",
                        ["방화벽 OFF — 보호 비활성"], raw)

    # 1) 실행 전 보안 검사
    # ★ 병합 (2026-07) — user를 같이 넘겨서 RBAC(역할 기반 권한)을 확인합니다.
    # data/rbac_roles.json에 등록 안 된 사용자는 전부 'general'로 취급되므로,
    # 지금까지 검증한 시나리오들의 결과는 그대로 유지됩니다(등록된 admin 계정만 달라짐).
    verdict = policy_engine.evaluate(action, user=user)
    decision = verdict["decision"]
    final_output = ""

    if decision == "BLOCK":
        final_output = "[차단] 위험한 행동이라 실행하지 않았습니다."
    elif decision == "NEED_APPROVAL":
        final_output = "[보류] 관리자 승인이 필요한 행동입니다. 승인 대기열에 등록했습니다."
        # ★ 병합 (2026-07) — action/user_input을 함께 저장합니다. 이전에는 summary(문자열)만
        # 저장해서, 나중에 관리자가 '승인'을 눌러도 실제로 무엇을 실행해야 할지 알 방법이
        # 없었습니다(그래서 승인은 상태만 바뀔 뿐 아무 일도 실제로 안 일어났습니다).
        # 이제 action 전체를 저장해두고, approval_service.approve()가 승인 시점에 이걸
        # 그대로 실행해서 "승인 → 진짜로 이메일 발송/고객 삭제"가 이어지게 만듭니다.
        approval_service.create_request(request_id, user, verdict["action_type"],
                                        summary=f"{action.get('tool')}.{action.get('operation')}",
                                        action=action, user_input=user_input)
    else:  # ALLOW / MASK → 실행 후 출구 검사
        raw = _run_tool(action)
        guard = output_guard.guard_output(raw)
        if guard["decision"] == "BLOCK":
            decision = "BLOCK"
        elif guard["decision"] == "MASK" or decision == "MASK":
            decision = "MASK"
        else:
            decision = "ALLOW"
        final_output = guard["output"]
        verdict["reasons"] += guard["reasons"]

    entry = _make_entry(request_id, now, user, user_input, action,
                        verdict["action_type"], verdict["risk_level"], verdict["risk_score"],
                        decision, verdict["reasons"],
                        status="DONE" if decision in ("ALLOW", "MASK") else decision)
    log_service.save_log(entry)

    # ★ 패치 (2026-07) #1 — Slack 알림을 여기서 한 곳에서만 발송합니다.
    # 전에는 main.py의 /agent/request 핸들러에서만 CRITICAL 체크를 해서,
    # /agent/message(자연어·멀티스텝, ★ 메인 입구)를 거친 CRITICAL 행동은 알림이 안 갔습니다.
    # _process_action은 두 입구 모두가 공통으로 거치므로, 여기 한 곳에만 두면 어느 경로로 와도 알림이 나갑니다.
    #
    # ★ 병합 (2026-07) #2 — 알림 발송 조건을 "risk_level == CRITICAL"에서
    # "decision이 BLOCK/NEED_APPROVAL 이면서 risk_level이 HIGH 이상"으로 넓혔습니다.
    # 기획서 KPI 표의 측정 방법이 "NEED_APPROVAL/BLOCK Webhook 발생 시 전송 속도"라서,
    # 원래는 위험한 차단·승인대기 건이면 알림이 가야 하는데, risk_score 계산상 HIGH
    # 등급(50~79점)으로 끝나는 BLOCK/NEED_APPROVAL 건이 실제로 많았습니다
    # (예: API 키 직접 조회 차단 R2, 권한상승 차단 R2b 등 — 100개 KPI 시나리오로 확인).
    # 특히 기획서의 5대 핵심 시나리오 중 3번(권한초과 도구 실행)과 5번(Excessive
    # Agency)이 둘 다 risk_level=HIGH라서, 옛날 조건이면 라이브 시연에서 "Slack
    # 알림이 안 뜨는" 문제가 있었습니다. 반대로 MEDIUM 등급(예: 평범한 전체공지
    # 메일 승인)까지는 굳이 안 울리게 HIGH 이상만 남겨서 알림 남발도 막았습니다.
    if entry["decision"] in ("BLOCK", "NEED_APPROVAL") and entry["risk_level"] in ("HIGH", "CRITICAL"):
        alert_service.alert_critical(entry)

    return _result(request_id, decision, verdict["risk_level"], verdict["risk_score"],
                   verdict["action_type"], verdict["reasons"], final_output)


def handle_request(user: str, user_input: str, action: dict) -> dict:
    """행동이 이미 정해진 1건을 처리. (테스트·/agent/request 용)"""
    firewall_on = control_service.is_firewall_on()
    if firewall_on and anomaly_guard.is_quarantined(user):
        return _quarantined_result(user, user_input)
    return _process_action(user, user_input, action, firewall_on)


def handle_message(user: str, user_input: str) -> dict:
    """자연어 요청 → 올라마 계획(멀티스텝) → 각 단계 검사·실행. (★ 메인 입구)"""
    firewall_on = control_service.is_firewall_on()

    # 1) 격리된 사용자면 즉시 차단
    if firewall_on and anomaly_guard.is_quarantined(user):
        return {"user": user, "user_input": user_input,
                "steps": [_quarantined_result(user, user_input)],
                "injection": False, "blocked_all": True}

    # 2) 프롬프트 인젝션 검사
    inj = injection_guard.scan(user_input)

    # 3) 올라마로 행동 계획(여러 단계) 만들기
    actions = llm_client.plan_actions(user_input)

    # ★ 병합 (2026-07) — 팀원 브랜치의 UX: 실행할 도구 작업이 하나도 없으면(전부 허깨비로
    # 걸러졌거나 애초에 매핑되는 도구가 없으면) 억지로 count_customers 같은 안전한 기본 조회를
    # 지어내지 않고, "처리할 작업이 없다"고 솔직하게 응답합니다. (llm_client._sanitize()도
    # 이제 전부 걸러지면 빈 배열을 그대로 돌려주도록 맞춰져 있습니다.)
    if not actions:
        return {"user": user, "user_input": user_input,
                "injection": inj["injection"], "injection_hits": inj["hits"],
                "steps": [{"request_id": "-", "decision": "ALLOW", "risk_level": "LOW",
                           "risk_score": 0, "action_type": "NONE",
                           "reasons": ["실행할 수 있는 도구 작업이 없습니다."],
                           "output": "처리할 수 있는 작업이 없습니다."}]}

    # 4) 각 단계 처리
    steps = []
    for action in actions:
        if firewall_on:
            action["injection"] = inj["injection"]   # 인젝션 결과를 검사에 반영
        res = _process_action(user, user_input, action, firewall_on)
        # 5) 위험하면 이상행동 카운트 → 누적되면 격리
        # ★ 2026-07 — risk_level을 같이 넘겨서, CRITICAL은 1회만 발생해도 즉시 격리되게 함
        # (HIGH는 기존처럼 60초 안에 3번 누적돼야 격리)
        if firewall_on and res["risk_level"] in ("HIGH", "CRITICAL"):
            q = anomaly_guard.register_risky(user, risk_level=res["risk_level"])
            res["quarantined"] = q["quarantined"]
        steps.append(res)

    return {"user": user, "user_input": user_input,
            "injection": inj["injection"], "injection_hits": inj["hits"],
            "steps": steps}


# ---------------- 작은 도우미들 ----------------
def _make_entry(request_id, now, user, user_input, action, action_type, risk_level,
                risk_score, decision, reasons, status):
    return {
        "request_id": request_id, "created_at": now, "user": user, "user_input": user_input,
        "tool": f"{action.get('tool')}.{action.get('operation')}",
        "action_type": action_type, "risk_level": risk_level, "risk_score": risk_score,
        "decision": decision, "reasons": reasons, "status": status,
    }


def _result(request_id, decision, risk_level, risk_score, action_type, reasons, output):
    return {"request_id": request_id, "decision": decision, "risk_level": risk_level,
            "risk_score": risk_score, "action_type": action_type,
            "reasons": reasons, "output": output}


def _quarantined_result(user, user_input=""):
    """
    격리된 사용자의 요청을 즉시 차단합니다.
    ★ 2026-07 — 예전에는 이 경로가 로그 저장(log_service.save_log)을 거치지 않아서,
    실제로 몇 번이나 격리-차단이 일어났는지 대시보드 Detection Log에 전혀 남지 않았습니다
    (사용자가 화면에서 직접 이 문제를 발견해 알려주셨습니다). request_id를 매번 새로 만들고
    로그로 남겨서, 격리 중 차단된 요청도 다른 요청과 똑같이 이력에 보이게 했습니다.
    """
    request_id = "req-" + uuid.uuid4().hex[:8]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    reasons = [f"사용자 '{user}' 는 이상행동으로 격리 중 → 모든 요청 차단"]
    entry = {
        "request_id": request_id, "created_at": now, "user": user, "user_input": user_input,
        "tool": "quarantine.blocked", "action_type": "QUARANTINED", "risk_level": "CRITICAL",
        "risk_score": 100, "decision": "BLOCK", "reasons": reasons, "status": "BLOCK",
    }
    log_service.save_log(entry)
    return _result(request_id, "BLOCK", "CRITICAL", 100, "QUARANTINED", reasons,
                   "[차단] 이상행동 격리 상태입니다. 관리자에게 문의하세요.")
