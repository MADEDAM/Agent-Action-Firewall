"""
policy_engine.py   (담당: 백이담)  ★ 보안 엔진의 '두뇌'

[이 파일이 하는 일]
다른 보안 모듈(분류·비밀값·개인정보·위험점수)을 모두 불러서, 최종적으로
ALLOW / MASK / BLOCK / NEED_APPROVAL 중 하나로 결론을 내립니다.

[판단 순서]
 1) action_classifier 로 행동 종류를 정한다
 2) secret_guard / pii_masker 로 비밀값·개인정보가 있는지 검사한다
 3) rbac 로 요청한 사용자의 등급(role)을 조회한다 — ★ 병합(2026-07)
 4) risk_scorer 로 위험 점수·등급을 매긴다
 5) policies.json 규칙을 위에서부터 검사해 처음 맞는 규칙의 결정을 따른다
 6) 맞는 규칙이 없으면 위험 등급으로 기본 결정을 내린다
 7) ★ 신규(2026-07) 결과가 R7(개인정보→마스킹)이면, Ollama에게 "진짜 개인정보 유출
    위험인지 예시/더미 데이터인지" 한 번 더 물어서 과탐(false positive)을 줄인다

[어디서 쓰이나]
- 조정우의 agent_service 가 도구를 실행하기 '전에' evaluate(action, user) 을 호출합니다.
- 결과(decision)를 보고 도구를 실행할지, 막을지, 승인 대기로 보낼지 정합니다.
"""
import json
import os

from .action_classifier import classify
from .secret_guard import has_secret as _has_secret
from .pii_masker import has_pii as _has_pii
from .risk_scorer import score_risk
from .injection_guard import is_injection
from . import rbac  # ★ 병합 (2026-07) — RBAC(역할 기반 권한). 자세한 설명은 rbac.py 참고.
from ..agent import llm_client  # ★ 신규 (2026-07) — 맥락 인지형 PII 오탐 방지 (check_pii_context)

# policies.json 파일을 한 번만 읽어둡니다.
_HERE = os.path.dirname(__file__)
_POLICY_PATH = os.path.join(_HERE, "..", "..", "data", "policies.json")
with open(_POLICY_PATH, encoding="utf-8") as f:
    POLICY = json.load(f)


def _match(rule_when: dict, ctx: dict) -> bool:
    """규칙의 조건(when)이 현재 상황(ctx)과 모두 맞으면 True."""
    for key, expected in rule_when.items():
        if key == "target_in":
            if ctx.get("target") not in expected:
                return False
        elif key == "action_type_in":
            if ctx.get("action_type") not in expected:
                return False
        elif ctx.get(key) != expected:
            return False
    return True


def evaluate(action: dict, user: str = None) -> dict:
    """
    action: 조정우의 agent_service 가 만든 '행동 계획' dict
    user  : ★ 병합 (2026-07) — 이 행동을 요청한 사용자 이름(RBAC 등급 조회용).
            안 넘기면(기본값 None) 예전과 똑같이 'general(일반 권한)'로 취급되어
            동작이 바뀌지 않습니다 — 기존 호출부(테스트 등)와 호환됩니다.
    돌려주는 값(보안 판단 결과):
      {
        "decision": "ALLOW" | "MASK" | "BLOCK" | "NEED_APPROVAL",
        "action_type": "DELETE", "risk_level": "CRITICAL", "risk_score": 95,
        "reasons": [...], "matched_rule": "R1" 또는 None, "role": "general" | "admin"
      }
    """
    # 1) 행동 종류 분류
    info = classify(action)

    # 2) 비밀값·개인정보·인젝션 검사 (요청 본문을 스캔)
    text = action.get("payload_text", "") or ""
    secret = _has_secret(text)
    pii = _has_pii(text)
    # 인젝션 여부: agent_service가 미리 넣어줬으면 그 값을, 없으면 본문을 직접 검사
    injection = action.get("injection")
    if injection is None:
        injection = is_injection(text)

    # 3) RBAC 등급 조회 (★ 병합 2026-07 — data/rbac_roles.json 참고)
    role = rbac.get_role(user)

    # 4) 위험 점수
    risk = score_risk(info, secret, pii, injection)

    # 검사에 쓸 상황(ctx) 모으기
    # ★ 주의 — ctx["has_pii"]는 항상 '정규식 원본 탐지 결과'를 그대로 씁니다. R1/R2/R4처럼
    # 더 위험한 규칙(운영DB삭제/시크릿/외부전송+개인정보)은 아래 7번 단계의 맥락 완화를
    # 절대 적용받지 않도록, 규칙 매칭 자체는 항상 보수적인 원본 값으로만 판단합니다.
    ctx = {
        "action_type": info["action_type"],
        "target": info["target"],
        "destination": info["destination"],
        "scope": info["scope"],
        "has_secret": secret,
        "has_pii": pii,
        "injection": injection,
        "role": role,  # ★ 병합 (2026-07) — RBAC 규칙(R_ADMIN*)이 이 값을 보고 판단
    }

    # 5) 규칙을 위에서부터 검사 → 처음 맞는 규칙의 결정 사용
    decision, reason, matched = None, None, None
    for rule in POLICY["rules"]:
        if _match(rule["when"], ctx):
            decision = rule["decision"]
            reason = rule["reason"]
            matched = rule["id"]
            break

    # 6) 맞는 규칙이 없으면 위험 등급으로 기본 결정
    if decision is None:
        decision = POLICY["fallback_by_risk"].get(risk["level"], "ALLOW")
        reason = f"규칙 미해당 → 위험등급 {risk['level']} 기본정책"
        matched = None

    # 7) ★ 신규(2026-07) — 맥락 인지형 개인정보 오탐(false positive) 방지.
    # "정규식 패턴이 우연히 개인정보처럼 생겼다"는 이유만으로 R7(마스킹)이 결론난 경우에
    # 한해서만, Ollama에게 "이게 진짜 유출 위험인지 예시/포맷/더미 데이터인지"를 한 번 더
    # 물어봅니다. R1(운영DB삭제)/R2(시크릿)/R2b(권한상승)/R4(외부전송+개인정보)처럼 이미
    # 더 심각한 규칙으로 결론난 경우는 여기 도달하지 않으므로 영향받지 않습니다 — "이건
    # 그냥 예시예요"라는 말만으로 실제 위험한 행동까지 우회시키면 안 되기 때문입니다.
    # Ollama가 꺼져있거나 판단이 애매하면 check_pii_context()가 안전하게 True(=마스킹 유지)를
    # 반환하므로(fail-closed), 이 단계는 오탐만 줄일 뿐 새로운 구멍을 만들지 않습니다.
    pii_context_relaxed = False
    if matched == "R7" and pii:
        if not llm_client.check_pii_context(text):
            decision = "ALLOW"
            reason = "개인정보 패턴이 감지됐지만 맥락상 예시/더미 데이터로 판단되어(Ollama 맥락검사) 마스킹 없이 통과"
            pii_context_relaxed = True

    reasons = list(risk["reasons"])
    if secret:
        reasons.append("비밀값 탐지됨")
    if pii:
        if pii_context_relaxed:
            reasons.append("개인정보 패턴 탐지됨 → Ollama 맥락검사 결과 예시/더미로 판단되어 통과")
        else:
            reasons.append("개인정보 탐지됨")
    if injection:
        reasons.append("프롬프트 인젝션 탐지됨")
    reasons.append(reason)

    return {
        "decision": decision,
        "action_type": info["action_type"],
        "risk_level": risk["level"],
        "risk_score": risk["score"],
        "reasons": reasons,
        "matched_rule": matched,
        "injection": injection,
        "role": role,  # ★ 병합 (2026-07) — 대시보드/로그에서 "누구 등급으로 판단했는지" 확인용
    }
