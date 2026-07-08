# PCS Airflow 오케스트레이션 서버

> 🗺️ 규약·레이아웃은 [`CLAUDE.md`](CLAUDE.md)부터. 목표 시나리오는 [design/09](design/09_SCENARIO_UTILITY_USAGE.md).

PCS Data Product 의 **Airflow 기반 오케스트레이션 서버** 레포. 이 서버에서는 오케스트레이션(Airflow + dbt/Cosmos)과
보조 메타데이터 서비스(OpenMetadata 카탈로그)만 켠다 — **데이터 DB(소스 Oracle·웨어하우스 Postgres)는 전부 외부 DB 서버**에 존재하며 `.env` 접속 정보로만 연결한다. → [adr/0005](design/adr/0005-slim-orchestration-topology.md)
현재 실행 가능한 코드는 SCADA 센서 샘플의 척추이며, [design/09](design/09_SCENARIO_UTILITY_USAGE.md) 시나리오(Utility 사용량, Postgres 웨어하우스)로 재작성 예정.

## 아키텍처

```
              ┌────────── Airflow (이 서버) ──────────┐
              │ 추출 DAG(DagFactory)   변환 DAG(Sensor+Cosmos) │
              └────┬──────────────────────────┬───┘
외부 Oracle(소스) ──►│  추출  ──► 외부 Postgres [LND] ─► [SLV→CORE→GOLD]
                    └────────── [CTL] 통제/관측 ◄──────────┘
카탈로그: OpenMetadata (.env COMPOSE_FILE 로 병합 — 함께 기동)
```

## 컨테이너 구성 (이 서버에서 뜨는 것)

`.env` 에 `COMPOSE_FILE`(→ [.env.example](.env.example))을 두면 `docker compose up -d --build` 하나로 아래가 **한 프로젝트**로 뜬다 (OM 병합, → [adr/0005](design/adr/0005-slim-orchestration-topology.md)):

| 스택 | 서비스 | 실행 중 개수 |
|---|---|---|
| 코어 (`docker-compose.yaml`) | postgres(Airflow 메타DB)·airflow-webserver·airflow-scheduler (+airflow-init 1회성) | **3** |
| OpenMetadata (COMPOSE_FILE 병합) | mysql·elasticsearch·openmetadata-server·ingestion (+execute-migrate-all 1회성) | **4** |
| | **합계 실행** | **7** (+1회성 2) |

> **dbt 는 별도 컨테이너가 아니다** — Airflow 이미지에 내장(`Dockerfile` dbt 전용 venv)돼 Cosmos 가 Task 로 실행한다. **OpenMetadata 는 코어는 아니지만** `COMPOSE_FILE` 병합으로 함께 뜬다(무거움: ES 힙 1GB+). `include:` 대신 `COMPOSE_FILE` 을 쓰는 이유는 구버전 Compose(<v2.20) 호환.

> 이보다 컨테이너가 많이 보이면 이 레포 밖의 잔여물이다. 진단:
> ```bash
> docker compose ls        # 살아있는 compose 프로젝트 목록
> docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Label "com.docker.compose.project"}}'
> #  → 이 레포 프로젝트명이 아닌 행 = 다른 프로젝트/과거 폴더명의 잔여물
> docker compose down --remove-orphans   # 현 프로젝트의 고아 컨테이너 정리
> docker container prune                 # 중지된 컨테이너 일괄 제거(내용 확인 후)
> ```

## 접속

| 컴포넌트 | 접속 |
|---|---|
| Airflow (LocalExecutor) | http://localhost:8080 · `airflow`/`airflow` |
| OpenMetadata | http://localhost:8585 · `admin@open-metadata.org`/`admin` |
| 소스 Oracle / 웨어하우스 Postgres | 외부 DB 서버 — `.env` 의 `PCS_ORACLE_*` / `PCS_WH_*` |

## 빌드 & 기동

코어 이미지(`pcs-airflow-practice:latest`, 베이스 `apache/airflow:2.9.3-python3.11`)를 빌드하고 OM 4종은 pull 하여 한 프로젝트로 띄운다. 코어 빌드 단계는 `Dockerfile` 참조: ① 사설 CA(`certs/*.crt`) 등록 → ② dbt-oracle 전용 venv(`/opt/airflow/dbt_venv`, Cosmos 가 호출) → ③ Airflow 패키지(`requirements.txt`) → ④ `PYTHONPATH=/opt/airflow` 루트 import → ⑤ oracledb 드라이버 모드(기본 `thin`).

```bash
cp .env.example .env          # COMPOSE_FILE(OM 병합)·외부 PCS_ORACLE_* / PCS_WH_* · OM JWT 채우기
docker compose up -d --build  # COMPOSE_FILE 로 코어 빌드 + OM pull → 실행 7 (+init·migrate 1회)
# UI: http://localhost:8080 (airflow) · http://localhost:8585 (OpenMetadata)
```
> `.env` 의 `COMPOSE_FILE` 이 OM 을 병합한다(구분자 Linux `:` / Windows `;`). 없으면 코어만 뜬다.

- **사내망 빌드**: 프록시(`HTTP(S)_PROXY`/`NO_PROXY`)·pip 미러(`PIP_INDEX_URL`/`PIP_EXTRA_INDEX_URL`)·사설 CA(`certs/*.crt`)를 `.env` 로 주입 — 빌드 시점에만 적용(런타임 미주입, `docker history` 미노출). 집 환경은 전부 비우면 no-op. → [design/08](design/08_AIRGAP_BUILD.md)
- **폐쇄망 반입**(레지스트리 없음): 프록시 서버에서 위 이미지 6종을 `docker save` 번들로 묶어 타겟에 옮겨 `docker load` → `platform/infra/ops/airgap_images.sh` ([런북](platform/infra/ops/README.md)). 타겟은 `docker compose up -d`(**--build 금지**).
- **실타깃 Oracle**(버전 상이): `ORA_PYTHON_DRIVER_TYPE=thick` + Instant Client 이미지 베이크(폐쇄망은 런타임 다운로드 불가).
- **dbt**: 별도 명령/컨테이너 없음 — Cosmos 가 Airflow Task 로 실행.

## 런북

> Windows(Git-Bash): `docker compose exec`에 `/opt/...` 절대경로를 넘길 때 `MSYS_NO_PATHCONV=1` 접두.

SCADA 센서 샘플 파이프라인 실행(척추·참조용). 외부 Oracle 에 원천/CTL 스키마([infra/init](platform/infra/init/README.md) DDL)가 적용돼 있어야 한다. `<oracle-host>` 는 `.env` 의 `PCS_ORACLE_HOST`.

```bash
# ① 목데이터 생성 (외부 Oracle 에 SCADA 원천 채움)
MSYS_NO_PATHCONV=1 docker compose exec -T airflow-scheduler \
  python /opt/airflow/tools/gen_mock_trace.py --date 2026-06-01 --host <oracle-host>
# ② 추출 DAG (원천 → PCS_LND)
MSYS_NO_PATHCONV=1 docker compose exec -T airflow-scheduler \
  airflow dags trigger scada_extract_daily -e "2026-06-01T00:00:00+00:00"
# ③ 변환 DAG (Sensor 게이트 → dbt)  — 같은 -e 날짜로
MSYS_NO_PATHCONV=1 docker compose exec -T airflow-scheduler \
  airflow dags trigger sensor_daily_transform -e "2026-06-01T00:00:00+00:00"
# ④ 결과 확인 — 외부 Oracle 에 직접 접속 (sqlplus / SQL 클라이언트)
#   SELECT * FROM PCS_GOLD.G_WP_EQP_SENSOR_KPI_D;
```

헬스: `PCS_CTL.V_FRESHNESS / V_BOTTLENECK / V_VOLUME_ANOMALY` (→ [quality/runbook](quality/runbook.md)).

## 디렉토리

역할 기반 레이아웃 — 각 폴더의 **CLAUDE.md**가 그 영역의 규칙·시작점이다.

| 폴더 | 무엇 |
|---|---|
| `governance/` | 용어집·도메인 (정의의 원천) |
| `transform/` | dbt 변환 (SLV→CORE→GOLD) |
| `platform/` | dags·extract·common·infra ([init](platform/infra/init/README.md)·[openmetadata](platform/infra/openmetadata/README.md) 런북) |
| `quality/` | 헬스 런북·점검 쿼리 |
| `workspace/` | 지시서·PDCA·패턴·교훈 (전원 공용) |
| `design/` | 설계문서 00~09 · ADR · 로드맵 ([인덱스](design/README.md)) |
| `dev/` | 목데이터 도구 · pytest |

## 공통 주의사항
- **외부 DB 전제**: 로컬 Oracle 컨테이너는 없다. 소스 Oracle·웨어하우스 Postgres 는 외부 서버이며 스키마·권한은 DBA 가 선(先)적용한다([infra/init](platform/infra/init/README.md) DDL 참조).
- **메모리**: 코어만이면 가볍다. OpenMetadata(ES 힙 1GB+)까지 켜면 Docker 8GB 이상 권장.
