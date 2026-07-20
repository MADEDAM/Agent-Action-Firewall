"""
log_service.py   (담당: 김나형)

[이 파일이 하는 일]
저장창고(SQLite 또는 DynamoDB)를 좀 더 쓰기 쉽게 감싼 '중간 관리자'.
다른 사람들은 이 파일 함수만 부르면 되고, 저장 방식은 몰라도 됩니다.

[백엔드 고르기]
환경변수 LOG_BACKEND 가 "dynamo" 면 DynamoDB, 아니면(기본) SQLite를 씁니다.
  - 발표/개발: (설정 안 함) → SQLite            ← 권장
  - 클라우드:   LOG_BACKEND=dynamo → DynamoDB
"""
import os

# 로그(logs)는 백엔드를 바꿀 수 있음. 승인/설정값은 항상 SQLite를 씀.
if os.getenv("LOG_BACKEND", "sqlite").lower() == "dynamo":
    from ..logs import dynamo_repository as _repo
else:
    from ..logs import log_repository as _repo


def save_log(entry: dict):
    """요청 1건의 처리 결과를 저장. (조정우의 agent_service가 호출)"""
    _repo.insert_log(entry)


def get_logs(decision=None, risk_level=None, action_type=None, limit=200):
    """대시보드 표/필터용 로그 목록."""
    return _repo.fetch_logs(decision, risk_level, action_type, limit)


def reset_logs():
    """대시보드 통계(Total/Blocked/Need Approval/Masked)를 0으로 초기화합니다.
    logs 테이블만 비우고, 승인/설정/격리 이력은 그대로 둡니다."""
    _repo.reset_logs()


def get_stats():
    """대시보드 상단 숫자 카드용 통계."""
    logs = _repo.fetch_logs(limit=10000)
    total = len(logs)
    blocked = sum(1 for x in logs if x["decision"] == "BLOCK")
    pending = sum(1 for x in logs if x["decision"] == "NEED_APPROVAL")
    masked = sum(1 for x in logs if x["decision"] == "MASK")
    by_risk = {}
    for x in logs:
        by_risk[x["risk_level"]] = by_risk.get(x["risk_level"], 0) + 1
    return {"total": total, "blocked": blocked, "pending": pending,
            "masked": masked, "by_risk": by_risk}
