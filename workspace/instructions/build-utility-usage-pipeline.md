# 작업 지시: Utility 사용량 파이프라인 구축 (design/09 구현)

- 상태: 진행중
- 요청자: 데이터 엔지니어 (본인)
- 작성일: 2026-07-07
- 대응 PDCA: `workspace/pdca/utility-usage/`

## 목표
[design/09](../../design/09_SCENARIO_UTILITY_USAGE.md) 시나리오를 동작하는 파이프라인으로 구현한다:
Oracle 5분 Parameter 테이블(목데이터로 모사) → **Postgres 웨어하우스** DB-to-DB 적재 → dbt-postgres 변환 → GOLD **설비별 일별 Utility 사용량**.

## 배경
- 시나리오·확정 사항(명명 규칙 식별 / 구간값 합산 / 지연 수 시간·lookback 24h / 세로형 소스)은 design/09 참조.
- 용어 `UtilityUsage`는 구현 착수 전 [governance/ontology/glossary.md](../../governance/ontology/glossary.md)에 정의한다 — 산식(구간값 일 합산)·단위·**결측 5분 버킷 처리 정책** 포함.
- 기존 SCADA 샘플(Oracle 단일 인스턴스)은 참조용 척추 — 이 작업에서 수정하지 않고, 완료 후 별도 지시로 정리한다.

## 범위
**포함** (단계 순):
- ⓐ 인프라: docker-compose에 웨어하우스용 Postgres 서비스 추가(Airflow 메타DB와 분리), 소스 Oracle에 세로형 5분 테이블 DDL + 목데이터 생성기(`dev/tools/`).
- ⓑ 추출: `platform/common/connectors/postgres.py` 실구현, `platform/extract/projects/pcs_param/` — chunked fetch(Oracle) + bulk insert(Postgres COPY/executemany), lookback 24h + 윈도 단위 delete-before-insert 멱등, CTL 기록, YAML config로 DAG 등록.
- ⓒ 변환: dbt-postgres 프로파일, SLV(표준화 + 명명 규칙 필터 — 패턴은 seed/변수로 외부화) → CORE(설비×센서×일 팩트, **incremental**) → GOLD(Utility 사용량 마트), CTL 스키마 Postgres 이관(on-run-end 훅 포팅).
- ⓓ 품질: schema.yml 테스트(키 unique/not_null + 사용량 ≥ 0 range), 모든 DAG에 `on_failure_callback` 배선.

**제외**: OpenMetadata 카탈로그 발행 자동화, 기존 SCADA 척추 삭제/정리, 대시보드·화면.

## 제약
- 각 폴더 **CLAUDE.md 저작 규칙 준수** (platform: 멱등성·lookback·크로스DB·알림 / transform: incremental·게이트 스코프·range 테스트).
- Airflow 파싱/실행 경로에 LLM 개입 금지(결정론적). PYTHONPATH-루트 패키징. 시크릿은 `.env`만.
- 사내 확인 전 가정값 사용: 명명 패턴 `UTIL_%`, lookback 24h — 가정임을 코드 주석·설정에 명시하고 확인 후 치환.

## 완료조건 (acceptance)
- [ ] 동일 logical date로 추출 2회 연속 실행 후 Postgres LND 중복 0건.
- [ ] lookback 윈도 내 소스 값 갱신(지연 데이터)이 재적재로 반영됨을 검증.
- [ ] 변환 게이트가 당일 적재분 기준으로 동작 (전체 `COUNT(*)` 게이트 금지).
- [ ] dbt test 전 계층 통과 + 사용량 range 테스트 포함.
- [ ] 태스크 강제 실패 시 `on_failure_callback` 알림 동작 확인.
- [ ] glossary에 `UtilityUsage` 정의 등록(산식·단위·결측 정책).

## 선행 액션 (사내 확인 — 병행 가능)
1. Utility Parameter 실제 명명 패턴 문자열.
2. 소스 5분 테이블/컬럼 실명세.
3. 지연 상한 실측 → lookback 조정.
4. 결측 버킷 처리 정책 확정 → glossary 반영.

## 참고문서
- [design/09_SCENARIO_UTILITY_USAGE.md](../../design/09_SCENARIO_UTILITY_USAGE.md)
- [platform/CLAUDE.md](../../platform/CLAUDE.md) · [transform/CLAUDE.md](../../transform/CLAUDE.md)
