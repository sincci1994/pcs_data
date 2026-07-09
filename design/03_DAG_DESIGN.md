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
| **기동 신호** | Manager는 시간표가 아니라 **extract DAG가 brz 적재 완료 시 발행하는 Asset 이벤트로 기동** (Airflow 3 data-aware scheduling) — "적재되는 신호를 받아 자동 실행". Sensor 2종(ExternalTaskSensor+SqlSensor) 게이트를 대체한다 |

## 규칙
1. `manifest.json`은 모델 머지 시 저작 단계에서 `dbt compile`로 갱신·커밋 — Airflow는 파일만 읽는다. 재컴파일 시 DAG 그래프가 자동 재구성된다 — 소스 변경(SLV 수정) 시 하류 자동 재정의도 같은 메커니즘 (→ [07](07_AUTHORING_FLOW.md)).
2. Model DAG 이름은 dbt 모델명에서 결정적으로 파생(`model__<name>`). 수동 DAG 작성 금지.
3. dbt test는 소속 모델의 Model DAG 안에서 실행 — 실패하면 해당 모델 하류가 트리거되지 않는다.
4. Publish 태스크는 gld 모델의 Model DAG 성공 이후에만 (Manager 말단).
5. `models/sbx/` 실험 모델은 `model__` DAG를 생성하되 **수동 트리거 전용** — Manager 편입·Publish 대상에서 제외 (→ [07](07_AUTHORING_FLOW.md)).
6. **manifest 머지 게이트** (CI): ① 재컴파일 결과와 커밋된 manifest의 그래프 일치 검증(stale manifest 차단) ② DAG 팩토리 dry-run — import 에러 0 ③ 저작 린트(slv/gld 테스트 존재, sbx 헤더 주석). manifest 머지 충돌의 해소 수단은 **재컴파일뿐** — 수동 편집 금지.

## Phase 3 확정 결정 (2026-07-09, 라이브 검증 완료 — 구현: platform/dags/factory__pcs_transform.py)
- **Manager→Model 트리거**: `TriggerDagRunOperator(wait_for_completion, poke_interval=10)` 동기 방식. deferrable 미사용 — 단일 ingestion 컨테이너에 triggerer 프로세스가 없다.
- **위상 간선 = 모델 직접 의존 + 테스트 유발 의존**: relationships 등 generic 테스트가 타 모델을 참조하면 그 모델을 선행시킨다 (예: dim_pipe 는 FK 테스트 때문에 dim_equipment 이후).
- **테스트 배치**: 모델 DAG 는 manifest `attached_node` 기준 **소속 테스트만** 명시 선택 실행 — dbt 기본 간접 선택(eager)은 "그 모델을 건드리는" 타 소속 테스트까지 끌어와 미빌드 참조로 실패한다. **교차 모델 singular 테스트는 Manager 말단(Publish 직전) 일괄 게이트**(`singular_tests` 태스크) — 규칙 3의 보완.
- extract 캐던스: 첫 제품(기준정보 스냅샷)은 **일 1회** — 5분 센서 시나리오(06) 재개 시 시간별 재검토.
- 동시 실행: Manager·Model 전부 `max_active_runs=1`. run 이 주기 초과 시 정책은 실측 후 (현 볼륨에선 초 단위 완주).
- **복구 UX [검증됨]**: 실패한 Manager run 에서 실패 trigger 태스크만 clear(`--downstream`) — 성공 태스크는 Airflow clear 의미론으로 자동 보존(성공분 스킵), 하류만 재개된다. 별도 스킵 판정 로직 불요.
- 실험(sbx) 필터: **폴더 경로(`models/sbx/`) 기준** — 승격 행위(폴더 이동)가 곧 상태 변경이라 태그보다 우월.
- 그룹핑: 1:1 유지 (모델 수 적음).
- Publish 대상 선언: 모델 `meta.publish_to` — 분석가가 모델 파일에서 선언하면 Manager 말단에 자동 배선.

## 후속 (보류)
- sbx 수동 실행 pool 격리 — sbx 실사용 개시 시 도입 (수동 전용이라 현재 경합 없음).
- manifest 스키마 버전 고정·파서 단위 테스트 — CI 머지 게이트(규칙 6) 구축과 함께.

## 이력
초기 척추는 Cosmos `DbtTaskGroup`(단일 DAG 내 태스크 전개)이었다 — 2026-07-09 Manager/Model 패턴으로 재설계 확정, Cosmos 제거. 근거와 트레이드오프는 [adr/0002](adr/0002-manager-model-dynamic-dag.md).
