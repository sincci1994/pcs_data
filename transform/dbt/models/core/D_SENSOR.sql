-- 센서 차원 (상/하한 포함)
SELECT
    STD_SENSOR_ID AS SENSOR_KEY,
    STD_SENSOR_ID,
    STD_EQP_ID    AS EQP_KEY,
    SENSOR_NM,
    UNIT,
    HI_LIMIT,
    LO_LIMIT
FROM {{ ref('S_SENSOR') }}
