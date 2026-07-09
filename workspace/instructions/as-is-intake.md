# 지시서 — AS-IS 인테이크 실행

## 목표
엔지니어별 Excel 그림자 데이터 프로덕트를 발굴해 표준 계층(dbt 모델)으로 이관한다.
절차 정의: [design/04_AS_IS_INTAKE.md](../../design/04_AS_IS_INTAKE.md) · 템플릿: [governance/intake/TEMPLATE.md](../../governance/intake/TEMPLATE.md)

## 범위
- 프로덕트 1건당 인테이크 문서 1개 (`governance/intake/<대상>.md`).
- 인터뷰는 사람이 수행 — Agent는 기록 정리·SQL 초안·대사 검증 쿼리 작성을 담당한다.

## 제약
- 정의(산식·단위·결측 정책)가 glossary에 확정되기 전에 모델을 승격하지 않는다.
- 대사 검증 없이 "레거시와 같다"고 판단하지 않는다.
- 레거시 오류 발견 시 임의 수정 금지 — 담당자 합의 기록 후 신규 정의 채택.

## 완료 조건 (프로덕트 1건 기준)
1. 인테이크 문서 1~7 섹션 전부 기재.
2. glossary 항목 확정 (미확정 필드 0).
3. 대사 검증 결과 기록 (차이 항목은 전부 원인 설명).
4. dbt 모델 + 테스트 머지, manifest 갱신.
