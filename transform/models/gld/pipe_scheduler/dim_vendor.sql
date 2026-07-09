-- 협력사(제조사) 기준정보 — PortMaster2 등장 maker 자동 생성 (레거시 01 §6 승계).
-- surrogate id 는 서빙 import 시점 책임 — gld 는 natural key(code) (→ design/09 확정 3).
{{ config(materialized='table', meta={'publish_to': 'srv.vendor'}) }}
select distinct
    seqp_maker as code,
    seqp_maker as name,
    'EQUIPMENT' as type_code,
    'PortMaster2 seqp_maker 기준 자동 생성' as description
from {{ ref('stg_ees__portmaster2') }}
where seqp_type in ('PUMP', 'SCRUBBER')
