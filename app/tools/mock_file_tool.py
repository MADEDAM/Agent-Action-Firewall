"""
mock_file_tool.py  (담당: 조정우)
'가짜 파일 도구'. 진짜 파일을 건드리지 않고 흉내만 냅니다.
"""


def read_file(path: str = "") -> str:
    return f"[MOCK] '{path}' 파일 내용을 읽었다고 가정합니다."


def write_file(path: str = "", content: str = "") -> str:
    return f"[MOCK] '{path}' 파일을 수정했다고 가정합니다. (실제 변경 없음)"


def delete_file(path: str = "") -> str:
    return f"[MOCK] '{path}' 파일을 삭제했다고 가정합니다. (실제 삭제 없음)"
