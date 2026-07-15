-- 설비→조직 매핑의 slv 인터페이스. v1 원천 = 더미 시드 (→ design/09 확정 2).
-- 모델명이 미래 소스(SMDM) 축인 이유: 실연동 시 원천만 seed → source(extract 적재분)로
-- 교체하면 하류(gld)가 자동 재정의된다 — 소스 변경 흡수 계층 (→ design/07·10).
-- 서빙: 소비 조회는 Oracle 로 통일 — SLV 도 publish (→ design/08 질의 경계).
{{ config(meta={'publish_to': 'srv.stg_smdm__eqp_org_mapping'}) }}
select
    eqp_id,
    team_code,
    division_code,
    site_code,
    line_code,
    area_code
from {{ ref('seed_eqp_org_mapping') }}
