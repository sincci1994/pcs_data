-- 설비 마스터 표준화 (원천값 SRC_* + 표준값 STD_* 병행 보관)
SELECT
    EQP_ID        AS SRC_EQP_ID,
    EQP_ID        AS STD_EQP_ID,
    EQP_NM,
    LINE_CD       AS SRC_LINE_CD,
    LINE_CD       AS STD_LINE_CD,
    MODEL_CD,
    USE_YN
FROM {{ source('lnd', 'L_SCADA_EQP') }}
