"""
SCADA(원천) → PCS_LND 추출 callable 모음 + PCS_CTL 통제 로깅.

Airflow OracleHook(oracle_pcs 커넥션, PCS_ETL 유저)을 사용한다.
PythonOperator 는 Airflow 2 에서 callable 의 **kwargs 로 실행 컨텍스트를 자동 주입하므로
각 함수는 **context 로 run_id / data_interval 등을 받는다.
"""
from airflow.providers.oracle.hooks.oracle import OracleHook

CONN_ID = "oracle_pcs"
SRC_SYS = "SCADA"


def _hook():
    return OracleHook(oracle_conn_id=CONN_ID)


# --------------------------------------------------------------------- CTL
def ctl_start(**context):
    """C_JOB_RUN 에 실행 시작 기록."""
    hook = _hook()
    hook.run(
        """INSERT INTO PCS_CTL.C_JOB_RUN (RUN_ID, DAG_ID, TASK_ID, STATE, START_TS)
           VALUES (:1, :2, :3, 'RUNNING', SYSTIMESTAMP)""",
        parameters=[context["run_id"], context["dag"].dag_id, "ctl_start"],
    )


def ctl_end(**context):
    """C_JOB_RUN 에 완료 기록 + LND 적재 건수 집계."""
    hook = _hook()
    cnt = hook.get_first(
        "SELECT COUNT(*) FROM PCS_LND.L_SCADA_TRACE WHERE LOAD_ID = :1",
        parameters=[context["run_id"]],
    )[0]
    hook.run(
        """INSERT INTO PCS_CTL.C_JOB_RUN (RUN_ID, DAG_ID, TASK_ID, STATE, END_TS, ROW_CNT)
           VALUES (:1, :2, :3, 'SUCCESS', SYSTIMESTAMP, :4)""",
        parameters=[context["run_id"], context["dag"].dag_id, "ctl_end", cnt],
    )


# ----------------------------------------------------------------- EXTRACT
def extract_masters(**context):
    """설비/센서 마스터 스냅샷을 PCS_LND 로 재적재(TRUNCATE→INSERT)."""
    hook = _hook()
    load_id = context["run_id"]
    hook.run("TRUNCATE TABLE PCS_LND.L_SCADA_EQP")
    hook.run(
        """INSERT INTO PCS_LND.L_SCADA_EQP (EQP_ID, EQP_NM, LINE_CD, MODEL_CD, USE_YN, LOAD_ID)
           SELECT EQP_ID, EQP_NM, LINE_CD, MODEL_CD, USE_YN, :1 FROM SRC_SCADA.EQP_MST""",
        parameters=[load_id],
    )
    hook.run("TRUNCATE TABLE PCS_LND.L_SCADA_SENSOR")
    hook.run(
        """INSERT INTO PCS_LND.L_SCADA_SENSOR
             (SENSOR_ID, EQP_ID, SENSOR_NM, UNIT, HI_LIMIT, LO_LIMIT, LOAD_ID)
           SELECT SENSOR_ID, EQP_ID, SENSOR_NM, UNIT, HI_LIMIT, LO_LIMIT, :1
           FROM SRC_SCADA.SENSOR_MST""",
        parameters=[load_id],
    )


def extract_trace(**context):
    """Watermark 기반 증분 추출: 마지막 적재 이후의 trace 만 PCS_LND 로 적재."""
    hook = _hook()
    load_id = context["run_id"]

    # 1) 워터마크 이후 데이터만 적재
    hook.run(
        """INSERT INTO PCS_LND.L_SCADA_TRACE
             (EQP_ID, SENSOR_ID, MEAS_TS, MEAS_VAL, STATUS_CD, LOAD_ID, SRC_SYS, INGESTED_AT)
           SELECT t.EQP_ID, t.SENSOR_ID, t.MEAS_TS, t.MEAS_VAL, t.STATUS_CD,
                  :1, 'SCADA', SYSTIMESTAMP
           FROM SRC_SCADA.TRACE_RAW t
           WHERE t.MEAS_TS > (
                 SELECT LAST_LOADED_TS FROM PCS_CTL.C_SOURCE_WATERMARK
                 WHERE SRC_SYS = :2 AND SRC_OBJ = 'TRACE_RAW')""",
        parameters=[load_id, SRC_SYS],
    )

    # 2) 워터마크를 이번에 적재한 최대 MEAS_TS 로 전진
    hook.run(
        """UPDATE PCS_CTL.C_SOURCE_WATERMARK w
           SET w.LAST_LOADED_TS = (
                 SELECT NVL(MAX(MEAS_TS), w.LAST_LOADED_TS)
                 FROM PCS_LND.L_SCADA_TRACE WHERE LOAD_ID = :1)
           WHERE w.SRC_SYS = :2 AND w.SRC_OBJ = 'TRACE_RAW'""",
        parameters=[load_id, SRC_SYS],
    )
