# quality/ — 파이프라인 건강·데이터 품질 (품질·모니터링 담당)

코드 내부가 아니라 **결과 테이블/뷰와 UI**를 본다.

## 관측 3계층
| 계층 | 어디서 | 무엇 |
|---|---|---|
| CTL | `PCS_CTL` 스키마 | 실행이력(`C_JOB_RUN`)·워터마크(`C_SOURCE_WATERMARK`)·DQ 결과(`A_DQ_RESULT`)·병목(`V_BOTTLENECK`) |
| Airflow UI | http://localhost:8080 | 런타임(실패/지연 단계 — Grid/Graph 뷰) |
| OpenMetadata | http://localhost:8585 | 비즈니스 카탈로그(도메인·용어·테이블) + 테이블 계보(dbt ingestion) |

핵심 뷰: `V_FRESHNESS`(신선도) · `V_BOTTLENECK`(병목) · `V_VOLUME_ANOMALY`(볼륨 이상) — 정의 `platform/infra/init/04_ctl_views.sql`, 점검 쿼리 `queries/health_check.sql`, 해석법 [runbook.md](runbook.md).

## 저작 규칙 (필수)
1. **헬스뷰는 사람 조회용에서 끝내지 않는다**: 새 점검 항목을 추가하면 자동 게이트(센서/테스트) 또는 알림에 연결하는 것까지가 완료 조건이다. "수동 sqlplus 조회"만 있는 점검은 미완성.
2. **DQ 규칙은 dbt test로**: 반복 품질 규칙은 리소스 담당자에게 dbt test 추가를 지시 — 결과는 `A_DQ_RESULT`로 자동 수집되는 계약을 유지한다.
3. **이상 발견 → 지시서**: 원인 단계는 Airflow UI·`V_BOTTLENECK`·OM 계보로 추적하고, 조치는 `../workspace/instructions/`에 지시서로 남긴다(구두/채팅 금지).

기준 시나리오: [design/09](../design/09_SCENARIO_UTILITY_USAGE.md)
