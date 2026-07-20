"""
log_repository.py  (담당: 김나형, 조정우와 함께 사용)

[이 파일이 하는 일]
모든 요청/판단/결과를 'SQLite'라는 작은 파일 데이터베이스에 저장하고 꺼내옵니다.
SQLite = 설치가 필요 없는 '파일 하나짜리 DB'. 파이썬에 기본 내장(sqlite3)이라 따로 설치 안 해도 돼요.
(원하면 나중에 DynamoDB로 바꿀 수 있게 저장 부분만 이 파일에 모아 뒀습니다.)
"""
import sqlite3
import os
import json

# DB 파일 위치: data/firewall.db  (환경변수로 바꿀 수 있음 → 테스트 때 임시파일 사용)
_DEFAULT = os.path.join(os.path.dirname(__file__), "..", "..", "data", "firewall.db")
# ★ 패치 (2026-07) — customers_repository.py와 동일한 이유로, 빈 문자열("")이어도
# 반드시 기본 경로를 쓰도록 안전하게 바꿨습니다. (자세한 이유는 customers_repository.py 참고)
DB_PATH = os.getenv("FIREWALL_DB") or _DEFAULT


def _conn():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    """테이블이 없으면 만들어 줍니다. 서버 시작할 때 한 번 부르면 됩니다."""
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id   TEXT,
                created_at   TEXT,
                user         TEXT,
                user_input   TEXT,
                tool         TEXT,
                action_type  TEXT,
                risk_level   TEXT,
                risk_score   INTEGER,
                decision     TEXT,
                reasons      TEXT,
                status       TEXT
            )""")
        c.execute("""
            CREATE TABLE IF NOT EXISTS approvals (
                request_id   TEXT PRIMARY KEY,
                created_at   TEXT,
                user         TEXT,
                action_type  TEXT,
                summary      TEXT,
                status       TEXT,         -- PENDING / APPROVED / REJECTED
                action_json  TEXT,         -- ★ 신규(2026-07): 승인 시 실제로 실행할 행동(JSON)
                user_input   TEXT          -- ★ 신규(2026-07): 원본 사용자 문장(로그용)
            )""")
        # ★ 신규(2026-07) — 이미 만들어진 옛날 firewall.db에는 위 두 컬럼이 없을 수 있으므로,
        # 없으면 추가합니다(있으면 조용히 무시). 기존 승인 이력은 그대로 유지됩니다.
        for col, coltype in (("action_json", "TEXT"), ("user_input", "TEXT")):
            try:
                c.execute(f"ALTER TABLE approvals ADD COLUMN {col} {coltype}")
            except sqlite3.OperationalError:
                pass  # 이미 컬럼이 있음
        # 켜고 끄는 스위치 등 설정값을 저장하는 key-value 표 (kill-switch가 여기 들어감)
        c.execute("""
            CREATE TABLE IF NOT EXISTS flags (
                key   TEXT PRIMARY KEY,
                value TEXT
            )""")
        # ★ 신규(2026-07) — 이상행동 자동격리(anomaly_guard) 상태를 SQLite에 저장.
        # 예전에는 파이썬 메모리(딕셔너리)에만 저장했는데, FastAPI 서버·관제 대시보드·
        # 채팅 UI가 전부 "따로 실행되는 프로세스"라서 메모리가 서로 공유되지 않았습니다.
        # 그 결과 채팅 UI에서는 "격리되었습니다"라고 응답이 나오는데, 정작 관제 대시보드의
        # QUARANTINE 패널에는 아무도 안 뜨는 문제가 있었습니다. 방화벽 on/off(flags)와
        # 똑같이 SQLite로 옮겨서, 어느 프로세스에서 보든 같은 격리 상태를 보게 만듭니다.
        c.execute("""
            CREATE TABLE IF NOT EXISTS anomaly_events (
                user TEXT,
                ts   REAL
            )""")
        c.execute("""
            CREATE TABLE IF NOT EXISTS anomaly_quarantine (
                user  TEXT PRIMARY KEY,
                until REAL
            )""")


def insert_log(row: dict):
    """로그 한 줄 저장. row 는 dict 형태."""
    with _conn() as c:
        c.execute("""INSERT INTO logs
            (request_id,created_at,user,user_input,tool,action_type,
             risk_level,risk_score,decision,reasons,status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (row["request_id"], row["created_at"], row["user"], row["user_input"],
             row["tool"], row["action_type"], row["risk_level"], row["risk_score"],
             row["decision"], json.dumps(row["reasons"], ensure_ascii=False), row["status"]))


def fetch_logs(decision=None, risk_level=None, action_type=None, limit=200):
    """필터(선택)에 맞는 로그를 최신순으로 돌려줍니다. 대시보드가 이걸 표로 그립니다."""
    q = "SELECT request_id,created_at,user,user_input,tool,action_type,risk_level,risk_score,decision,reasons,status FROM logs"
    cond, args = [], []
    if decision:    cond.append("decision=?");    args.append(decision)
    if risk_level:  cond.append("risk_level=?");  args.append(risk_level)
    if action_type: cond.append("action_type=?"); args.append(action_type)
    if cond:
        q += " WHERE " + " AND ".join(cond)
    q += " ORDER BY id DESC LIMIT ?"
    args.append(limit)
    cols = ["request_id","created_at","user","user_input","tool","action_type",
            "risk_level","risk_score","decision","reasons","status"]
    with _conn() as c:
        rows = c.execute(q, args).fetchall()
    out = []
    for r in rows:
        d = dict(zip(cols, r))
        d["reasons"] = json.loads(d["reasons"]) if d["reasons"] else []
        out.append(d)
    return out


def upsert_approval(row: dict):
    with _conn() as c:
        c.execute("""INSERT OR REPLACE INTO approvals
            (request_id,created_at,user,action_type,summary,status,action_json,user_input)
            VALUES (?,?,?,?,?,?,?,?)""",
            (row["request_id"], row["created_at"], row["user"],
             row["action_type"], row["summary"], row["status"],
             row.get("action_json", ""), row.get("user_input", "")))


def fetch_approvals(status=None):
    q = "SELECT request_id,created_at,user,action_type,summary,status,action_json,user_input FROM approvals"
    args = []
    if status:
        q += " WHERE status=?"; args.append(status)
    q += " ORDER BY created_at DESC"
    cols = ["request_id","created_at","user","action_type","summary","status","action_json","user_input"]
    with _conn() as c:
        return [dict(zip(cols, r)) for r in c.execute(q, args).fetchall()]


def fetch_approval_one(request_id: str):
    """승인 1건을 request_id로 정확히 조회합니다. (approve() 실행 시 원본 action을 꺼낼 때 사용)"""
    cols = ["request_id","created_at","user","action_type","summary","status","action_json","user_input"]
    q = "SELECT " + ",".join(cols) + " FROM approvals WHERE request_id=?"
    with _conn() as c:
        row = c.execute(q, (request_id,)).fetchone()
    return dict(zip(cols, row)) if row else None


def set_approval_status(request_id: str, status: str):
    with _conn() as c:
        c.execute("UPDATE approvals SET status=? WHERE request_id=?", (status, request_id))


# ---------- 설정값(flags) 저장/조회 : kill-switch 등에 사용 ----------
def get_flag(key: str, default: str = None):
    with _conn() as c:
        row = c.execute("SELECT value FROM flags WHERE key=?", (key,)).fetchone()
    return row[0] if row else default


def set_flag(key: str, value: str):
    with _conn() as c:
        c.execute("INSERT OR REPLACE INTO flags(key, value) VALUES (?, ?)", (key, value))


# ---------- 이상행동 자동격리(anomaly_guard) 상태 : SQLite로 프로세스 간 공유 ----------
def add_anomaly_event(user: str, ts: float):
    """위험행동 발생 시각 1건 기록."""
    with _conn() as c:
        c.execute("INSERT INTO anomaly_events(user, ts) VALUES (?, ?)", (user, ts))


def prune_anomaly_events(user: str, before_ts: float):
    """이 사용자의, 관찰 시간(WINDOW)보다 오래된 기록은 지움."""
    with _conn() as c:
        c.execute("DELETE FROM anomaly_events WHERE user=? AND ts<=?", (user, before_ts))


def count_anomaly_events(user: str, since_ts: float) -> int:
    """since_ts 이후에 남아있는(=최근 WINDOW 안의) 위험행동 개수."""
    with _conn() as c:
        row = c.execute(
            "SELECT COUNT(*) FROM anomaly_events WHERE user=? AND ts>?", (user, since_ts)
        ).fetchone()
    return row[0] if row else 0


def set_quarantine(user: str, until_ts: float):
    with _conn() as c:
        c.execute("INSERT OR REPLACE INTO anomaly_quarantine(user, until) VALUES (?, ?)",
                   (user, until_ts))


def get_quarantine(user: str):
    with _conn() as c:
        row = c.execute("SELECT until FROM anomaly_quarantine WHERE user=?", (user,)).fetchone()
    return row[0] if row else None


def clear_quarantine_flag(user: str):
    """격리 시간이 자연 만료됐을 때: 격리 상태만 지움 (행동 이력은 남겨둠)."""
    with _conn() as c:
        c.execute("DELETE FROM anomaly_quarantine WHERE user=?", (user,))


def release_anomaly_user(user: str):
    """관리자가 수동으로 격리 해제: 격리 상태 + 위험행동 이력을 전부 지움."""
    with _conn() as c:
        c.execute("DELETE FROM anomaly_quarantine WHERE user=?", (user,))
        c.execute("DELETE FROM anomaly_events WHERE user=?", (user,))


def list_quarantined(now_ts: float):
    """현재 격리 중인 사용자 전체. [(user, until), ...]"""
    with _conn() as c:
        return c.execute(
            "SELECT user, until FROM anomaly_quarantine WHERE until>?", (now_ts,)
        ).fetchall()


def reset_anomaly_state():
    """테스트/데모용 전체 초기화."""
    with _conn() as c:
        c.execute("DELETE FROM anomaly_events")
        c.execute("DELETE FROM anomaly_quarantine")


# ---------- 대시보드 리셋 버튼용 ----------
def reset_logs():
    """대시보드 상단 카드(Total/Blocked/Need Approval/Masked)가 세는 logs 테이블만 비웁니다.
    approvals/flags/anomaly_* 테이블은 건드리지 않습니다 (Settings 화면의 '리셋' 버튼이 호출)."""
    with _conn() as c:
        c.execute("DELETE FROM logs")
