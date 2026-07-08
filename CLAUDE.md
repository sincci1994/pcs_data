# CLAUDE.md — PCS 파이프라인 (START HERE)

PCS 설비 데이터 거버넌스 파이프라인의 **오케스트레이션 서버** 레포 — Airflow + dbt(Cosmos) + OpenMetadata 카탈로그.
데이터 DB(소스 Oracle·웨어하우스 Postgres)는 **외부 DB 서버** — 이 서버는 오케스트레이션·메타데이터만 켠다. → [adr/0005](design/adr/0005-slim-orchestration-topology.md)
목적: 담당자마다 다른 지표 정의를 SQL 중심 + 문서 기반으로 표준화.

> **첫 번째 데이터 제품**: [design/09_SCENARIO_UTILITY_USAGE.md](design/09_SCENARIO_UTILITY_USAGE.md) — Oracle 5분 Parameter → Postgres 적재 → 설비별 일별 Utility 사용량. 샘플 재작성의 기준이며, 시나리오는 필요 시 09, 10…으로 추가된다. 현재 코드는 이전 SCADA 샘플의 척추(참조용)다.

## 레이아웃 (역할 기반 7폴더)

| 폴더 | 무엇 | 누구 |
|---|---|---|
| `governance/` | 용어집·도메인 — **정의의 원천** | 도메인 전문가 |
| `transform/` | SQL 변환(dbt: SLV→CORE→GOLD) | 리소스 담당자 |
| `platform/` | dags(오케스트레이션)·extract(수집)·common(커넥터)·infra(배포) | 시스템 담당자 |
| `quality/` | 헬스 런북·점검 쿼리 (CTL 뷰·dbt test·OpenMetadata) | 품질·모니터링 |
| `workspace/` | instructions(지시)·pdca(계획/결과)·patterns·mistakes | 전원 + Agent |
| `design/` | 설계문서(00~09)·ADR·로드맵 | 설계/아키텍처 |
| `dev/` | tools(목데이터)·tests(pytest) | 개발 |

> **영역별 저작 규칙은 각 폴더의 CLAUDE.md에 있다** (platform/transform/governance/quality/workspace). 해당 폴더에서 작업하면 자동 로드된다 — 이 파일에 중복 기재하지 않는다.

## Agent 운영 규약
1. **지시는 `workspace/instructions/*.md`** 에서 읽는다 (목표/범위/제약/완료조건).
2. **계획·실행결과는 `workspace/pdca/<feature>/`** 에 남긴다: plan→do→check→act. 성공 패턴 → `patterns/`, 실패 교훈 → `mistakes/`.
3. 정의(용어·지표)는 **`governance/` 가 단일 원천** — 작업 전 먼저 확인.
4. 크로스세션 지속 사실 = Claude Code 파일 메모리(`.claude/.../memory`).

## 불변 규칙
- **호스트/컨테이너 분리**: 호스트 트리는 역할 기반(사람용), 컨테이너 안은 `/opt/airflow/{dags,extract,common,transform}` 관례 유지(기계용) — 번역은 docker-compose 마운트가 담당. import 문자열·Cosmos 경로는 컨테이너 기준. → [adr/0004](design/adr/0004-role-based-tree.md)
- **북극성**: Airflow 파싱/실행 경로에 LLM 금지 — 결정론적 제어평면. Agent는 오프라인 저작만.
- **패키징**: PYTHONPATH-루트(설치형 패키지 없음). 폐쇄망 전제. → [design/08](design/08_AIRGAP_BUILD.md) · [adr/0003](design/adr/0003-airgap-packaging.md)
- **시크릿**: 크리덴셜/JWT는 `.env`(→ [.env.example](.env.example))로만. 커밋 금지.

세부 사용법 → [README.md](README.md), 구조 근거 → [design/02](design/02_DIRECTORY_STRUCTURE.md).
