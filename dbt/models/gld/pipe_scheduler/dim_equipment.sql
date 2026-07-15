-- 배관 스케줄러 설비 계층 노드 8종 — 레거시 검증 완료 변환 규칙의 이식 (규칙 변경 없음).
-- 노드 유형: MAIN / CHAMBER / PUMP / SCRUBBER / SCRUBBER_NOR_VALVE / SCRUBBER_BYP_VALVE
--            / SCRUBBER_MERGE / LATERAL_DUCT
--
-- 컬럼:
--   code                설비 노드 코드 (전역 유일)
--   type_code           노드 유형 8종 (위)
--   main_equipment_code 소속 메인설비 (MAIN 자신은 NULL). Pair 스크러버는 NOR 소유 설비
--   team/division/site/line/area_code  조직 코드 (org 매핑 유래)
--   group_code          프론트 렌더링 묶음 키 — 스크러버군(스크러버·밸브·MERGE)은 스크러버 코드 공유
--   layer_order         렌더링 레이어 (1=MAIN/CHAMBER, 2=PUMP, 3=SCRUBBER/밸브, 4=MERGE, 5=DUCT)
--   vendor_code         제조사 자연키 (MAIN/CHAMBER 는 NULL 허용). surrogate id 는 소비 측 책임

with pm as (
    select * from {{ ref('stg_ees__portmaster2') }}
),

org as (
    select * from {{ ref('stg_smdm__eqp_org_mapping') }}
),

-- 메인설비 (org 매핑이 있는 설비만 — 레거시 INNER JOIN 승계)
main_eqp as (
    select distinct
        pm.eqp_id as code,
        pm.eqp_id as group_code,
        pm.eqp_id as eqp_id,
        1 as layer_order,
        org.team_code, org.division_code, org.site_code, org.line_code, org.area_code
    from pm
    join org on org.eqp_id = pm.eqp_id
),

-- 챔버: 공정(해당 chamber 에 스크러버 존재)은 경로(posn)별 분리, TM/LL 은 단일 (하이브리드)
chambers as (
    select distinct
        pm.eqp_id || '_' || pm.eqp_chamber_id || '_' || pm.eqp_chamber_posn as code,
        pm.eqp_id as group_code,
        pm.eqp_id,
        1 as layer_order,
        org.team_code, org.division_code, org.site_code, org.line_code, org.area_code
    from pm
    join org on org.eqp_id = pm.eqp_id
    where exists (
        select 1 from pm s
        where s.eqp_id = pm.eqp_id
          and s.eqp_chamber_id = pm.eqp_chamber_id
          and s.seqp_type = 'SCRUBBER'
    )
    union
    select distinct
        pm.eqp_id || '_' || pm.eqp_chamber_id,
        pm.eqp_id,
        pm.eqp_id,
        1,
        org.team_code, org.division_code, org.site_code, org.line_code, org.area_code
    from pm
    join org on org.eqp_id = pm.eqp_id
    where not exists (
        select 1 from pm s
        where s.eqp_id = pm.eqp_id
          and s.eqp_chamber_id = pm.eqp_chamber_id
          and s.seqp_type = 'SCRUBBER'
    )
),

-- 펌프: code = seqp_id 그대로 (이미 eqp_id 접두사 포함 — 재접두사 금지)
pumps as (
    select distinct
        pm.seqp_id as code,
        pm.seqp_id as group_code,
        pm.eqp_id,
        2 as layer_order,
        pm.seqp_maker,
        org.team_code, org.division_code, org.site_code, org.line_code, org.area_code
    from pm
    join org on org.eqp_id = pm.eqp_id
    where pm.seqp_type = 'PUMP'
),

-- 스크러버: physical code 당 1행 — Pair 구조에서 소유(NOR) 행을 결정론적으로 채택
scrubbers as (
    select distinct on (pm.seqp_id || pm.seqp_ch)
        pm.seqp_id || pm.seqp_ch as code,
        pm.seqp_id || pm.seqp_ch as group_code,
        pm.eqp_id,
        3 as layer_order,
        pm.seqp_maker,
        org.team_code, org.division_code, org.site_code, org.line_code, org.area_code
    from pm
    join org on org.eqp_id = pm.eqp_id
    where pm.seqp_type = 'SCRUBBER'
      and pm.seqp_ch is not null
    order by
        pm.seqp_id || pm.seqp_ch,
        case when pm.eqp_posn = 'NOR' then 0 else 1 end,   -- 소유(NOR) 우선
        pm.eqp_id                                          -- 안정적 tie-break
),

-- 밸브 (NOR/BYP): posn 이 경로 짝짓기 키이므로 코드에 포함
valves as (
    select distinct
        pm.seqp_id || pm.seqp_ch || '_' || pm.eqp_posn || '_'
            || pm.eqp_chamber_id || '_' || pm.eqp_chamber_posn as code,
        pm.seqp_id || pm.seqp_ch as group_code,
        pm.eqp_id,
        pm.eqp_posn,
        3 as layer_order,
        pm.seqp_maker,
        org.team_code, org.division_code, org.site_code, org.line_code, org.area_code
    from pm
    join org on org.eqp_id = pm.eqp_id
    where pm.seqp_type = 'SCRUBBER'
      and pm.eqp_posn in ('NOR', 'BYP')
      and pm.seqp_ch is not null
),

unioned as (
    select code, 'MAIN' as type_code, null as main_equipment_code,
           team_code, division_code, site_code, line_code, area_code,
           group_code, layer_order, null as vendor_code, 1 as type_priority
    from main_eqp

    union all
    select code, 'CHAMBER', eqp_id,
           team_code, division_code, site_code, line_code, area_code,
           group_code, layer_order, null, 2
    from chambers

    union all
    select code, 'PUMP', eqp_id,
           team_code, division_code, site_code, line_code, area_code,
           group_code, layer_order, seqp_maker, 3
    from pumps

    union all
    select code, 'SCRUBBER', eqp_id,
           team_code, division_code, site_code, line_code, area_code,
           group_code, layer_order, seqp_maker, 4
    from scrubbers

    union all
    select code, 'SCRUBBER_NOR_VALVE', eqp_id,
           team_code, division_code, site_code, line_code, area_code,
           group_code, layer_order, seqp_maker, 5
    from valves where eqp_posn = 'NOR'

    union all
    select code, 'SCRUBBER_BYP_VALVE', eqp_id,
           team_code, division_code, site_code, line_code, area_code,
           group_code, layer_order, seqp_maker, 6
    from valves where eqp_posn = 'BYP'

    -- MERGE: 스크러버당 1개, group_code = 자기 스크러버 code (프론트 스크러버군 묶음 키)
    union all
    select code || '_MERGE', 'SCRUBBER_MERGE', eqp_id,
           team_code, division_code, site_code, line_code, area_code,
           code, 4, seqp_maker, 7
    from scrubbers

    -- DUCT: 스크러버 보유 메인설비당 1개. vendor 는 결정론 채택(maker 알파벳→코드 순)
    union all
    select m.code || '_DUCT', 'LATERAL_DUCT', m.code,
           m.team_code, m.division_code, m.site_code, m.line_code, m.area_code,
           m.code || '_DUCT', 5,
           (
               select s.seqp_maker from scrubbers s
               where s.eqp_id = m.code
               order by s.seqp_maker nulls last, s.code
               limit 1
           ),
           8
    from main_eqp m
    where exists (select 1 from scrubbers s where s.eqp_id = m.code)
)

-- 레거시 ON CONFLICT DO NOTHING(삽입 순서 우선) 의미론 재현: code 충돌 시 앞선 타입 유지
select
    code, type_code, main_equipment_code,
    team_code, division_code, site_code, line_code, area_code,
    group_code, layer_order, vendor_code
from (
    select *, row_number() over (partition by code order by type_priority) as rn
    from unioned
) dedup
where rn = 1
