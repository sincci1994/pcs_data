# 02. 디렉토리 구조 (역할 기반 레이아웃)

**호스트 트리 = 사람(역할)용, 컨테이너 경로 = 기계(관례)용.** 번역은 docker-compose 마운트가 담당한다. 근거: [ADR 0004](adr/0004-role-based-tree.md).

## 최상위 = 역할 (7폴더)

| 폴더 | 역할 | 책임 |
|---|---|---|
| `governance/` | 🧭 도메인 전문가 | 용어집·도메인 — **정의의 원천** (컬럼 설명은 dbt schema.yml로 일원화) |
| `transform/` | 🔧 리소스 담당자 | SQL 변환(dbt). 향후 `transform/<engine>/` 확장 |
| `platform/` | ⚙️ 시스템 담당자 | `dags/`(오케스트레이션)·`extract/`(수집)·`common/`(커넥터)·`infra/`(배포) |
| `quality/` | 📊 품질·모니터링 | 헬스 런북·점검 쿼리 (CTL 뷰·DQ·OpenMetadata) |
| `workspace/` | 🤝 전원 + Agent | instructions(지시)·pdca(계획/결과)·patterns·mistakes |
| `design/` | 📐 설계 | 설계문서·ADR·기획서·로드맵 |
| `dev/` | 개발 | tools(목데이터)·tests(pytest) |

## platform/ 내부 (캐논 레포 멘탈모델 보존)
사내 캐논 레포(coldchainservice)의 스테이지 구조는 `platform/` **안에서** 유지된다:
- `platform/extract/modules/collectors/` : 재사용 ABC. `platform/extract/projects/<소스>/` : 구체 구현.
- `platform/common/connectors/` : 멀티엔진 커넥션(Oracle thin/thick 구현, Postgres는 시나리오 [09](09_SCENARIO_UTILITY_USAGE.md) 구현 시 추가). `common/control/` : CTL 제어평면.
- `platform/dags/extract_dags/` : YAML→DAG(소스별 폴더). `platform/dags/transform_dags/` : Cosmos dbt DAG.

## 호스트↔컨테이너 매핑 (docker-compose)
| 호스트 | 컨테이너 |
|---|---|
| `platform/dags` | `/opt/airflow/dags` |
| `platform/extract` | `/opt/airflow/extract` |
| `platform/common` | `/opt/airflow/common` |
| `transform` | `/opt/airflow/transform` (Cosmos 하드코딩 경로 — 유지) |
| `dev/tools` | `/opt/airflow/tools` |

→ import 문자열(`extract.projects...`)·PYTHONPATH·YAML callable 은 **컨테이너 기준**이라 호스트 재편의 영향을 받지 않는다. 새 마운트도 반드시 이 관례를 따를 것.

## 패키징
설치형 패키지·`src/` 미사용. **PYTHONPATH-루트**(plain dir + `__init__.py`). 호스트 테스트는 `dev/tests/conftest.py` 가 `ROOT/platform` 을 주입. 근거: [ADR 0003](adr/0003-airgap-packaging.md).

## 예약(로드맵)
- [계약 엔진](roadmap/contracts-engine.md) : SQL-메타데이터 계약 → 자동 Task+Sensor (미구현).
- [Agent 저작 툴링](roadmap/agent-authoring.md) : 오프라인 저작 자동화 (미구현).
