# 05. Transform 레이어 (dbt)

SQL 로 **어떻게** 가공하나. `transform/dbt/` 에 위치.

## 계층 = 폴더 → 스키마 매핑
| dbt 폴더 | 타깃 스키마 | 성격 |
|---|---|---|
| `slv/` | `PCS_SLV` | 정제 |
| `core/` | `PCS_CORE` | 차원·팩트 |
| `gold/` | `PCS_GOLD` | 데이터 프로덕트 |

## 모델 prefix 규약
| prefix | 의미 | 예 |
|---|---|---|
| `S_` | Silver 정제 | `S_SENSOR` |
| `D_` | Dimension | `D_EQP` |
| `F_` | Fact | `F_SENSOR_DAILY` |
| `X_` | Bridge/매핑 | `X_SYS_LINE_MGMT_LINE` |
| `G_` | Gold KPI | `G_WP_EQP_SENSOR_KPI_D` |

## 자동전개
- `.sql` 모델 추가 → **Cosmos** 가 파싱해 Airflow Task 로 자동전개(수동 Task 정의 불필요).
- 실행 순서는 `ref()` 의존성에서 도출.

## 테스트
- `schema.yml` 에 컬럼 테스트(not_null/unique/relationships 등) 선언.
- 결과는 on-run-end 매크로로 `PCS_CTL.A_DQ_RESULT` 기록. → [07_OPERATIONS.md](07_OPERATIONS.md)

> TODO: gold KPI 정의(SQL) 목록 표 추가.
