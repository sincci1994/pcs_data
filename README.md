# PCS Airflow Practice

회사 PCS Data Product 파이프라인 구축에 앞서, 집에서 **Oracle + Airflow + dbt**로
설비 센서 데이터 파이프라인을 end-to-end로 만들어 보고, 그 위에 **데이터 옵저버빌리티(Marquez)**와
**비즈니스 카탈로그(OpenMetadata)**까지 붙여 보는 연습 프로젝트.

> 첫 데이터 제품: **설비 센서 일별 집계** `PCS_GOLD.G_WP_EQP_SENSOR_KPI_D`
> (설비×센서×일 단위 평균/최대/알람건수/가동률)

---

## 전체 아키텍처

```
                      ┌──────────── Airflow (오케스트레이션) ────────────┐
                      │  추출 DAG (DagFactory)   변환 DAG (Sensor+Cosmos) │
                      └───────┬───────────────────────────┬─────────────┘
                              │ OracleHook                 │ dbt run (ref→Task 자동)
   목데이터 ─► [SRC_SCADA] ──►│ [PCS_LND] ─► [PCS_SLV] ─► [PCS_CORE] ─► [PCS_GOLD]
   gen_mock     원천 모사     │  수신버퍼     표준화        Fact/Dim/Bridge   공식 마트
                              │                                              │
                              └──────────── [PCS_CTL] 통제/관측 ◄────────────┘
                                            (실행이력·품질·헬스 뷰)

   관측·해석 레이어:
     Marquez (OpenLineage)     = 기술 계보 + 런타임 헬스 (어느 단계가 느리고 끊겼나)
     OpenMetadata              = 비즈니스 온톨로지 (7도메인·용어집·카탈로그)
```

데이터는 전부 **Oracle 단일 인스턴스** 안의 스키마(=유저) 6계층으로 흐른다. Airflow 메타DB(Postgres)는 엔진 살림용일 뿐 데이터가 아니다.

---

## 기술 스택 / 접속

| 컴포넌트 | 역할 | 접속 |
|---|---|---|
| **Oracle** (gvenzl/oracle-free) | 데이터 계층 전부 (SRC/LND/SLV/CORE/GOLD/CTL) | `localhost:1521` · service `FREEPDB1` · `SYSTEM`/`oracle` |
| **Airflow** (LocalExecutor) | 추출·변환 오케스트레이션 | http://localhost:8080 · `airflow`/`airflow` |
| **dbt** (dbt-oracle, Cosmos) | SLV→CORE→GOLD 변환 | (Airflow 안에서 실행) |
| **Marquez** | 데이터 플로우 + 런타임 헬스 | http://localhost:3000 (namespace `pcs`) |
| **OpenMetadata** | 비즈니스 도메인·카탈로그 | http://localhost:8585 · `admin@open-metadata.org`/`admin` |

> Postgres(8080 아님)·Redis 등은 인프라용. Marquez/OpenMetadata는 선택 레이어.

---

## 빠른 시작

```bash
# 1) 파이프라인 본체 (Oracle + Airflow + Marquez)
docker compose up -d --build          # Oracle 최초 기동 60~90초 소요

# 2) 비즈니스 카탈로그(선택)
cd openmetadata && docker compose up -d && cd ..
```
기동 후 Oracle 객체/권한이 다 잡혔는지 확인하고, 누락 시 [`init/README.md`](init/README.md)의 수동 보정 절차를 따른다.

---

## end-to-end 사용법 (런북)

> Windows(Git-Bash)에서는 `docker compose exec`에 절대경로를 넘길 때 **`MSYS_NO_PATHCONV=1`** 접두.

```bash
# ① 목데이터 생성 (원천에 하루치 적재)
MSYS_NO_PATHCONV=1 docker compose exec -T airflow-scheduler \
  python /opt/airflow/tools/gen_mock_trace.py --date 2026-06-01 --host oracle

# ② 추출 DAG 트리거 (원천 → PCS_LND)
MSYS_NO_PATHCONV=1 docker compose exec -T airflow-scheduler \
  airflow dags trigger scada_extract_daily -e "2026-06-01T00:00:00+00:00"

# ③ 변환 DAG 트리거 (Sensor 게이트 → dbt: SLV→CORE→GOLD)
MSYS_NO_PATHCONV=1 docker compose exec -T airflow-scheduler \
  airflow dags trigger sensor_daily_transform -e "2026-06-01T00:00:00+00:00"

# ④ 결과 검증
docker compose exec -T oracle bash -lc \
  "echo 'SELECT * FROM PCS_GOLD.G_WP_EQP_SENSOR_KPI_D;' | sqlplus -s system/oracle@localhost:1521/FREEPDB1"

# ⑤ 헬스/계보 확인
#   - 병목/끊김:  PCS_CTL.V_BOTTLENECK / V_FRESHNESS / V_VOLUME_ANOMALY
#   - 데이터 플로우: Marquez(localhost:3000) / 비즈니스 도메인: OpenMetadata(localhost:8585)
```

---

## 디렉토리 & 문서 인덱스

각 시스템의 상세 설명·사용법·겪은 이슈는 해당 폴더 README에 있다.

| 폴더 | 무엇 | 문서 |
|---|---|---|
| `init/` | Oracle 스키마·권한·원천/CTL 초기화 SQL | [init/README](init/README.md) |
| `tools/` | 목데이터 생성기 | [tools/README](tools/README.md) |
| `common/` | 추출 callable + CTL 로깅 (OracleHook) | [common/README](common/README.md) |
| `dags/` | 오케스트레이션 — DagFactory(YAML) + Cosmos(.sql) + Sensor | [dags/README](dags/README.md) |
| `transform/dbt/` | Medallion 변환 모델 (SLV/CORE/GOLD) | [transform/dbt/README](transform/dbt/README.md) |
| `openmetadata/` | 비즈니스 온톨로지/카탈로그 | [openmetadata/README](openmetadata/README.md) |

루트 파일: `docker-compose.yaml`(Oracle/Postgres/Airflow/Marquez), `Dockerfile`(airflow+dbt venv), `requirements.txt`.

---

## 이 프로젝트의 핵심 학습 포인트

1. **`.sql`만 추가 → Task 자동 생성**: dbt `ref()` 의존성을 Cosmos가 Airflow Task로 자동 전개. 병렬 가지는 동시 실행(소요시간=critical path). → [dags](dags/README.md)
2. **Sensor 게이트**: 시간이 아닌 **데이터 도착/선행완료 기준** 트리거(ExternalTaskSensor + SqlSensor). → [dags](dags/README.md)
3. **Medallion + Prefix**: LND→SLV→CORE→GOLD, 원천값/표준값 병행, Grain 확정, X_ Bridge(비즈니스 재해석). → [transform/dbt](transform/dbt/README.md)
4. **옵저버빌리티 두 레이어**: 기술 계보·헬스(Marquez) vs 비즈니스 온톨로지(OpenMetadata). → [openmetadata](openmetadata/README.md)

---

## 공통 주의사항

- **Windows 경로 변환**: `docker compose exec`에 `/opt/...` 절대경로 → `MSYS_NO_PATHCONV=1` 접두.
- **gvenzl 최초 init 변덕**: 첫 기동 시 일부 grants/DDL 미반영 가능 → 기동 후 검증, 누락 시 수동 재적용([init](init/README.md)).
- **완전 초기화**: `docker compose down -v`로 볼륨까지 지운 뒤 `up`하면 init이 처음부터 다시 실행된다.
- **메모리**: Oracle+Airflow+Marquez(+OpenMetadata)까지 띄우면 Docker에 8GB 이상 권장.
