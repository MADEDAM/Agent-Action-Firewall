"""
mock_db_tool.py   (담당: 조정우)

[이 파일이 하는 일]
'데이터베이스 도구'입니다.

★ 병합 (2026-07) — "진짜로 작동하는" 시연을 위한 변경
지금까지 read_customers()/count_customers()는 파이썬 리스트(_FAKE_CUSTOMERS)를 흉내만
냈습니다. 이제는 customers_repository.py 가 관리하는 '진짜 SQLite 테스트 DB'를 읽고 씁니다.
그래서 delete_customer()로 고객을 지우면, 그 다음 read_customers()에는 실제로 그 사람이
빠져서 나옵니다 (서버를 재시작해도 유지됩니다).

[※ 안전 경계선 — 매우 중요]
delete_database() / delete_backup() 은 '운영 DB' / '백업'을 흉내 낸 것으로,
지금도 앞으로도 절대 진짜로 지우는 코드를 넣지 않습니다. 정책 엔진(R1)이 항상 이 둘을
차단(BLOCK)하기도 하지만, 설사 정책이 뚫리더라도 이 함수들 자체가 아무것도 지우지
않는 완전한 모의(mock)라서 이중으로 안전합니다. '진짜로 지워지는 것'은 오직
delete_customer() 가 다루는 테스트 고객 데이터뿐입니다.

[어디서 쓰이나]
- 조정우의 agent_service(정확히는 app/agent/tool_runner.py) 가 "보안 검사를 통과한
  행동"만 여기 함수를 불러 실행합니다. 차단(BLOCK)된 행동은 이 함수가 아예 실행되지 않습니다.
"""
from . import customers_repository as _repo
from . import personal_repository as _personal


def search_mail(query: str = "") -> str:
    rows = _personal.search_mail(query)
    if not rows:
        return "관련 메일을 찾을 수 없습니다"
    lines = [
        f"{m['subject']} / 보낸 사람: {m['sender']}\n{m['body']}"
        for m in rows
    ]
    return "메일 검색 결과:\n" + "\n\n".join(lines)


def list_subscriptions() -> str:
    rows = _personal.list_subscription_payments()
    if not rows:
        return "이번 달 구독 결제 내역이 없습니다"
    total = sum(p["amount"] for p in rows)
    lines = [
        f"{p['paid_at']} / {p['merchant']} / {p['amount']}원 / 카드 끝자리 {p['card_last4']}"
        for p in rows
    ]
    return "구독 결제 내역:\n" + "\n".join(lines) + f"\n합계: {total}원"


def read_contacts(name: str = "") -> str:
    rows = _personal.read_contacts(name)
    if not rows:
        return "해당 연락처를 찾을 수 없습니다"
    if name:
        c = rows[0]
        return f"연락처: {c['name']} / {c['email']} / {c['phone']}"
    lines = [f"{c['name']} / {c['email']} / {c['phone']}" for c in rows]
    return "연락처 목록:\n" + "\n".join(lines)


def summarize_file(query: str = "") -> str:
    found = _personal.read_file(query)
    if not found:
        return "관련 파일을 찾을 수 없습니다"
    return f"파일 요약: {found['name']}\n{found['body']}"


def read_secure_note(query: str = "") -> str:
    found = _personal.read_secure_note(query)
    if not found:
        return "관련 보안 메모를 찾을 수 없습니다"
    return f"보안 메모: {found['title']}\n{found['body']}"


def add_calendar_event(title: str = "", when_text: str = "") -> str:
    event = _personal.add_calendar_event(title, when_text)
    when = f" ({event['when_text']})" if event["when_text"] else ""
    return f"캘린더에 '{event['title']}' 일정을 추가했습니다{when}."


def read_customers() -> str:
    """고객 목록을 글자로 돌려줍니다. (개인정보가 들어있어 output_guard가 마스킹합니다)
    ★ 병합(2026-07): 이제 진짜 SQLite 테스트 DB에서 읽어옵니다."""
    rows = _repo.read_all()
    if not rows:
        return "고객 목록: (남아있는 고객이 없습니다)"
    lines = [f"{c['name']} / {c['email']} / {c['phone']}" for c in rows]
    return "고객 목록:\n" + "\n".join(lines)


def count_customers() -> str:
    """고객 '수'만 돌려줍니다. (개인정보가 없어 안전 → ALLOW)
    ★ 병합(2026-07): 진짜 SQLite 테스트 DB 기준 실제 카운트."""
    return f"전체 고객 수: {_repo.count()}명"


def read_orders(customer_name: str = "") -> str:
    """특정 고객의 주문 내역만 조회합니다. 고객이 없으면 전체 고객 목록으로 대체하지 않습니다."""
    name = (customer_name or "").strip()
    if not name:
        return "해당 고객을 찾을 수 없습니다"

    result = _repo.read_orders(name)
    customer = result["customer"]
    if not customer:
        return "해당 고객을 찾을 수 없습니다"

    orders = result["orders"]
    if not orders:
        return f"{name} 고객의 주문 내역이 없습니다"

    lines = [
        f"{o['order_no']} / {o['item']} / {o['amount']}원 / {o['status']}"
        for o in orders
    ]
    return (
        f"{name} 고객 주문 내역\n"
        f"고객 연락처: {customer['email']} / {customer['phone']}\n"
        + "\n".join(lines)
    )


def delete_customer(name: str = "") -> str:
    """
    ★ 신규(2026-07) — 테스트 고객 DB에서 실제로 삭제합니다 (진짜 삭제, 흉내 아님).

    name 인자에는 보통 사용자 문장 전체(또는 대상 이름/이메일이 포함된 텍스트)가 들어옵니다.
    그 문장 안에 실제로 존재하는 고객의 이름/이메일이 들어있으면 그 고객만 정확히 지우고,
    없으면 아무것도 지우지 않고 그렇게 알려줍니다 (엉뚱한 고객이 삭제되는 사고 방지).

    ※ 이 함수는 보통 정책 엔진 규칙 R8(그 외 삭제 행동)에 걸려 NEED_APPROVAL(승인 대기)로
    빠집니다. 관리자가 대시보드에서 '승인'을 누르는 순간 이 함수가 실제로 호출되어
    데이터가 진짜로 사라집니다 — 승인 전에는 절대 실행되지 않습니다.
    """
    result = _repo.delete_matching(name)
    if not result["deleted"]:
        return (f"[삭제 실패] '{name}' 안에서 일치하는 테스트 고객을 찾지 못해 아무것도 "
                f"지우지 않았습니다. (남은 고객 {result['remaining']}명)")
    who = ", ".join(f"{c['name']}({c['email']})" for c in result["deleted"])
    return (f"[실제삭제] 테스트 고객 DB에서 {who} 을(를) 실제로 삭제했습니다. "
            f"(남은 고객 {result['remaining']}명)")


def delete_database() -> str:
    """※ 가짜 함수. 실제로는 아무것도 지우지 않습니다. (운영 DB — 항상 모의, 정책 R1로 통상 차단됨)"""
    return "[MOCK] 운영 DB 삭제를 '흉내'만 냈습니다. 실제 삭제는 일어나지 않습니다."


def delete_backup() -> str:
    """※ 가짜 함수. 실제로는 아무것도 지우지 않습니다. (백업 — 항상 모의, 정책 R1로 통상 차단됨)"""
    return "[MOCK] 백업 삭제를 '흉내'만 냈습니다. 실제 삭제는 일어나지 않습니다."
