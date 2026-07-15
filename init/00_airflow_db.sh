#!/bin/bash
# Airflow 메타DB — warehouse Postgres 겸용 (로컬 실습 스택, down -v 로 전체 리셋)
set -euo pipefail

psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<EOSQL
CREATE ROLE airflow LOGIN PASSWORD 'airflow';
CREATE DATABASE airflow OWNER airflow;
EOSQL
