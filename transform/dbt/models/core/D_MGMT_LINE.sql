-- 관리 라인 차원 (우리팀 관점). 시스템 라인 여러 개 → 관리 라인 1개 (비즈니스 재해석)
SELECT DISTINCT
    MGMT_LINE_CD AS MGMT_LINE_KEY,
    MGMT_LINE_CD,
    MGMT_LINE_NM
FROM {{ ref('mgmt_line_map') }}
