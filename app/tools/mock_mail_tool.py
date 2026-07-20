"""
mock_mail_tool.py  (담당: 조정우)

★ 병합 (2026-07) — "진짜로 작동하는" 시연을 위한 변경
지금까지는 진짜로 메일을 보내지 않고 흉내만 냈습니다. 이제 .env에 SMTP(Gmail 등) 계정
정보를 채워두면, ALLOW/MASK로 통과했거나 NEED_APPROVAL 후 관리자가 '승인'을 누른 메일은
실제로 발송됩니다. alert_service.py(Slack 알림)와 완전히 같은 패턴입니다:
  - .env에 SMTP_USER/SMTP_APP_PASSWORD가 채워져 있으면 → 진짜 발송
  - 비어 있으면 → 예전처럼 콘솔에 "[MOCK] ... 실제 발송 없음" 출력으로 자동 대체
그래서 이 코드는 발표 환경(SMTP 없음)에서도, 실제 연동 환경(SMTP 있음)에서도 똑같이
안전하게 동작합니다. 값은 항상 호출 시점에 os.getenv로 새로 읽습니다(캐싱 없음).

★ 보안 주의: 이 파일에는 절대 실제 이메일 주소/비밀번호를 직접 적지 마세요.
반드시 .env 파일에만 넣으세요 (.env는 .gitignore로 git 추적에서 제외돼 있습니다).
Gmail을 쓴다면 일반 로그인 비밀번호가 아니라 '앱 비밀번호'를 발급해서 넣어야 합니다.
(Google 계정 → 보안 → 2단계 인증 → 앱 비밀번호)
"""
import os
import smtplib
import ssl
from email.mime.text import MIMEText


def _smtp_settings():
    """호출 시점마다 최신 환경변수를 읽습니다. (모듈 임포트 시점에 값을 고정해두지 않음)"""
    # ★ 패치 (2026-07) — SMTP_HOST가 ".env"에 값 없이 키만 있으면(예: "SMTP_HOST=") 빈
    # 문자열이 될 수 있어 "or 기본값"으로 방어합니다. (customers_repository.py와 동일한 이유)
    return {
        "host": os.getenv("SMTP_HOST") or "smtp.gmail.com",
        "port": int(os.getenv("SMTP_PORT") or "587"),
        "user": os.getenv("SMTP_USER", ""),
        "app_password": os.getenv("SMTP_APP_PASSWORD", ""),
    }


def _send_real(to: str, subject: str, body: str) -> None:
    """실제 SMTP로 메일 한 통을 보냅니다. 실패하면 예외를 그대로 던집니다(호출부에서 처리)."""
    cfg = _smtp_settings()
    msg = MIMEText(body or "(본문 없음)", _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = cfg["user"]
    msg["To"] = to

    ctx = ssl.create_default_context()
    with smtplib.SMTP(cfg["host"], cfg["port"], timeout=10) as server:
        server.starttls(context=ctx)
        server.login(cfg["user"], cfg["app_password"])
        server.sendmail(cfg["user"], [to], msg.as_string())


def send_mail(to: str = "", body: str = "") -> str:
    """한 명에게 메일 보내기. SMTP 설정이 있으면 실제 발송, 없으면 흉내."""
    cfg = _smtp_settings()
    if not (cfg["user"] and cfg["app_password"] and to):
        return f"[MOCK] '{to}' 에게 메일을 보냈다고 가정합니다. (SMTP 미설정 — 실제 발송 없음)"
    try:
        _send_real(to, "[Agent Action Firewall] 자동 발송 메일", body)
        return f"[실제발송] '{to}' 에게 이메일을 실제로 발송했습니다."
    except Exception as e:
        return f"[발송실패] '{to}' 발송 중 오류가 나서 실제로는 전달되지 않았습니다: {e}"


def send_all(body: str = "") -> str:
    """
    전체에게 메일 보내기. 보통 NEED_APPROVAL 로 승인 대기 됩니다.

    안전장치: 승인됐다고 해서 진짜로 회사 전체 메일링 리스트에 보내면 사고가 나므로,
    .env의 DEMO_BROADCAST_RECIPIENTS(콤마로 구분된 이메일 목록)에 등록된 주소로만
    실제 발송합니다. 이 값이 비어 있으면 예전처럼 흉내만 냅니다.
    """
    cfg = _smtp_settings()
    recipients_raw = os.getenv("DEMO_BROADCAST_RECIPIENTS", "")
    recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]

    if not (cfg["user"] and cfg["app_password"] and recipients):
        return "[MOCK] 전체 사용자에게 메일을 보냈다고 가정합니다. (SMTP/수신자 미설정 — 실제 발송 없음)"

    ok, failed = [], []
    for to in recipients:
        try:
            _send_real(to, "[Agent Action Firewall] 전체 공지 메일", body)
            ok.append(to)
        except Exception as e:
            failed.append(f"{to}({e})")

    msg = f"[실제발송] 데모 수신자 {len(ok)}명에게 실제로 발송했습니다: {', '.join(ok) or '없음'}."
    if failed:
        msg += f" 실패 {len(failed)}건: {', '.join(failed)}"
    return msg
