"""Publish — 운영 산출물(slv/gld) → 서빙 전량 교체, 원자성 불변조건 (→ design/08 §3, 02 결정 ②).

소규모 기준정보 경로: 단일 트랜잭션 delete+insert — 소비자는 항상 완전한 직전/신규
스냅샷만 본다. 실패 시 rollback 으로 이전 상태 보존 (TRUNCATE 금지).
대규모(설비×일 grain) 윈도 교체 변형은 해당 프로덕트 등장 시 추가 (→ design/08 §3).

서빙 대상은 PCS_SRV_DRIVER 로 디스패치 (→ common/db.py):
  postgres(기본) = warehouse 내 srv 스키마 — 로컬 대역, PCS_SRV_* env 미사용.
  oracle         = 외부 서빙 Oracle. publish_to 의 'srv' 는 논리 네임스페이스 —
                   <PCS_SRV_USER 대문자>.<이름 대문자> 로 매핑. 테이블이 없으면
                   warehouse 타입에서 자동 생성 (DBA 사전 생성 테이블과 호환: if-missing 만).
"""
import logging
import os
import re

from common import db, pg

log = logging.getLogger("pcs.publish")

_IDENT = re.compile(r"^[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*$")
FETCH_CHUNK = 10_000


def _check_ident(name: str) -> str:
    if not _IDENT.match(name):
        raise ValueError(f"허용되지 않는 식별자: {name!r}")
    return name


def publish_full_replace(gold_relation: str, srv_relation: str, **_) -> int:
    """운영 릴레이션(schema.table|view) → 서빙 전량 교체. 0행 게이트 포함."""
    gold = _check_ident(gold_relation)
    srv = _check_ident(srv_relation)
    if db.driver("PCS_SRV") == "oracle":
        return _publish_oracle(gold, srv)
    return _publish_postgres(gold, srv)


def _publish_postgres(gold: str, srv: str) -> int:
    """같은 warehouse 내 srv 스키마로 교체 — 단일 접속·단일 트랜잭션 (MVCC 원자성)."""
    with pg.wh_conn() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT count(*) FROM {gold}")
        gold_count = cur.fetchone()[0]
        if gold_count == 0:
            raise RuntimeError(f"{gold} 0행 — publish 중단(서빙 이전 상태 보존)")

        cur.execute(f"CREATE TABLE IF NOT EXISTS {srv} (LIKE {gold} INCLUDING ALL)")
        cur.execute(f"DELETE FROM {srv}")
        cur.execute(f"INSERT INTO {srv} SELECT * FROM {gold}")
        published = cur.rowcount
        if published != gold_count:
            raise RuntimeError(f"행수 불일치 gold={gold_count} published={published}")
        conn.commit()
    log.info("publish 완료: %s → %s (%d행)", gold, srv, published)
    return published


def _ora_type(data_type: str, char_len, num_prec, num_scale) -> str:
    """Postgres information_schema data_type → Oracle 컬럼 타입. 미지원 타입은 fail-fast."""
    if data_type == "character varying":
        return f"VARCHAR2({char_len} CHAR)" if char_len else "VARCHAR2(4000 CHAR)"
    if data_type == "character":
        return f"CHAR({char_len} CHAR)" if char_len else "CHAR(1 CHAR)"
    if data_type == "text":
        return "VARCHAR2(4000 CHAR)"
    if data_type in ("smallint", "integer", "bigint"):
        return "NUMBER(19,0)"
    if data_type == "numeric":
        return f"NUMBER({num_prec},{num_scale})" if num_prec is not None else "NUMBER"
    if data_type in ("double precision", "real"):
        return "BINARY_DOUBLE"
    if data_type == "timestamp with time zone":
        return "TIMESTAMP WITH TIME ZONE"
    if data_type == "timestamp without time zone":
        return "TIMESTAMP"
    if data_type == "date":
        return "DATE"
    if data_type == "boolean":
        return "NUMBER(1)"  # 19c 이식성 — 23ai BOOLEAN 미사용
    raise ValueError(f"Oracle 타입맵 미지원 Postgres 타입: {data_type}")


def _publish_oracle(gold: str, srv: str) -> int:
    """warehouse 에서 읽어 서빙 Oracle 로 교체 — 규칙 3(chunked fetch + executemany).
    Oracle 쪽 단일 트랜잭션: DELETE → INSERT → 건수 assert → commit (실패 시 close 가 rollback)."""
    srv_schema, srv_table = srv.split(".")
    if srv_schema != "srv":
        raise ValueError(f"publish_to 는 srv.<name> 형식만 허용: {srv!r}")
    owner = os.environ["PCS_SRV_USER"].upper()
    target = f"{owner}.{srv_table.upper()}"

    with pg.wh_conn() as wconn:
        with wconn.cursor() as wcur:
            wcur.execute(f"SELECT count(*) FROM {gold}")
            gold_count = wcur.fetchone()[0]
            if gold_count == 0:
                raise RuntimeError(f"{gold} 0행 — publish 중단(서빙 이전 상태 보존)")
            g_schema, g_table = gold.split(".")
            wcur.execute(
                """
                SELECT column_name, data_type, character_maximum_length,
                       numeric_precision, numeric_scale
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
                """,
                (g_schema, g_table),
            )
            cols = wcur.fetchall()
        if not cols:
            raise RuntimeError(f"{gold} 컬럼 조회 실패 — 릴레이션 부재?")
        names = [c[0] for c in cols]
        col_list = ", ".join(names)

        with db.connect("PCS_SRV") as oconn:
            ocur = oconn.cursor()
            # 테이블 없으면 자동 생성 — Oracle DDL 은 auto-commit 이므로 DML 트랜잭션 이전에 실행
            ocur.execute(
                "SELECT count(*) FROM all_tables WHERE owner = :1 AND table_name = :2",
                (owner, srv_table.upper()),
            )
            if ocur.fetchone()[0] == 0:
                ddl_cols = ", ".join(f"{c[0]} {_ora_type(c[1], c[2], c[3], c[4])}" for c in cols)
                ocur.execute(f"CREATE TABLE {target} ({ddl_cols})")
                log.info("서빙 테이블 생성: %s", target)

            ocur.execute(f"DELETE FROM {target}")
            binds = ", ".join(f":{i + 1}" for i in range(len(names)))
            insert_sql = f"INSERT INTO {target} ({col_list}) VALUES ({binds})"
            rcur = wconn.cursor(name=f"publish_{srv_table}")
            rcur.itersize = FETCH_CHUNK
            rcur.execute(f"SELECT {col_list} FROM {gold}")
            try:
                while True:
                    rows = rcur.fetchmany(FETCH_CHUNK)
                    if not rows:
                        break
                    ocur.executemany(
                        insert_sql,
                        [tuple(int(v) if isinstance(v, bool) else v for v in r) for r in rows],
                    )
            finally:
                rcur.close()
            ocur.execute(f"SELECT count(*) FROM {target}")
            published = ocur.fetchone()[0]
            if published != gold_count:
                raise RuntimeError(f"행수 불일치 gold={gold_count} published={published}")
            oconn.commit()
    log.info("publish 완료: %s → %s (%d행)", gold, target, published)
    return published
