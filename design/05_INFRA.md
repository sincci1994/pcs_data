# 05. 인프라 — 로컬 검증 스택 + 원격 이식

> 상태: 설계 확정(2026-07-09, 舊 계획수정안 편입) — 구축은 **Phase 2**.
> 원격 리눅스 서버(`~/personal/ssc/pcs_data`)의 기존 스택 문제를 로컬(Win11 + Docker Desktop/WSL2)에서 표준 구성으로 재현·검증 후 이식한다.

## 배경 — 원격 스택의 구조적 문제 2건

1. **Airflow 메타DB 초기화·admin 생성 미자동화** — 첫 기동 시 logs 볼륨 권한 오류(UID 50000) → 수동 chown 후에도 "please run airflow db init" 크래시 루프.
2. **Airflow 이미지에 dbt 미설치** — dbt 변환이 의도였으나 이미지에 반영 안 됨.

**근본 원인**: OpenMetadata 공식 패턴은 `ingestion_dependency.sh` 엔트리포인트가 단일 컨테이너에서 `db migrate`→admin 생성→기동을 전부 수행한다. 원격은 webserver/scheduler를 쪼갠 커스텀 구성이라 이 초기화 체인이 빠짐. 또한 "db init" 문구는 Airflow 2.x — 최신 OM ingestion(1.12.x)은 Airflow 3.x(`db migrate`, SimpleAuthManager)로 명령 체계가 다르다.

## 버전 핀 (호환성 확인 완료)

| 구성요소 | 버전 | 비고 |
|---|---|---|
| OpenMetadata server/ingestion/postgresql 이미지 | 1.12.13 | **3개 태그 동일 버전 유지** |
| ingestion 베이스 Airflow | 3.1.5 (Py3.10) | OM 1.12.13 기준 |
| dbt-core / dbt-postgres | 1.11.12 / 1.10.2 | 별도 venv 격리 |
| Elasticsearch | 9.3.0 | OM quickstart 기본 |
| dbt 웨어하우스 | postgres:16-alpine | 원격에선 기존 DB로 치환 |

> 舊 계획의 astronomer-cosmos는 Manager/Model 재설계([adr/0002](adr/0002-manager-model-dynamic-dag.md))로 **제외** — 커스텀 이미지에서 cosmos 설치 불필요.

## compose 구성 (공식 quickstart-postgres 1.12.13 대비 diff 최소화)

| 서비스 | 처리 |
|---|---|
| `postgresql` | 유지 — openmetadata_db + airflow_db 자동 생성 |
| `elasticsearch` | 유지, `ES_JAVA_OPTS=-Xms512m -Xmx512m` 하향 |
| `execute-migrate-all` | 유지 (Exited(0)이 정상) |
| `openmetadata-server` | 유지 (`PIPELINE_SERVICE_CLIENT_ENDPOINT: http://ingestion:8080`) |
| `ingestion` | **수정**: `build:` 커스텀 이미지. entrypoint는 공식 그대로(초기화 체인 담당 — 별도 airflow-init 불필요). env(AIRFLOW_ADMIN_*, DBT_*)·volumes(dags, dbt)·depends_on(warehouse healthy) 추가 |
| `warehouse` | **신규**: postgres:16-alpine, `5433:5432`, healthcheck, named volume |

커스텀 이미지 (dbt는 의존성 충돌 방지 위해 venv 격리):

```dockerfile
FROM docker.getcollate.io/openmetadata/ingestion:1.12.13
USER root
RUN python -m venv /opt/airflow/dbt_venv \
    && /opt/airflow/dbt_venv/bin/pip install --no-cache-dir dbt-core==1.11.12 dbt-postgres==1.10.2 \
    && chown -R airflow:0 /opt/airflow/dbt_venv
USER airflow
```

## Windows(WSL2) 사전 조치
- `.wslconfig`: `[wsl2] memory=12GB` (스택 합계 ~6GB) → `wsl --shutdown` 후 Docker Desktop 재시작.
- ES `vm.max_map_count=262144` 확인: `wsl -d docker-desktop sysctl vm.max_map_count`.
- dags/·dbt/만 bind mount, DB/ES/logs는 named volume.

## 검증 시나리오 (Phase 2 완료 조건)
1. `docker compose config` → `up -d --build` → `ps`: execute-migrate-all Exited(0), 나머지 healthy.
2. ingestion 로그에서 db migrate 완료 + scheduler 기동 (**원격 문제 1 재발 체크포인트**).
3. Airflow(`:8080`)·OM(`:8585`) 로그인.
4. DAG 팩토리가 manifest에서 Model/Manager DAG 전개 (**Dynamic DAG 체크포인트** — Phase 3 코드 필요).
5. 샘플 모델 빌드 성공 → warehouse에서 결과 조회.
6. OM에서 Postgres 서비스 + dbt Agent 실행 → Lineage 확인 (**OM 통합 체크포인트**).

## 원격(pcs_data) 이식 체크리스트
1. webserver/scheduler 분리 구성 → **단일 ingestion 컨테이너**(공식 패턴)로 통합.
2. Airflow 2→3 차이 반영: `db init`→`db migrate`, `users create`→SimpleAuthManager 환경변수. **주의**: SimpleAuthManager는 로컬 검증용 — 원격에서 여러 명이 쓰면(분석가 wrk 트리거 vs 운영 clear 권한 구분) FAB auth manager 전환 검토.
3. 리눅스 bind mount: `chown -R 50000:0 dags dbt`; logs는 named volume.
4. 기존 OM DB/ES named volume 백업 후 migrate; Airflow 메타DB 초기화 허용 여부 사전 확인. 운영 개시 후에는 Airflow 메타DB·OM DB **상시 백업**을 Phase 2 산출물로 구성 (warehouse는 소모성 — 백업 불요, → [08 §1](08_DATA_OPS.md)).
5. `vm.max_map_count` 영구 설정, `.env` 비밀번호 전면 교체, 내부 포트 외부 노출 차단.
6. server/ingestion/postgresql 이미지 3태그 동일 버전 규칙.
7. 사내망(폐쇄망·프록시·사설 CA) 빌드 인자 — 이전 구현의 처리 방식은 git 히스토리(`8716803`) 참조.
8. **배포 동기화**: "커밋 → DAG 자동 생성"이 성립하려면 서버가 저장소를 clone하고 주기적 `git pull`(또는 배포 스크립트)로 dags/·dbt/를 갱신해야 한다 — 반영 지연 허용치와 함께 방식 확정 (Phase 2).
