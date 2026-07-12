#!/usr/bin/env bash
# [로컬 실습 전용] EES 목킹 소유자(src)·서빙 소유자(pcs_srv) 생성 — 빈 oracle-data 볼륨 첫 부팅 1회.
# 실 EES/서빙 Oracle 에는 해당 없음 (계정은 DBA 발급 — → design/09 §34).
set -euo pipefail

sqlplus -s system/"$ORACLE_PASSWORD"@localhost/FREEPDB1 <<EOF
WHENEVER SQLERROR EXIT SQL.SQLCODE
CREATE USER src IDENTIFIED BY "$PCS_ORA_SRC_PASSWORD" QUOTA UNLIMITED ON users;
GRANT CREATE SESSION, CREATE TABLE TO src;
CREATE USER pcs_srv IDENTIFIED BY "$PCS_ORA_SRV_PASSWORD" QUOTA UNLIMITED ON users;
GRANT CREATE SESSION, CREATE TABLE TO pcs_srv;
EOF
echo "PCS: src / pcs_srv 사용자 생성 완료"
