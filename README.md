# PCS 데이터 파이프라인

.sql 기반 Extract → Transform → Load 를 **쉽게 보는** 것이 목적이다.
반도체 부대설비(스크러버·펌프·칠러) PCS기술팀의 데이터를 brz→slv→gld 계층으로 표준화한다 —
엔지니어 개인 Excel 가공으로 흩어진 데이터 프로덕트의 재정착 (배경 원문: [archive/](archive/)).

## 개념 — 도구가 각자 맡는 것

| 관심사 | 도구 | 어떻게 |
|---|---|---|
| 데이터 모델 정의 | **dbt** | 모델 1개 = .sql 1개. 설명은 .sql 헤더 주석, 테스트는 옆의 `_*__models.yml` — 정의가 전부 `dbt/` 안에서 끝난다 |
| DAG 자동화 | **Cosmos** | dbt 프로젝트를 파싱해 모델·테스트 태스크를 자동 생성 — dbt 모델 추가 = 파이프라인 반영, 오케스트레이션 코드 작업 없음 |
| 데이터 계보 | **dbt** | `ref()`/`source()` 선언이 곧 의존 그래프 — `dbt docs generate` 가 리니지 문서 산출 |
| 품질 체크 | **dbt test** | 모델 run 직후 소속 테스트 실행(Cosmos AFTER_EACH), 실패 시 하류 차단 |
| 데이터 도착 감지 | **Airflow sensor / Asset** | extract 완료가 Asset 이벤트를 발행 → dbt DAG 자동 기동. API 수신 감지는 deferrable HttpSensor ([dags/sensor_api_demo.py](dags/sensor_api_demo.py)) |
| 대용량 추출·변환 | **Spark (실서버)** | 여러 대의 운영 Oracle → 회사 Spark 로 추출, 임시 저장소는 S3 또는 Postgres ([spark/jobs/](spark/jobs/)) |

## 데이터 흐름

```
운영 Oracle DB 들 (EES 등)
   │  Extract — 로컬: python 로더(dags/lib/snapshot.py) / 실서버: Spark job(spark/jobs/)
   ▼
warehouse Postgres (임시 저장소 — 소모성 연산 공간, 정본 아님)
   brz(원형 보존) ──[dbt: Cosmos 가 DAG 화]──▶ slv(정제·표준화) ──▶ gld(비즈니스 마트)
                     각 모델 run 직후 dbt test — 실패 시 하류 차단
```

- 기동은 cron 이 아니라 **데이터 이벤트**: extract 가 brz 적재를 마치면 Asset 이벤트 발행 → `dbt_pcs_transform` DAG 가 구독해 깬다.
- 주기의 유일한 결정 지점은 [dags/lib/sources.yml](dags/lib/sources.yml) 의 `schedule` — dbt 모델은 주기를 갖지 않는다.

## 시작하기

```bash
docker compose up -d --build     # warehouse Postgres + Airflow standalone (mock 소스 자동 시드)
# http://localhost:8080  (로컬 실습 — 로그인 생략)
```

DAG 3종이 보이면 성공: `extract__ees_portmaster2` → (Asset) → `dbt_pcs_transform`, 그리고 `sensor_api_demo`.
extract 를 트리거하면 mock 47행이 brz 로 적재되고, dbt DAG 가 자동 기동해 slv 뷰 → gld 테이블(설비/배관/협력사 기준정보) → 테스트까지 이어진다.

```bash
# 계보 문서 (모델 간 의존 그래프)
docker compose exec airflow /opt/airflow/dbt_venv/bin/dbt docs generate --project-dir /opt/airflow/dbt --profiles-dir /opt/airflow/dbt
# 전체 리셋
docker compose down -v
```

## 늘리는 법

**모델 추가** — `dbt/models/` 에 .sql 하나. 헤더 주석에 설명, 옆 yml 에 테스트. 끝 — Cosmos 가 다음 파싱에서 태스크로 편입한다.

**소스 추가** — [dags/lib/sources.yml](dags/lib/sources.yml) 에 블록 하나. 블록 1개 = extract DAG 1개 + Asset 자동 생성.

**실서버 전환** — 대용량 Oracle 소스는 extract 의 PythonOperator 자리를 `SparkSubmitOperator` 로 교체하고 ([spark/jobs/extract_portmaster2_full.py](spark/jobs/extract_portmaster2_full.py) 스텁 참조), 임시 저장소를 S3 또는 스테이징 Postgres 로 잡는다. dbt 이후 구간은 그대로.

## 구조

```
dags/               extract 팩토리 · Cosmos dbt DAG · sensor 데모 (+ lib/ 공용 코드·소스 선언)
dbt/                데이터 모델 정의 전부 — models(slv/gld/sbx) · seeds · tests
spark/              실서버용 Spark 추출 job (로컬 미실행 스텁)
init/               warehouse 초기화 (스키마·롤·mock 시드)
archive/            프로젝트 배경·요구사항 기록 (참고용 보관)
docker-compose.yml  로컬 스택 2서비스 — warehouse Postgres + Airflow standalone
```

계층 규칙: **slv** 는 원천값 보존(정제만, `stg_<소스>__` 명명), **gld** 는 비즈니스 판단(`dim_`/`fct_`), **sbx** 는 자유 실험 후 승격. 시크릿은 `.env` 로만 (커밋 금지).
