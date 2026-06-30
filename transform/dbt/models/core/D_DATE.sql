-- 날짜 차원 (trace 에 등장하는 날짜로 구성)
SELECT DISTINCT
    TO_NUMBER(TO_CHAR(MEAS_TS, 'YYYYMMDD')) AS DATE_KEY,
    TRUNC(MEAS_TS)                          AS CAL_DATE,
    EXTRACT(YEAR  FROM MEAS_TS)             AS YEAR_NO,
    EXTRACT(MONTH FROM MEAS_TS)             AS MONTH_NO,
    EXTRACT(DAY   FROM MEAS_TS)             AS DAY_NO
FROM {{ ref('S_SENSOR_TRACE_H') }}
