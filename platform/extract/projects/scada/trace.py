"""SCADA trace 증분 추출(Watermark 기반) → PCS_LND."""
from __future__ import annotations

from common.control.ctl import WatermarkStore

from .scada_base import SRC_SYS, connector

_LND_TRACE = "PCS_LND.L_SCADA_TRACE"


def extract_trace(**context) -> None:
    """마지막 적재 이후의 trace 만 PCS_LND 로 적재하고 워터마크를 전진."""
    c = connector()
    load_id = context["run_id"]

    # 1) 워터마크 이후 데이터만 적재
    c.execute(
        """INSERT INTO PCS_LND.L_SCADA_TRACE
             (EQP_ID, SENSOR_ID, MEAS_TS, MEAS_VAL, STATUS_CD, LOAD_ID, SRC_SYS, INGESTED_AT)
           SELECT t.EQP_ID, t.SENSOR_ID, t.MEAS_TS, t.MEAS_VAL, t.STATUS_CD,
                  :1, 'SCADA', SYSTIMESTAMP
           FROM SRC_SCADA.TRACE_RAW t
           WHERE t.MEAS_TS > (
                 SELECT LAST_LOADED_TS FROM PCS_CTL.C_SOURCE_WATERMARK
                 WHERE SRC_SYS = :2 AND SRC_OBJ = 'TRACE_RAW')""",
        [load_id, SRC_SYS],
    )

    # 2) 워터마크를 이번에 적재한 최대 MEAS_TS 로 전진
    WatermarkStore(c).advance_from_lnd(
        src_sys=SRC_SYS,
        src_obj="TRACE_RAW",
        lnd_table=_LND_TRACE,
        load_id=load_id,
    )
