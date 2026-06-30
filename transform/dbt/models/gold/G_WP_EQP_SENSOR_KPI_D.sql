-- 공식 제공 마트: 화면/리포트가 바로 SELECT 하는 일별 KPI (차원 조인 완료, 비정규화)
SELECT
    d.CAL_DATE,
    ml.MGMT_LINE_NM,
    l.STD_LINE_CD       AS SYS_LINE_CD,
    e.EQP_NM,
    se.SENSOR_NM,
    se.UNIT,
    f.MEAS_CNT,
    f.AVG_VAL,
    f.MIN_VAL,
    f.MAX_VAL,
    f.STDDEV_VAL,
    f.ALARM_CNT,
    f.UPTIME_RATIO
FROM {{ ref('F_SENSOR_DAILY') }} f
JOIN {{ ref('D_DATE') }}   d  ON f.DATE_KEY   = d.DATE_KEY
JOIN {{ ref('D_EQP') }}    e  ON f.EQP_KEY    = e.EQP_KEY
JOIN {{ ref('D_SENSOR') }} se ON f.SENSOR_KEY = se.SENSOR_KEY
JOIN {{ ref('D_LINE') }}   l  ON e.LINE_KEY   = l.LINE_KEY
JOIN {{ ref('X_SYS_LINE_MGMT_LINE') }} x ON l.LINE_KEY = x.LINE_KEY
JOIN {{ ref('D_MGMT_LINE') }} ml ON x.MGMT_LINE_KEY = ml.MGMT_LINE_KEY
