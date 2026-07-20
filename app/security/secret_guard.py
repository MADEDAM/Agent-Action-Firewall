"""
secret_guard.py   (담당: 백이담)

[이 파일이 하는 일]
글자 속에 'API Key, AWS 액세스 키, 비밀번호, 토큰' 같은 비밀값이 들어 있는지 찾아냅니다.
비유: 편지(글자)를 X-ray로 비춰서 '열쇠'가 들어있는지 검사하는 기계예요.

[어디서 쓰이나]
- 보안 엔진(policy_engine)이 "이 요청/응답에 비밀값이 있나?"를 물어볼 때 사용합니다.
- output_guard 가 AI 응답을 내보내기 전에도 한 번 더 검사합니다.
"""
import re

# 비밀값처럼 생긴 글자들의 '패턴'(정규식) 목록.
# 각 항목: (이름, 정규식). re.IGNORECASE 로 대소문자 구분 없이 찾습니다.
SECRET_PATTERNS = [
    ("AWS_ACCESS_KEY", re.compile(r"AKIA[0-9A-Z]{16}")),                 # AWS 액세스 키
    ("AWS_SECRET_KEY", re.compile(r"(?i)aws_secret[^\s]*['\":=\s]+[A-Za-z0-9/+]{20,}")),
    ("OPENAI_KEY",     re.compile(r"sk-[A-Za-z0-9]{20,}")),              # OpenAI 키
    ("PRIVATE_KEY",    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("BEARER_TOKEN",   re.compile(r"(?i)bearer\s+[A-Za-z0-9\.\-_]{15,}")),
    ("PASSWORD",       re.compile(r"(?i)(password|passwd|pwd)\s*[:=]\s*\S+")),
    ("GENERIC_APIKEY", re.compile(r"(?i)(api[_-]?key|token|secret)\s*[:=]\s*\S{8,}")),
]


def scan_secrets(text: str):
    """
    글자(text) 안에서 비밀값을 찾아 [{"type": 종류, "match": 찾은조각}, ...] 리스트로 돌려줍니다.
    하나도 없으면 빈 리스트 [] 를 돌려줍니다.
    """
    if not text:
        return []
    found = []
    for name, pattern in SECRET_PATTERNS:
        for m in pattern.findall(text):
            # findall 은 그룹이 있으면 튜플을 주므로 문자열로 정리
            piece = m if isinstance(m, str) else m[0]
            found.append({"type": name, "match": str(piece)[:40]})
    return found


def has_secret(text: str) -> bool:
    """비밀값이 하나라도 있으면 True, 없으면 False."""
    return len(scan_secrets(text)) > 0
