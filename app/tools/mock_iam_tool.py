"""
mock_iam_tool.py  (담당: 조정우)
'가짜 IAM(권한) 도구'. 진짜 권한을 바꾸지 않고 흉내만 냅니다.
관리자 권한 상승(Privilege Escalation) 시연용 — 보통 BLOCK 됩니다.
"""


def put_user_policy(user: str = "", policy: str = "") -> str:
    """※ 사용자에게 권한 정책을 붙이는(권한 상승) 흉내. 보통 PRIV_ESC 로 분류되어 BLOCK."""
    return f"[MOCK] '{user}' 에게 관리자 권한 정책을 붙였다고 가정합니다. (실제 변경 없음)"


def attach_user_policy(user: str = "", policy: str = "") -> str:
    """※ 관리자 정책 연결(권한 상승) 흉내."""
    return f"[MOCK] '{user}' 에 관리자 정책을 연결했다고 가정합니다. (실제 변경 없음)"
