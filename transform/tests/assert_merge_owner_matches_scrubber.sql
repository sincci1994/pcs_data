-- 레거시 02 검증(B) 이식: SCRUBBER_MERGE 의 main 이 자기 스크러버(main=group_code 조인)와 일치하는가.
select m.code, m.main_equipment_code
from {{ ref('dim_equipment') }} m
join {{ ref('dim_equipment') }} s
    on s.code = m.group_code and s.type_code = 'SCRUBBER'
where m.type_code = 'SCRUBBER_MERGE'
  and m.main_equipment_code <> s.main_equipment_code
