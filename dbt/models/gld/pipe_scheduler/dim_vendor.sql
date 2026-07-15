-- 협력사(제조사) 기준정보 — PortMaster2 등장 maker 자동 생성 (레거시 승계).
-- gld 는 natural key(code = seqp_maker) — surrogate id 는 소비 측 책임.
-- 컬럼: code(제조사 자연키) / name(v1 = 코드와 동일, 실명칭은 후속 큐레이션)
--       / type_code(고정 EQUIPMENT) / description(생성 출처)
select distinct
    seqp_maker as code,
    seqp_maker as name,
    'EQUIPMENT' as type_code,
    'PortMaster2 seqp_maker 기준 자동 생성' as description
from {{ ref('stg_ees__portmaster2') }}
where seqp_type in ('PUMP', 'SCRUBBER')
