# 품질·모니터링 런북

일상 점검 루틴. 쿼리는 [queries/](queries) 재사용. 접속 정보는 루트 [README](../README.md).

## ① 헬스뷰 3종 (Oracle `PCS_CTL`)

| 뷰 | 무엇을 | 읽는 법 |
|---|---|---|
| `V_FRESHNESS` | 최신성/끊김 | `STATUS='STALE'`(48h 초과) 행이 있으면 해당 LAYER(SOURCE=수집, MODEL=변환) 담당에게 확인 |
| `V_BOTTLENECK` | 단계별 소요시간 | `AVG_SEC`/`MAX_SEC` 상위 = 병목. 추이가 늘면 리소스 배치 재검토(→ transform/CLAUDE.md 규칙) |
| `V_VOLUME_ANOMALY` | 건수 급감/공백 | `FLAG='EMPTY'`(0건)·`'DROP'`(직전 5회 평균의 50%↓) 행 추적 |

실행: [queries/health_check.sql](queries/health_check.sql)

## ② DQ 결과 (`A_DQ_RESULT`)
dbt test 가 돌 때마다 자동 적재(on-run-end 매크로). 실패(`PASS_YN='N'`) 행 발견 시:
1. 해당 모델·테스트명 확인 → 리소스 담당자에게 `../workspace/instructions/` 로 지시.
2. 반복 실패는 `../workspace/mistakes/` 에 교훈으로 기록 요청.

## ③ 계보/런타임
- 실패/지연 단계는 Airflow UI(8080) Grid/Graph 뷰 + ①의 `V_BOTTLENECK` 으로 확인.
- 테이블/컬럼 계보("어느 테이블이 어디서 오나")는 OpenMetadata(8585) — dbt ingestion 이 dbt DAG 계보를 적재하며, 비즈니스 언어(도메인·용어)로 탐색.
- (참고) 과거 Marquez 기반 런 단위 계보는 제거됨 — 근거·재도입 경로: [adr/0005](../design/adr/0005-slim-orchestration-topology.md)

## 이상 시 에스컬레이션
| 증상 | 1차 확인 | 담당 |
|---|---|---|
| SOURCE STALE | 수집 DAG 실패 여부(Airflow UI) | ⚙️ 시스템 |
| MODEL STALE / DQ FAIL | dbt test 로그, 모델 정의 | 🔧 리소스 |
| 정의가 이상함 | `governance/ontology` 용어 정의 | 🧭 도메인 |
