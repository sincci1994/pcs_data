# 03. Manager/Model 동적 DAG 설계 (요구 6)

## 목표
- **개발자 코드 작업 불필요**: dbt 모델(.sql) 추가 → DAG 자동 등장.
- **모델 단위 운영**: 모델별 독립 재시도·백필·모니터링.
- **의존성 기반 복구**: 실패 시 실패 지점부터 재개, 성공한 상류는 건너뜀.

## 구조

```
dbt manifest.json ──(파싱: DAG 팩토리)──┬→ Model DAG × N   (model__<모델명>)
                                        └→ Manager DAG × 1 (manager__<프로젝트>)

Manager DAG:  ← extract DAG의 Asset 이벤트로 기동 (적재 완료 신호 — cron 아님)
  trigger(model__a) → trigger(model__b, model__c) → … (위상 정렬 순)
      └ wait_for_completion — 실패 시 하류 트리거 중단

Model DAG (하나의 모델 데이터를 만드는 일련의 태스크):
  dbt run --select <모델> → dbt test --select <모델>
```

| 구성요소 | 책임 |
|---|---|
| **DAG 팩토리** | 커밋된 `manifest.json` 파싱 → Model/Manager DAG 생성. 런타임 dbt 컴파일 금지(결정론) |
| **Manager DAG** | 의존 그래프 위상 정렬 순으로 Model DAG 트리거. 실패 시 의존 관계 기반 복구(재실행 시 성공분 스킵) |
| **Model DAG** | 모델 1개의 run→test. 단독 트리거 가능(개별 백필·재시도) |
| **기동 신호** | Manager는 시간표가 아니라 **extract DAG가 LND 적재 완료 시 발행하는 Asset 이벤트로 기동** (Airflow 3 data-aware scheduling) — "적재되는 신호를 받아 자동 실행". Sensor 2종(ExternalTaskSensor+SqlSensor) 게이트를 대체한다 |

## 규칙
1. `manifest.json`은 모델 머지 시 저작 단계에서 `dbt compile`로 갱신·커밋 — Airflow는 파일만 읽는다. 재컴파일 시 DAG 그래프가 자동 재구성된다 — 소스 변경(SLV 수정) 시 하류 자동 재정의도 같은 메커니즘 (→ [07](07_AUTHORING_FLOW.md)).
2. Model DAG 이름은 dbt 모델명에서 결정적으로 파생(`model__<name>`). 수동 DAG 작성 금지.
3. dbt test는 소속 모델의 Model DAG 안에서 실행 — 실패하면 해당 모델 하류가 트리거되지 않는다.
4. Publish 태스크는 GOLD 모델의 Model DAG 성공 이후에만 (Manager 말단).
5. `models/wrk/` 실험 모델은 `model__` DAG를 생성하되 **수동 트리거 전용** — Manager 편입·Publish 대상에서 제외 (→ [07](07_AUTHORING_FLOW.md)).
6. **manifest 머지 게이트** (CI): ① 재컴파일 결과와 커밋된 manifest의 그래프 일치 검증(stale manifest 차단) ② DAG 팩토리 dry-run — import 에러 0 ③ 저작 린트(slv/gold 테스트 존재, wrk 헤더 주석). manifest 머지 충돌의 해소 수단은 **재컴파일뿐** — 수동 편집 금지.

## Phase 3 구현 시 확정할 것
- **Manager→Model** 트리거 방식: `TriggerDagRunOperator(wait_for_completion)` vs Asset 체인 — Model DAG 간 배선만 미결 (Manager 기동은 extract Asset 이벤트로 확정).
- extract 캐던스: 소스 5분 테이블 대비 추출 주기(시간별/일별) — Manager는 여기 종속되므로 별도 스케줄 없음.
- 동시 실행 통제: Manager `max_active_runs=1` + run이 주기를 초과할 때 skip/queue 정책.
- wrk 수동 실행과 운영 run의 격리 (별도 pool 등 — 리소스 경합 방지).
- 그룹핑 granularity: 모델 1:1 vs 태그·폴더 단위 묶음 (모델 수가 적은 초기엔 1:1).
- 복구 UX: Manager run clear 시 성공 Model DAG 스킵 판정 로직.
- manifest 스키마 버전 고정과 파서 테스트.
- wrk 모델 필터링 기준 (폴더 경로 vs dbt 태그).

## 이력
초기 척추는 Cosmos `DbtTaskGroup`(단일 DAG 내 태스크 전개)이었다 — 2026-07-09 Manager/Model 패턴으로 재설계 확정, Cosmos 제거. 근거와 트레이드오프는 [adr/0002](adr/0002-manager-model-dynamic-dag.md).
