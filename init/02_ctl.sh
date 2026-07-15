#!/bin/bash
# ctl(운영 메타데이터) 테이블 — 최초 기동 init (01 다음 순서).
set -euo pipefail

psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<EOSQL
-- ctl.watermark: 소스×테이블 워터마크 (스냅샷 소스는 last_loaded_at 만 사용)
CREATE TABLE IF NOT EXISTS ctl.watermark (
    source_name    varchar(100) NOT NULL,
    table_name     varchar(200) NOT NULL,
    watermark_ts   timestamptz,
    last_loaded_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (source_name, table_name)
);

-- ctl.job_audit: run 단위 감사 — dag_id+logical_date 유니크, 재시도는 갱신
CREATE TABLE IF NOT EXISTS ctl.job_audit (
    dag_id       varchar(250) NOT NULL,
    logical_date timestamptz  NOT NULL,
    run_id       varchar(250),
    status       varchar(20)  NOT NULL,
    row_count    bigint,
    started_at   timestamptz  NOT NULL DEFAULT now(),
    finished_at  timestamptz,
    detail       text,
    PRIMARY KEY (dag_id, logical_date)
);

ALTER TABLE ctl.watermark OWNER TO ${PCS_DBT_USER};
ALTER TABLE ctl.job_audit OWNER TO ${PCS_DBT_USER};
EOSQL
