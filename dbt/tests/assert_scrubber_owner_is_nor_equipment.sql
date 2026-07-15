-- 레거시 02 검증(A) 이식: SCRUBBER 의 소속(main)이 소유(NOR) 설비와 일치하는가.
-- Pair 구조 소속 비결정은 전역 FK 로 못 잡는다 — 위반 행이 있으면 테스트 실패.
select e.code, e.main_equipment_code
from {{ ref('dim_equipment') }} e
where e.type_code = 'SCRUBBER'
  and exists (
      select 1 from {{ ref('stg_ees__portmaster2') }} r
      where r.seqp_id || r.seqp_ch = e.code and r.eqp_posn = 'NOR'
  )
  and not exists (
      select 1 from {{ ref('stg_ees__portmaster2') }} r
      where r.seqp_id || r.seqp_ch = e.code
        and r.eqp_posn = 'NOR'
        and r.eqp_id = e.main_equipment_code
  )
