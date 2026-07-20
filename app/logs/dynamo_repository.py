"""
dynamo_repository.py   (담당: 김나형 + 조정우)      ★ 고급 기능 4 — boto3 실제 AWS(DynamoDB) 연동

[무슨 기능인가요? — 쉽게]
로그를 내 컴퓨터의 SQLite 대신, AWS의 클라우드 DB인 'DynamoDB'에 저장합니다.
log_repository.py 와 '같은 함수 이름'을 제공해서, 환경변수만 바꾸면 갈아끼울 수 있어요.

[켜는 법]
  pip install boto3
  환경변수: LOG_BACKEND=dynamo   AAF_LOG_TABLE=aaf_logs   AWS_REGION=ap-northeast-2
  (AWS 자격증명은 aws configure 로 설정 — 키는 코드/깃에 절대 넣지 말 것)

[★ 패치 (2026-07) — TTL(Time To Live) 자동 만료]
기획서 요구사항: "불필요한 테스트 로그 및 임시 데이터 자동 만료 처리를 통한 스토리지 최적화".
테이블 생성 직후 ttl 속성에 TTL을 걸어두고, 로그 저장 시마다 ttl(만료 시각, epoch 초)을 같이 넣습니다.
기본 보관 기간은 30일이며 AAF_LOG_TTL_DAYS 환경변수로 조절할 수 있습니다.

[중요] 이건 '선택' 기능이에요. 발표는 SQLite로도 충분합니다.
"""
import json
import os
import time

TABLE_NAME = os.getenv("AAF_LOG_TABLE", "aaf_logs")
REGION = os.getenv("AWS_REGION", "ap-northeast-2")
TTL_DAYS = int(os.getenv("AAF_LOG_TTL_DAYS", "30"))

_table = None


def _get_table():
    """DynamoDB 테이블 객체를 준비(없으면 생성)합니다. boto3가 있을 때만 동작."""
    global _table
    if _table is not None:
        return _table
    import boto3                          # 여기서 import → boto3 없어도 SQLite 모드엔 영향 없음
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    existing = [t.name for t in dynamodb.tables.all()]
    is_new_table = TABLE_NAME not in existing
    if is_new_table:
        dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[{"AttributeName": "request_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "request_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        ).wait_until_exists()
    _table = dynamodb.Table(TABLE_NAME)
    if is_new_table:
        _enable_ttl(dynamodb)
    return _table


def _enable_ttl(dynamodb):
    """테이블의 'ttl' 속성을 만료 기준으로 활성화합니다. (막 생성한 테이블에만 1번 시도)"""
    try:
        dynamodb.meta.client.update_time_to_live(
            TableName=TABLE_NAME,
            TimeToLiveSpecification={"Enabled": True, "AttributeName": "ttl"},
        )
    except Exception as e:
        # TTL 활성화 실패해도 로그 저장 자체는 계속 동작해야 하므로 조용히 경고만 남깁니다.
        print("[dynamo_repository] TTL 활성화 실패(무시하고 계속 진행):", e)


def init_db():
    """테이블 준비. (서버 시작 시 호출)"""
    _get_table()


def insert_log(row: dict):
    """로그 1건 저장. (reasons는 리스트라 문자열로 변환, ttl로 자동 만료 설정)"""
    item = dict(row)
    item["reasons"] = json.dumps(row.get("reasons", []), ensure_ascii=False)
    now = int(time.time())
    item["ts"] = now                              # 정렬용 타임스탬프
    item["ttl"] = now + TTL_DAYS * 86400           # DynamoDB TTL — 이 시각 이후 자동 삭제
    _get_table().put_item(Item=item)


def fetch_logs(decision=None, risk_level=None, action_type=None, limit=200):
    """필터에 맞는 로그를 돌려줍니다. (DynamoDB는 scan + 필터)"""
    from boto3.dynamodb.conditions import Attr
    fe = None
    for key, val in [("decision", decision), ("risk_level", risk_level), ("action_type", action_type)]:
        if val:
            cond = Attr(key).eq(val)
            fe = cond if fe is None else fe & cond
    kwargs = {"FilterExpression": fe} if fe is not None else {}
    items = _get_table().scan(**kwargs).get("Items", [])
    items.sort(key=lambda x: x.get("ts", 0), reverse=True)
    for it in items:
        if isinstance(it.get("reasons"), str):
            it["reasons"] = json.loads(it["reasons"])
        it["risk_score"] = int(it.get("risk_score", 0))
    return items[:limit]


def reset_logs():
    """대시보드 상단 카드(Total/Blocked/Need Approval/Masked)용 로그를 전부 지웁니다.
    log_repository.reset_logs()와 이름을 맞춰서, Settings 화면의 '리셋' 버튼이
    LOG_BACKEND 값과 상관없이 그대로 동작하게 합니다."""
    table = _get_table()
    items = table.scan(ProjectionExpression="request_id").get("Items", [])
    with table.batch_writer() as batch:
        for it in items:
            batch.delete_item(Key={"request_id": it["request_id"]})
