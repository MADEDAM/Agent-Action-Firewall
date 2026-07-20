"""
incident_report.py   (담당: 김나형)

[이 파일이 하는 일]
저장된 로그를 모아 '사고 요약 리포트'를 만듭니다.
예: 오늘 차단 몇 건, 위험도 분포, 가장 위험했던 사건 목록.

[왜 필요한가]
발표나 보고 때 "그래서 무슨 일이 있었는데?"를 한 장으로 보여주는 게 사고 리포트입니다.
대시보드의 'Incident Report' 화면이 이 함수 결과를 그립니다.
"""
from ..logs import log_service


def build_report():
    """로그를 분석해 리포트 dict 를 돌려줍니다."""
    logs = log_service.get_logs(limit=10000)
    stats = log_service.get_stats()

    # 위험했던(차단/승인대기) 사건만 추려서 최근 10건
    incidents = [x for x in logs if x["decision"] in ("BLOCK", "NEED_APPROVAL")][:10]

    # 행동 종류별 건수
    by_action = {}
    for x in logs:
        by_action[x["action_type"]] = by_action.get(x["action_type"], 0) + 1

    return {
        "summary": {
            "총_요청": stats["total"],
            "차단": stats["blocked"],
            "승인대기": stats["pending"],
            "마스킹": stats["masked"],
        },
        "위험도_분포": stats["by_risk"],
        "행동종류별": by_action,
        "주요_사건": incidents,
    }
