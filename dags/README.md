# `dags/` — 오케스트레이션 (Airflow DAG)

## 목적
"무엇을, 언제, 어떤 순서로" 실행할지 정의한다. 이 프로젝트의 **핵심 학습 포인트**인 "설정/`.sql`만 추가하면 Task가 자동 생성되는" 두 메커니즘이 여기 있다.

## 파일·역할
| 파일 | 역할 |
|---|---|
| `factory_loader.py` | `configs/*.yaml`을 전부 DAG으로 자동 로드 (단 3줄) |
| `dagfactory/core.py` | 경량 DagFactory — YAML을 읽어 DAG/Task를 동적 생성 |
| `configs/scada_extract_daily.yaml` | 추출 DAG 정의(원천→LND) |
| `transform_dbt_dag.py` | 변환 DAG — Sensor 게이트 + Cosmos가 dbt 모델을 Task로 자동 전개 |

## ★ 자동 Task 생성은 두 종류
### 1) 추출 = DagFactory (YAML → DAG)
`configs/`에 YAML 한 개를 추가하면 DAG이 생긴다. YAML에 `operator`(클래스 경로)와 `python_callable`(함수 경로)을 **문자열로** 적으면, `core.py`가 `import_string`으로 실제 객체를 동적 로드한다.
```yaml
tasks:
  extract_trace:
    operator: airflow.operators.python.PythonOperator
    python_callable: common.oracle_etl.extract_trace   # ← 문자열로 함수 지정
    dependencies: [ctl_start]
```

### 2) 변환 = dbt + Cosmos (.sql → Task)  ← 당신이 원했던 "그 그림"
`transform/dbt/models/`에 `.sql` 모델을 추가하고 `{{ ref('다른모델') }}`로 연결하면:
- dbt가 `ref()`/`source()`를 파싱해 **의존성 그래프**를 만들고
- **astronomer-cosmos**의 `DbtTaskGroup`이 **모델 1개 = Airflow Task 1개**로 자동 전개한다.
- 의존성 없는 가지는 **병렬 실행**되고, 전체 소요시간은 가장 긴 경로(critical path).
- 즉 **YAML/DAG 코드 수정 없이 `.sql`만 추가**하면 그래프에 Task가 자동으로 낀다.

## Sensor 게이트 (transform_dbt_dag.py 앞단)
시간이 아니라 **데이터/선행작업 기준**으로 다음 단계를 연다:
```
wait_for_extract (ExternalTaskSensor) → 추출 DAG의 ctl_end 완료(같은 logical date) 대기
        ↓
wait_lnd_ready (SqlSensor)            → PCS_LND.L_SCADA_TRACE 행수 > 0 확인
        ↓
dbt_pcs (DbtTaskGroup)               → 모델/seed/test 자동 Task
```

## 사용/실행법
```bash
# DAG 보이기/강제 재파싱
docker compose exec -T airflow-scheduler airflow dags reserialize
docker compose exec -T airflow-scheduler airflow dags list

# 특정 logical date로 트리거 (Windows는 MSYS_NO_PATHCONV=1)
MSYS_NO_PATHCONV=1 docker compose exec -T airflow-scheduler \
  airflow dags trigger scada_extract_daily -e "2026-06-01T00:00:00+00:00"

# 실패 Task만 다시 실행
MSYS_NO_PATHCONV=1 docker compose exec -T airflow-scheduler \
  airflow tasks clear sensor_daily_transform --start-date 2026-06-01 --end-date 2026-06-01 --yes
```
UI: http://localhost:8080 (airflow / airflow) → Graph View에서 자동 생성된 Task 확인.

## 주의·겪은 이슈
- **DagFactory DAG이 안 보이는데 에러도 없을 때**: Airflow `safe_mode`는 파일에 **"airflow"와 "dag" 문자열이 둘 다** 있어야 DAG 파일로 인식한다. `factory_loader.py` docstring에 'airflow'를 넣어 해결.
- **ExternalTaskSensor 정렬**: 추출/변환 DAG 둘 다 `@daily`라 **같은 logical date**로 매칭된다. 트리거할 때 두 DAG을 같은 `-e` 날짜로.
- **Cosmos OpenLineage**: LOCAL 실행모드(`dbt_executable_path` 사용)에서만 lineage 이벤트를 emit → Marquez로 전송됨.
- **Windows 경로 변환**: `docker compose exec`에 `/opt/...` 절대경로를 넘기면 Git-Bash가 변환 → `MSYS_NO_PATHCONV=1` 접두.

↑ [최상위 README](../README.md) · 관련: [`common/`](../common/README.md)(추출 함수), [`transform/dbt/`](../transform/dbt/README.md)(모델)
