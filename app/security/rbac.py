"""
rbac.py   (담당: 백이담)  ★ Action Guard 보강 — RBAC(역할 기반 권한 관리)

[RBAC이 뭔가요? — 쉽게]
회사 건물에 비유하면, '일반 사원증'으로는 금고가 있는 방(관리자 전용 구역)에 아예 들어갈
수 없고, '관리자 사원증'이 있어야 그 방 앞에서 경비원에게 한 번 더 확인(승인 대기)을
받고서야 들어갈 수 있는 것과 같습니다. 사원증(=역할/role) 확인 없이 아무나 똑같이
문을 열 수 있으면 안 되니까, "누가 요청했는지(user)"를 행동 계획과 같이 넘겨받아서
등급을 확인하는 게 이 파일의 역할입니다.

[전에는 왜 없었나 — 그래서 뭐가 바뀌나]
지금까지는 시크릿 조회·권한상승·운영DB삭제 같은 민감한 행동을 "요청한 사람이 누구든"
무조건 차단했습니다. 차단율(KPI) 숫자는 똑같이 100%로 나오지만, 기획서가 말한
"RBAC 기반 사용자 권한 매핑"(즉, 사용자 등급에 따라 다르게 처리)은 실제로 구현돼 있지
않았습니다. 이 파일 + policy_engine의 R_ADMIN 규칙으로 그 차이를 실제로 만듭니다.

[등급별 차이 — '관리자 전용' 행동(시크릿 조회/권한상승/운영DB·백업 삭제)에 한해서만]
  - general(일반 권한, 기본값) : 그냥 차단(BLOCK)               — 지금까지와 동일
  - admin(관리자)               : 즉시 차단 대신 '관리자 승인 대기(NEED_APPROVAL)'로 완화
    (그래도 무조건 허용은 아닙니다 — 이런 파괴적 행동은 관리자라도 사람이 한 번 더
     확인하게 만드는 게 안전합니다. '아예 못 들어감'과 '경비원 확인 후 입장'의 차이입니다.)

[사용자 등급은 어디서 정하나]
data/rbac_roles.json 표에 있는 사용자만 "admin"이고, 나머지는 전부 "general"입니다.
실제 서비스라면 사내 계정 시스템(LDAP/SSO)에서 받아와야 하지만, 이 프로젝트는 모의
환경이라 이 JSON 표로 대신합니다. ★ 중요: 이 등급은 요청 본문(action)의 값이 아니라
서버가 user 이름으로 직접 조회해서 정하므로, 클라이언트가 "나는 관리자"라고 우겨도
등급이 바뀌지 않습니다.
"""
import json
import os

_HERE = os.path.dirname(__file__)
_ROLES_PATH = os.path.join(_HERE, "..", "..", "data", "rbac_roles.json")

with open(_ROLES_PATH, encoding="utf-8") as f:
    _DATA = json.load(f)

_ROLES = _DATA.get("roles", {})

DEFAULT_ROLE = "general"


def get_role(user: str) -> str:
    """등급 조회. data/rbac_roles.json에 없는 사용자는 전부 'general'(일반 권한)입니다."""
    if not user:
        return DEFAULT_ROLE
    return _ROLES.get(user, DEFAULT_ROLE)
