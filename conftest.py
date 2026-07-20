"""
conftest.py (공통)
프로젝트 루트를 sys.path에 넣어 'app' 패키지를 어디서 pytest를 실행해도 찾게 합니다.
테스트용 임시 SQLite 파일을 쓰도록 환경변수도 여기서 맞춰줍니다.
"""
import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 테스트가 실제 data/firewall.db를 더럽히지 않도록 임시 DB 경로 사용
os.environ.setdefault("FIREWALL_DB", os.path.join(ROOT_DIR, "data", "test_firewall.db"))
