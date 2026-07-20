"""
pii_masker.py   (담당: 백이담)

[이 파일이 하는 일]
글자 속의 '개인정보'(이메일, 전화번호, 주민번호, 카드번호)를 찾아내고,
필요하면 가려줍니다(마스킹). 예: hong@test.com  ->  ho***@test.com

[어디서 쓰이나]
- 보안 엔진이 "이 응답에 개인정보가 있나?"를 판단할 때
- 결과가 MASK 로 정해지면, 실제로 개인정보를 가린 글자를 만들 때
"""
import re

# 개인정보처럼 생긴 패턴들
PII_PATTERNS = {
    "EMAIL": re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"),
    "PHONE": re.compile(r"01[016789]-?\d{3,4}-?\d{4}"),           # 한국 휴대폰
    "RRN":   re.compile(r"\d{6}-\d{7}"),                           # 주민등록번호
    "CARD":  re.compile(r"\d{4}-\d{4}-\d{4}-\d{4}"),               # 카드번호
}


def scan_pii(text: str):
    """글자 안의 개인정보를 [{"type":종류,"match":찾은값}, ...] 로 돌려줍니다."""
    if not text:
        return []
    found = []
    for name, pattern in PII_PATTERNS.items():
        for m in pattern.findall(text):
            found.append({"type": name, "match": m})
    return found


def has_pii(text: str) -> bool:
    """개인정보가 하나라도 있으면 True."""
    return len(scan_pii(text)) > 0


def _mask_email(s):
    name, _, domain = s.partition("@")
    keep = name[:2] if len(name) > 2 else name[:1]
    return keep + "***@" + domain


def mask_text(text: str) -> str:
    """
    글자 속 개인정보를 가린 새 글자를 돌려줍니다.
    - 이메일: 앞 2글자만 남기고 가림
    - 전화/주민/카드: 뒷자리를 **** 로 가림
    """
    if not text:
        return text
    text = PII_PATTERNS["EMAIL"].sub(lambda m: _mask_email(m.group()), text)
    text = PII_PATTERNS["RRN"].sub(lambda m: m.group()[:6] + "-*******", text)
    text = PII_PATTERNS["CARD"].sub(lambda m: m.group()[:9] + "****-****", text)
    text = PII_PATTERNS["PHONE"].sub(lambda m: m.group()[:3] + "-****-****", text)
    return text
