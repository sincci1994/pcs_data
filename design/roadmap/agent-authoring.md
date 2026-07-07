# 로드맵: 오프라인 Agent 저작 툴링 (미구현)

Agent *코드/툴링*은 **나중** 단계다(이해관계자 결정: "사람 우선, Agent는 나중").

> **혼동 주의 — 두 개의 "agent"를 구분한다:**
> - **이 로드맵** = 향후 자동화 **코드/툴링**(오프라인 저작 엔진). 아직 없음.
> - **문서 운영 루프**(지금 활성) = `workspace/instructions`(지시) · `workspace/pdca`(계획·결과) · `workspace/patterns` · `workspace/mistakes` — 규칙: [workspace/CLAUDE.md](../../workspace/CLAUDE.md).
>
> 즉 "사람이 .md로 지시하고 Agent가 결과를 문서로 남기는" 흐름은 이미 `workspace/` 에서 돈다. 이 로드맵은 그걸 자동화할 *코드*의 미래 설계다.

## 역할 (구현 시)
Agent 는 **런타임 밖(오프라인)**에서 다음을 *초안 작성*한다:
- [계약 엔진](contracts-engine.md)의 SQL-메타데이터 계약
- `governance/` 의 비즈니스 문서(용어·도메인) 및 dbt `schema.yml` 컬럼 설명 초안

## 하네스 원칙
Agent 산출물은 **검증 게이트**를 통과한 것만 커밋된다:
`JSON-Schema 검증 → dbt parse → 계보 순환검사 → dry-run`.
사람이 PR 리뷰, 결정론적 엔진이 실행. **Agent 는 Airflow import/실행 경로에 절대 들어가지 않는다.**

## 지식원
Agent 는 `governance/`(정의) + `workspace/`(지시·이력) 의 버전관리 `.md` 를 지식원으로 읽는다(Confluence 동기화는 이후 옵션).

## 현재 상태
로드맵만. 구현 착수 전 별도 설계 필요. 구현 위치(예정): `platform/` 밖의 별도 최상위 또는 `dev/`(런타임 import 경로 밖이면 됨).
