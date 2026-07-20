"""
circuit_breaker.py   (담당: 조정우)   ★ 신규(2026-07) — 서킷 브레이커 / Fail-safe

[무슨 기능인가요? — 쉽게]
Ollama가 다운되거나 느려질 때마다 매번 OLLAMA_TIMEOUT(기본 120초)을 꽉 채워서
기다렸다가 실패하는 건, 실제 서비스에서는 요청 지연이 계속 쌓이는 방식으로 문제가
됩니다. "연속 3번 실패하면, 잠시(30초) 동안은 아예 Ollama에게 묻지 않고 곧바로
폴백(fallback)으로 넘어간다"는 넷플릭스식 서킷 브레이커 패턴을 넣었습니다.

[왜 필요한가 — "기존 시스템에 붙였을 때 안전한가" 질문에 대한 답]
이 방화벽을 실제 회사 시스템 앞단에 붙였는데 Ollama(방화벽의 AI 부분)가 느려지거나
죽으면, 그 뒤에 있는 진짜 업무 시스템까지 요청이 쌓여서 같이 마비될 위험이 있습니다.
이 모듈은 그걸 막는 스위치입니다. Ollama가 죽어있는 동안에는 서킷이 열려서(open)
매 요청마다 120초씩 기다리지 않고 즉시 우회(폴백)합니다.

★ 중요 — 이 서킷 브레이커가 "우회"시키는 건 Ollama 호출(행동 계획 수립/결과 문장
다듬기)뿐입니다. secret_guard/pii_masker/policy_engine/risk_scorer 같은 진짜 보안
판단 로직은 전부 순수 파이썬·정규식이라 Ollama 상태와 아무 상관 없이 항상 그대로
작동합니다. 즉 "Ollama가 다운돼도 방화벽의 차단·마스킹 기능 자체는 절대 안 죽는다"가
핵심이고, 이 모듈은 그 위에서 "속도"만 보호합니다.

[상태 관리]
이 프로세스(FastAPI 서버 또는 Streamlit 프로세스) 안에서만 유지되는 값입니다.
anomaly_guard(격리 상태)처럼 여러 프로세스가 반드시 같은 값을 봐야 하는 보안 상태가
아니라, "지금 이 프로세스 입장에서 Ollama가 반응이 없다"는 성능/가용성 최적화 신호라서
SQLite 같은 공유 저장소에 옮길 필요가 없습니다(프로세스마다 따로 판단해도 안전합니다).
"""
import time

MAX_FAILURES = 3     # 연속 실패 허용 횟수 (이 이상이면 서킷을 엽니다)
COOLDOWN = 30         # 서킷이 열린 뒤 우회(Fail-safe) 모드로 지내는 시간(초)

_fail_count = 0
_open_until = 0.0


def is_open(now=None) -> bool:
    """지금 서킷이 열려있는가(=Ollama를 아예 안 부르고 곧바로 우회해야 하는가)?"""
    now = now if now is not None else time.time()
    return now < _open_until


def record_success():
    """Ollama 호출이 성공하면 실패 카운트를 초기화합니다."""
    global _fail_count, _open_until
    _fail_count = 0
    _open_until = 0.0


def record_failure(now=None):
    """Ollama 호출이 실패(타임아웃/연결거부 등)하면 카운트를 올리고, 기준을 넘으면 서킷을 엽니다."""
    global _fail_count, _open_until
    now = now if now is not None else time.time()
    _fail_count += 1
    if _fail_count >= MAX_FAILURES:
        _open_until = now + COOLDOWN
        print(f"[circuit] Ollama 연속 {_fail_count}회 실패 → {COOLDOWN}초 동안 우회(Fail-safe) 모드 진입")


def status(now=None) -> dict:
    """대시보드/디버깅용 현재 상태."""
    now = now if now is not None else time.time()
    return {"fail_count": _fail_count, "open": now < _open_until,
            "remaining_sec": max(0, int(_open_until - now))}


def reset():
    """테스트/데모용 초기화."""
    global _fail_count, _open_until
    _fail_count = 0
    _open_until = 0.0
