"""
mock_aws_tool.py  (담당: 조정우)
'가짜 AWS 도구'. 진짜 AWS를 부르지 않고 흉내만 냅니다.
(나중에 원하면 boto3로 진짜 AWS 연동으로 바꿀 수 있는 자리입니다 — 단, 발표는 Mock 권장.)
"""


def get_secret(name: str = "") -> str:
    """※ 비밀값 조회(흉내). 보통 SECRET_ACCESS 로 분류되어 BLOCK 됩니다."""
    # 일부러 비밀값처럼 생긴 가짜 문자열을 넣어 두었습니다(전부 가짜).
    return "AKIAFAKEEXAMPLE12345 (가짜 키 - 실제 사용 불가)"


def export_to_url(url: str = "", data: str = "") -> str:
    """※ 외부 URL로 데이터 전송(흉내). 보통 EXPORT+external 로 BLOCK 됩니다."""
    return f"[MOCK] '{url}' 로 데이터를 보냈다고 가정합니다. (실제 전송 없음)"
