#!/bin/bash
# warehouse 초기화 — 계층 스키마 + 롤/권한 (최초 기동 시 1회 실행, → design/02 권한 원칙, 명명 → design/10)
#  - 파이프라인 롤(PCS_DBT_USER): brz~gld·sbx·ctl 쓰기 (extract + dbt 실행 계정)
#  - 분석가 롤(PCS_ANALYST_USER): sbx 쓰기 / slv·gld 읽기 + statement_timeout. ctl 접근 불가.
# 시크릿은 컨테이너 env(.env 유래)로만 받는다 — 이 파일에 하드코딩 금지.
set -euo pipefail

psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<EOSQL
-- 롤
CREATE ROLE ${PCS_DBT_USER} LOGIN PASSWORD '${PCS_DBT_PASSWORD}';
CREATE ROLE ${PCS_ANALYST_USER} LOGIN PASSWORD '${PCS_ANALYST_PASSWORD}';
ALTER ROLE ${PCS_ANALYST_USER} SET statement_timeout = '5min';

-- 계층 스키마 (brz/slv/gld + sbx 실험 + ctl 제어)
CREATE SCHEMA brz AUTHORIZATION ${PCS_DBT_USER};
CREATE SCHEMA slv AUTHORIZATION ${PCS_DBT_USER};
CREATE SCHEMA gld AUTHORIZATION ${PCS_DBT_USER};
CREATE SCHEMA sbx AUTHORIZATION ${PCS_DBT_USER};
CREATE SCHEMA ctl AUTHORIZATION ${PCS_DBT_USER};

-- 분석가: sbx 쓰기 / slv·gld 읽기 (brz·ctl 은 접근 불가)
GRANT USAGE, CREATE ON SCHEMA sbx TO ${PCS_ANALYST_USER};
GRANT USAGE ON SCHEMA slv, gld TO ${PCS_ANALYST_USER};
ALTER DEFAULT PRIVILEGES FOR ROLE ${PCS_DBT_USER} IN SCHEMA slv
    GRANT SELECT ON TABLES TO ${PCS_ANALYST_USER};
ALTER DEFAULT PRIVILEGES FOR ROLE ${PCS_DBT_USER} IN SCHEMA gld
    GRANT SELECT ON TABLES TO ${PCS_ANALYST_USER};
EOSQL
