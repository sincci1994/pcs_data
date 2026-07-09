# ADR 0002 — Manager/Model 동적 DAG (Cosmos 대체)

- 상태: 채택 (설계 확정, 구현 Phase 3)
- 날짜: 2026-07-09

## 맥락
요구 6: Airflow에서 DAG를 직접 추가·관리하는 부조리를 없앤다 — dbt 의존성 그래프를 파싱해
개발자 코드 작업 없이 Dynamic DAG를 구성하고, Manager DAG(의존성 관리·순차 트리거·복구)와
Model DAG(모델 1개를 만드는 일련의 태스크)로 구분한다.

이전 척추는 Cosmos `DbtTaskGroup` — 단일 DAG 안에 모델별 태스크를 자동 전개했다.
"SQL 추가→자동 반영"은 충족했지만, 모델 단위 독립 DAG(개별 트리거·백필)와
Manager 주도의 의존성 복구는 Cosmos 밖 요구였다. 2026-07-09 사용자 확정: Manager/Model로 재설계.

## 결정
- 커밋된 dbt `manifest.json`을 파싱하는 **자체 DAG 팩토리**를 구현한다 (`platform/dags/`).
- 모델별 `model__<name>` DAG + 프로젝트당 `manager__<project>` DAG 생성. → [03_DAG_DESIGN.md](../03_DAG_DESIGN.md)
- Cosmos는 사용하지 않는다 (이미지에서 제외).
- manifest는 저작 단계에서 `dbt compile`로 갱신·커밋 — Airflow 런타임 컴파일 금지(결정론).

## 결과
- (+) 모델 단위 독립 재시도·백필·모니터링, 의존성 기반 부분 복구, DAG 목록이 곧 모델 목록.
- (+) 요구 6을 문자 그대로 충족 — 분석가는 .sql과 schema.yml만 만진다.
- (−) 팩토리 코드(파서·트리거 배선·복구 로직)를 직접 유지보수 — Cosmos의 profile 매핑·버전 호환 편의 상실.
- (−) DAG 수가 모델 수에 비례 — 스케줄러 부하는 모델 수 증가 시 그룹핑으로 완화(03 참조).
