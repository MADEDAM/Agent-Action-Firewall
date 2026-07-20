"""
config.py  (공통)

[이 파일이 하는 일]
프로젝트 전체에서 쓰는 '설정값'을 한곳에 모읍니다.
비밀값(슬랙 주소 등)은 .env 파일이나 환경변수로 넣고, 여기서는 os.getenv 로 읽어옵니다.
★ 비밀값을 코드에 직접 적지 마세요. (GitHub에 올라가면 큰일납니다)
"""
import os

# 로그를 저장할 SQLite 파일 위치
FIREWALL_DB = os.getenv("FIREWALL_DB", "data/firewall.db")

# 슬랙 알림 주소 (없으면 알림은 콘솔 출력으로 대체)
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

# Critical 위험이 뜨면 자동으로 알림을 보낼지
ALERT_ON_CRITICAL = os.getenv("ALERT_ON_CRITICAL", "true").lower() == "true"
