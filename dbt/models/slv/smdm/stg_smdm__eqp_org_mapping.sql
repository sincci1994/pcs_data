-- 설비→조직 매핑의 slv 인터페이스. v1 원천 = 더미 시드.
-- 모델명이 미래 소스(SMDM) 축인 이유: 실연동 시 원천만 seed → source(extract 적재분)로
-- 교체하면 하류(gld)가 자동 재정의된다 — 소스 변경 흡수 계층.
--
-- 컬럼: eqp_id(메인설비 ID, 유일키) / team_code(팀) / division_code(사업부)
--       / site_code(사이트) / line_code(라인) / area_code(공정 영역)
select
    eqp_id,
    team_code,
    division_code,
    site_code,
    line_code,
    area_code
from {{ ref('seed_eqp_org_mapping') }}
