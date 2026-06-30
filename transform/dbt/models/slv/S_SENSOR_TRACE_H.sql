-- 센서 trace 표준화 (이벤트 grain). 원천 ID 보존 + 표준 ID 부여.
-- LND 는 7일 보존이므로 full rebuild 가 부담 적음. (incremental 전환은 향후 연습 과제)
SELECT
    EQP_ID        AS SRC_EQP_ID,
    EQP_ID        AS STD_EQP_ID,
    SENSOR_ID     AS SRC_SENSOR_ID,
    SENSOR_ID     AS STD_SENSOR_ID,
    CAST(MEAS_TS AS TIMESTAMP) AS MEAS_TS,
    MEAS_VAL,
    STATUS_CD,
    SRC_SYS,
    LOAD_ID
FROM {{ source('lnd', 'L_SCADA_TRACE') }}
