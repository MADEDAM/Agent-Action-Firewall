"""
output_guard.py   (담당: 백이담)

[이 파일이 하는 일]
도구(Mock Tool)가 만들어낸 '응답 결과'를 사용자에게 돌려주기 전에 마지막으로 한 번 더 검사합니다.
- 응답 안에 비밀값이 있으면 통째로 막고(BLOCK)
- 개인정보가 있으면 가린(MASK) 글자로 바꿉니다.

비유: 택배 나가기 직전에 한 번 더 X-ray 찍는 '출구 검사대'.

[어디서 쓰이나]
- 조정우의 agent_service 가 READ 같은 안전한 도구를 실행한 '뒤'에 호출합니다.
- 실행 전 검사(policy_engine)는 '하려는 행동'을, 이 검사(output_guard)는 '실제 나온 결과'를 봅니다.
"""
from .secret_guard import scan_secrets
from .pii_masker import scan_pii, mask_text


def guard_output(output_text: str) -> dict:
    """
    output_text: 도구가 만든 응답 글자
    돌려주는 값:
      {
        "decision": "ALLOW" | "MASK" | "BLOCK",
        "output": 최종적으로 사용자에게 줄 글자,
        "reasons": [...]
      }
    """
    reasons = []
    secrets = scan_secrets(output_text)
    pii = scan_pii(output_text)

    # 1) 응답에 비밀값이 있으면 막는다
    if secrets:
        return {
            "decision": "BLOCK",
            "output": "[차단됨] 응답에 비밀값(키/토큰)이 포함되어 제공할 수 없습니다.",
            "reasons": [f"응답에 비밀값 {len(secrets)}건"],
        }

    # 2) 개인정보가 있으면 가린다
    if pii:
        return {
            "decision": "MASK",
            "output": mask_text(output_text),
            "reasons": [f"응답에 개인정보 {len(pii)}건 → 마스킹"],
        }

    # 3) 아무것도 없으면 그대로 허용
    return {"decision": "ALLOW", "output": output_text, "reasons": ["안전한 응답"]}
