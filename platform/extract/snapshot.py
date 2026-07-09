"""범용 전량 스냅샷 로더 — sources.yml 선언으로 구동 (mode: snapshot).

멱등성 = warehouse 단일 트랜잭션 delete+insert (재시도가 중복 행을 만들면 실패 — 규칙 1).
소스 드라이버: 로컬 검증 = Postgres. 원격 실 EES(Oracle)는 python-oracledb 접속·
ALL_TAB_COLUMNS 계약 체크 분기 추가 필요 (이미지에 드라이버 베이크, → design/05 체크리스트 7).
mode: watermark(증분+lookback)는 선언만 예약 — 센서 시나리오(design/06) 재개 시 구현.
"""
import logging

import psycopg2.extras

from common import pg

log = logging.getLogger("pcs.extract.snapshot")

FETCH_CHUNK = 10_000


def _column_types_ddl(columns: list) -> str:
    # bronze 는 원형 보존 계층 — 소스 타입 정밀도 대신 텍스트 수용 (해석은 slv 의 몫)
    cols = ",\n        ".join(f"{c} text" for c in columns)
    return cols


def load(source_name: str, src: dict, dag_id: str, logical_date, run_id: str) -> int:
    """계약 체크 → 전량 적재 → 워터마크·감사 — 전부 승계된 불변조건대로."""
    columns = src.get("select_columns", src["expected_columns"])
    schema, table = src["table"].split(".")
    target = src["target"]

    # pre-flight 계약 체크 (조용한 드리프트 금지, → design/08 §6)
    with pg.src_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = %s AND table_name = %s",
            (schema, table),
        )
        actual = {r[0] for r in cur.fetchall()}
    if not actual:
        raise RuntimeError(f"소스 테이블 부재: {src['table']}")
    missing = set(src["expected_columns"]) - actual
    if missing:
        raise RuntimeError(f"스키마 계약 위반 — 소스에 없는 기대 컬럼: {sorted(missing)}")
    log.info("계약 체크 통과: %s 컬럼 %d개", src["table"], len(src["expected_columns"]))

    select_sql = f"SELECT {', '.join(columns)} FROM {src['table']}"
    if src.get("filter"):
        select_sql += f" WHERE {src['filter']}"
    insert_sql = f"INSERT INTO {target} ({', '.join(columns)}) VALUES %s"
    ddl = (
        f"CREATE TABLE IF NOT EXISTS {target} (\n        "
        f"{_column_types_ddl(columns)},\n        "
        f"loaded_at timestamptz NOT NULL DEFAULT now()\n    )"
    )

    pg.audit_start(dag_id, logical_date, run_id)
    try:
        with pg.src_conn() as sconn, pg.wh_conn() as wconn:
            scur = sconn.cursor(name=f"{source_name}_fetch")   # server-side cursor
            scur.itersize = FETCH_CHUNK
            scur.execute(select_sql)

            with wconn.cursor() as wcur:
                wcur.execute(ddl)
                wcur.execute(f"DELETE FROM {target}")
                total = 0
                while True:
                    rows = scur.fetchmany(FETCH_CHUNK)
                    if not rows:
                        break
                    psycopg2.extras.execute_values(wcur, insert_sql, rows, page_size=FETCH_CHUNK)
                    total += len(rows)

                # 빈 스냅샷 방어: 소스 0행이면 기존 bronze 를 지우지 않고 실패시킨다
                if total == 0:
                    raise RuntimeError("소스 스냅샷 0행 — 적재 중단(기존 bronze 보존)")

                wcur.execute(
                    """
                    INSERT INTO ctl.watermark (source_name, table_name, last_loaded_at)
                    VALUES (%s, %s, now())
                    ON CONFLICT (source_name, table_name)
                    DO UPDATE SET last_loaded_at = now()
                    """,
                    (source_name, target),
                )
            wconn.commit()
        pg.audit_finish(dag_id, logical_date, "success", row_count=total)
        log.info("%s 적재 완료: %d행", target, total)
        return total
    except Exception as exc:
        pg.audit_finish(dag_id, logical_date, "failed", detail=str(exc)[:2000])
        raise
