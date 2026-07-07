# governance/ — 비즈니스 정의의 단일 원천 (도메인 전문가)

여기 없는 정의는 공식이 아니다. **정의 먼저, 구현은 그 다음.**

| 폴더 | 무엇 |
|---|---|
| `ontology/` | 도메인 구분(`domains.md`) + 용어집(`glossary.md` — 지표 정의) |

## 저작 규칙 (필수)
1. **새 지표/용어는 `ontology/glossary.md`에 정의 확정 후 구현 지시** — 표기·산식·단위 포함. 담당자 간 정의 통일이 이 프로젝트의 존재 이유다.
2. **컬럼 사전을 별도 마크다운으로 만들지 않는다**: 컬럼 설명의 단일 원천은 dbt `schema.yml`의 description — 병렬 문서는 반드시 드리프트한다. 필요하면 dbt docs/OpenMetadata로 파생시킨다.
3. **테이블 비즈니스 설명(오너·그레인·갱신주기)은 카탈로그(OpenMetadata)에 기록**하고, 여기 문서는 도메인·용어 수준만 유지한다.
4. **OM 발행 스크립트와 동기화**: `domains.md`/`glossary.md`를 고치면 `platform/infra/openmetadata/om_setup_domains.py` 재실행이 필요함을 지시서에 명시.

## 흐름
1. 용어 정의(`ontology/glossary.md`) → 2. 구현 필요 시 `../workspace/instructions/TEMPLATE.md` 복사해 지시서 작성(목표/범위/제약/완료조건) → 3. 결과는 `../workspace/pdca/<작업명>/`에서 확인.

전체 데이터 흐름: [design/03](../design/03_DATA_FLOW.md) · 기준 시나리오: [design/09](../design/09_SCENARIO_UTILITY_USAGE.md)
