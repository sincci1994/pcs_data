"""Publish — GOLD → 서빙 전량 교체, 원자성 불변조건 (→ design/08 §3, 02 결정 ②).

소규모 기준정보 경로: 단일 트랜잭션 delete+insert — MVCC 로 소비자는 항상
완전한 직전/신규 스냅샷만 본다. 실패 시 rollback 으로 이전 상태 보존 (TRUNCATE 금지).
대규모(설비×일 grain) 윈도 교체 변형은 해당 프로덕트 등장 시 추가.
로컬 서빙 대역 = warehouse srv 스키마. 실서빙(외부 DB) 전환 시 접속만 교체 (→ design/09 미확정 3).
"""
import logging
import re

from common import pg

log = logging.getLogger("pcs.publish")

_IDENT = re.compile(r"^[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*$")


def _check_ident(name: str) -> str:
    if not _IDENT.match(name):
        raise ValueError(f"허용되지 않는 식별자: {name!r}")
    return name


def publish_full_replace(gold_relation: str, srv_relation: str, **_) -> int:
    """gold_relation(schema.table) → srv_relation 전량 교체. 0행 게이트 포함."""
    gold = _check_ident(gold_relation)
    srv = _check_ident(srv_relation)
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
