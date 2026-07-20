"""
customers_repository.py   (담당: 조정우)   ★ 신규 (2026-07) — "진짜로 작동하는" 시연용

[이 파일이 하는 일]
'테스트 고객 DB'를 진짜 SQLite 파일로 관리합니다. 이전에는 mock_db_tool.py 안에
파이썬 리스트(_FAKE_CUSTOMERS)로만 있어서, 서버를 껐다 켜면 항상 원상복구되고
"삭제해줘"라고 해도 실제로는 아무것도 지워지지 않았습니다 (완전한 흉내).

이제는 실제 파일 DB에 저장하기 때문에:
  - "홍길동 고객 삭제해줘" → 실제로 이 SQLite 테이블에서 그 행이 사라집니다.
  - 그 다음 "고객 목록 보여줘"를 하면 진짜로 홍길동이 빠진 목록이 나옵니다.
  - 서버를 재시작해도 삭제 결과가 유지됩니다 (파일에 저장되므로).

[※ 중요 — 안전 경계선]
이건 어디까지나 '테스트/데모용 고객 DB'입니다. 운영 DB(prod_db)나 백업(backup) 삭제는
이 파일과 완전히 분리되어 있고, mock_db_tool.py의 delete_database()/delete_backup()은
여전히 100% 모의(가짜)입니다 — 정책 엔진(R1)이 그 두 가지는 항상 BLOCK 하기도 하고,
설사 통과되더라도 실제로 지우는 코드 자체가 없습니다. '진짜로 지워지는 것'은 오직
이 파일이 관리하는 테스트 고객 데이터뿐입니다.
"""
import os
import sqlite3

_DEFAULT = os.path.join(os.path.dirname(__file__), "..", "..", "data", "customers.db")
# ★ 패치 (2026-07) — .env에 "CUSTOMERS_DB=" 처럼 값 없이 키만 있으면 os.getenv가
# 빈 문자열("")을 그대로 돌려줍니다(기본값 무시). sqlite3.connect("")는 파일이 아니라
# '연결이 끝나면 바로 사라지는 임시 DB'를 매번 새로 만들기 때문에, 방금 저장한 내용도
# 다음 호출에서는 통째로 사라진 것처럼 보여 "no such table: customers" 오류가 났습니다.
# os.getenv(...) or 기본값 형태로 바꿔서, 빈 문자열이어도 반드시 기본 경로를 쓰게 고쳤습니다.
DB_PATH = os.getenv("CUSTOMERS_DB") or _DEFAULT

_SEED = [
    ("홍길동", "hong@test.com", "010-1234-5678"),
    ("김백조", "baekjo@test.com", "010-7777-8888"),
    ("김영희", "young@test.com", "010-2222-3333"),
    ("이철수", "chulsoo@test.com", "010-3333-4444"),
]

_ORDER_SEED = [
    ("김백조", "ORD-2026-0701", "프리미엄 키보드", 129000, "배송 완료"),
    ("김백조", "ORD-2026-0702", "무선 마우스", 59000, "결제 완료"),
    ("홍길동", "ORD-2026-0609", "USB-C 허브", 45000, "배송 중"),
    ("김영희", "ORD-2026-0618", "보안 교육 바우처", 88000, "배송 완료"),
    ("이철수", "ORD-2026-0622", "노트북 파우치", 32000, "결제 완료"),
]


def _conn():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    """테이블이 없으면 만들고, 비어 있으면 데모용 가짜 고객 3명을 심어 둡니다."""
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                name  TEXT,
                email TEXT,
                phone TEXT
            )""")
        c.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT,
                order_no      TEXT,
                item          TEXT,
                amount        INTEGER,
                status        TEXT
            )""")
        row = c.execute("SELECT COUNT(*) FROM customers").fetchone()
        if row[0] == 0:
            c.executemany("INSERT INTO customers (name, email, phone) VALUES (?,?,?)", _SEED)
        else:
            for name, email, phone in _SEED:
                exists = c.execute("SELECT 1 FROM customers WHERE name=?", (name,)).fetchone()
                if not exists:
                    c.execute("INSERT INTO customers (name, email, phone) VALUES (?,?,?)", (name, email, phone))
        order_row = c.execute("SELECT COUNT(*) FROM orders").fetchone()
        if order_row[0] == 0:
            c.executemany(
                "INSERT INTO orders (customer_name, order_no, item, amount, status) VALUES (?,?,?,?,?)",
                _ORDER_SEED,
            )


def read_all() -> list:
    """현재 남아있는 고객 전체를 돌려줍니다."""
    init_db()
    with _conn() as c:
        rows = c.execute("SELECT name, email, phone FROM customers ORDER BY id").fetchall()
    return [{"name": r[0], "email": r[1], "phone": r[2]} for r in rows]


def count() -> int:
    init_db()
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM customers").fetchone()[0]


def find_by_name(name: str) -> dict | None:
    init_db()
    with _conn() as c:
        row = c.execute(
            "SELECT name, email, phone FROM customers WHERE name=?",
            ((name or "").strip(),),
        ).fetchone()
    if not row:
        return None
    return {"name": row[0], "email": row[1], "phone": row[2]}


def read_orders(customer_name: str) -> dict:
    init_db()
    name = (customer_name or "").strip()
    customer = find_by_name(name)
    if not customer:
        return {"customer": None, "orders": []}
    with _conn() as c:
        rows = c.execute(
            """
            SELECT order_no, item, amount, status
            FROM orders
            WHERE customer_name=?
            ORDER BY id
            """,
            (name,),
        ).fetchall()
    return {
        "customer": customer,
        "orders": [
            {"order_no": r[0], "item": r[1], "amount": r[2], "status": r[3]}
            for r in rows
        ],
    }


def delete_matching(query_text: str) -> dict:
    """
    query_text(사용자 문장 등) 안에 이름 또는 이메일이 '포함되어' 있는 고객을 실제로 삭제합니다.
    (예: "홍길동 고객 삭제해줘" 라는 문장이 오면, 이름이 "홍길동"인 행을 찾아 지웁니다.)

    돌려주는 값: {"deleted": [지워진 고객 dict, ...], "remaining": 남은 고객 수}
    이름/이메일이 문장에 하나도 안 걸리면 deleted는 빈 리스트입니다(아무것도 안 지움 — 안전).
    """
    init_db()
    q = (query_text or "")
    all_rows = read_all()
    to_delete = [c for c in all_rows if c["name"] and c["name"] in q
                 or c["email"] and c["email"].lower() in q.lower()]

    if to_delete:
        with _conn() as c:
            for cust in to_delete:
                c.execute("DELETE FROM customers WHERE name=? AND email=?",
                          (cust["name"], cust["email"]))

    return {"deleted": to_delete, "remaining": count()}


def reset_seed():
    """데모를 여러 번 반복할 때, 지운 고객을 원래대로 되돌리고 싶으면 이 함수를 호출하세요.
    (코드 어디서도 자동으로 부르지 않습니다 — 필요할 때 수동으로만 사용)"""
    with _conn() as c:
        c.execute("DELETE FROM customers")
        c.execute("DELETE FROM orders")
        c.executemany("INSERT INTO customers (name, email, phone) VALUES (?,?,?)", _SEED)
        c.executemany(
            "INSERT INTO orders (customer_name, order_no, item, amount, status) VALUES (?,?,?,?,?)",
            _ORDER_SEED,
        )
