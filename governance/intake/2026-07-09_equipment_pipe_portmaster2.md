# 인테이크 — Equipment / Pipe 기준정보 (PortMaster2)

> 절차 전체: [design/04](../../design/04_AS_IS_INTAKE.md).
> **특수 케이스**: 발굴·논리 기록·SQL화·검증이 별도 저장소에서 이미 완료된 상태로 인입 —
> 이 문서는 그 결과를 본 저장소 체계(정의→모델→대사)로 편입하는 기록이다.

## 1. 대상
- 프로덕트: 배관 스케줄러(pipe-scheduler)의 `equipment`(설비 계층)·`pipe`(배관 연결) 기준정보
- 업무 담당자: 본인(PCS기술팀) / 발굴 완료: 2026-05~06 (pipe-scheduler-works 저장소에서)
- 현재 사용처: pipe-scheduler 프론트 설비정보 화면 렌더링 (챔버 선택 → 단일 공정 경로 하이라이트)

## 2. 소스 (레거시)
- 원천: EES `pcs_sq_port_mst_2nd` (**PortMaster2**, `db_user='PF_PCS'`, PUMP/SCRUBBER) — 배관 구성 본체
- 부가(enrichment): SMDM `zte_equipment`(조직), GPM `mes_line_mapping_info`(라인 매핑) — **v1 범위 제외** (아래 §4)
- 기존 절차: DataGrip에서 SQL 01→02→03 수동 실행 → CSV 수동 export/import → 04 검증 (**반수동**)
- 로직 원문 위치 (외부 저장소): `pipeschedule/pipe-scheduler-works/레거시전처리코드/`
  — `문서/변환규칙.md`(규칙 정본) · `실행SQL/01·02`(구현 정본) · `검증샘플/sourcedata.md`(입력 샘플)

## 3. 변환 논리 (발굴 결과 요지 — 원문은 위 변환규칙.md 보존)
- PortMaster2 행 = 설비×챔버×경로×서브설비. 이를 8종 설비 노드 + 6종 배관 엣지로 전개.
- 챔버 분리 하이브리드: 공정 챔버(스크러버 존재)는 `eqp_chamber_posn`별 분리, TM/LL(chamber 0)은 단일.
- `eqp_chamber_posn`은 pump↔NOR↔BYP를 같은 경로끼리 짝짓는 조인 키 (카테시안 곱 방지).
- Pair 구조(자기 NOR + 상대 설비 BYP 공유)에서 스크러버·MERGE 소속은 **NOR 소유 설비로 결정론 배정**.
- NOR-only 챔버: BYP는 LEFT JOIN — SS/ALLBYPASS만 조건부 미생성, 배관 소실 방지.
- `seqp_id`는 이미 `eqp_id` 접두사 포함 — 재접두사 금지.

## 4. 정리 논리 (본 저장소 표준화 — 레거시와 달라지는 점)
- 정의 확정: [glossary — 설비/배관](../glossary.md) (2026-07-09).
- **계층 재배치**: 레거시 etl_export 작업테이블 → `brz.ees__portmaster2`(원형) → `slv`(01의 NULL/빈값 필터 승계) → `dim_equipment`/`dim_pipe`(02의 변환 로직 이식, 스키마 gld). ※ 2026-07-09 명명 체계 확정([design/10](../../design/10_NAMING_ORGANIZATION.md))으로 리네임 — 초판 명칭은 lnd/gold_*.
- **조직 enrichment는 v1 더미 시드**: 레거시 변환규칙 §3-4(부트스트랩 더미)와 동일 접근 — `eqp_org_mapping`을 dbt seed로 공급, SMDM/GPM 실연동 시 seed→extract 교체(slv 흡수, → design/07). staging 인터페이스명은 미래 소스 축(`stg_smdm__eqp_org_mapping`).
- **line_mapping 수기표 → dbt seed 승격**: 레거시 자동화 선결과제 2("SQL 상수가 아닌 관리 테이블로") 해소.
- **vendor surrogate id 미사용**: gld는 natural key(`vendor_code`) — serial id 부여는 서빙 DB import 시점 책임 (레거시 04의 sequence 보정과 동일 영역).
- 수동 CSV export/import → Publish 태스크(원자적 전량 교체)로 대체 (레거시 자동화 선결과제의 "높음" 구간).

## 5. SQL화
- dbt 모델: `transform/models/slv/ees/stg_ees__portmaster2.sql`, `transform/models/gld/pipe_scheduler/dim_equipment.sql`, `dim_pipe.sql`, `dim_vendor.sql`

## 6. 대사 검증
- 비교 기준: 레거시 검증 완료 수치 (변환규칙.md §6, 샘플 3설비) —
  equipment: SLWB331=25 · TBNP708=41 · WTCB7G1=28 / pipe: 26 · 38 · 25
  타입별: equipment `MAIN 3, CHAMBER 19, PUMP 21, SCRUBBER 11, NOR 16, BYP 10, MERGE 11, DUCT 3` / pipe `FORELINE 21, PS 16, SS 10, ALLBYPASS 10, SD1 16, SD2 16`
- 검증 쿼리: `quality/reconciliation/equipment_pipe/` (재실행 가능)
- 결과: **완전 일치 (2026-07-09)** — 설비별·타입별 카운트 전 항목 0건 불일치, FK 누락 0건. 레거시 오류 발견 없음.

## 7. 승격
- glossary 확정: 2026-07-09 / OM 발행: PCS.Equipment·PCS.Pipe (2026-07-09) / 모델 머지·manifest 갱신: 2026-07-09 커밋
