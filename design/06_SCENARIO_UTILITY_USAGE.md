# 06. 시나리오 — Utility 사용량 Summary (첫 번째 데이터 제품)

> 시나리오는 필요 시 07, 08…로 추가된다. 각 시나리오는 extract 구현·dbt 모델·정의서 단위로
> 나란히 얹히는 구조라 서로 충돌하지 않는다.

## 업무 배경
레거시 **EES(설비로그)** 에는 PCS 설비의 센서 Parameter 데이터가 2초 주기로 쌓이고, 사내 시스템이 이를 **5분 데이터 테이블**로 집계해 관리한다(2초→5분 집계는 범위 밖 — **5분 테이블이 소스**). 이 중 Utility 관련 센서만 추려 설비별 Summary 데이터 프로덕트를 만든다:

- **일단위 Utility 사용량** (설비×일)
- **현재 평균 사용량** (당일 진행분 기준)

## 파이프라인
```
레거시 EES (5min Parameter 테이블, Oracle)
   │  ① Extract — chunked fetch + bulk insert (크로스 DB)
   ▼
warehouse.lnd (랜딩)
   │  ② dbt — Utility 센서 필터 → 설비×일 집계 + 당일 평균
   ▼
warehouse.slv → warehouse.gold: Utility 사용량 Summary
   │  ③ dbt test 통과 시 Publish
   ▼
서빙 + OpenMetadata 카탈로그 발행
```

## 확정 사항 (2026-07-07 협의 승계)
1. **Utility 센서 식별 = 명명 규칙**: Parameter 이름/코드 패턴. 패턴은 하드코딩하지 않고 dbt seed/변수로 외부화.
2. **사용량 산식 = 구간값 합산**: 5분 값이 해당 구간의 사용량 → 일 합산 (누적계 차분 아님).
3. **지연 특성 = 수 시간 갱신 가능** → 추출 lookback 기본 24시간(보수적), 실측 후 축소. 겹침 구간은 delete-before-insert로 멱등 재적재.
4. **소스 구조 = 세로형**: 행 = 설비×Parameter×5분버킷 + 값 컬럼 1개 — 센서가 늘어도 스키마 불변.

볼륨·보존·지연·결측 등 운영 정책: [08_DATA_OPS.md](08_DATA_OPS.md)

## 미확정 (구현 착수 전/중 확정 — glossary 정의 선행)
1. **"현재 평균 사용량" 정의**: 집계 윈도(당일 0시~현재? 최근 N시간?)·갱신 주기·표시 단위 — 분모(경과 버킷 vs 수신 버킷)는 결측 정책과 결합 (→ [08 §5](08_DATA_OPS.md)).
2. **대상 설비 범위**: 전체 15만 대 vs 초기 부분집합 — warehouse 작업 윈도 볼륨 산정의 1차 입력 (→ [08 §2](08_DATA_OPS.md)).
3. 실제 명명 패턴 문자열 (확인 전 목데이터 가정값: `UTIL_%`).
4. EES 소스 테이블/컬럼 실명세 → 목데이터 스키마를 실물에 맞춰 조정.
5. **타임존·일 경계**: 일 = Asia/Seoul 00:00 [기본값], LND는 소스 타임스탬프 원형+TZ 보존 — glossary 확정 시 명시.
6. 기존에 담당자가 보던 Excel 산출물 존재 여부 → 있으면 대사 검증 대상([04_AS_IS_INTAKE.md](04_AS_IS_INTAKE.md) 6단계) 포함.

> 결측 5분 버킷은 **기본 0 취급으로 확정** (일 합산에서는 제외와 동일 결과) — → [08 §5](08_DATA_OPS.md).

## 완료 조건
- 추출 태스크 동일 logical date 2회 연속 실행 후 중복 0건.
- lookback 윈도 내 지연 데이터 재적재 검증.
- dbt test 전 계층 통과 (키 unique/not_null + 사용량 음수 금지 range).
- glossary에 "Utility 사용량"·"현재 평균 사용량" 정의 확정 + OM 카탈로그 발행.
- 기존 Excel 산출물이 있으면 대사 검증 기록.
