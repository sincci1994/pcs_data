# PCS 데이터 파이프라인

반도체 부대설비(스크러버·펌프·칠러) 담당 PCS기술팀의 데이터 표준화 파이프라인 — **Airflow 3.x + dbt + OpenMetadata**.
엔지니어 개인 Excel 가공으로 흩어진 데이터 프로덕트를 표준 계층(brz→slv→gld)과 비즈니스 정의(온톨로지)로 재정착시킨다.

- 처음 쓰는 사람 → [GUIDE.md](GUIDE.md)
- 요구사항 원문 → [design/00_REQUIREMENTS.md](design/00_REQUIREMENTS.md) · 목표 구조 설계안 → [design/11_TARGET_ARCHITECTURE.md](design/11_TARGET_ARCHITECTURE.md)

## 1. 풀려는 문제

```
시스템 데이터 불신 → 협력업체 엑셀 의존 → 시스템 입력 등한시 → 시스템 방치 → 불신 심화 (악순환)
```

- 레거시 앱 VIEW_TABLE을 못 믿어 엔지니어마다 Excel로 재가공 → 개인 판단에 의존한 불규칙한 "그림자 데이터 프로덕트" 난립.
- 전체 비즈니스 플로우 문서 부재, 이 문제를 풀 전문가 부재 — 지식을 사람이 아니라 시스템(정의·기록·규칙)에 축적해야 한다.
- 접근: 실무자의 변환 로직을 인터뷰로 발굴(AS-IS 인테이크) → SQL(dbt 모델)로 표준화 → 레거시 산출물과 대사 검증 → 승격. 이후는 분석가가 SQL만 추가하면 파이프라인에 자동 반영되는 셀프서비스 구조.

규모 전제: 설비 자산등록 25만 대 / 운영 중 15만 대(파이프라인 볼륨 기준), 소스 시스템 4종(EES·SMDM·GEMS·EAM). 상세 → [design/11 §1·2](design/11_TARGET_ARCHITECTURE.md)

## 2. 전체 아키텍처

```
소스 (EES 등 — 시스템 I/F로 주기 제공)
   │  ① Extract — Airflow 태스크 (chunked fetch + bulk insert, 워터마크+lookback 멱등)
   ▼
warehouse Postgres  ← 소모성 변환 연산 공간 (rolling window만 보유, 정본 아님·백업 안 함)
   brz(원형 보존) → [dbt] slv(정제·표준화) → gld(비즈니스 마트)
   │  ② Validate — dbt test (실패 시 Publish 차단)
   │  ③ Publish — staging 적재 후 원자적 swap (전량/윈도 교체)
   ▼
서빙 Oracle  ← 저장·서빙 전용 (IT부서 소유, 리소스 제한 제약 — 연산 부하 없음)
   + OpenMetadata — 카탈로그·리니지·용어집·테스트 결과
```

- **저장 책임 분리**: 장기 보관은 소스 Oracle(원본)과 서빙 Oracle(SLV+GOLD 이력)이 담당. warehouse는 언제든 재적재 가능한 계산 캐시. → [design/08 §1](design/08_DATA_OPS.md)
- **질의 경계**: 소비자는 서빙 Oracle만, 저작자(분석가)는 warehouse만 본다. → [design/08 §1.1](design/08_DATA_OPS.md)

## 3. 핵심 설계 결정과 근거

평가자가 짚을 만한 결정들. 전체 결정 표는 [design/02](design/02_ARCHITECTURE.md), DAG 상세는 [design/03](design/03_DAG_DESIGN.md).

### 모델당 DAG + Manager 오케스트레이션 (DAG-of-DAGs)

통상의 "DAG 하나에 태스크 몰아넣기"(Cosmos DbtTaskGroup이 초기 척추였음) 대신, dbt 모델 1개 = `model__<이름>` DAG 1개로 쪼개고 `manager__` DAG가 의존 위상 순으로 트리거한다.

- 연결의 정본은 SQL 속 `ref()`/`source()` 선언 하나 — dbt manifest의 의존 그래프를 DAG 팩토리가 파싱해 Manager 트리거 간선을 만들고, 같은 그래프가 OM 리니지로 발행된다. 실행 순서와 데이터 계보가 한 원천에서 나온다.
- 선택 이유: 모델 단위 독립 재실행·백필·run 이력(분석가 셀프서비스의 운영 단위 = 데이터 제품), DAG 목록 = 자산 목록. 트레이드오프와 함께 [adr/0002](design/adr/0002-manager-model-dynamic-dag.md)에 기록.
- DAG 수는 설비 수가 아니라 **모델 수**에 비례(현재 8개 수준, 현실 상한 수백). 확장 손잡이: trigger pool 격리 → deferrable+triggerer → 그룹핑 해제 → 팩토리 분할.

### 스케줄이 아니라 데이터 이벤트로 기동

Manager는 cron이 아니라 extract DAG가 brz 적재 완료 시 발행하는 **Asset 이벤트**(Airflow 3 data-aware scheduling)로 깬다. 소스마다 적재 주기가 달라도 의존성 연쇄가 자동으로 이어진다.

주기의 유일한 결정 지점은 `sources.yml`의 `schedule`(extract cron)이다 — dbt 모델은 주기를 갖지 않고, 소스 적재 grain(예: 5분 집계)과 파이프라인 캐던스(예: 3시간 배치 추출)는 분리해 결정한다. → [design/03 캐던스](design/03_DAG_DESIGN.md)

### 런타임 결정론 — LLM·컴파일 금지

DAG 파싱·실행 경로에는 커밋된 `manifest.json`/`sources.yml`만 존재한다. dbt compile은 저작 단계(CI 머지 게이트)에서, AI Agent는 오프라인 저작에서만. 운영 중 그래프가 변하는 경로가 없다.

### 분석가 셀프서비스 (불변 규칙)

모델(.sql)+schema.yml+manifest 커밋 = DAG 자동 생성·Manager 편입·Publish·OM 발행까지 자동. **모델 추가에 개발자 코드 작업이 필요해지면 설계 위반.** 신규 소스도 `sources.yml` 선언만. → [design/07](design/07_AUTHORING_FLOW.md)

### 승격 게이트 (거버넌스)

`sbx` 실험 계층(수동 트리거 전용, Manager·Publish 제외)에서 자유 탐색 → glossary 정의 확정 + 테스트 + (이관 모델) 레거시 대사 검증 통과 시에만 slv/gld 진입. 데이터 질의 브레이크가 기술이 아니라 정의에 걸려 있다. → [design/07](design/07_AUTHORING_FLOW.md) · [design/04](design/04_AS_IS_INTAKE.md)

### 온톨로지 — 시멘틱 정보의 3층 관계 축

정의는 glossary(산식·단위·**관계** `[[용어명]]` 필드), 컬럼은 schema.yml, 계보는 manifest→OM 리니지 — 세 원천이 각각 용어 간/테이블 간/자산 간 관계를 담당한다. 쿼리 타임 시멘틱 레이어(MetricFlow·Cube류)는 **의도적 미도입**: "정의 1곳/소비 N곳"을 gld 물질화가 빌드 타임에 달성하고 소비자는 서빙 테이블을 직접 읽는다. 지식그래프(GraphRAG 등)가 필요해지면 3층을 합쳐 구성한다. → [design/02 온톨로지](design/02_ARCHITECTURE.md)

### 운영 정책

지연 도착 2단 방어(lookback 24h + 주기 재동기화), 스키마 드리프트 fail-fast, Publish 원자성(staging+swap), 알림 단일 notifier, 파티션 drop 기반 보존. → [design/08](design/08_DATA_OPS.md)

## 4. 알려진 트레이드오프 — 여기를 도전해 달라

| 결정 | 지불한 비용 | 현재 판단 |
|---|---|---|
| 자체 DAG 팩토리 (Cosmos 제거) | 파서·트리거 배선·복구 로직 직접 유지보수 | 요구(모델 단위 운영)가 Cosmos 밖 — [adr/0002](design/adr/0002-manager-model-dynamic-dag.md) |
| Manager의 동기 트리거 (`wait_for_completion`, deferrable 미사용) | trigger 태스크가 대기 중 워커 슬롯 점유 — 그래프 병렬 폭이 슬롯에 근접하면 교착 위험 | 현 볼륨(폭 좁음, max_active_runs=1)에선 단순함이 우선. triggerer 도입은 확장 손잡이 |
| dbt-postgres 단일 엔진 (PySpark 보류) | 5분 grain 4억~13억 행/일 시나리오 재개 시 단일 노드 한계 가능 | 실측 초과 시점이 재검토 트리거 — [adr/0003](design/adr/0003-defer-pyspark-multi-engine.md) |
| SLV까지 서빙 Oracle에 publish | 전송·저장 비용 증가 | 소비자가 warehouse를 몰라도 되는 경계 유지가 우선, 비용 손잡이 3개 확보 — [design/08 §3](design/08_DATA_OPS.md) |
| 인터뷰 기반 AS-IS 발굴 (자동화 안 함) | 사람 시간 소요 | 변환 의도는 쿼리에서 복원 불가 — 한시적 프로세스로 한정 |
| 소비자용 결측 가시화 미구현 | "어떤 정보가 안 오는지"는 현재 운영자 알림 중심 | 인지된 갭 — [design/11 §6](design/11_TARGET_ARCHITECTURE.md) · [roadmap](design/roadmap.md) |
| Manager의 Asset 리스트 구독 = AND 의미론 | 캐던스 다른 두 번째 소스 추가 시 느린 소스에 묶이고, 한 소스 실패가 전체 기동 차단 | 소스 1개인 현재는 미발현. 전환 조건·방식(AssetAny+영향 하위그래프 트리거) 명문화 — [design/03 캐던스](design/03_DAG_DESIGN.md) |

## 5. 저장소 구조 (역할 기반)

```
governance/   용어집·AS-IS 인테이크 기록 (정의의 원천)
transform/    dbt 모델 (slv→gld + sbx)
platform/     dags(팩토리 2종) · extract(sources.yml+로더) · common · infra(compose 스택)
quality/      대사 검증 · dbt test 정책
workspace/    instructions(지시) · pdca(계획/실행/평가/개선)
design/       요구사항 · 아키텍처 · ADR · 로드맵
```

각 폴더의 CLAUDE.md에 저작 규칙이 있다. 전체 규약은 [CLAUDE.md](CLAUDE.md).

## 6. 문서 인덱스

| 문서 | 내용 |
|---|---|
| [design/00_REQUIREMENTS.md](design/00_REQUIREMENTS.md) | 요구사항 원문 + 반영 매핑 |
| [design/11_TARGET_ARCHITECTURE.md](design/11_TARGET_ARCHITECTURE.md) | 목표 구조 설계안 — 조직·소스 지형·팀 경계·저장소 제약 |
| [design/01_OVERVIEW.md](design/01_OVERVIEW.md) | 문제·목적·범위 |
| [design/02_ARCHITECTURE.md](design/02_ARCHITECTURE.md) | 전체 아키텍처·계층·역할 분담 |
| [design/03_DAG_DESIGN.md](design/03_DAG_DESIGN.md) | Manager/Model 동적 DAG 설계 |
| [design/04_AS_IS_INTAKE.md](design/04_AS_IS_INTAKE.md) | 레거시 로직 발굴 워크플로 |
| [design/05_INFRA.md](design/05_INFRA.md) | 로컬 검증 스택 + 원격 이식 |
| [design/07_AUTHORING_FLOW.md](design/07_AUTHORING_FLOW.md) | 분석가 직접 저작 + 소스 변경 자동 재정의 |
| [design/08_DATA_OPS.md](design/08_DATA_OPS.md) | 볼륨·보존·지연·드리프트·옵저버빌리티 정책 |
| [design/09_SCENARIO_EQUIPMENT_PIPE.md](design/09_SCENARIO_EQUIPMENT_PIPE.md) | **첫 데이터 제품** — Equipment/Pipe 기준정보 |
| [design/06_SCENARIO_UTILITY_USAGE.md](design/06_SCENARIO_UTILITY_USAGE.md) | Utility 사용량 시나리오 [보류] |
| [design/10_NAMING_ORGANIZATION.md](design/10_NAMING_ORGANIZATION.md) | 계층 계약·명명·폴더 조직 전략 |
| [design/roadmap.md](design/roadmap.md) | 보류·후속 항목 |

## 7. 현재 상태

| Phase | 내용 | 상태 |
|---|---|---|
| 1 | 문서·구조 스켈레톤 (요구사항 재정렬) | 완료 (2026-07-09) |
| 2 | 인프라: OpenMetadata+Airflow compose 스택 로컬 검증 | 완료 (2026-07-09) → [platform/infra/README.md](platform/infra/README.md) |
| 3 | 코드: Manager/Model DAG 팩토리 · dbt 프로젝트 · extract | 완료 (2026-07-09) — 로컬 E2E 통과 → [design/03](design/03_DAG_DESIGN.md) |
| 4 | 첫 데이터 제품: Equipment/Pipe 기준정보 (로컬) | 완료 (2026-07-09) — 레거시 대사 일치 → [design/09](design/09_SCENARIO_EQUIPMENT_PIPE.md) |
| 5 | 원격 이식: 프록시 빌드→폐쇄망 반입 경로 | 준비 완료 (2026-07-10) — 실행은 후순위 → [ops/README](platform/infra/ops/README.md) |
| 6 | 운영 유사 로컬: Oracle 왕복(소스→변환→서빙) | 완료 (2026-07-11) — SLV+GOLD Oracle 서빙 실증 → [design/08 §1.1](design/08_DATA_OPS.md) · [GUIDE 트랙 0](GUIDE.md) |
| — | 원격 전환 잔여: EES 실접속·pcs_data 배포 | 조직 이슈 대기 → [design/05](design/05_INFRA.md) |

이전 구현(Cosmos 기반 SCADA 샘플)은 git 히스토리(`db02606` 이전)에서 참조 가능.
