-- PortMaster2 표준화 — 원천값 보존, 레거시 01 스크립트의 유효행 필터만 승계 (비즈니스 판단 없음).
-- 소스가 바뀌면 이 모델과 _ees__sources.yml 만 수정한다 — 하류(gld)는 ref() 그래프로 자동 재정의.
select distinct
    eqp_id,
    eqp_chamber_id,
    eqp_chamber_posn,
    eqp_posn,
    seqp_type,
    seqp_maker,
    seqp_model_code,
    seqp_id,
    seqp_ch,
    seqp_port
from {{ source('brz_ees', 'ees__portmaster2') }}
where eqp_id is not null
  and eqp_chamber_id is not null
  and eqp_chamber_posn is not null
  and eqp_posn is not null
  and seqp_type is not null
  and seqp_maker is not null and seqp_maker <> ''
  and seqp_id is not null and seqp_id <> ''
  and (seqp_type <> 'SCRUBBER' or seqp_ch is not null)
