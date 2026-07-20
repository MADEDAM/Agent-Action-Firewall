"""
anomaly_guard.py   (담당: 백이담)  ★ 고급 기능 2 — 이상행동 자동격리

[무슨 기능인가요? — 쉽게]
한 사용자가 '짧은 시간에 위험한 행동을 여러 번' 시도하면,
그 사용자를 잠시 '격리(차단)'해서 더 이상 아무 행동도 못 하게 막습니다.
비유: 은행에서 비밀번호를 연속으로 틀리면 계정이 '잠기는' 것과 같아요.

[규칙]
- CRITICAL 등급 행동은 "단 1번"만 발생해도 즉시 격리 (★ 2026-07 추가)
  (예: 프롬프트 인젝션으로 120점 등 CRITICAL이 찍히면, 다음 요청을 기다릴 것도 없이 그 자리에서 잠금)
- HIGH 등급은 기존대로 최근 WINDOW(60초) 안에 LIMIT(3)번 이상 → 격리
- 격리되면 QUARANTINE(300초) 동안 그 사용자의 모든 요청은 자동 BLOCK

[★ 2026-07 변경 이유 #1 — CRITICAL 즉시격리]
실제 시연에서 CRITICAL(인젝션) 요청 뒤에 HIGH 요청들이 30~40초 간격으로 이어지자,
60초 슬라이딩 창 특성상 3번째 요청 시점엔 1번째가 이미 창 밖으로 밀려나 있어
"위험 행동이 5번 있었는데도 격리가 안 되는" 것처럼 보였습니다. CRITICAL은 그 자체로
즉시 격리해야 할 만큼 위험하다고 보고, 1회 발생 즉시 격리하도록 규칙을 하나 더 추가했습니다.

[★ 2026-07 변경 이유 #2 — 메모리 딕셔너리 → SQLite로 이전 (더 중요한 수정)]
원래는 이 파일 안의 파이썬 딕셔너리(_events/_quarantine)에만 상태를 저장했습니다.
그런데 FastAPI 백엔드 / 관제 대시보드(streamlit_app.py) / 채팅 UI(chat_app.py)는
전부 "따로 실행되는 프로세스"라서 메모리를 서로 공유하지 않습니다. 그래서 채팅 UI
에서는 "반복된 위험 행동으로 자동 격리되었습니다"라고 응답 문구는 나오는데, 정작
관제 대시보드의 QUARANTINE 패널에는 아무도 안 뜨고 격리 해제 버튼도 무의미했던
것입니다(대시보드 프로세스의 _quarantine 딕셔너리는 항상 비어있었으므로). control_service.py가
kill-switch 상태를 SQLite(flags 테이블)에 저장해 이 문제를 안 겪는 것과 같은 이유로,
이 파일도 log_repository.py의 anomaly_events/anomaly_quarantine 테이블에 저장하도록
바꿨습니다. 이제 어느 프로세스에서 보든 같은 격리 상태를 봅니다. 함수 시그니처(공개
인터페이스)는 그대로라서, 이 파일을 쓰는 agent_service.py/대시보드 쪽 코드는 수정할
필요가 없습니다.

[어디서 쓰이나]
- agent_service 가 위험한 판정이 날 때마다 register_risky(user, risk_level) 를 부른다
- 다음 요청 때 is_quarantined(user) 가 True면 즉시 차단
- 김나형 대시보드가 status() 로 '현재 격리된 사용자'를 보여줌, release() 로 수동 해제
"""
import time

from ..logs import log_repository as repo

WINDOW = 60         # 관찰 시간(초)
LIMIT = 3           # 이 횟수 이상이면 격리
QUARANTINE = 300    # 격리 지속 시간(초)


def _now():
    return time.time()


def is_quarantined(user: str, now=None) -> bool:
    """이 사용자가 지금 격리 상태인가?"""
    now = now if now is not None else _now()
    until = repo.get_quarantine(user)
    if until is None:
        return False
    if now >= until:            # 시간이 지나면 자동 해제
        repo.clear_quarantine_flag(user)
        return False
    return True


def register_risky(user: str, risk_level: str = None, now=None) -> dict:
    """
    위험한 행동 1건을 기록하고, 격리해야 하는지 판단합니다.
    risk_level: "HIGH" 또는 "CRITICAL" (agent_service가 판정 등급을 그대로 넘겨줌)
    돌려주는 값: {"count": 최근 위험행동 수, "quarantined": True/False}

    ★ 2026-07 변경: CRITICAL은 누적 없이 1회 즉시 격리. HIGH는 기존 3-in-60s 유지.
    """
    now = now if now is not None else _now()
    repo.prune_anomaly_events(user, now - WINDOW)   # 오래된 건 버림
    repo.add_anomaly_event(user, now)
    count = repo.count_anomaly_events(user, now - WINDOW)

    if risk_level == "CRITICAL":
        repo.set_quarantine(user, now + QUARANTINE)     # 즉시 격리 (누적 카운트 필요 없음)
        return {"count": count, "quarantined": True}

    if count >= LIMIT:
        repo.set_quarantine(user, now + QUARANTINE)     # 격리 시작
        return {"count": count, "quarantined": True}
    return {"count": count, "quarantined": is_quarantined(user, now)}


def release(user: str):
    """관리자가 수동으로 격리 해제."""
    repo.release_anomaly_user(user)


def status(now=None) -> list:
    """현재 격리된 사용자 목록 (대시보드용)."""
    now = now if now is not None else _now()
    rows = repo.list_quarantined(now)
    return [{"user": u, "남은초": int(until - now)} for u, until in rows]


def reset():
    """테스트/데모용 초기화."""
    repo.reset_anomaly_state()
