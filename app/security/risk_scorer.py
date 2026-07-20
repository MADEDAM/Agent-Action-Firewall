"""
risk_scorer.py   (담당: 백이담)

[이 파일이 하는 일]
행동이 얼마나 위험한지 '점수'로 매기고, 점수를 등급(Low/Medium/High/Critical)으로 바꿉니다.
비유: 놀이기구 안전요원이 키·나이를 보고 '위험 점수'를 매겨 탑승 여부를 정하는 것.

[점수 계산 방법]
  기본 점수(행동 종류) + 가산점(대상/목적지/범위/비밀값/개인정보)

[어디서 쓰이나]
- policy_engine 이 정책 규칙에서 결론이 안 나면, 이 점수 등급으로 최종 결정을 내립니다.
- 대시보드(김나형)는 이 점수와 등급으로 통계 차트를 그립니다.
"""

# 행동 종류별 기본 점수
BASE_SCORE = {
    "READ": 0, "WRITE": 20, "SEND": 25, "EXPORT": 40,
    "DELETE": 50, "SECRET_ACCESS": 60, "PII_ACCESS": 30,
    "PRIV_ESC": 55,   # ★ 병합(2026-07): 관리자 권한 상승(Privilege Escalation)
}


def score_risk(info: dict, has_secret: bool, has_pii: bool, injection: bool = False) -> dict:
    """
    info: action_classifier.classify() 가 돌려준 분류 결과
    has_secret / has_pii: secret_guard / pii_masker 의 검사 결과(True/False)
    injection: 프롬프트 인젝션이 탐지됐는지(True/False)

    돌려주는 값: {"score": 정수, "level": 등급, "reasons": [이유들]}
    """
    score = 0
    reasons = []

    base = BASE_SCORE.get(info["action_type"], 0)
    score += base
    if base:
        reasons.append(f"행동종류 {info['action_type']} (+{base})")

    # 대상이 운영DB/백업이면 위험 가산
    if info.get("target") in ("prod_db", "backup"):
        score += 30
        reasons.append(f"민감 대상 {info['target']} (+30)")

    # 외부로 나가면 위험 가산
    if info.get("destination") == "external":
        score += 30
        reasons.append("외부 전송 (+30)")

    # 전체 발송(브로드캐스트)이면 가산
    if info.get("scope") == "broadcast":
        score += 20
        reasons.append("전체 발송 (+20)")

    # 비밀값/개인정보 포함 가산
    if has_secret:
        score += 40
        reasons.append("비밀값 포함 (+40)")
    if has_pii:
        score += 20
        reasons.append("개인정보 포함 (+20)")

    # 프롬프트 인젝션이 의심되면 크게 가산
    if injection:
        score += 40
        reasons.append("프롬프트 인젝션 의심 (+40)")

    level = level_from_score(score)
    return {"score": score, "level": level, "reasons": reasons}


def level_from_score(score: int) -> str:
    """점수를 등급으로 변환."""
    if score >= 80:
        return "CRITICAL"
    if score >= 50:
        return "HIGH"
    if score >= 20:
        return "MEDIUM"
    return "LOW"
