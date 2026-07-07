# 09. 시나리오 — PCS 설비 Utility 사용량 (첫 번째 데이터 제품)

> 이 레포의 **첫 번째 데이터 제품(기준 시나리오)**. 시나리오는 미리 여러 개 정의하지 않고
> 필요해질 때 09, 10, …으로 추가한다 — 각 시나리오는 `extract/projects/<소스>/`·dbt 모델·
> YAML config 단위로 나란히 얹히는 구조라 서로 충돌하지 않는다. 시나리오 공통 저작 규칙
> (멱등성·lookback·게이트 스코프 등)은 시나리오 문서가 아니라 각 폴더 CLAUDE.md에 있다.
> 기존 SCADA 센서 KPI 샘플은 참조용 척추로만 남아 있으며, 이 시나리오 구현 시 대체된다.
> 구현 지시서: [workspace/instructions/build-utility-usage-pipeline.md](../workspace/instructions/build-utility-usage-pipeline.md)

## 업무 배경
사내 Oracle DB에는 PCS 설비의 각종 Parameter 데이터가 **2초 주기**로 쌓이고, 사내 시스템이 이를 **5분 데이터 테이블**로 집계해 관리한다(2초→5분 집계는 우리 범위 밖 — **5분 테이블이 우리의 소스**). 이 중 **Utility 관련 센서**만 추려 **설비별 하루 Utility 사용량** 지표를 만들어 제공한다.

## 파이프라인
```
사내 Oracle (5min Parameter 테이블)
   │  ① 추출: DB-to-DB 적재 (사내 안내 방식)
   ▼
Postgres LND (랜딩)
   │  ② 변환: dbt-postgres — Utility 센서 필터 → 설비×일 집계
   ▼
Postgres SLV → CORE → GOLD:  지표 "Utility 사용량" (설비별 일별)
```

## 계층별 요구사항

### ① 추출 (Oracle → Postgres)
- 크로스 엔진이므로 단일 `INSERT...SELECT` 불가 → **chunked fetch(Oracle) + bulk insert(Postgres COPY/executemany)**.
- 소스는 **세로형**(행 = 설비×Parameter×5분버킷, 값 컬럼 1개) — 센서가 늘어도 스키마 불변.
- 워터마크 = 5분 버킷 타임스탬프. 소스는 **수 시간 지연 갱신 가능** → **lookback 기본 24시간**(실측 후 축소), 겹침 구간은 윈도 단위 delete-before-insert로 멱등 재적재.
- 재시도·backfill이 중복을 만들지 않을 것 (→ platform/CLAUDE.md 저작 규칙 1·2·7).

### ② 변환 (dbt-postgres)
- SLV: 5분 데이터 표준화(원천값 보존). Utility 센서는 **Parameter 명명 규칙으로 식별** — 패턴은 하드코딩하지 않고 dbt seed/변수로 외부화.
- CORE: 설비×센서×일 grain 팩트 — **incremental 필수** (5분×전 센서는 대용량 경로).
- GOLD: 설비별 일별 **Utility 사용량** 마트. 산식 = **구간값 합산**(5분 값이 해당 구간의 사용량 → 일 합산). 결측 5분 버킷 처리 정책은 지표 정의에 명시.
- 테스트: 키 unique/not_null + 사용량 음수 금지 range 테스트 (→ transform/CLAUDE.md 규칙 1·4).

### ③ 서빙·거버넌스
- `governance/ontology/glossary.md`에 "Utility 사용량" 용어 정의(산식·단위) 먼저 확정 후 구현.
- GOLD 지표는 OpenMetadata 카탈로그로 발행.

## 스택 변경점 (기존 샘플 대비)
| 항목 | 기존 (SCADA 샘플) | 이 시나리오 |
|---|---|---|
| 웨어하우스 | Oracle 단일 인스턴스 (전 계층) | **Postgres** (LND~GOLD·CTL) — Oracle은 소스 전용 |
| dbt 어댑터 | dbt-oracle | **dbt-postgres** |
| 적재 방식 | Oracle 내부 `INSERT...SELECT` | **크로스 DB** fetch+bulk insert (Postgres 커넥터 신규 구현 필요) |
| compose | Oracle + Airflow 메타 Postgres | + **웨어하우스용 Postgres 서비스 추가** (Airflow 메타 DB와 분리) |
| CTL 스키마 | Oracle `PCS_CTL` | Postgres로 이관 (뷰·on-run-end 훅 포팅, COMMIT 훅은 불필요해질 수 있음 — 재검토) |

## 확정 사항 (2026-07-07)
1. **Utility 센서 식별 = 명명 규칙**: Parameter 이름/코드 패턴으로 구분. 패턴은 seed/변수로 외부화.
2. **사용량 산식 = 구간값 합산**: 5분 값이 해당 구간의 사용량 — 일별 합산. (누적계 차분 아님)
3. **지연 특성 = 수 시간 갱신 가능** → lookback 기본 24시간(보수적), 실측 후 축소.
4. **소스 구조 = 세로형**: 행 = 설비×Parameter×5분버킷 + 값 컬럼 1개.

## 사내 확인 잔여 (구현 착수 전/중 확정)
1. 실제 명명 패턴 문자열 (확인 전 목데이터 가정값: `UTIL_%`).
2. 소스 테이블/컬럼 실명세 → 목데이터 스키마를 실물에 맞춰 조정.
3. 지연 상한 실측 → lookback 24h 조정.
4. 결측 5분 버킷 처리 정책 (0 취급 / 제외 / 보간) — `UtilityUsage` 지표 정의에 명시.

## 완료 조건 (구현 시)
- 추출 태스크 2회 연속 실행(동일 logical date) 후 중복 0건.
- lookback 윈도 내 지연 데이터 재적재 검증.
- 변환 게이트가 당일 적재분 기준으로 동작 (전체 COUNT 금지).
- dbt test 전 계층 통과 + 사용량 range 테스트 포함.
- `on_failure_callback` 알림 동작 확인.
