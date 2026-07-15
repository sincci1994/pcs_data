#!/bin/bash
# warehouse 초기화 — 계층 스키마 + 파이프라인 롤 (최초 기동 시 1회 실행)
#  - 파이프라인 롤(PCS_DBT_USER): brz~gld·sbx·ctl 쓰기 (extract + dbt 실행 계정)
# 시크릿은 컨테이너 env 로만 받는다 — 이 파일에 하드코딩 금지.
set -euo pipefail

psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<EOSQL
CREATE ROLE ${PCS_DBT_USER} LOGIN PASSWORD '${PCS_DBT_PASSWORD}';

-- 계층 스키마 (brz/slv/gld + sbx 실험 + ctl 제어)
CREATE SCHEMA brz AUTHORIZATION ${PCS_DBT_USER};
CREATE SCHEMA slv AUTHORIZATION ${PCS_DBT_USER};
CREATE SCHEMA gld AUTHORIZATION ${PCS_DBT_USER};
CREATE SCHEMA sbx AUTHORIZATION ${PCS_DBT_USER};
CREATE SCHEMA ctl AUTHORIZATION ${PCS_DBT_USER};
EOSQL
