# 07. 운영 / 관측성

## 관측성 3계층
| 계층 | 도구 | 답하는 질문 |
|---|---|---|
| 자체 메트릭 | `PCS_CTL` 스키마 + 뷰 | 신선도/병목/이상 적재량 |
| 계보 | OpenLineage → Marquez | 어떤 Task 가 무엇을 읽고 썼나 |
| 카탈로그 | OpenMetadata | 데이터 프로덕트/오너/문서 |

## PCS_CTL 테이블·뷰
| 객체 | 유형 | 설명 |
|---|---|---|
| `C_JOB_RUN` | 테이블 | job/모델 실행 타이밍 |
| `C_SOURCE_WATERMARK` | 테이블 | 소스별 증분 워터마크 |
| `A_DQ_RESULT` | 테이블 | DQ/dbt 테스트 결과 |
| `M_DATA_PRODUCT` | 테이블 | 데이터 프로덕트 등록부 |
| `V_FRESHNESS` | 뷰 | 신선도 |
| `V_BOTTLENECK` | 뷰 | 병목(장기 실행) |
| `V_VOLUME_ANOMALY` | 뷰 | 적재량 이상 |

## dbt → CTL 연동
- on-run-end 매크로 `log_run_results_to_ctl()`:
  - 모델 타이밍 → `C_JOB_RUN`
  - 테스트 결과 → `A_DQ_RESULT`
- Elementary 대체(자체 구현). 테이블 정의: `platform/infra/init/03_lnd_ctl_ddl.sql`

## 시크릿
- 자격증명은 `.env` 로 외부화. 템플릿: `.env.example`(레포에 커밋). 실제 `.env` 는 커밋 금지.

## 폐쇄망
- 빌드/배포 제약: [08_AIRGAP_BUILD.md](08_AIRGAP_BUILD.md)
