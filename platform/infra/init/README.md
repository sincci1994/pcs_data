# `init/` — Oracle 스키마·권한·원천 초기화 DDL (참조용)

> ⚠️ **참조 아티팩트**: 로컬 Oracle 컨테이너는 제거됐다([adr/0005](../../../design/adr/0005-slim-orchestration-topology.md)). 이 SQL 은 더 이상 자동 실행되지 않는다 — **외부 Oracle 에 DBA 가 수동 적용**하거나 SCADA 샘플을 재현할 때 참고한다. SCADA 샘플은 척추(참조)이며 [design/09](../../../design/09_SCENARIO_UTILITY_USAGE.md) 시나리오 정착 시 이 폴더째 삭제 예정.

## 목적
데이터 계층(스키마), 접근 권한, 원천(SCADA) 모사 테이블, 통제(CTL) 테이블·뷰를 만드는 SQL 스크립트 모음. 알파벳 순(01→04)으로 적용한다.

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
외부 Oracle 실서버에 `SYSTEM`(또는 상응 권한)으로 01~04 를 순서대로 적용한다:
```bash
sqlplus -s system/<pw>@<PCS_ORACLE_HOST>:1521/<service> @01_users.sql
# 02_src_scada_ddl.sql → 03_lnd_ctl_ddl.sql → 04_ctl_views.sql 순으로 반복
```

## 주의·겪은 이슈
- **TRUNCATE에는 `DROP ANY TABLE` 필요**: `PCS_ETL`이 타 스키마(`PCS_LND`) 테이블을 TRUNCATE하려면 `DROP ANY TABLE` 권한이 있어야 한다(`ORA-01031` 회피). `01_users.sql`에 포함됨.
- **적용 순서 의존**: 01(유저/권한) → 02·03(테이블) → 04(뷰). 앞 단계 누락 시 뒤 스크립트가 실패한다.

↑ [최상위 README](../../../README.md)
