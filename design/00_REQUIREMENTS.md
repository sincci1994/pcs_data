# 00. 요구사항 정의 (원문 보존)

> 작성 2026-07-09. 이 문서가 **저장소 전체의 원천 요구사항**이다. 원문은 수정하지 않고,
> 반영 상태는 하단 매핑 표로 관리한다.

## 원문

1. 해당 파이프라인은 PCS기술팀의 업무 능력 및 데이터 활용능력 향상을 위한 파이프 라인이다.
2. 레거시 앱의 UI에서 제공하는 VIEW_TABLE을 못믿어서 추출후 자기의 나름대로 Excel을 통한 가공 처리를 진행해서 엔지니어 개인판단이 만든 불규칙적인 데이터 프로덕트들이 존재함
3. 엔지니어는 일부 비즈니스에만 개입해서 본인의 역할에만 충실하는 상황이고 전체적인 비즈니스 플로우가 어떻게 되는지에 대한 문서가 존재하지 않음. 오래전에 개발된 시스템으로 불편 VOC를 모아서 일부 변형이 일어나고, 기존에 협의 된 사항의 정보는 방치되고 그런 부분들이 존재
4. 위와 같은 상황이다보니 국지적으로 일어나고 있는 하지만 그 중에서 업무 처리 자체를 담당하는 사람의 데이터 변환 방식을 토대로 현재 LND SILVER GOLD 수준으로 만들어서 데이터 흐름 및 정의된 비즈니스들을 토대로 팔란티어의 온톨로지 처럼 비즈니스 정의로 현재 흐름을 보겠단 것
5. 여기서 이제 대규모 수정이 병행 될 수 있다고 보는데 그 주체는 데이터 도메인 지식이 높은 분석가가 직접 모델을 추가하고 (SQL이나 데이터 정의서등을 수정할 것임 물론 AI Agent도 활용할 것임) 자유롭게 볼 수 있는 구조가 필요함
6. 여기서 최근 분석활동을 위한 파이프라인 형태를 보면 Airflow 에서 DAG를 직접 추가하고 관리시에 느끼는 부조리를 개선하기 위해 DBT 의존성 그래프 파일을 파싱하여 Dynamic DAG를 구성하고 (개발자 코드 작업 불필요) Manager DAG, Model DAG 유형으로 구분하며 Manager DAG : Model DAG 의존성 관리 / Model DAG : 하나의 모델 데이터를 만들기 위한 일련의 TASK. Manager DAG에서 의존 관계가 있는 Model DAG를 순차 Trigger. Model DAG 실패시, Manager DAG에서 의존 관계에 따라 복구 가능
7. DBT를 활용해서 모델 작성 및 계보 자동생성, 데이터 민주화 및 검증관리. SQL, PySpark 모델 지원, Partition 기반의 의존성 지원. 모든 Engine의 모델을 빌드 과정을 통해 하나의 의존 그래프로 구성 된다.
8. 6,7은 5번 같은 구조를 하다가 불편함을 해소하기 위해 생각해낸 아이디어를 찾아서 적은 것이다.
9. 다만 여기서 나는 작업 자체를 Claude Code Agent 기반으로 할 계획이다. (더 편리하게 할 수 있음)
10. 현재 초기 구조를 CLAUDE.md 처럼 만들었지만 위 상황이 다 반영 되었는지 확인이 필요하고 안되었다면 전면 수정을 해야한다.

## 반영 매핑

| 요구 | 반영 위치 | 상태 |
|---|---|---|
| 1 팀 역량·데이터 활용능력 향상 | [01_OVERVIEW.md](01_OVERVIEW.md) 목적 | 반영 |
| 2 그림자 데이터 프로덕트 표준화 | [04_AS_IS_INTAKE.md](04_AS_IS_INTAKE.md) + quality/ 대사 검증 | 반영 |
| 3 비즈니스 플로우 문서화 | governance/ + OpenMetadata 용어집·리니지 | 반영 |
| 4 LND/SILVER/GOLD + 온톨로지 | [02_ARCHITECTURE.md](02_ARCHITECTURE.md) 계층 | 반영 |
| 5 분석가 셀프서비스 (SQL·정의서 직접 추가) | [07_AUTHORING_FLOW.md](07_AUTHORING_FLOW.md) + transform/ 규칙 + [03_DAG_DESIGN.md](03_DAG_DESIGN.md) | 반영 |
| 6 Manager/Model Dynamic DAG | [03_DAG_DESIGN.md](03_DAG_DESIGN.md) · [adr/0002](adr/0002-manager-model-dynamic-dag.md) | 설계 확정, 구현 Phase 3 |
| 7 dbt 계보·검증 / SQL+PySpark 멀티엔진 | dbt+OM 반영 / PySpark는 [adr/0003](adr/0003-defer-pyspark-multi-engine.md) | 일부 보류 |
| 9 Claude Code Agent 기반 작업 | workspace/ 운영 규약 (CLAUDE.md) | 반영 |
| 10 전면 재구축 | 2026-07-09 본 재구축 커밋 | 완료 |

## 확정 결정 (2026-07-09 질의응답)

1. **첫 데이터 제품** = Utility 사용량: 레거시 EES 설비로그 센서 데이터 → 일단위 사용량 + 현재 평균 사용량 Summary. → [06_SCENARIO_UTILITY_USAGE.md](06_SCENARIO_UTILITY_USAGE.md)
2. **DAG 구조** = Manager/Model DAG로 재설계 (Cosmos 단일 DAG 폐기). → [adr/0002](adr/0002-manager-model-dynamic-dag.md)
3. **PySpark·멀티엔진** = 로드맵 보류. → [adr/0003](adr/0003-defer-pyspark-multi-engine.md)
4. **AS-IS 확보 상태**: VIEW_TABLE까지의 쿼리는 존재. 데이터 프로덕트는 Excel(변환이 엑셀 함수) — 동료 인터뷰로 전처리 논리를 기록 → SQL화 → 데이터 검증 → 완성 쿼리 탑재. 이 발굴 과정은 **한시적**이며 개별 Agent로 수행.
