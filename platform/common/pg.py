"""warehouse/소스 Postgres 접속 + ctl 기록 헬퍼.

크리덴셜은 전부 컨테이너 env(.env 유래)로만 받는다 — 하드코딩·기본 비밀번호 금지.
소스가 Oracle 인 원격 환경에서는 extract 모듈이 소스 접속만 교체한다 (이 모듈은 warehouse 전용 + 로컬 목소스 겸용).
"""
import os
from contextlib import contextmanager

import psycopg2
import psycopg2.extras


def _dsn(prefix: str) -> dict:
    return {
        "host": os.environ[f"{prefix}_HOST"],
        "port": int(os.environ.get(f"{prefix}_PORT", "5432")),
        "dbname": os.environ[f"{prefix}_DB"],
        "user": os.environ[f"PCS_DBT_USER"] if prefix == "PCS_WH" else os.environ[f"{prefix}_USER"],
        "password": os.environ["PCS_DBT_PASSWORD"] if prefix == "PCS_WH" else os.environ[f"{prefix}_PASSWORD"],
    }


@contextmanager
def wh_conn(autocommit: bool = False):
    """warehouse 접속 (파이프라인 롤). 기본은 명시적 트랜잭션 — 멱등 적재는 단일 tx 로 묶는다."""
    conn = psycopg2.connect(**_dsn("PCS_WH"))
    conn.autocommit = autocommit
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def src_conn():
    """소스 접속 (로컬 검증 = warehouse 내 src 목스키마). 읽기 전용 사용.
    server-side(named) 커서는 트랜잭션을 요구하므로 autocommit 을 켜지 않는다."""
    conn = psycopg2.connect(**_dsn("PCS_SRC"))
    conn.set_session(readonly=True)
    try:
        yield conn
    finally:
        conn.close()


def audit_start(dag_id: str, logical_date, run_id: str) -> None:
    """run 단위 감사 시작 기록 — dag_id+logical_date 유니크, 재시도는 갱신 (규칙 6)."""
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
