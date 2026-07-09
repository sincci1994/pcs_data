# PCS 데이터 파이프라인

PCS기술팀의 데이터 활용능력 향상을 위한 오케스트레이션·거버넌스 저장소.
엔지니어 개인 Excel 가공으로 흩어진 데이터 프로덕트를 **표준 계층(LND→SLV→GOLD)과 비즈니스 정의(온톨로지)** 로 재정착시킨다.

## 배경

| 현상 | 결과 |
|---|---|
| 레거시 앱 VIEW_TABLE 불신 | 엔지니어별 Excel 재가공 → 불규칙한 그림자 데이터 프로덕트 |
| 비즈니스 플로우 문서 부재 | VOC 패치로만 시스템 변형, 합의 사항 방치 |
| 담당자별 상이한 지표 정의 | 같은 지표가 사람마다 다른 값 |

**접근**: 실무 담당자의 변환 논리를 인터뷰·수집(AS-IS 인테이크)해 SQL(dbt 모델)로 표준화하고, 레거시 산출물과 대사 검증 후 승격한다. 이후 분석가가 SQL만 추가하면 파이프라인에 자동 반영되는 셀프서비스 구조를 유지한다.

## 아키텍처

```
소스 (레거시 EES 등)                      Airflow (오케스트레이션)
      │                 ┌──────────────────────────────────────────┐
      └→ [Extract 태스크] → warehouse LND → [dbt: SLV → GOLD] → [Publish 태스크] → 서빙 DB
                        │        Manager DAG ──trigger──> Model DAG (모델별)      │
                        └──── OpenMetadata: 카탈로그 · 리니지 · 용어집 · 테스트결과 ────┘
```

- **Manager/Model DAG**: dbt manifest를 파싱해 모델별 DAG를 동적 생성. Manager DAG가 의존 순서로 트리거하고, 실패 시 의존 관계에 따라 복구한다. 모델(.sql) 추가에 개발자 코드 작업 불필요. → [design/03_DAG_DESIGN.md](design/03_DAG_DESIGN.md)
- **분석가 직접 저작**: SLV(표준화된 데이터) 기반으로 GOLD를 직접 추가 — `wrk` 실험 계층에서 자유 탐색 후 glossary 확정으로 승격. 소스(Biz Process) 변경은 SLV에서 흡수되어 하류가 자동 재정의된다. → [design/07_AUTHORING_FLOW.md](design/07_AUTHORING_FLOW.md)
- **검증 2중**: 이관 시 레거시 산출물과 대사(parallel-run), 운영 시 dbt test가 Publish를 게이트.
- **가시성**: OpenMetadata가 카탈로그·리니지·용어집을 담당 — "비즈니스 정의로 흐름을 본다".

## 저장소 구조

```
governance/   용어집·AS-IS 인테이크 기록 (정의의 원천)
transform/    dbt 모델 (SLV→GOLD)
platform/     dags · extract · common · infra
quality/      대사 검증 · dbt test 정책
workspace/    instructions(지시) · pdca(계획/실행/평가/개선)
design/       요구사항 · 아키텍처 · ADR · 로드맵
```

각 폴더의 CLAUDE.md에 저작 규칙이 있다. 전체 규약은 [CLAUDE.md](CLAUDE.md).

## 문서 인덱스

| 문서 | 내용 |
|---|---|
| [design/00_REQUIREMENTS.md](design/00_REQUIREMENTS.md) | 요구사항 원문 + 반영 매핑 |
| [design/01_OVERVIEW.md](design/01_OVERVIEW.md) | 문제·목적·범위 |
| [design/02_ARCHITECTURE.md](design/02_ARCHITECTURE.md) | 전체 아키텍처·계층·역할 분담 |
| [design/03_DAG_DESIGN.md](design/03_DAG_DESIGN.md) | Manager/Model 동적 DAG 설계 |
| [design/04_AS_IS_INTAKE.md](design/04_AS_IS_INTAKE.md) | 레거시 로직 발굴 워크플로 |
| [design/05_INFRA.md](design/05_INFRA.md) | 로컬 검증 스택 + 원격 이식 |
| [design/06_SCENARIO_UTILITY_USAGE.md](design/06_SCENARIO_UTILITY_USAGE.md) | 첫 데이터 제품 |
| [design/07_AUTHORING_FLOW.md](design/07_AUTHORING_FLOW.md) | 분석가 직접 저작 + 소스 변경 자동 재정의 |
| [design/08_DATA_OPS.md](design/08_DATA_OPS.md) | 볼륨·보존·지연·드리프트·옵저버빌리티 정책 |
| [design/roadmap.md](design/roadmap.md) | 보류·후속 항목 |

## 현재 상태 (2026-07-09 재구축)

| Phase | 내용 | 상태 |
|---|---|---|
| 1 | 문서·구조 스켈레톤 (요구사항 재정렬) | **완료 — 이 커밋** |
| 2 | 인프라: OpenMetadata+Airflow compose 스택 로컬 검증 | 예정 → [design/05_INFRA.md](design/05_INFRA.md) |
| 3 | 코드: Manager/Model DAG 팩토리 · dbt 프로젝트 · extract | 예정 |
| 4 | AS-IS 인테이크 실행 → 첫 데이터 제품 이관 | 예정 |

이전 구현(Cosmos 기반 SCADA 샘플)은 git 히스토리(`db02606` 이전)에서 참조 가능.
