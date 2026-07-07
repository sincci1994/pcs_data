# transform/ — SQL 변환 (dbt, 리소스 담당)

모든 변환은 dbt 모델(`dbt/models/`). `.sql`에 `{{ ref() }}`만 연결하면 Cosmos가 Airflow Task로 자동 전개한다 — DAG 코드는 만지지 않는다.

## 계층·네이밍
| 폴더 | 스키마 | prefix | 의미 |
|---|---|---|---|
| `dbt/models/slv/` | PCS_SLV | `S_` | 표준화 (원천값 `SRC_*` + 표준값 `STD_*` 병행 보관) |
| `dbt/models/core/` | PCS_CORE | `D_`/`F_`/`X_` | 차원/팩트/브리지 (X_ = 비즈니스 재해석) |
| `dbt/models/gold/` | PCS_GOLD | `G_` | 공식 마트 (화면이 직접 SELECT) |

## 저작 규칙 — 모델을 쓰거나 고칠 때 (필수)
1. **대용량 경로는 incremental**: 트레이스/5분 데이터처럼 이력이 쌓이는 모델을 full-refresh `table`로 두지 않는다. full refresh는 소형 디멘전만. 비용은 당일 델타에 비례해야 한다.
2. **데이터 도착 게이트는 당일 적재분 스코프**: `COUNT(*) > 0` 같은 전체 카운트 게이트 금지 — 첫 적재 이후 항상 참이 되어 무의미하다. LOAD_ID/INGESTED_AT로 해당 logical date 분을 확인.
3. **팩트에서 디멘전 INNER JOIN 무음 탈락 금지**: 미등록 키는 orphan으로 캡처하거나 relationships 테스트로 검출되게 한다.
4. **테스트는 전 계층**: 키 unique/not_null은 기본, 비율·사용량 지표는 range/accepted_values 테스트 추가. 지시서의 완료조건에 적힌 테스트는 반드시 구현.
5. **디멘전 이력(SCD) 필요 여부를 모델링 전에 판단**: stateless rebuild는 속성 변경을 덮어쓴다 — 과거 재현이 필요하면 snapshot.
6. **컬럼 설명은 schema.yml에**: 별도 마크다운 사전을 만들지 않는다(→ governance 규칙).

## dbt 어댑터 특이점 (겪은 이슈 — 지우지 말 것)
- `generate_schema_name` 매크로 override 필수: 기본 dbt는 `<target>_<custom>`으로 스키마명을 합친다. 접두 없이 그대로 쓰게 한 매크로 유지.
- dbt-oracle은 on-run-end DML을 자동 커밋하지 않는다 → `log_to_ctl.sql` 끝의 `COMMIT` 유지. (Postgres 전환 시 재검토)
- relationships 테스트는 대상 모델 빌드 후 실행돼야 함 → Cosmos `TestBehavior.AFTER_ALL` 유지.
- Snowflake 문법(`QUALIFY`/`COPY INTO`) 금지 — 대상 엔진 문법으로.

## 흐름
1. 지시서(`../workspace/instructions/`) → 지표 정의(`../governance/ontology/glossary.md`) 확인.
2. 계층 폴더에 `.sql` 작성(첫 줄 주석으로 비즈니스 설명 1줄) + `schema.yml`에 테스트.
3. 실행 결과는 on-run-end 훅이 `PCS_CTL.C_JOB_RUN`/`A_DQ_RESULT`에 자동 기록.

상세 설계: [design/05](../design/05_TRANSFORM_LAYER.md) · 기준 시나리오: [design/09](../design/09_SCENARIO_UTILITY_USAGE.md)
