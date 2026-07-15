#!/bin/bash
# mock 소스(src 스키마) 읽기 권한 — extract 로더가 PCS_SRC_USER(=dbt 롤)로 접속해 읽는다.
set -euo pipefail

psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<EOSQL
GRANT USAGE ON SCHEMA src TO ${PCS_DBT_USER};
GRANT SELECT ON ALL TABLES IN SCHEMA src TO ${PCS_DBT_USER};
EOSQL
