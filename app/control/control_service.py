"""
control_service.py (담당: 백이담이 로직 / 김나형이 대시보드 버튼 연결)
★ 고급 기능 — Kill-switch (방화벽 ON/OFF 스위치)

[무슨 기능인가요? — 쉽게]
대시보드에서 '방화벽'을 껐다 켰다 할 수 있게 해줍니다.
- 방화벽 ON  : 정상 보호 (위험행동 차단/마스킹/승인)
- 방화벽 OFF : 보호를 잠시 끔 → 모든 행동이 그냥 실행됨 (★ 발표 시연용으로 강력)

[왜 필요한가]
1) 발표 비교 시연: "방화벽 끄면 운영DB 삭제가 그냥 실행돼요 → 다시 켜니 막혀요"
   라고 보여주면 방화벽의 가치가 한눈에 와요.
2) 비상시: 방화벽이 오작동(정상 업무를 자꾸 막음)하면 잠깐 꺼서 업무를 풀 수 있어요.

[저장 위치]
flags 테이블에 "firewall_enabled" = "on"/"off" 로 저장합니다. (서버를 꺼도 유지됨)
"""
from ..logs import log_repository as repo

FLAG_KEY = "firewall_enabled"


def is_firewall_on() -> bool:
    """방화벽이 켜져 있으면 True. (기본값: 켜짐)"""
    return repo.get_flag(FLAG_KEY, "on") == "on"


def set_firewall(on: bool):
    """방화벽을 켜거나(True) 끕니다(False)."""
    repo.set_flag(FLAG_KEY, "on" if on else "off")
    return {"firewall_enabled": on}


def toggle() -> dict:
    """현재 상태를 반대로 뒤집습니다. (대시보드 토글 버튼이 호출)"""
    new_state = not is_firewall_on()
    return set_firewall(new_state)
