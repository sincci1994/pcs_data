"""Postgres 접속 + ctl 기록 헬퍼 — 소스({prefix}_*)·warehouse(PCS_WH_*) 공용.

크리덴셜은 전부 컨테이너 env 로만 받는다 — 하드코딩 금지.
실서버의 대용량 Oracle 소스는 파이썬 로더가 아니라 Spark job 담당(→ spark/jobs/) —
그래서 이 모듈은 postgres 전용이다. 여기의 소스 접속은 로컬 mock(src 스키마)용.
"""
import os
from contextlib import contextmanager

import psycopg2


@contextmanager
def connect(prefix: str, readonly: bool = False):
    """{prefix}_HOST/PORT/DB/USER/PASSWORD 로 접속."""
    conn = psycopg2.connect(
        host=os.environ[f"{prefix}_HOST"],
        port=int(os.environ.get(f"{prefix}_PORT", "5432")),
        dbname=os.environ[f"{prefix}_DB"],
        user=os.environ[f"{prefix}_USER"],
        password=os.environ[f"{prefix}_PASSWORD"],
    )
    if readonly:
        conn.set_session(readonly=True)
    try:
        yield conn
    finally:
        conn.close()  # 미커밋 트랜잭션은 close 시 rollback


@contextmanager
def wh_conn(autocommit: bool = False):
    """warehouse 접속 (dbt 실행 롤 재사용). 기본은 명시적 트랜잭션 — 멱등 적재는 단일 tx."""
    conn = psycopg2.connect(
        host=os.environ["PCS_WH_HOST"],
        port=int(os.environ.get("PCS_WH_PORT", "5432")),
        dbname=os.environ["PCS_WH_DB"],
        user=os.environ["PCS_DBT_USER"],
        password=os.environ["PCS_DBT_PASSWORD"],
    )
    conn.autocommit = autocommit
    try:
        yield conn
    finally:
        conn.close()


def fetch_columns(prefix: str, schema: str, table: str) -> set:
    """소스 딕셔너리의 실제 컬럼 집합 (pre-flight 계약 체크용) — 소문자로 통일해 반환."""
    sql = ("SELECT column_name FROM information_schema.columns "
           "WHERE table_schema = %s AND table_name = %s")
    with connect(prefix, readonly=True) as conn, conn.cursor() as cur:
        cur.execute(sql, (schema, table))
        return {r[0].lower() for r in cur.fetchall()}


def fetch_chunks(conn, sql: str, chunk: int, name: str):
    """SELECT 를 chunk 단위 rows 로 스트리밍 — server-side named cursor."""
    cur = conn.cursor(name=name)
    cur.itersize = chunk
    cur.execute(sql)
    try:
        while True:
            rows = cur.fetchmany(chunk)
            if not rows:
                return
            yield rows
    finally:
        cur.close()


def audit_start(dag_id: str, logical_date, run_id: str) -> None:
    """run 단위 감사 시작 기록 — dag_id+logical_date 유니크, 재시도는 갱신."""
    with wh_conn(autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO ctl.job_audit (dag_id, logical_date, run_id, status, started_at)
            VALUES (%s, %s, %s, 'running', now())
            ON CONFLICT (dag_id, logical_date)
            DO UPDATE SET run_id = EXCLUDED.run_id, status = 'running',
                          started_at = now(), finished_at = NULL, detail = NULL
            """,
            (dag_id, logical_date, run_id),
        )


def audit_finish(dag_id: str, logical_date, status: str, row_count=None, detail=None) -> None:
    with wh_conn(autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE ctl.job_audit
            SET status = %s, row_count = %s, finished_at = now(), detail = %s
            WHERE dag_id = %s AND logical_date = %s
            """,
            (status, row_count, detail, dag_id, logical_date),
        )
