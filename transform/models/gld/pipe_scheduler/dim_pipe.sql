-- 배관 연결 엣지 6종 — 레거시 02 의 검증 완료 로직 이식. code = {from}_{to}_{chamber}.
-- NOR-only 챔버(BYP 없음)는 SS/ALLBYPASS 만 조건부 미생성 — 나머지 배관 소실 금지.
{{ config(materialized='table', meta={'publish_to': 'srv.pipe'}) }}

with pm as (
    select * from {{ ref('stg_ees__portmaster2') }}
),

org as (
    select * from {{ ref('stg_smdm__eqp_org_mapping') }}
),

-- 공정 경로 연결: pump ↔ NOR ↔ BYP 를 (설비,챔버,posn) 경로 키로 짝짓기 (카테시안 곱 방지)
chamber_connections as (
    select distinct
        pump.eqp_id,
        pump.eqp_id || '_' || pump.eqp_chamber_id || '_' || pump.eqp_chamber_posn as chamber_code,
        pump.seqp_id as pump_code,
        nor.seqp_id || nor.seqp_ch as nor_scrubber_code,
        nor.seqp_maker as nor_scrubber_maker,
        nor.seqp_id || nor.seqp_ch || '_NOR_' || nor.eqp_chamber_id || '_' || nor.eqp_chamber_posn as nor_valve_code,
        nor.seqp_id || nor.seqp_ch || '_MERGE' as nor_merge_code,
        byp.seqp_id || byp.seqp_ch || '_BYP_' || byp.eqp_chamber_id || '_' || byp.eqp_chamber_posn as byp_valve_code,
        byp.seqp_id || byp.seqp_ch || '_MERGE' as byp_merge_code
    from pm pump
    join org on org.eqp_id = pump.eqp_id
    join pm nor
        on nor.eqp_id = pump.eqp_id
        and nor.eqp_chamber_id = pump.eqp_chamber_id
        and nor.eqp_chamber_posn = pump.eqp_chamber_posn
        and nor.seqp_type = 'SCRUBBER'
        and nor.eqp_posn = 'NOR'
        and nor.seqp_ch is not null
    left join pm byp
        on byp.eqp_id = pump.eqp_id
        and byp.eqp_chamber_id = pump.eqp_chamber_id
        and byp.eqp_chamber_posn = pump.eqp_chamber_posn
        and byp.seqp_type = 'SCRUBBER'
        and byp.eqp_posn = 'BYP'
        and byp.seqp_ch is not null
    where pump.seqp_type = 'PUMP'
      and pump.eqp_posn = '0'
),

-- TM/LL 챔버(스크러버 없음)의 펌프 연결 — FORELINE 만 생성
tmll_connections as (
    select distinct
        pm.eqp_id,
        pm.eqp_id || '_' || pm.eqp_chamber_id as chamber_code,
        pm.seqp_id as pump_code
    from pm
    join org on org.eqp_id = pm.eqp_id
    where pm.seqp_type = 'PUMP'
      and pm.eqp_posn = '0'
      and not exists (
          select 1 from pm s
          where s.eqp_id = pm.eqp_id
            and s.eqp_chamber_id = pm.eqp_chamber_id
            and s.seqp_type = 'SCRUBBER'
      )
)

select distinct
    chamber_code || '_' || pump_code || '_' || chamber_code as code,
    'FORELINE' as type_code, eqp_id as main_equipment_code, chamber_code,
    chamber_code as from_equipment_code, pump_code as to_equipment_code,
    null as vendor_code, 5.0 as length_m, 150 as mtbf_days
from chamber_connections

union all
select distinct
    chamber_code || '_' || pump_code || '_' || chamber_code,
    'FORELINE', eqp_id, chamber_code,
    chamber_code, pump_code,
    null, 5.0, 150
from tmll_connections

union all
select distinct
    pump_code || '_' || nor_valve_code || '_' || chamber_code,
    'PS', eqp_id, chamber_code,
    pump_code, nor_valve_code,
    null, 3.0, 150
from chamber_connections

union all
select distinct
    nor_valve_code || '_' || byp_valve_code || '_' || chamber_code,
    'SS', eqp_id, chamber_code,
    nor_valve_code, byp_valve_code,
    nor_scrubber_maker, 1.0, 150      -- SS vendor = NOR 스크러버 제조사 (레거시 승계)
from chamber_connections
where byp_valve_code is not null

union all
select distinct
    byp_valve_code || '_' || byp_merge_code || '_' || chamber_code,
    'ALLBYPASS', eqp_id, chamber_code,
    byp_valve_code, byp_merge_code,
    null, 3.0, 150
from chamber_connections
where byp_valve_code is not null

union all
select distinct
    nor_scrubber_code || '_' || nor_merge_code || '_' || chamber_code,
    'SD1', eqp_id, chamber_code,
    nor_scrubber_code, nor_merge_code,
    null, 3.0, 150
from chamber_connections

union all
select distinct
    nor_merge_code || '_' || eqp_id || '_DUCT_' || chamber_code,
    'SD2', eqp_id, chamber_code,
    nor_merge_code, eqp_id || '_DUCT',
    null, 6.0, 150
from chamber_connections
