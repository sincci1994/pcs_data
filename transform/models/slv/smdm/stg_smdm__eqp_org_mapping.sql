-- 설비→조직 매핑의 slv 인터페이스. v1 원천 = 더미 시드 (→ design/09 확정 2).
-- 모델명이 미래 소스(SMDM) 축인 이유: 실연동 시 원천만 seed → source(extract 적재분)로
-- 교체하면 하류(gld)가 자동 재정의된다 — 소스 변경 흡수 계층 (→ design/07·10).
select
    eqp_id,
    team_code,
    division_code,
    site_code,
    line_code,
    area_code
from {{ ref('seed_eqp_org_mapping') }}
