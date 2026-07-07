# PCS Airflow Practice

> 🗺️ 규약·레이아웃은 [`CLAUDE.md`](CLAUDE.md)부터. 목표 시나리오는 [design/09](design/09_SCENARIO_UTILITY_USAGE.md).

회사 PCS Data Product 구축에 앞서 **Oracle + Airflow + dbt**로 설비 데이터 파이프라인을
end-to-end 연습하는 레포. 옵저버빌리티(Marquez) + 비즈니스 카탈로그(OpenMetadata) 포함.
현재 실행 가능한 코드는 SCADA 센서 샘플의 척추이며, [design/09](design/09_SCENARIO_UTILITY_USAGE.md) 시나리오(Utility 사용량, Postgres 웨어하우스)로 재작성 예정.

## 아키텍처 (현재 샘플)

```
              ┌────────── Airflow ──────────┐
              │ 추출 DAG(DagFactory)  변환 DAG(Sensor+Cosmos) │
              └────┬─────────────────────┬───┘
목데이터 ─► [SRC_SCADA] ─► [PCS_LND] ─► [PCS_SLV→CORE→GOLD]
              └──────── [PCS_CTL] 통제/관측 ◄────────┘
관측: Marquez(기술 계보·런타임) · OpenMetadata(비즈니스 카탈로그)
```

## 접속

| 컴포넌트 | 접속 |
|---|---|
| Oracle (gvenzl/oracle-free) | `localhost:1521` · service `FREEPDB1` · `SYSTEM`/`oracle` |
| Airflow (LocalExecutor) | http://localhost:8080 · `airflow`/`airflow` |
| Marquez | http://localhost:3000 (namespace `pcs`) |
| OpenMetadata (선택) | http://localhost:8585 · `admin@open-metadata.org`/`admin` |

## 빠른 시작 / 런북

> Windows(Git-Bash): `docker compose exec`에 `/opt/...` 절대경로를 넘길 때 `MSYS_NO_PATHCONV=1` 접두.

```bash
docker compose up -d --build     # Oracle 최초 기동 60~90초. 시크릿은 .env (커밋 금지)

# ① 목데이터 생성
MSYS_NO_PATHCONV=1 docker compose exec -T airflow-scheduler \
  python /opt/airflow/tools/gen_mock_trace.py --date 2026-06-01 --host oracle
# ② 추출 DAG (원천 → PCS_LND)
MSYS_NO_PATHCONV=1 docker compose exec -T airflow-scheduler \
  airflow dags trigger scada_extract_daily -e "2026-06-01T00:00:00+00:00"
# ③ 변환 DAG (Sensor 게이트 → dbt)  — 같은 -e 날짜로
MSYS_NO_PATHCONV=1 docker compose exec -T airflow-scheduler \
  airflow dags trigger sensor_daily_transform -e "2026-06-01T00:00:00+00:00"
# ④ 결과 확인
docker compose exec -T oracle bash -lc \
  "echo 'SELECT * FROM PCS_GOLD.G_WP_EQP_SENSOR_KPI_D;' | sqlplus -s system/oracle@localhost:1521/FREEPDB1"
```

헬스: `PCS_CTL.V_FRESHNESS / V_BOTTLENECK / V_VOLUME_ANOMALY` (→ [quality/runbook](quality/runbook.md)).
카탈로그(선택): `cd platform/infra/openmetadata && docker compose up -d` (→ [런북](platform/infra/openmetadata/README.md)).

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
- **gvenzl 최초 init 변덕**: 첫 기동 시 일부 grants/DDL 미반영 가능 → 검증 후 수동 재적용([infra/init](platform/infra/init/README.md)). 완전 초기화는 `docker compose down -v` 후 `up`.
- **메모리**: Oracle+Airflow+Marquez(+OM)까지 띄우면 Docker 8GB 이상 권장.
