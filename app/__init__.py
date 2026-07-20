"""
app 패키지 초기화.

.env 파일이 있으면 자동으로 읽어 환경변수로 로딩합니다 (python-dotenv, requirements.txt에 이미 포함).
'app.무엇이든'을 import하는 모든 진입점(main.py, dashboard/streamlit_app.py, poc 스크립트 등)은
반드시 이 파일을 먼저 거치므로, 여기 한 곳에만 넣어두면 어디서 실행하든 .env 값이 적용됩니다.

★ 실제 키(SLACK_WEBHOOK_URL, AWS 자격증명 등)는 .env 파일에만 적으세요.
  .env는 .gitignore에 이미 포함되어 있어 git에는 절대 올라가지 않습니다.
  값을 채우는 방법은 프로젝트 루트의 .env.example 참고.

[★ 패치 (2026-07) #1] python-dotenv가 아직 설치 안 된 환경에서도 서버 전체가 죽지 않도록,
import 실패 시 조용히 건너뛰고 안내 메시지만 남깁니다.

[★ 패치 (2026-07) #2] load_dotenv()를 인자 없이 부르면 'python-dotenv가 알아서 .env를 찾는'
방식에 의존하게 되는데, 실행 위치나 인코딩(특히 Windows에서 메모장/일부 에디터가 저장하는
UTF-8 BOM)에 따라 못 찾거나 못 읽는 경우가 있었습니다. 그래서 이 파일의 위치를 기준으로
'프로젝트 루트/.env' 경로를 직접 계산해서 넘겨주고, utf-8-sig(=BOM이 있어도 자동으로 제거)로
읽도록 명시했습니다 — 실행 방법·인코딩과 무관하게 항상 같은 파일을 찾습니다.
"""
import os

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENV_PATH = os.path.join(_PROJECT_ROOT, ".env")

try:
    from dotenv import load_dotenv
    if os.path.exists(_ENV_PATH):
        load_dotenv(_ENV_PATH, encoding="utf-8-sig")
        print(f"[app] .env loaded: {_ENV_PATH}")
    else:
        print(f"[app] .env not found ({_ENV_PATH}) - using default environment values.")
except ImportError:
    print("[app] python-dotenv is not installed; skipping .env auto-load.")
    print("[app] Install with: pip install -r requirements.txt or pip install python-dotenv")
    print("[app] Until then, set environment variables manually.")
