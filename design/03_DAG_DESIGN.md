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

## 캐던스와 기동 의미론

### 주기의 유일한 결정 지점 = `sources.yml`의 `schedule`

dbt 모델은 주기를 갖지 않는다 — 모델은 "무엇을 만들지"만 정의한다. 파이프라인 전체의 캐던스는
**extract cron(sources.yml `schedule`) 한 곳에서 결정**되고, 이후 brz 적재 완료 → Asset 이벤트 →
Manager → slv → gld 로 같은 캐던스가 연쇄 전파된다. 모델 저작자는 주기를 신경 쓰지 않는다 —
주기는 소스를 선언하는 시점에 1회 결정한다.

### grain ≠ cadence

소스의 적재 주기(grain)를 파이프라인이 따라가지 않는다. 예: N2 유틸리티 — 소스 Oracle에
2초 수집분이 5분 집계로 계속 쌓이지만, 파이프라인이 5분마다 도는 것은 비효율 —
**추출은 배치 주기로 끊는다** (예: 3시간마다 "지난 워터마크 이후 쌓인 5분 행 전부").
grain은 데이터의 속성이고, cadence는 sources.yml의 결정이다.

### 추출 모드 결정 기준

| 소스 성격 | mode | 상태 |
|---|---|---|
| 기준정보·소용량 (전량 재적재 가능) | `snapshot` — 전량 교체 | 구현됨 |
| 계속 쌓이는 누적형 (N2 등 센서·이력) | `watermark` — 증분 + lookback 24h + `ctl.watermark` (→ [08 §4](08_DATA_OPS.md)) | 설계 완비·**미구현** — 첫 누적형 소스 실명세 확보 시 (→ [roadmap](roadmap.md)) |

### Manager 다중 소스 기동 의미론 — 전환 조건 명시

현재 Manager는 선언된 **모든** 소스 Asset의 리스트를 구독한다 = Airflow **AND 의미론**
(모든 Asset이 갱신돼야 기동). 소스가 1개인 현재만 유효하다. 캐던스가 다른 두 번째 소스가
추가되는 순간 두 가지 함정이 발현된다: ① Manager가 가장 느린 소스에 묶인다 ② 한 소스의
추출 실패가 다른 소스의 신선분 반영까지 차단한다.

**전환 시점 = sources.yml에 상이 캐던스의 두 번째 블록이 추가될 때** (함정 발현 전 선행):
- `AssetAny`(OR)로 구독 전환 — 아무 소스나 도착하면 기동.
- 기동 시 `triggering_asset_events`로 갱신된 소스를 확인하고, manifest의 소스→모델 매핑으로
  **영향받는 하위 그래프만 트리거** (전체 그래프 재실행 방지). → [roadmap](roadmap.md)

## 확정 구현 결정 (구현: platform/dags/factory__pcs_transform.py — 라이브 검증 완료)
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
