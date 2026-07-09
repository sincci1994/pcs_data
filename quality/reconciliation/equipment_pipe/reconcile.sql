-- 대사 검증 — dim_equipment/dim_pipe vs 레거시 검증 완료 수치 (이관 승격 게이트).
-- 기준: pipe-scheduler-works/레거시전처리코드/문서/변환규칙.md §6 (샘플 3설비, FK 누락 0건 상태).
-- 실행: docker exec -i pcs_warehouse psql -U pcs_admin -d pcs_wh < quality/reconciliation/equipment_pipe/reconcile.sql
-- 판정: 모든 SELECT 가 0행이면 일치(PASS). 행이 나오면 그 행이 불일치 내역이다.

-- 1) 설비별 equipment 건수 (code = 설비 자신 포함)
with expected(eqp_id, cnt) as (
    values ('SLWB331', 25), ('TBNP708', 41), ('WTCB7G1', 28)
),
actual as (
    select coalesce(main_equipment_code, code) as eqp_id, count(*) as cnt
    from gld.dim_equipment
    group by 1
)
select 'equipment_count' as issue, e.eqp_id, e.cnt as expected, coalesce(a.cnt, 0) as actual
from expected e
left join actual a using (eqp_id)
where coalesce(a.cnt, 0) <> e.cnt;

-- 2) 설비별 pipe 건수
with expected(eqp_id, cnt) as (
    values ('SLWB331', 26), ('TBNP708', 38), ('WTCB7G1', 25)
),
actual as (
    select main_equipment_code as eqp_id, count(*) as cnt
    from gld.dim_pipe
    group by 1
)
select 'pipe_count' as issue, e.eqp_id, e.cnt as expected, coalesce(a.cnt, 0) as actual
from expected e
left join actual a using (eqp_id)
where coalesce(a.cnt, 0) <> e.cnt;

-- 3) equipment 타입별 건수
with expected(type_code, cnt) as (
    values ('MAIN', 3), ('CHAMBER', 19), ('PUMP', 21), ('SCRUBBER', 11),
           ('SCRUBBER_NOR_VALVE', 16), ('SCRUBBER_BYP_VALVE', 10),
           ('SCRUBBER_MERGE', 11), ('LATERAL_DUCT', 3)
),
actual as (
    select type_code, count(*) as cnt from gld.dim_equipment group by 1
)
select 'equipment_type_count' as issue, e.type_code, e.cnt as expected, coalesce(a.cnt, 0) as actual
from expected e
left join actual a using (type_code)
where coalesce(a.cnt, 0) <> e.cnt;

-- 4) pipe 타입별 건수
with expected(type_code, cnt) as (
    values ('FORELINE', 21), ('PS', 16), ('SS', 10), ('ALLBYPASS', 10), ('SD1', 16), ('SD2', 16)
),
actual as (
    select type_code, count(*) as cnt from gld.dim_pipe group by 1
)
select 'pipe_type_count' as issue, e.type_code, e.cnt as expected, coalesce(a.cnt, 0) as actual
from expected e
left join actual a using (type_code)
where coalesce(a.cnt, 0) <> e.cnt;

-- 5) pipe FK 논리 누락 (레거시 02 검증 승계 — dbt relationships 테스트와 이중이지만 대사 기록용)
select 'pipe_fk_missing' as issue, p.code, col.ref_code
from gld.dim_pipe p
cross join lateral (
    values ('main', p.main_equipment_code), ('chamber', p.chamber_code),
           ('from', p.from_equipment_code), ('to', p.to_equipment_code)
) as col(kind, ref_code)
where not exists (select 1 from gld.dim_equipment e where e.code = col.ref_code);
