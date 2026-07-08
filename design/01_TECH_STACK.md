# 01. 기술 스택

## 구성
| 영역 | 기술 | 버전 | 비고 |
|---|---|---|---|
| 오케스트레이션 | Airflow | 2.9.3 | LocalExecutor |
| 런타임 | Python | 3.11 | |
| 메타DB | PostgreSQL | 13 | Airflow 메타스토어 |
| 변환 | dbt-oracle | 1.8.4 | SQL 모델 |
| dbt↔Airflow | Cosmos | 1.5.1 | dbt 모델→Task 자동전개 |
| 원천/타깃 | Oracle | 외부 실서버 | 컨테이너 없음 — `.env` `PCS_ORACLE_*` 접속. thin(기본)/thick(실타깃) |
| 관측성 | Oracle CTL 스키마 | - | 자체 메트릭(PCS_CTL) |
| 관측성 | OpenMetadata | - | 카탈로그/데이터 프로덕트 + 계보(dbt ingestion). Marquez 는 제거(→ [adr/0005](adr/0005-slim-orchestration-topology.md)) |

## 의존성 파일 분리
- `requirements.txt`(Airflow) / `requirements-dbt.txt`(dbt) **분리** → 두 생태계의 의존성 충돌 회피.
- 핀 전략·폐쇄망 빌드: [08_AIRGAP_BUILD.md](08_AIRGAP_BUILD.md)

## Oracle 드라이버
- 기본 thin, 실타깃 **thick**(버전 상이). → `OracleConnector`([06_COMMON_LAYER.md](06_COMMON_LAYER.md))
