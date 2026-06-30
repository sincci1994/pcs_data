# `init/` — Oracle 스키마·권한·원천 초기화

## 목적
Oracle 컨테이너가 **최초 1회 기동될 때** 실행되는 SQL 스크립트 모음. 데이터 계층(스키마), 접근 권한, 원천(SCADA) 모사 테이블, 통제(CTL) 테이블·뷰를 만든다.

> gvenzl/oracle-free 이미지는 `/container-entrypoint-initdb.d/` 안의 `*.sql`을 **알파벳 순서로, 최초 기동 때 한 번만** 실행한다. (docker-compose에서 이 폴더가 그 경로에 마운트됨)

## 파일·역할
| 파일 | 역할 |
|---|---|
| `01_users.sql` | 스키마(=Oracle 유저) 6계층 + ETL/dbt 실행 유저 생성, 권한 부여 |
| `02_src_scada_ddl.sql` | 원천 모사: `EQP_MST`·`SENSOR_MST`·`TRACE_RAW` + 마스터 시드 |
| `03_lnd_ctl_ddl.sql` | `PCS_LND`(수신버퍼) + `PCS_CTL`(통제) 테이블, 워터마크·카탈로그 초기값 |
| `04_ctl_views.sql` | 헬스 모니터링 뷰 3종(`V_FRESHNESS`/`V_BOTTLENECK`/`V_VOLUME_ANOMALY`) |

## 왜 이렇게 (개념)
- **스키마 = 유저**: Oracle은 "스키마"가 곧 "유저"다. 그래서 계층(LND/SLV/CORE/GOLD/CTL)을 각각 별도 유저로 만들어 격리한다. 회사의 "PCSNRDK DB 안에 계층 스키마" 시나리오와 동일.
- **권한 분리**: `PCS_ETL`(Airflow 추출용) / `DBT_EXEC`(dbt 변환용)을 따로 둬서 누가 무엇을 하는지 명확히 한다.
- **SLV/CORE/GOLD 테이블은 여기서 안 만든다**: dbt가 모델 실행 시 생성한다. init은 원천·LND·CTL까지만.

### 6계층 스키마
| 스키마 | 역할 | Prefix |
|---|---|---|
| `SRC_SCADA` | 원천(SCADA 운영 Schema) 모사 | — |
| `PCS_LND` | 수신 버퍼(Landing) | `L_` |
| `PCS_SLV` | 표준화(Silver) | `S_` |
| `PCS_CORE` | 분석 모델(Fact/Dim/Bridge) | `F_ D_ X_` |
| `PCS_GOLD` | 공식 제공 마트 | `G_` |
| `PCS_CTL` | 통제/감사/카탈로그 | `C_ A_ M_ V_` |

## 사용/실행법
- **자동**: `docker compose up`으로 Oracle이 처음 뜰 때 01~04가 자동 실행된다.
- **수동 재적용**(기존 볼륨이 있어 자동 실행이 안 될 때):
  ```bash
  docker compose exec -T oracle bash -lc \
    "sqlplus -s system/oracle@localhost:1521/FREEPDB1 @/container-entrypoint-initdb.d/04_ctl_views.sql"
  ```
- **완전 초기화 후 재실행**: `docker compose down -v` (볼륨 삭제) 후 다시 `up`.

## 주의·겪은 이슈
- **TRUNCATE에는 `DROP ANY TABLE` 필요**: `PCS_ETL`이 타 스키마(`PCS_LND`) 테이블을 TRUNCATE하려면 `DROP ANY TABLE` 권한이 있어야 한다(`ORA-01031` 회피). `01_users.sql`에 포함됨.
- **gvenzl 최초 init 변덕**: 첫 기동 때 스크립트가 "DONE"으로 찍혀도 일부 grants/DDL이 미반영될 수 있었다. 기동 후 객체·권한을 검증하고, 누락 시 위 수동 재적용으로 보정.
- **`04_ctl_views.sql`은 나중에 추가**됐으므로 기존 볼륨엔 자동 적용 안 됨 → 수동 적용 필요.

↑ [최상위 README](../README.md)
