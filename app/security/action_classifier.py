"""
action_classifier.py   (담당: 백이담)

[이 파일이 하는 일]
AI가 "어떤 도구로 무슨 작업을 하려는지"를 보고, 그 행동의 '종류(action_type)'를 정합니다.
비유: 택배 상자를 보고 '이건 깨지는 물건', '이건 음식' 하고 분류 스티커를 붙이는 것.

[행동 종류 7가지 + 확장 1종]
 READ          : 읽기/조회 (예: 고객 목록 조회)
 WRITE         : 수정/쓰기 (예: 파일 내용 변경)
 DELETE        : 삭제 (예: DB 삭제, 백업 삭제)
 SEND          : 보내기 (예: 메일 발송)
 EXPORT        : 외부로 내보내기 (예: 외부 URL 전송)
 SECRET_ACCESS : 비밀값 접근 (예: API Key 조회)
 PII_ACCESS    : 개인정보 접근 (예: 고객 개인정보 조회)
 PRIV_ESC      : 권한 상승 (예: IAM 사용자에게 관리자 정책 부여)
                 ★ 병합(2026-07): 팀원 브랜치(mock_iam_tool)에 있던 권한상승 탐지 기능을
                 원본 7종 분류체계에 8번째 유형으로 병합했습니다.

[어디서 쓰이나]
- 조정우의 agent_service 가 만든 '행동 계획(action)'을 받아서
- 백이담의 policy_engine 이 판단하기 전에 분류표를 붙입니다.
"""

# (도구이름, 작업이름) -> 행동 종류 매핑표.
# 조정우의 Mock Tool 들이 내놓는 operation 이름과 똑같이 맞춰야 합니다. (★ 인터페이스 약속)
TOOL_ACTION_MAP = {
    ("mock_db_tool", "search_mail"):     "PII_ACCESS",
    ("mock_db_tool", "list_subscriptions"): "PII_ACCESS",
    ("mock_db_tool", "read_contacts"):   "PII_ACCESS",
    ("mock_db_tool", "summarize_file"):  "PII_ACCESS",
    ("mock_db_tool", "read_secure_note"): "SECRET_ACCESS",
    ("mock_db_tool", "add_calendar_event"): "WRITE",
    ("mock_db_tool", "read_orders"):     "PII_ACCESS",
    ("mock_db_tool", "read_customers"):  "READ",
    ("mock_db_tool", "delete_database"): "DELETE",
    ("mock_db_tool", "delete_backup"):   "DELETE",
    # ★ 신규(2026-07) — 테스트 고객 DB에서 실제로 지우는 행동. 운영DB/백업과 달리
    # target이 "customer_db"라서 risk_scorer의 +30 민감대상 가산은 안 붙지만,
    # DELETE 기본 점수(50) 때문에 여전히 R8(그 외 삭제)에 걸려 승인 대기가 됩니다.
    ("mock_db_tool", "delete_customer"): "DELETE",
    ("mock_mail_tool", "send_mail"):     "SEND",
    ("mock_mail_tool", "send_all"):      "SEND",
    ("mock_file_tool", "read_file"):     "READ",
    ("mock_file_tool", "write_file"):    "WRITE",
    ("mock_file_tool", "delete_file"):   "DELETE",
    ("mock_aws_tool", "get_secret"):     "SECRET_ACCESS",
    ("mock_aws_tool", "export_to_url"):  "EXPORT",
    ("mock_iam_tool", "put_user_policy"):    "PRIV_ESC",
    ("mock_iam_tool", "attach_user_policy"): "PRIV_ESC",
}


def classify(action: dict) -> dict:
    """
    action 예시:
      {
        "tool": "mock_db_tool",
        "operation": "delete_database",
        "target": "prod_db",          # 무엇을 대상으로? (customer_db / prod_db / backup ...)
        "destination": "internal",     # 어디로? (internal / external)
        "scope": "single",             # 범위? (single / broadcast)
        "payload_text": "..."          # 검사할 본문 글자 (비밀값·개인정보 탐지용)
      }
    돌려주는 값(분류 결과 dict):
      {
        "action_type": "DELETE",
        "target": "prod_db", "destination": "internal", "scope": "single"
      }
    """
    tool = action.get("tool", "")
    op = action.get("operation", "")
    action_type = TOOL_ACTION_MAP.get((tool, op), "READ")  # 모르면 가장 안전한 READ로
    if (tool, op) == ("mock_db_tool", "read_customers"):
        payload = (action.get("payload_text", "") or "").lower()
        asks_contact_fields = any(w in payload for w in ("개인정보", "이메일", "email", "전화번호", "연락처", "phone"))
        asks_all = any(w in payload for w in ("전체", "모든", "목록", "명단", "all"))
        if asks_contact_fields and asks_all:
            action_type = "PII_ACCESS"

    return {
        "action_type": action_type,
        "target": action.get("target", "none"),
        "destination": action.get("destination", "internal"),
        "scope": action.get("scope", "single"),
    }
