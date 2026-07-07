"""SCADA 소스 공통 — 커넥터 팩토리 + 상수.

extract/projects/scada/* 의 수집 콜러블이 공유한다.
현재는 Oracle OracleHook 경로(oracle_pcs)로 '동작 불변'을 유지.
"""
from __future__ import annotations

from common.connectors.oracle import OracleConnector

CONN_ID = "oracle_pcs"
SRC_SYS = "SCADA"


def connector() -> OracleConnector:
    """현 운영 경로: Airflow OracleHook(oracle_pcs) 래핑."""
    return OracleConnector.from_airflow_conn(CONN_ID)
