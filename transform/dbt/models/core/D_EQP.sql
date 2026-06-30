-- 설비 차원
SELECT
    STD_EQP_ID    AS EQP_KEY,
    STD_EQP_ID,
    EQP_NM,
    MODEL_CD,
    STD_LINE_CD   AS LINE_KEY
FROM {{ ref('S_EQP') }}
