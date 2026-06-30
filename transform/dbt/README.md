# `transform/dbt/` — Medallion 변환 (dbt on Oracle)

## 목적
`PCS_LND`의 원시 데이터를 `.sql` 모델로 표준화·집계해 `PCS_SLV → PCS_CORE → PCS_GOLD`로 끌어올린다. 모델 간 의존성(`ref()`)이 곧 데이터 계보(lineage)이자 Airflow Task 그래프가 된다.

## 구조
```
transform/dbt/
├─ dbt_project.yml      폴더=계층 매핑(+schema), on-run-end 훅
├─ profiles.yml         Oracle 연결(oracledb thin, 유저 DBT_EXEC)
├─ models/
│  ├─ slv/   S_EQP, S_SENSOR, S_SENSOR_TRACE_H        (표준화: 원천값+표준값)
│  ├─ core/  D_*, F_SENSOR_DAILY, X_SYS_LINE_MGMT_LINE (차원/팩트/브릿지)
│  └─ gold/  G_WP_EQP_SENSOR_KPI_D                     (공식 마트)
├─ seeds/    mgmt_line_map.csv                         (시스템라인→관리라인 매핑)
├─ macros/   generate_schema_name.sql, log_to_ctl.sql
└─ tests/    (schema.yml의 not_null/unique/relationships)
```

## 왜 이렇게 (개념)
- **계층 = 폴더 + Prefix**: `models/slv|core|gold` 폴더가 각각 `+schema: PCS_SLV|PCS_CORE|PCS_GOLD`로 매핑된다. 테이블 접두(`S_/D_/F_/X_/G_`)로 역할이 한눈에.
- **`ref()`가 계보**: `G_WP...`가 `{{ ref('F_SENSOR_DAILY') }}`를 쓰면 dbt가 자동으로 "F → G" 의존성을 안다. 이걸 Cosmos가 Airflow Task 의존성으로 그대로 옮긴다(→ [`dags/`](../../dags/README.md)).
- **Grain 확정 지점 = `F_SENSOR_DAILY`**: 고빈도 trace를 "설비×센서×일"로 집계하는 곳. 분석의 기준 알갱이.
- **X_ Bridge = 비즈니스 재해석**: `mgmt_line_map` seed로 시스템 라인(L02/L03)을 관리 라인 1개("Deposition Line")로 묶는다. 단순 표준화(SLV)가 아니라 업무 관점 재해석이라 CORE에 둔다.
- **SLV는 원천값 보존**: `SRC_*`(원천)와 `STD_*`(표준)를 함께 보관 — 앞단 오류 추적용.

## 사용/실행법
보통은 변환 DAG(Cosmos)이 자동 실행한다. 수동으로 돌릴 때:
```bash
docker compose exec -T airflow-scheduler bash -lc \
  "source /opt/airflow/dbt_venv/bin/activate && cd /opt/airflow/transform/dbt && \
   dbt run --profiles-dir . && dbt test --profiles-dir ."

# 계보 시각화 (자체 포함형 HTML)
... dbt docs generate --static --profiles-dir .   # → target/static_index.html
```

## 관측 연동 (on-run-end)
`macros/log_to_ctl.sql`이 dbt 실행 끝마다 모델 timing→`PCS_CTL.C_JOB_RUN`, test 결과→`A_DQ_RESULT`에 적재한다(Elementary가 Oracle 미지원이라 자체 구현). → [`init/`](../../init/README.md)의 헬스 뷰가 이 데이터를 읽는다.

## 주의·겪은 이슈
- **`generate_schema_name` override 필수**: 기본 dbt는 `+schema`를 `<target>_<custom>`으로 합쳐버린다. 매크로로 **접두 없이 그대로**(`PCS_SLV`) 쓰게 했다. 그래야 `DBT_EXEC`가 `CREATE ANY TABLE` 권한으로 각 계층 스키마에 객체를 만든다.
- **dbt-oracle은 on-run-end DML을 자동 커밋하지 않음**: 훅에서 INSERT해도 롤백된다. 매크로 끝에 `{% do run_query('COMMIT') %}`를 넣어 해결.
- **Snowflake 문법 금지**: 레퍼런스의 `QUALIFY`/`COPY INTO` 대신 Oracle 문법(`ROW_NUMBER() OVER`, `MERGE`)을 쓴다.
- **테스트는 AFTER_ALL**: relationships 테스트가 대상 모델 빌드 전에 돌면 `ORA-00942`. Cosmos에서 `TestBehavior.AFTER_ALL`로 전 모델 빌드 후 일괄 실행(→ [`dags/`](../../dags/README.md)).

↑ [최상위 README](../../README.md)
