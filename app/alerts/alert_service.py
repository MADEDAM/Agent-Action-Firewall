"""
alert_service.py   (담당: 김나형)

[이 파일이 하는 일]
Critical(아주 위험) 같은 사건이 생기면 Slack으로 알림을 보냅니다.
Slack 주소가 없으면 그냥 화면(콘솔)에 출력합니다. (발표 때는 콘솔만으로도 충분)

[왜 필요한가]
관리자가 대시보드를 24시간 보고 있을 순 없으니, 위험한 일이 생기면
'먼저 알려주는 알림'이 필요합니다. 이게 Alert Center의 핵심이에요.

[★ 패치 (2026-07) #1 — SLACK_WEBHOOK_URL을 "매번" 새로 읽도록 수정]
기존엔 `from ..config import SLACK_WEBHOOK_URL`로 값을 한 번만 가져와서 이 모듈에
고정해뒀습니다. 이러면 서버가 이미 켜진 상태에서 .env에 나중에 URL을 채워 넣어도
(uvicorn --reload는 .py 파일 변경만 감지하고 .env 변경은 감지하지 못하므로) 서버를
완전히 재시작하기 전까지는 계속 빈 값으로 남아있어서 Slack 대신 콘솔로만 출력되는
사고가 있었습니다. os.getenv를 호출 시점마다 다시 읽도록 바꿨습니다. (그래도 .env를
새로 반영하려면 서버 재시작은 필요합니다.)

[★ 패치 (2026-07) #2 — print에 flush=True 추가 + 진행상황 로그 추가]
uvicorn --reload는 Windows에서 자식 프로세스를 파이프로 띄우는 구조라, flush 없는
평범한 print()가 콘솔에 안 보이거나 한참 뒤에야 보이는 경우가 있었습니다(위험도
CRITICAL 판정에 실제로는 도달했는데도 콘솔에 아무 것도 안 뜨는 것처럼 보이던 문제).
모든 print에 flush=True를 붙이고, Slack 전송 시도/응답 상태도 로그로 남겨서 "코드가
어디까지 실행됐는지"를 콘솔만 보고도 바로 알 수 있게 했습니다.

[★ 보안 주의] 이 파일에는 절대 실제 Slack Webhook URL을 직접 적지 마세요. 이 파일은
git에 커밋되는 소스 코드라서, 여기 적으면 실제 웹훅 주소가 저장소에 그대로 노출됩니다.
반드시 .env 파일에만 넣으세요 (.env는 .gitignore로 이미 git 추적에서 제외돼 있습니다).
"""
import json
import os
import urllib.request


def _slack_webhook_url() -> str:
    """호출 시점마다 최신 환경변수를 읽습니다. (모듈 임포트 시점에 값을 고정해두지 않음)
    ★ 절대 여기에 실제 URL을 하드코딩하지 마세요 — .env에만 넣으세요."""
    return os.getenv("SLACK_WEBHOOK_URL", "")


def send_alert(text: str) -> dict:
    """알림 한 건 보내기. Slack 주소가 있으면 슬랙으로, 없으면 콘솔로."""
    slack_url = _slack_webhook_url()
    if not slack_url:
        print("[ALERT]", text, flush=True)        # 주소 없을 때: 그냥 출력
        return {"ok": True, "via": "console"}

    print(f"[ALERT] Slack으로 전송 시도 중... (URL 앞 30자: {slack_url[:30]}...)", flush=True)
    data = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(slack_url, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f"[ALERT] Slack 응답 status={resp.status}", flush=True)
            return {"ok": resp.status == 200, "via": "slack"}
    except Exception as e:
        print("[ALERT-ERROR]", e, flush=True)
        return {"ok": False, "error": str(e)}


def alert_critical(entry: dict):
    """고위험(HIGH 이상) BLOCK/NEED_APPROVAL 로그가 들어오면 보기 좋게 만들어 알림을 보냅니다.
    (★ 병합 2026-07: 예전엔 risk_level=CRITICAL 일 때만 호출됐지만, 지금은 agent_service._process_action이
    'decision이 BLOCK/NEED_APPROVAL 이면서 risk_level이 HIGH 이상'일 때 이 함수를 호출합니다.
    함수 이름은 호환성을 위해 그대로 두었습니다.)"""
    print(f"[ALERT] alert_critical() 호출됨 — risk_level={entry.get('risk_level')} "
          f"score={entry.get('risk_score')}", flush=True)
    text = (f"[CRITICAL] {entry.get('decision')} | "
            f"{entry.get('tool')} | 사용자={entry.get('user')} | "
            f"점수={entry.get('risk_score')} | {entry.get('user_input')}")
    return send_alert(text)
