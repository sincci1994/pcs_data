# transform/ — dbt 모델 (분석가)

dbt 프로젝트(wrk·SLV→GOLD)가 들어올 자리 — Phase 3에서 생성. 계층 정의: [design/02](../design/02_ARCHITECTURE.md) · 저작 플로우: [design/07](../design/07_AUTHORING_FLOW.md)

## 저작 규칙 — 모델을 쓰거나 고칠 때 (필수)
1. **정의 선행 (slv/gold 한정)**: 운영 계층 모델은 `governance/glossary.md`에 지표 정의(산식·단위·결측 정책)가 확정된 뒤에만 만든다. 이관 모델은 인테이크 문서(대사 검증 포함)가 선행한다. 탐색·초안은 `models/wrk/`에서 정의 없이 가능 (규칙 7).
2. **테스트 없는 모델 금지**: 키 `unique`/`not_null` + 도메인 range 테스트(예: 사용량 음수 금지)를 `schema.yml`에 함께 커밋한다.
3. **컬럼 설명은 `schema.yml`이 단일 원천** — OpenMetadata로 발행된다. 비워두지 말 것.
4. **SLV는 원천값 보존**: 정제·표준화만, 비즈니스 판단(필터·산식)은 GOLD에서. 센서 식별 패턴 등 업무 상수는 하드코딩하지 않고 seed/변수로 외부화.
5. **대용량 경로는 incremental**: 5분×전 센서 grain을 스캔하는 모델은 incremental 필수.
6. **모델 추가 후 manifest 갱신**: `dbt compile` 산출 `manifest.json`을 함께 커밋해야 DAG가 생성된다 (→ [design/03](../design/03_DAG_DESIGN.md)). 개발자에게 DAG 작업을 요청하는 순간 설계 위반.
7. **wrk 실험 계층**: 소유자·생성일을 모델 헤더 주석에 필수 기재. `wrk → slv/gold` ref 허용, **역방향 금지** (실험이 운영 의존성이 되면 안 됨). 승격 절차(정의 확정+테스트+폴더 이동)는 [design/07](../design/07_AUTHORING_FLOW.md).
8. **소스 변경은 SLV에서 흡수**: 소스가 바뀌면 `sources.yml`+SLV 모델만 수정 — GOLD가 소스를 직접 참조하지 않게 유지해야 하류 자동 재정의가 성립한다.
