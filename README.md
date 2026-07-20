1. 처음 한 번만 설치
Windows 기준입니다.
Node.js 설치:
Node.js LTS 설치 후 CMD에서 확인
node -v
npm -v
Python 설치 확인:
python --version
프로젝트 폴더로 이동:
cd C:\원하는위치\Agent-Action-Firewall-2026-07-05
Python 가상환경 생성 및 패키지 설치:
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
프론트엔드 패키지 설치:
cd frontend
npm install
2. 실행 방법
실행할 때는 CMD 창을 3개 열면 편합니다.
CMD 1: 백엔드 API 서버 실행
cd C:\원하는위치\Agent-Action-Firewall-2026-07-05
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
확인 주소:
http://127.0.0.1:8000/docs
CMD 2: UI 클라이언트 실행
cd C:\원하는위치\Agent-Action-Firewall-2026-07-05\frontend
npm run dev
실행 후 CMD에 뜨는 주소로 접속:
http://localhost:5173
CMD 3: 관제 대시보드 실행
cd C:\원하는위치\Agent-Action-Firewall-2026-07-05
.venv\Scripts\activate
streamlit run dashboard/streamlit_app.py
보통 자동으로 열리는 주소:
http://localhost:8501
3. 매번 실행할 때 요약
이미 설치가 끝난 뒤에는 이것만 하면 됩니다.
백엔드:
cd C:\원하는위치\Agent-Action-Firewall-2026-07-05
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
UI 클라이언트:
cd C:\원하는위치\Agent-Action-Firewall-2026-07-05\frontend
npm run dev
관제 대시보드:
cd C:\원하는위치\Agent-Action-Firewall-2026-07-05
.venv\Scripts\activate
streamlit run dashboard/streamlit_app.py
C:\원하는위치\... 부분은 팀원이 GitHub에서 받은 실제 폴더 위치로 바꾸면 됩니다.
