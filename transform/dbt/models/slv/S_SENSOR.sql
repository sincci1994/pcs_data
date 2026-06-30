-- 센서 마스터 표준화
SELECT
    SENSOR_ID     AS SRC_SENSOR_ID,
    SENSOR_ID     AS STD_SENSOR_ID,
    EQP_ID        AS SRC_EQP_ID,
    EQP_ID        AS STD_EQP_ID,
    SENSOR_NM,
    UNIT,
    HI_LIMIT,
    LO_LIMIT
FROM {{ source('lnd', 'L_SCADA_SENSOR') }}
