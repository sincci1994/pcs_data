# 02. 전체 아키텍처

## 흐름

```
소스 (레거시 EES 등, 별도 시스템에서 주기 제공)
   │  ① Extract — Airflow 태스크 (크로스 DB: chunked fetch + bulk insert)
   ▼
warehouse.brz (bronze — 원형 보존)
   │  ② Transform — dbt (Manager/Model DAG로 실행)
   ▼
warehouse.slv (silver — 정제·표준화) → warehouse.gld (gold — 비즈니스 데이터 프로덕트)
   │  ③ Validate — dbt test (실패 시 Publish 차단)
   │  ④ Publish — Airflow 태스크 (볼륨 기준 전량/윈도 교체, 원자적 swap)
   ▼
서빙 DB (운영 DB 또는 별도 DB) / OpenMetadata 카탈로그 (리니지·용어집·테스트결과)
```

**저장 책임 분리** [확정]: 장기 보관(5년)은 운영 Oracle(소스 원본)과 서빙 DB(GOLD 이력)가 담당한다.
**warehouse Postgres는 변환 연산 자원 전용** — 작업 윈도(rolling window)만 보유하는 소모성 작업 공간이며, 서빙·장기 축적을 하지 않는다. → [08_DATA_OPS.md](08_DATA_OPS.md)

## 계층 (요구 4의 LND/SILVER/GOLD — 메달리온 축약 체계로 구현, 명명 정본: [10](10_NAMING_ORGANIZATION.md))

| 계층 | 스키마 | 역할 | 담당 |
|---|---|---|---|
| Bronze | `brz` | 소스 원형 보존, 워터마크 기반 적재 | Extract (Airflow) |
| Silver | `slv` | 정제·표준화 (원천값 보존) — **소스 변경 흡수 계층**: gold는 slv만 참조하므로 소스 교체 영향이 여기서 격리된다 | dbt |
| Gold | `gld` | 비즈니스 데이터 프로덕트 (지표·Summary) | dbt |
| Sandbox | `sbx` | 분석가 실험 계층 — Publish·OM 발행 제외, 승격 게이트로만 slv/gld 진입 (→ [07](07_AUTHORING_FLOW.md)) | 분석가 |
| Control | `ctl` | 운영 메타데이터 — `ctl.watermark`(소스×테이블 이벤트타임 워터마크)·`ctl.job_audit`(dag_id+logical_date 유니크, 행수·상태)·운영 메트릭. **platform 전용** (분석가·dbt 접근 불가). 컬럼 상세는 Phase 3 | Extract·notifier |

**권한 원칙** (GRANT 스크립트는 Phase 2 infra 산출물): 분석가 롤 = `sbx` 쓰기 / `slv`·`gld` 읽기 + `statement_timeout` 기본 적용. 파이프라인 롤 = `brz`~`gld` 쓰기. `ctl`은 platform 전용 — 규칙이 관례가 아니라 DB 롤로 강제되게 한다.

> CORE(스타 스키마) 중간 계층은 도입하지 않는다 — 모델 수·복잡도가 커지면 재검토 (→ [roadmap.md](roadmap.md)).

## 역할 분담

| 단계 | 담당 | 레거시 대응 |
|---|---|---|
| Extract/Load | Airflow 태스크 (dbt는 DB 간 이동 불가) | 수동 추출 구간 |
| Transform | dbt 모델 (slv→gld) | 개인 Excel 가공 로직 |
| Validate | dbt test — 실패 시 Publish 차단 | 사후 수동 검증 SQL |
| Publish | Airflow 태스크 — 소규모 마트는 전량 교체, 대규모(설비×일 grain)는 윈도 교체. **원자성 불변조건**: staging 적재 후 단일 트랜잭션 swap — 소비자는 항상 완전한 스냅샷만 보고, 실패 시 이전 상태 보존 (→ [08 §3](08_DATA_OPS.md)) | 수동 CSV export/import |
| 가시성 | OpenMetadata | (신규) |

## 아키텍처 결정 (합의 완료)

| # | 결정 | 선택 | 근거 |
|---|---|---|---|
| ① | 변환 위치 | **중앙 warehouse** (Postgres) | 소스/서빙 부하 분리, dbt 표준 패턴 |
| ② | 서빙 반영 | **볼륨 기준 택일**: 소규모 마트 전량 교체 / 대규모 윈도 교체(최근 N일) — 둘 다 원자적 swap | 전량 교체 단순성은 유지하되 15만 설비×일 grain의 이력 전체 재적재는 배제 (→ [08 §3](08_DATA_OPS.md)) |
| ⑥ | 서빙 DB 실체 | **운영 DB(Oracle) 또는 별도 DB** — warehouse 아님 | 장기 보관 책임 분리 [확정]. GOLD 이력 보존(5년)은 서빙 DB 측 정책. 소비 원칙: Excel로 재추출하더라도 **원천은 항상 서빙 GOLD**(개인 재가공 재발 방지), 읽기 전용 접근 + OM 카탈로그로 발견 |
| ③ | 소스 접근 | **별도 시스템에서 주기 제공** | Extract 태스크가 채널 대응. 상세는 원격 환경 확인 후. I/F 선택지(시스템 I/F 지향 vs DataLake)와 소스 지형은 [11 §2](11_TARGET_ARCHITECTURE.md) |
| ④ | 오케스트레이션 | **Manager/Model Dynamic DAG** | → [03_DAG_DESIGN.md](03_DAG_DESIGN.md) · [adr/0002](adr/0002-manager-model-dynamic-dag.md) |
| ⑤ | 변환 엔진 | **dbt-postgres 단일** (PySpark 보류) | → [adr/0003](adr/0003-defer-pyspark-multi-engine.md) |

## 온톨로지 (요구 4 "비즈니스 정의로 흐름을 본다")

- **정의**: `governance/glossary.md` — 지표·용어의 단일 원천. dbt `schema.yml` 컬럼 설명과 함께 OpenMetadata로 발행.
- **관계 — 3층 원천** (2026-07-15 형식화): ① 용어↔용어 = glossary 항목의 **관계** 필드(`[[용어명]]` 문법, OM related terms로 발행) ② 테이블·컬럼 = `schema.yml` + relationships 테스트 ③ 자산 계보 = dbt `ref()` 그래프(manifest) → OM 리니지. 지식그래프(GraphRAG 등)가 필요해지면 이 3층을 합치는 것으로 구성한다 — 별도 온톨로지 도구(RDF/OWL) 도입 없음.
- **흐름 조회**: OpenMetadata UI에서 용어 → 연결 자산 → 리니지로 탐색.
- **시멘틱 레이어 포지션**: 쿼리 타임 메트릭 계층(MetricFlow·Cube류)은 도입하지 않는다 — "정의 1곳/소비 N곳"은 glossary 정의 → gld 물질화가 **빌드 타임**에 달성하고, 소비자는 서빙 테이블을 직접 읽는다([08 §1.1](08_DATA_OPS.md)). BI 셀프서비스 질의 수요가 실체화될 때 재검토.
- **운영**: OM ingestion(메타데이터 + dbt artifacts)은 일 1회 스케줄 파이프라인으로 platform이 소유. `glossary.md` → OM Glossary 발행은 승격 시점에 수동(초기) — 자동화는 [roadmap](roadmap.md).
