"""PCS_CTL 제어평면 — 잡 실행 로깅 + 소스 워터마크.

기존 common/oracle_etl.py 의 CTL 로직을 커넥터 기반으로 추출한 것.
관측성(Elementary 대체)의 자체 메트릭 저장소인 PCS_CTL 스키마에 기록한다.
"""
from __future__ import annotations

from common.connectors.base import StorageConnector


class JobRunLogger:
    """C_JOB_RUN 에 잡 실행 상태를 기록."""

    def __init__(self, connector: StorageConnector) -> None:
        self._c = connector

    def start(self, run_id: str, dag_id: str, task_id: str) -> None:
        self._c.execute(
            """INSERT INTO PCS_CTL.C_JOB_RUN (RUN_ID, DAG_ID, TASK_ID, STATE, START_TS)
               VALUES (:1, :2, :3, 'RUNNING', SYSTIMESTAMP)""",
            [run_id, dag_id, task_id],
        )

    def end(self, run_id: str, dag_id: str, task_id: str, row_cnt: int) -> None:
        self._c.execute(
            """INSERT INTO PCS_CTL.C_JOB_RUN
                 (RUN_ID, DAG_ID, TASK_ID, STATE, END_TS, ROW_CNT)
               VALUES (:1, :2, :3, 'SUCCESS', SYSTIMESTAMP, :4)""",
            [run_id, dag_id, task_id, row_cnt],
        )


class WatermarkStore:
    """C_SOURCE_WATERMARK 기반 증분 적재 워터마크 조회/전진."""

    def __init__(self, connector: StorageConnector) -> None:
        self._c = connector

    def advance_from_lnd(
        self,
        *,
        src_sys: str,
        src_obj: str,
        lnd_table: str,
        load_id: str,
        ts_col: str = "MEAS_TS",
    ) -> None:
        """이번 load_id 로 적재된 최대 ts 로 워터마크를 전진."""
        self._c.execute(
            f"""UPDATE PCS_CTL.C_SOURCE_WATERMARK w
                SET w.LAST_LOADED_TS = (
                      SELECT NVL(MAX({ts_col}), w.LAST_LOADED_TS)
                      FROM {lnd_table} WHERE LOAD_ID = :1)
                WHERE w.SRC_SYS = :2 AND w.SRC_OBJ = :3""",
            [load_id, src_sys, src_obj],
        )
