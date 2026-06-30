-- 설비 × 센서 × 일 집계 Fact (고빈도 trace → 일별 KPI 로 Grain 확정)
WITH t AS (
    SELECT
        STD_EQP_ID,
        STD_SENSOR_ID,
        TRUNC(MEAS_TS) AS CAL_DATE,
        MEAS_VAL,
        STATUS_CD
    FROM {{ ref('S_SENSOR_TRACE_H') }}
),
lim AS (
    SELECT SENSOR_KEY, HI_LIMIT, LO_LIMIT FROM {{ ref('D_SENSOR') }}
)
SELECT
    TO_NUMBER(TO_CHAR(t.CAL_DATE, 'YYYYMMDD')) AS DATE_KEY,
    t.STD_EQP_ID                               AS EQP_KEY,
    t.STD_SENSOR_ID                            AS SENSOR_KEY,
    COUNT(*)                                   AS MEAS_CNT,
    ROUND(AVG(t.MEAS_VAL), 3)                  AS AVG_VAL,
    MIN(t.MEAS_VAL)                            AS MIN_VAL,
    MAX(t.MEAS_VAL)                            AS MAX_VAL,
    ROUND(STDDEV(t.MEAS_VAL), 3)               AS STDDEV_VAL,
    SUM(CASE WHEN t.MEAS_VAL > lim.HI_LIMIT
              OR t.MEAS_VAL < lim.LO_LIMIT THEN 1 ELSE 0 END) AS ALARM_CNT,
    ROUND(SUM(CASE WHEN t.STATUS_CD = 'RUN' THEN 1 ELSE 0 END) / COUNT(*), 4) AS UPTIME_RATIO
FROM t
JOIN lim ON t.STD_SENSOR_ID = lim.SENSOR_KEY
GROUP BY
    TO_NUMBER(TO_CHAR(t.CAL_DATE, 'YYYYMMDD')),
    t.STD_EQP_ID,
    t.STD_SENSOR_ID
