# 07. 저작 플로우 — 분석가 직접 저작 + 소스 변경 자동 재정의 (요구 5)

> **상시 운영 경로**. 레거시 Excel 로직의 발굴·이관은 별도의 한시적 경로 → [04_AS_IS_INTAKE.md](04_AS_IS_INTAKE.md).

## 1. 분석가 신규 gold 직접 저작

시스템이 필터·표준화해 둔 slv 데이터를 조회할 수 있게 되면, 분석가는 그것을 기반으로
gold 프로덕트를 직접 만든다 — 개발자 코드 작업 없이.

```
slv 조회·탐색  (필요 시 sbx 스키마에서 초안 실험 — 정의·테스트 불요)
   ↓
governance/glossary.md 정의 확정 (산식·단위·결측)          ← 승격 게이트
   ↓
transform/models/gld/<도메인>/ 에 모델 .sql + schema.yml (설명·테스트)
   ↓
dbt compile → manifest 커밋
   ↓
model__ DAG 자동 생성 + Manager 편입
   ↓
dbt test 통과 → Publish → OpenMetadata 카탈로그 발행
```

대사 검증은 이관 프로덕트 전용 — 신규 프로덕트는 dbt test가 게이트다.

### sbx 실험 계층 (승격 게이트 앞의 자유 공간 — 구 wrk)

| 항목 | 규칙 |
|---|---|
| 위치 | Postgres 스키마 `sbx`, dbt `models/sbx/` |
| 게이트 | 없음 — glossary 정의·테스트·컬럼 설명 불요 |
| 표기 | 소유자·생성일을 모델 헤더 주석에 필수 기재 (방치 방지 — 주기적 승격/폐기 판단) |
| ref 방향 | `sbx → slv/gld` 참조 **허용** (운영 데이터 읽기), `slv/gld → sbx` 참조 **금지** (실험이 운영 의존성이 되면 안 됨) |
| 실행 | `model__` DAG 생성되나 **수동 트리거 전용** — Manager 편입·Publish·OM 발행 제외 |

### 승격 게이트 (sbx → slv/gld)
1. glossary 정의 확정 — 미확정 필드 0.
2. `schema.yml` 컬럼 설명 + 테스트(키 unique/not_null + 도메인 range).
3. 모델을 `models/sbx/` → 정식 계층 폴더(명명 규칙은 [10](10_NAMING_ORGANIZATION.md))로 이동, manifest 재컴파일·커밋.
4. 자동 결과: Manager 편입 + Publish 대상 + OM 발행.

## 2. 소스 변경 자동 재정의 (Biz Process 수정 대응)

비즈니스 프로세스 재검토·수정이 병행된다 — 이때 바뀌는 것은 **소스**이고, 파이프라인은
의존 그래프를 따라 **자동으로 재정의**된다. 이것은 설계 보장이다:

- 소스가 바뀌면 **소스 선언(`_<소스>__sources.yml`) + slv 모델만 수정**한다. 하류 gold는 `ref()` 그래프를 따라 자동 재구성·재빌드되고, Manager DAG는 재컴파일된 manifest에서 자동 재생성된다.
- **slv가 소스 변경의 흡수 계층**: gold는 slv 인터페이스만 참조하므로 소스 교체의 영향 반경이 slv에서 격리된다 — slv "원천값 보존·표준화" 역할의 존재 이유. staging 모델명이 미래 소스 축(예: `stg_smdm__eqp_org_mapping`)인 것도 같은 이유 (→ [10](10_NAMING_ORGANIZATION.md)).
- 산식·의미 자체가 바뀌는 변경이면 glossary 갱신이 선행한다 (governance 규칙 — 정의 변경은 glossary 먼저).
