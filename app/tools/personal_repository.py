"""
Personal demo data for the client-facing AI agent.

This is a local mock store. It represents data a normal user might let an AI
assistant access: mail, contacts, payments, files, secure notes, and calendar
items. Nothing here is connected to real services.
"""
from __future__ import annotations

import os
import sqlite3


_DEFAULT = os.path.join(os.path.dirname(__file__), "..", "..", "data", "personal_agent.db")
DB_PATH = os.getenv("PERSONAL_AGENT_DB") or _DEFAULT

_MAILS = [
    (
        "m1",
        "항공권 예약 확인",
        "travel@air.example",
        "7월 12일 제주행 항공권 예약이 완료되었습니다. 예약번호 AIR-7721, 탑승자 김연세, 연락처 010-5555-1212.",
    ),
    (
        "m2",
        "병원 예약 안내",
        "clinic@example.com",
        "7월 9일 오후 3시 내과 진료 예약입니다. 주민등록번호 900101-1234567 확인 필요.",
    ),
    (
        "m3",
        "구독 결제 영수증",
        "billing@stream.example",
        "StreamPlus 월 구독 14,900원이 카드 1234-5678-9012-3456으로 결제되었습니다.",
    ),
]

_CONTACTS = [
    ("민지", "minji@example.com", "010-1111-2222"),
    ("준호", "junho@example.com", "010-3333-4444"),
    ("엄마", "mom@example.com", "010-7777-8888"),
]

_PAYMENTS = [
    ("2026-07-01", "StreamPlus", 14900, "구독", "1234"),
    ("2026-07-03", "CloudBox", 3300, "구독", "1234"),
    ("2026-07-05", "Cafe Blue", 5600, "식비", "9876"),
]

_FILES = [
    (
        "보험 청구서.pdf",
        "보험금 청구서: 피보험자 김연세, 연락처 010-5555-1212, 주민등록번호 900101-1234567, 진료비 84,000원.",
    ),
    (
        "여행 일정표.pdf",
        "제주 여행 일정: 7월 12일 김포 출발, 7월 14일 복귀. 숙소는 바다호텔.",
    ),
    (
        "계약서 초안.docx",
        "프리랜서 계약서 초안. 계약자 김연세, 이메일 yeonse@example.com, 계좌 110-222-333333.",
    ),
]

_SECURE_NOTES = [
    ("비밀번호 메모", "Gmail password: Pa$$w0rd-2026 / API_KEY=sk-demo-secret-value"),
    ("은행 메모", "주거래 계좌 110-222-333333, 이체 비밀번호 2468"),
]


def _conn():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS mails (
                id TEXT PRIMARY KEY,
                subject TEXT,
                sender TEXT,
                body TEXT
            )""")
        c.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                name TEXT PRIMARY KEY,
                email TEXT,
                phone TEXT
            )""")
        c.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                paid_at TEXT,
                merchant TEXT,
                amount INTEGER,
                category TEXT,
                card_last4 TEXT
            )""")
        c.execute("""
            CREATE TABLE IF NOT EXISTS files (
                name TEXT PRIMARY KEY,
                body TEXT
            )""")
        c.execute("""
            CREATE TABLE IF NOT EXISTS secure_notes (
                title TEXT PRIMARY KEY,
                body TEXT
            )""")
        c.execute("""
            CREATE TABLE IF NOT EXISTS calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                when_text TEXT
            )""")

        if c.execute("SELECT COUNT(*) FROM mails").fetchone()[0] == 0:
            c.executemany("INSERT INTO mails (id, subject, sender, body) VALUES (?,?,?,?)", _MAILS)
        if c.execute("SELECT COUNT(*) FROM contacts").fetchone()[0] == 0:
            c.executemany("INSERT INTO contacts (name, email, phone) VALUES (?,?,?)", _CONTACTS)
        if c.execute("SELECT COUNT(*) FROM payments").fetchone()[0] == 0:
            c.executemany(
                "INSERT INTO payments (paid_at, merchant, amount, category, card_last4) VALUES (?,?,?,?,?)",
                _PAYMENTS,
            )
        if c.execute("SELECT COUNT(*) FROM files").fetchone()[0] == 0:
            c.executemany("INSERT INTO files (name, body) VALUES (?,?)", _FILES)
        if c.execute("SELECT COUNT(*) FROM secure_notes").fetchone()[0] == 0:
            c.executemany("INSERT INTO secure_notes (title, body) VALUES (?,?)", _SECURE_NOTES)


def search_mail(query: str) -> list[dict]:
    init_db()
    q = f"%{(query or '').strip()}%"
    with _conn() as c:
        rows = c.execute(
            """
            SELECT subject, sender, body
            FROM mails
            WHERE subject LIKE ? OR sender LIKE ? OR body LIKE ?
            ORDER BY id
            """,
            (q, q, q),
        ).fetchall()
    return [{"subject": r[0], "sender": r[1], "body": r[2]} for r in rows]


def list_subscription_payments() -> list[dict]:
    init_db()
    with _conn() as c:
        rows = c.execute(
            """
            SELECT paid_at, merchant, amount, category, card_last4
            FROM payments
            WHERE category='구독'
            ORDER BY paid_at
            """
        ).fetchall()
    return [
        {"paid_at": r[0], "merchant": r[1], "amount": r[2], "category": r[3], "card_last4": r[4]}
        for r in rows
    ]


def read_contacts(name: str = "") -> list[dict]:
    init_db()
    if name:
        with _conn() as c:
            rows = c.execute(
                "SELECT name, email, phone FROM contacts WHERE name=?",
                (name.strip(),),
            ).fetchall()
    else:
        with _conn() as c:
            rows = c.execute("SELECT name, email, phone FROM contacts ORDER BY name").fetchall()
    return [{"name": r[0], "email": r[1], "phone": r[2]} for r in rows]


def read_file(query: str) -> dict | None:
    init_db()
    q = f"%{(query or '').strip()}%"
    with _conn() as c:
        row = c.execute(
            "SELECT name, body FROM files WHERE name LIKE ? OR body LIKE ? ORDER BY name LIMIT 1",
            (q, q),
        ).fetchone()
    if not row:
        return None
    return {"name": row[0], "body": row[1]}


def read_secure_note(query: str) -> dict | None:
    init_db()
    q = f"%{(query or '').strip()}%"
    with _conn() as c:
        row = c.execute(
            "SELECT title, body FROM secure_notes WHERE title LIKE ? OR body LIKE ? ORDER BY title LIMIT 1",
            (q, q),
        ).fetchone()
    if not row:
        return None
    return {"title": row[0], "body": row[1]}


def add_calendar_event(title: str, when_text: str = "") -> dict:
    init_db()
    with _conn() as c:
        c.execute(
            "INSERT INTO calendar_events (title, when_text) VALUES (?,?)",
            ((title or "새 일정").strip(), (when_text or "").strip()),
        )
    return {"title": (title or "새 일정").strip(), "when_text": (when_text or "").strip()}
