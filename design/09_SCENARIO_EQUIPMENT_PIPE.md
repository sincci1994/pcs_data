# 09. 시나리오 — Equipment / Pipe 기준정보 (첫 번째 데이터 제품)

> 2026-07-09 사용자 결정: Utility 사용량([06](06_SCENARIO_UTILITY_USAGE.md) — **보류**) 대신 이것이 첫 제품.
> 발굴 로직·검증 수치의 원문: 외부 저장소 `pipe-scheduler-works/레거시전처리코드/` —
> 본 저장소 편입 기록: [governance/intake/2026-07-09_equipment_pipe_portmaster2.md](../governance/intake/2026-07-09_equipment_pipe_portmaster2.md)

## 업무 배경
배관 스케줄러(pipe-scheduler)의 `equipment`/`pipe` 기준정보는 레거시 EES **PortMaster2**를
DataGrip 수동 SQL + CSV 수동 export/import로 변환하는 **반수동 절차**로 채워지고 있다.
이 절차를 파이프라인으로 표준화·자동화한다 — AS-IS 발굴·SQL화·검증이 이미 완료된 로직의 **이관** 케이스.

## 파이프라인
```
EES PortMaster2 (Oracle — 로컬 검증은 warehouse 내 src 스키마 목데이터)
   │  ① Extract — 전량 스냅샷 (기준정보, 워터마크 아님) + pre-flight 계약 체크
   ▼
warehouse.brz.ees__portmaster2 (원형)
   │  ② dbt — stg(01 필터 승계) + seed(조직 더미·line_mapping) → mart 3종
   ▼
dim_equipment (8종 노드) · dim_pipe (6종 엣지) · dim_vendor  (스키마 gld)
   │  ③ dbt test (unique/not_null/accepted_values/relationships FK 0건)
   │  ④ Publish — 전량 교체·원자적 (소규모 기준정보 → 02 결정 ②)
   ▼
서빙: pipe-scheduler-db (로컬 대역: warehouse srv 스키마) + OM 카탈로그
```

## 확정 사항 (2026-07-09)
1. **변환 규칙 = 레거시 정본 그대로 이식**: 명명·챔버 분리 하이브리드·NOR 소유 결정론·NOR-only 배관 보존·배관 6종 상수(길이/MTBF). 규칙 변경 없음 — 대사 검증으로 동일성 증명.
2. **조직 enrichment는 v1 더미 시드** (`eqp_org_mapping` dbt seed): 레거시 부트스트랩(변환규칙 §3-4)과 동일. SMDM/GPM 실연동 시 seed→extract 교체 — sources.yml+SLV만 수정하면 하류 자동 재정의 (→ [07](07_AUTHORING_FLOW.md)의 실증 케이스).
3. **gld는 natural key**(`vendor_code`): serial `vendor_id` 부여는 서빙 import 시점 책임.
4. **Extract = 전량 스냅샷**: 기준정보(소규모)라 이벤트타임 워터마크·lookback 불필요 — 단일 트랜잭션 delete+insert 멱등. `ctl.job_audit` 기록은 동일 적용.
5. 갱신 주기 [기본값]: extract 일 1회 → Asset 이벤트로 Manager 기동.

## 미확정 (사내 확인)
1. **EES(pcsdb) 직접 접속 권한** — 레거시 자동화 선결과제 1. 확보 전까지 원격 이식 불가.
2. 조직·holiday 실소스 연동 시점 (v1 더미 시드의 교체 시점).
3. 서빙(pipe-scheduler-db) 반영 방식 — 직접 커넥션 vs CSV 핸드오프 (04 검증 스크립트 게이트화 포함).
4. 대상 설비 범위 확대 시 명세 (현재 검증 샘플 3설비 → 실 PortMaster2 전체).

## 완료 조건 — **전 항목 통과 (2026-07-09 로컬 E2E)**
- [x] extract 동일 조건 반복 실행 후 bronze 중복 0건 (3회 실행, 47행 유지).
- [x] dbt test 전 계층 통과 (55/55) — pipe→equipment FK 누락 0건 포함.
- [x] **대사 검증 완전 일치** (equipment 25/41/28, pipe 26/38/25 + 타입별) — [quality/reconciliation/equipment_pipe/](../quality/reconciliation/equipment_pipe/README.md).
- [x] Publish 원자성: 0행 스냅샷 주입 시 중단·srv 이전 상태 보존 확인.
- [x] glossary 정의(설비/배관) OM 발행 (PCS.Equipment / PCS.Pipe) + 리니지 brz→slv→gld 확인.
- 2026-07-09 후속: 명명 체계 확정([10](10_NAMING_ORGANIZATION.md))에 따라 모델·스키마 리네임 (gold_*→dim_*, lnd→brz 등) — 로직 불변, 대사 재통과로 증명.

남는 것은 **원격 전환** 항목뿐 — 위 미확정 1~4 (EES 접속 권한이 1순위).
