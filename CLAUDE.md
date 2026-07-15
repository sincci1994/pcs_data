# CLAUDE.md — PCS 데이터 파이프라인 (START HERE)

PCS기술팀의 **업무 능력·데이터 활용능력 향상**을 위한 데이터 파이프라인 — Airflow + dbt + OpenMetadata.
요구사항 원문과 반영 매핑: [design/00_REQUIREMENTS.md](design/00_REQUIREMENTS.md) · 궁극 구조 기획(조직·소스 지형·팀 경계): [design/11_TARGET_ARCHITECTURE.md](design/11_TARGET_ARCHITECTURE.md)

## 왜 만드는가
- 레거시 앱 VIEW_TABLE을 못 믿어 엔지니어마다 Excel로 재가공 → **개인 판단이 만든 불규칙한 그림자 데이터 프로덕트** 난립.
- 전체 비즈니스 플로우 문서 부재 — VOC 패치로만 변형, 합의된 정보는 방치.
- **이 문제를 풀 전문가의 부재** — 그래서 지식은 사람이 아니라 시스템(정의·기록·규칙·가이드)에 축적되어야 한다.
- 해법: 실무 담당자의 변환 방식을 **발굴(AS-IS 인테이크)** 해 brz→slv→gld 계층으로 표준화하고, 비즈니스 정의(온톨로지)로 데이터 흐름을 본다. 명명 정본: [design/10](design/10_NAMING_ORGANIZATION.md)

> **첫 번째 데이터 제품**: [design/09_SCENARIO_EQUIPMENT_PIPE.md](design/09_SCENARIO_EQUIPMENT_PIPE.md) — 레거시 EES **PortMaster2** → 배관 스케줄러 **equipment/pipe 기준정보** (반수동 ETL의 이관). Utility 사용량([design/06](design/06_SCENARIO_UTILITY_USAGE.md))은 보류.

## 레이아웃 (역할 기반)

| 폴더 | 무엇 | 누구 |
|---|---|---|
| `governance/` | 용어집·AS-IS 인테이크 기록 — **정의의 원천** | 도메인 전문가·분석가 |
| `transform/` | dbt 모델 (slv→gld) | 분석가 — **SQL만 추가하면 파이프라인 자동 반영** |
| `platform/` | dags(Manager/Model DAG 팩토리)·extract·common·infra | 시스템 담당 |
| `quality/` | 대사 검증(레거시 산출물 vs 신규 모델)·dbt test 정책 | 품질 |
| `workspace/` | instructions(지시)·pdca(plan→do→check→act) | 전원 + Agent |
| `design/` | 요구사항·아키텍처·ADR·로드맵 | 설계 |

> 영역별 저작 규칙은 각 폴더의 CLAUDE.md에 있다 — 해당 폴더에서 작업하면 자동 로드된다. 이 파일에 중복 기재하지 않는다.

## Agent 운영 규약
1. **지시는 `workspace/instructions/*.md`** 에서 읽는다 (목표/범위/제약/완료조건).
2. **계획·실행결과는 `workspace/pdca/<feature>/`** 에 남긴다: plan→do→check→act.
3. 정의(용어·지표)는 **`governance/` 가 단일 원천** — 작업 전 먼저 확인.
4. AS-IS 발굴(인터뷰→논리 기록→SQL화→대사 검증)은 [governance/intake/TEMPLATE.md](governance/intake/TEMPLATE.md)를 따른다.
5. 크로스세션 지속 사실 = Claude Code 파일 메모리(`.claude/.../memory`).

## 불변 규칙
- **분석가 셀프서비스**: dbt 모델(.sql) 추가만으로 DAG가 자동 생성된다 — 모델 추가에 개발자 코드 작업이 필요해지면 설계 위반. → [design/03_DAG_DESIGN.md](design/03_DAG_DESIGN.md)
- **Manager/Model DAG**: dbt manifest 파싱 → 모델별 Model DAG + 의존성 트리거·복구 Manager DAG. 파싱·실행 경로는 결정론적 — **런타임 LLM 금지**, Agent는 오프라인 저작만. → [adr/0002](design/adr/0002-manager-model-dynamic-dag.md)
- **정의 우선**: 운영 계층(slv/gld) 승격 전 glossary 정의 확정 — 이관 모델은 대사 검증도 통과. 탐색은 `sbx` 실험 계층에서 자유. → [design/07](design/07_AUTHORING_FLOW.md)
- **시크릿**: 크리덴셜은 `.env`로만. 커밋 금지.
- **사내망 전제**: 폐쇄망·프록시 환경 — 원격 이식은 [design/05_INFRA.md](design/05_INFRA.md) 체크리스트를 따른다.

세부 사용법 → [README.md](README.md).
