# 로드맵: SQL-메타데이터 계약 → 자동등록 엔진 (미구현)

기획서의 헤드라인 기능:

> "**의존성만 기록된 SQL 을 추가하면 자동으로 의존성이 걸린 Task 가 추가되고, Task 완료 메시지를 전달하는 Sensor 도 자동 추가**된다."

## 설계 방향 (구현 시)
1. 각 SQL(또는 콜로케이트된 `*.contract.yaml`)이 **선언적 메타데이터**를 싣는다: 타겟 테이블·상위 의존성·스케줄·센서 스펙·비즈니스 설명.
2. **빌드타임 파서**(순수 파이썬)가 계약을 읽어 레지스트리를 만들고, `platform/extract/dagfactory` 에 먹여 Task + 완료 Sensor 를 **결정론적으로** 생성한다.
3. dbt 모델은 이미 `ref()` → Cosmos 로 이 그림의 절반이 동작한다(`platform/dags/transform_dags/`). 이 엔진은 **비-dbt 원시 SQL** 까지 일반화하는 것.

## 북극성 제약
**Airflow 파싱 시점에 LLM 이 절대 개입하지 않는다.** 계약 파싱·DAG 생성은 100% 결정론적. LLM 은 [Agent 저작 평면](agent-authoring.md)에서 *오프라인*으로만 계약을 초안 작성한다.

## 구현 위치(예정)
`platform/` 아래(오케스트레이션 기계의 일부이므로). 재사용 씨앗: `platform/extract/dagfactory/core.py`(YAML→DAG), `platform/infra/openmetadata/om_add_lineage.py`(manifest→엣지).
