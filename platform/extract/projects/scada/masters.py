"""SCADA 마스터(설비/센서) 스냅샷 추출 → PCS_LND (TRUNCATE→INSERT)."""
from __future__ import annotations

from .scada_base import connector


def extract_masters(**context) -> None:
    """설비/센서 마스터 스냅샷을 PCS_LND 로 재적재."""
    c = connector()
    load_id = context["run_id"]

    c.truncate("PCS_LND.L_SCADA_EQP")
    c.execute(
        """INSERT INTO PCS_LND.L_SCADA_EQP
             (EQP_ID, EQP_NM, LINE_CD, MODEL_CD, USE_YN, LOAD_ID)
           SELECT EQP_ID, EQP_NM, LINE_CD, MODEL_CD, USE_YN, :1
           FROM SRC_SCADA.EQP_MST""",
        [load_id],
    )

    c.truncate("PCS_LND.L_SCADA_SENSOR")
    c.execute(
        """INSERT INTO PCS_LND.L_SCADA_SENSOR
             (SENSOR_ID, EQP_ID, SENSOR_NM, UNIT, HI_LIMIT, LO_LIMIT, LOAD_ID)
           SELECT SENSOR_ID, EQP_ID, SENSOR_NM, UNIT, HI_LIMIT, LO_LIMIT, :1
           FROM SRC_SCADA.SENSOR_MST""",
        [load_id],
    )
