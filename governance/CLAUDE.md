# governance/ — 정의의 원천 (도메인 전문가·분석가)

| 파일/폴더 | 무엇 |
|---|---|
| `glossary.md` | 용어·지표 정의 (산식·단위·결측 정책) — **저장소 유일의 정의 원천** |
| `intake/` | AS-IS 인테이크 기록 — 프로덕트 1건당 1파일, [TEMPLATE.md](intake/TEMPLATE.md) 사용 |

## 규칙
1. **정의 없이 구현 없다 (slv/gld)**: 운영 계층 dbt 모델은 glossary 항목(산식·단위·결측 정책 확정) 이후에만 작성한다. 예외: `sbx` 실험 계층은 정의 없이 저작 가능 — slv/gld 승격 시 확정 (→ [design/07](../design/07_AUTHORING_FLOW.md)).
2. **정의 변경은 여기서 먼저**: 산식이 바뀌면 glossary 수정 → 모델 수정 순서. 역방향 금지.
3. glossary 정의는 OpenMetadata Glossary로 발행되어 자산과 연결된다 — 항목명은 발행 후 변경하지 않는다.
4. 인테이크 문서는 인터뷰 원문(담당자 표현)을 보존한다 — 요약으로 대체하지 말 것. 이 축적이 비즈니스 플로우 문서가 된다 (요구 3).
5. 컬럼 수준 설명의 단일 원천은 dbt `schema.yml` — glossary에는 지표·용어 수준만 둔다.
