# 10. 명명·조직 전략 — 계층 계약과 탐색성

> 확정 2026-07-09 (사용자 결정). 모델 수가 늘어도 "어디에 만들고 어디서 찾는지"가
> 자명하도록 저장소 전체의 명명 규칙을 여기 한 곳에 정본화한다.
> 요구 4의 "LND/SILVER/GOLD" 어휘는 이 문서의 메달리온 축약 체계로 구현된다.

## 1. 계층 계약 (스키마 = 데이터 품질 단계)

| 스키마 | 의미 | 허용 동작 | 금지 |
|---|---|---|---|
| `brz` | bronze — 소스 원형 | extract 적재만 (컬럼 추가·해석 없음, `loaded_at` 부착) | dbt 모델 생성 금지 (extract 소유) |
| `slv` | silver — 정제·표준화 | 타입 캐스팅, NULL/빈값 필터, dedup, 이름 표준화, 경량 결합 | **비즈니스 판단(지표 산식·업무 필터) 금지** — 원천값 보존 |
| `gld` | gold — 비즈니스 데이터 제품 | 지표 산식, 업무 규칙, 집계 — glossary 정의 선행 | **소스(brz) 직접 참조 금지** — slv 인터페이스만 |
| `sbx` | sandbox — 실험 (구 wrk) | 무엇이든 (소유자·날짜 헤더만 필수) | slv/gld → sbx 참조 금지 (실험이 운영 의존성 불가) |
| `ctl` | 제어 (watermark·job_audit) | platform 코드만 | 분석가·dbt 접근 불가 |
| `srv` | 서빙 대역 (로컬 검증용) | Publish 태스크만 | — |

**동작(clean/filter 등)은 폴더로 나누지 않는다** — 모델 하나가 rename+cast+filter+dedup 을
한 SELECT 로 수행하므로 동작별 폴더는 인위적 파편화(모델 수 폭발)만 만든다. 동작이 사는 곳:
① 이 계약 표(계층별 허용 동작) ② `int_` 모델명의 동사 ③ 모델 내부 CTE 명.

## 2. dbt 폴더 구조 (폴더 = 스키마 미러 + 계층별 축)

```
transform/models/
├─ slv/                        # 스키마 slv — 소스 시스템 축
│  ├─ ees/
│  │  ├─ _ees__sources.yml     #   brz 테이블 선언
│  │  ├─ stg_ees__portmaster2.sql
│  │  └─ int_ees__<동사구>.sql  #   (복잡 변환의 중간 단계 — 필요 시)
│  └─ smdm/
│     └─ stg_smdm__eqp_org_mapping.sql
├─ gld/                        # 스키마 gld — 비즈니스 도메인 축
│  └─ pipe_scheduler/          #   첫 도메인. utility 등 도메인 단위로 추가
│     ├─ dim_equipment.sql · dim_pipe.sql · dim_vendor.sql
│     └─ (후속) fct_*.sql
└─ sbx/                        # 실험 — 하위 폴더 자유
```

## 3. 명명 규칙

| 대상 | 규칙 | 예 |
|---|---|---|
| brz 테이블 | `brz.<소스>__<엔티티>` | `brz.ees__portmaster2` |
| staging 모델 | `stg_<소스>__<엔티티>` | `stg_ees__portmaster2` |
| intermediate 모델 | `int_<대상>_<동사구>` — **동사가 사는 곳** | `int_paths_paired`, `int_scrubber_owner_resolved` |
| mart 모델 | `dim_<엔티티>` / `fct_<이벤트/지표>` — **비즈니스명만** | `dim_equipment`, `fct_utility_usage_daily` |
| seed | `seed_<내용>` (스키마 slv — 큐레이션 참조 데이터) | `seed_eqp_org_mapping` |
| Asset URI | `postgresql://warehouse/pcs_wh/brz/<소스>__<엔티티>` | |
| DAG | `extract__<소스>_<엔티티>` / `model__<모델명>` / `manager__<프로젝트>` | |

### 축 원칙 — 소스명은 slv 까지, gld 는 비즈니스명만
- **slv = 소스 축**: 이 계층의 정체성이 "어느 시스템에서 왔나"다. 미래 소스 기준으로 명명한다
  (예: `stg_smdm__eqp_org_mapping` 은 v1 원천이 seed 더미여도 SMDM 인터페이스로 명명 —
  실연동 시 원천만 교체하면 하류 불변, → [07](07_AUTHORING_FLOW.md)).
- **gld = 비즈니스 축**: 소비자는 출처가 아니라 비즈니스 개념으로 찾는다. mart 이름에 소스명이
  박히면 소스 교체 시 이름이 거짓말이 되고 다중 소스 제품은 명명 불가. 출처 추적은 OM 리니지가 담당.
- 도메인 분류는 `gld/<도메인>/` 폴더로. 도메인별 스키마 분리는 권한 요구가 생길 때 재검토 (→ roadmap).

## 4. 탐색 규칙 ("모델이 많아지면 어떻게 찾나")
1. **비즈니스 개념으로**: OpenMetadata 검색 → 용어집(글로서리) → 연결 자산 → 리니지.
2. **저장소에서**: 계층(폴더) → 축(소스/도메인) → 접두사. 이름만으로 계층·역할이 읽히게 유지.
3. 신규 저작 위치 판단은 [GUIDE.md](../GUIDE.md) 치트시트.
