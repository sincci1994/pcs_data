"""크로스 DB 접속 디스패치 — 소스(PCS_SRC)·서빙(PCS_SRV) 끝점 전용. warehouse/ctl 은 pg.py.

드라이버는 env 로만 선택: {prefix}_DRIVER = postgres(기본) | oracle — 코드·선언(sources.yml,
publish_to)은 로컬-postgres / 로컬-oracle(practice-oracle 프로파일) / 원격-EES 에서 동일하다.

Oracle 주의:
  - 비인용 식별자는 대문자 폴딩 — 이 모듈과 호출자는 항상 비인용 식별자만 쓴다.
  - VARCHAR2 의 '' 는 NULL 과 동치 (소비 측 의미 차이 → design/08).
  - thin 모드 기본(Oracle Free 23ai·12.1+ 충분). 실 EES 에서 thick 필요 시
    PCS_ORACLE_THICK=1 → init_oracle_client() (Instant Client 는 이미지 베이크, → design/05).
"""
import os
from contextlib import contextmanager

import psycopg2

_DRIVERS = {"postgres", "oracle"}
_thick_done = False


def driver(prefix: str) -> str:
    d = os.environ.get(f"{prefix}_DRIVER", "postgres")
    if d not in _DRIVERS:
        raise ValueError(f"{prefix}_DRIVER 미지원 값: {d!r} (postgres|oracle)")
    return d


def _oracledb():
    global _thick_done
    import oracledb
    if os.environ.get("PCS_ORACLE_THICK") and not _thick_done:
        oracledb.init_oracle_client()
        _thick_done = True
    return oracledb


@contextmanager
def connect(prefix: str, readonly: bool = False):
    """{prefix}_HOST/PORT/DB/USER/PASSWORD 로 접속. oracle 은 _DB 를 서비스명으로 사용.
    readonly 는 postgres 만 세션 설정 — oracle 소스 계정은 SELECT 권한만 갖는 것으로 갈음."""
    drv = driver(prefix)
    host = os.environ[f"{prefix}_HOST"]
    dbname = os.environ[f"{prefix}_DB"]
    user = os.environ[f"{prefix}_USER"]
    password = os.environ[f"{prefix}_PASSWORD"]
    if drv == "postgres":
        conn = psycopg2.connect(
            host=host, port=int(os.environ.get(f"{prefix}_PORT", "5432")),
            dbname=dbname, user=user, password=password,
        )
        if readonly:
            conn.set_session(readonly=True)
    else:
        port = os.environ.get(f"{prefix}_PORT", "1521")
        conn = _oracledb().connect(user=user, password=password, dsn=f"{host}:{port}/{dbname}")
    try:
        yield conn
    finally:
        conn.close()  # 미커밋 트랜잭션은 양쪽 드라이버 모두 close 시 rollback


def fetch_columns(prefix: str, schema: str, table: str) -> set:
    """소스 딕셔너리의 실제 컬럼 집합 (pre-flight 계약 체크용) — 소문자로 통일해 반환."""
    if driver(prefix) == "postgres":
        sql = ("SELECT column_name FROM information_schema.columns "
               "WHERE table_schema = %s AND table_name = %s")
    else:
        sql = ("SELECT column_name FROM all_tab_columns "
               "WHERE owner = UPPER(:1) AND table_name = UPPER(:2)")
    with connect(prefix, readonly=True) as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, (schema, table))
            return {r[0].lower() for r in cur.fetchall()}
        finally:
            cur.close()


def fetch_chunks(conn, prefix: str, sql: str, chunk: int, name: str):
    """SELECT 를 chunk 단위 rows 로 스트리밍 (규칙 3: 크로스 DB 는 chunked fetch + bulk insert).
    postgres = server-side named cursor / oracle = arraysize 커서 + 비문자열 값 str 강제
    (브론즈는 all-text — psycopg2 는 숫자→text 암묵 캐스팅을 하지 않는다)."""
    if driver(prefix) == "postgres":
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
    else:
        cur = conn.cursor()
        cur.arraysize = chunk
        cur.prefetchrows = chunk + 1
        cur.execute(sql)
        try:
            while True:
                rows = cur.fetchmany(chunk)
                if not rows:
                    return
                yield [
                    tuple(v if (v is None or isinstance(v, str)) else str(v) for v in row)
                    for row in rows
                ]
        finally:
            cur.close()
