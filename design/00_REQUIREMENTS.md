# 00. 요구사항 정의 (원문 보존)

> 작성 2026-07-09. 이 문서가 **저장소 전체의 원천 요구사항**이다. 원문은 수정하지 않고,
> 반영 상태는 하단 매핑 표로 관리한다.

## 원문

### 배경 (Why)

1. 본 파이프라인의 목적은 PCS 기술팀의 데이터 활용 역량과 업무 처리 능력 향상이다.

2. [문제] 레거시 앱 UI가 제공하는 VIEW_TABLE의 신뢰도가 낮아, 엔지니어들이
   데이터를 추출한 뒤 Excel로 개별 가공한다. 그 결과 개인 판단에 의존한
   불규칙하고 검증되지 않은 데이터 프로덕트가 산재한다.

3. [문제] 엔지니어는 자신이 담당한 일부 업무에만 관여하며, 전체 비즈니스
   플로우를 설명하는 문서가 없다. 오래된 시스템이 VOC 기반으로 국소적으로
   변형되어 왔고, 과거 협의 내용은 방치되어 현재 흐름을 파악하기 어렵다.

4. [문제] 해당 문제를 인식하고 풀어나갈 전문가의 부재가 있다.

### 접근 (What)

4. [해법] 실제 업무를 담당하는 사람의 데이터 변환 로직을 출발점으로 삼아
   LND → Silver → Gold 계층을 구성한다. 이를 통해 흩어진 국지적 처리를
   Palantir 온톨로지처럼 '비즈니스 정의' 관점에서 통합해, 현재의 데이터
   흐름과 정의된 비즈니스를 조망한다.

5. [핵심 제약] 이 구조는 지속적으로 대규모 수정을 수반한다. 수정 주체는
   도메인 지식이 높은 분석가이며, 개발자 개입 없이 직접 모델(SQL, 데이터
   정의서)을 추가·수정하고 결과를 자유롭게 확인할 수 있어야 한다.
   (AI Agent 활용 포함)

### 파이프라인 설계 (How) — ※ 별도 ARCHITECTURE.md 권장

6. [분석가 자율성 확보] 5번 구조를 운영하며 겪은 불편(Airflow에서 DAG를
   직접 추가·관리하는 부담)을 해소하기 위해, dbt 의존성 그래프를 파싱하여
   Dynamic DAG를 자동 생성한다 (개발자 코드 작업 불필요).
   - Manager DAG: Model DAG 간 의존 관계 관리. 의존 순서대로 순차 Trigger,
     Model DAG 실패 시 의존 관계에 따라 복구.
   - Model DAG: 하나의 모델 데이터를 생성하는 Task 집합.

7. dbt로 모델 작성·계보 자동 생성·데이터 검증을 수행한다. SQL과 PySpark
   모델을 모두 지원하고, Partition 기반 의존성을 관리하며, 모든 엔진의 모델을
   빌드 과정을 통해 단일 의존성 그래프로 통합한다.

### 작업 방식 (Execution)

8. 실제 작업은 Claude Code Agent 기반으로 수행한다.


## 반영 매핑 (원문 구분 체계 기준 — 2026-07-09 개정)

| 원문 항목 | 반영 위치 | 상태 |
|---|---|---|
| 배경 1 — 팀 역량·데이터 활용능력 향상 | [01_OVERVIEW.md](01_OVERVIEW.md) 목적 | 반영 |
| 문제 2 — 그림자 데이터 프로덕트 | [04_AS_IS_INTAKE.md](04_AS_IS_INTAKE.md) 발굴·표준화 + quality/ 대사 검증 | 반영 |
| 문제 3 — 비즈니스 플로우 문서 부재 | governance/(정의·인테이크 기록) + OpenMetadata 용어집·리니지 | 반영 |
| **문제 4 — 전문가 부재** | 전문 지식을 사람이 아니라 **시스템에 축적**: glossary·인테이크 기록(암묵지의 문서화), 계층 계약·명명 규칙([10](10_NAMING_ORGANIZATION.md)), 온보딩 [GUIDE.md](../GUIDE.md)(비전문가 진입장벽 최소화), Agent 협업([workspace/](../workspace/CLAUDE.md)) — 배경 1의 역량 향상이 내부 전문가를 길러내는 경로 | 반영 (2026-07-09 추가) |
| 해법 4 — LND/Silver/Gold 계층 + 온톨로지 | [02_ARCHITECTURE.md](02_ARCHITECTURE.md) 계층 — 어휘는 메달리온 축약 `brz/slv/gld`로 구현 (→ [10](10_NAMING_ORGANIZATION.md)) | 반영 |
| 제약 5 — 분석가 셀프서비스 (SQL·정의서 직접 추가) | [07_AUTHORING_FLOW.md](07_AUTHORING_FLOW.md) + transform/ 규칙 + 소스 추가도 선언형(extract/sources.yml) | 반영·검증 |
| 설계 6 — Manager/Model Dynamic DAG | [03_DAG_DESIGN.md](03_DAG_DESIGN.md) · [adr/0002](adr/0002-manager-model-dynamic-dag.md) | **구현·라이브 검증 완료** (2026-07-09) |
| 설계 7 — dbt 계보·검증 / SQL+PySpark 멀티엔진 | dbt+OM 반영 / PySpark는 [adr/0003](adr/0003-defer-pyspark-multi-engine.md) | 일부 보류 |
| 실행 8 — Claude Code Agent 기반 작업 | workspace/ 운영 규약 (CLAUDE.md) | 반영 |

> 구판 원문의 "10 전면 재구축" 요구는 2026-07-09 재구축 커밋으로 완료되어 원문 정리 시 제거됨.

## 확정 결정 (2026-07-09 질의응답)

1. **첫 데이터 제품** = Utility 사용량 → **당일 교체**: PortMaster2 기반 Equipment/Pipe 기준정보([09](09_SCENARIO_EQUIPMENT_PIPE.md), 완료). Utility 사용량([06](06_SCENARIO_UTILITY_USAGE.md))은 CurrentAvgUsage 정의 확정 시 재개.
2. **DAG 구조** = Manager/Model DAG로 재설계 (Cosmos 단일 DAG 폐기). → [adr/0002](adr/0002-manager-model-dynamic-dag.md)
3. **PySpark·멀티엔진** = 로드맵 보류. → [adr/0003](adr/0003-defer-pyspark-multi-engine.md)
4. **AS-IS 확보 상태**: VIEW_TABLE까지의 쿼리는 존재. 데이터 프로덕트는 Excel(변환이 엑셀 함수) — 동료 인터뷰로 전처리 논리를 기록 → SQL화 → 데이터 검증 → 완성 쿼리 탑재. 이 발굴 과정은 **한시적**이며 개별 Agent로 수행.
