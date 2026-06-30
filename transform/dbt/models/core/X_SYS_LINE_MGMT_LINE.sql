-- 시스템라인 → 관리라인 Bridge (N:1). SLV 가 아닌 CORE 에서 관리(비즈니스 재해석).
SELECT
    SYS_LINE_CD  AS LINE_KEY,
    MGMT_LINE_CD AS MGMT_LINE_KEY
FROM {{ ref('mgmt_line_map') }}
