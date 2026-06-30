# `common/` — 공통 추출 로직 + CTL 로깅

## 목적
Airflow 추출 DAG이 호출하는 **재사용 Python 함수**들. Oracle 연결(OracleHook)로 원천을 읽어 `PCS_LND`에 적재하고, 실행 이력을 `PCS_CTL`에 남긴다.

## 파일·역할
| 파일 | 역할 |
|---|---|
| `oracle_etl.py` | OracleHook 기반 추출 callable + CTL 로깅 함수 |

### 함수 4종
| 함수 | 하는 일 |
|---|---|
| `ctl_start` | `C_JOB_RUN`에 실행 시작 기록 |
| `extract_masters` | `EQP_MST`/`SENSOR_MST` 스냅샷을 `L_SCADA_EQP`/`L_SCADA_SENSOR`로 재적재(TRUNCATE→INSERT) |
| `extract_trace` | **워터마크 이후** trace만 `L_SCADA_TRACE`로 증분 적재 + 워터마크 전진 |
| `ctl_end` | 적재 건수 집계 후 `C_JOB_RUN`에 완료 기록 |

## 왜 이렇게 (개념)
- **OracleHook + `oracle_pcs` 커넥션**: Airflow가 환경변수 `AIRFLOW_CONN_ORACLE_PCS`(유저 `PCS_ETL`)로 Oracle에 붙는다. 커넥션을 코드에 하드코딩하지 않는다.
- **워터마크 증분**: `C_SOURCE_WATERMARK.LAST_LOADED_TS` 이후의 데이터만 가져와, 매번 전량 재적재하지 않는다. 적재 후 이번에 들어온 최대 `MEAS_TS`로 워터마크를 전진시킨다.
- **컨텍스트 자동 주입**: Airflow 2의 PythonOperator는 callable의 `**context`로 `run_id`·`dag` 등을 자동 전달한다. 그래서 함수들이 `**context`를 받는다. `run_id`는 적재 묶음 식별자(`LOAD_ID`)로 쓴다.
- **INSERT ... SELECT (DB 내 이동)**: 원천→LND가 같은 Oracle 안이므로, Python으로 행을 끌어오지 않고 SQL로 직접 옮긴다(가볍고 빠름). 무거운 연산은 Airflow worker가 아니라 DB/엔진이 하도록 한다는 설계 원칙과 일치.

## 사용/실행법
직접 실행하지 않는다. `dags/configs/scada_extract_daily.yaml`에서 `python_callable: common.oracle_etl.extract_trace` 형태로 참조되어 DagFactory가 Task로 만든다. → [`dags/README.md`](../dags/README.md)

## 주의·겪은 이슈
- `extract_masters`의 TRUNCATE는 타 스키마 대상이라 `PCS_ETL`에 `DROP ANY TABLE` 권한 필요(→ [`init/`](../init/README.md)).
- `import` 가능하려면 `/opt/airflow`·`/opt/airflow/common`이 PYTHONPATH에 있어야 함(Dockerfile에서 설정).

↑ [최상위 README](../README.md)
