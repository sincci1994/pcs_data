-- PortMaster2 표준화 — 원천값 보존, 레거시 01 스크립트의 유효행 필터만 승계 (비즈니스 판단 없음).
-- 소스가 바뀌면 이 모델과 _ees__sources.yml 만 수정한다 — 하류(gld)는 ref() 그래프로 자동 재정의.
--
-- 컬럼:
--   eqp_id           메인설비 ID (예: SLWB331)
--   eqp_chamber_id   챔버 ID (0=TM/LL, A/B 또는 1~N=공정)
--   eqp_chamber_posn 챔버 내 경로 위치 (LL1/TM/PRO/DIVERT/PED) — 경로 짝짓기 조인 키
--   eqp_posn         서브설비 위치 (0=펌프, NOR/BYP=스크러버 계통)
--   seqp_type        서브설비 유형 (PUMP | SCRUBBER)
--   seqp_maker       제조사 코드 (= vendor 자연키)
--   seqp_model_code  서브설비 모델 코드 (소스 그대로, NULL 허용)
--   seqp_id          서브설비 ID — 이미 eqp_id 접두사 포함 (재접두사 금지)
--   seqp_ch          스크러버 채널 (펌프는 0) — SCRUBBER 는 NOT NULL 이 아래 필터로 보장
--   seqp_port        포트 (참고용)
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
