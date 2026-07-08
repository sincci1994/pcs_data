# `openmetadata/` — 비즈니스 온톨로지 / 데이터 카탈로그

## 목적
OpenMetadata(OM)는 **기술 계보**(테이블/컬럼, dbt ingestion) 위에 **비즈니스 해석**을 입힌다: "이 테이블은 ❶설비마스터 도메인", "이 흐름은 ❷가동성능". 팔란티어의 *Ontology*에 해당하는 레이어. 이 프로젝트 관측성의 단일 카탈로그다(과거 Marquez 병행 → 제거, [adr/0005](../../../design/adr/0005-slim-orchestration-topology.md)).

## 파일·역할
| 파일 | 역할 |
|---|---|
| `docker-compose.yml` | OM 공식 1.13.1 스택(mysql + elasticsearch + server + ingestion) |
| `om_setup_domains.py` | 7도메인 등록 + 테이블 귀속 + 용어집(Glossary) 생성 (REST API) |
| `om_add_lineage.py` | dbt manifest 의존성을 읽어 OM 테이블 간 lineage 엣지를 직접 PUT |
| `oracle_ingest.yaml` | Oracle 메타데이터 인제스트 설정(생성됨) |
| `dbt_ingest.yaml` | dbt 인제스트 설정(생성됨, 참고용) |

## 왜 이렇게 (개념)
- **루트에 include**: OM 스택은 무겁지만 폐쇄망 반입을 단일 명령·단일 이미지 번들로 끝내기 위해 루트 compose 가 이 파일을 `include` 한다 → `docker compose up -d --build` 에 함께 뜬다([adr/0005](../../../design/adr/0005-slim-orchestration-topology.md)). 이 파일 자체는 그대로라 standalone 기동도 가능.
- **Oracle 인제스트 호스트**: 외부 Oracle 실서버 주소(`PCS_ORACLE_HOST`)로 직접 붙는다. OM 컨테이너에서 도달 가능한 주소여야 한다(사내 DNS/IP). 로컬 Oracle 컨테이너는 없다.
- **도메인 = 비즈니스 해석**: 인제스트된 테이블(기술적)에 7도메인(업무적)을 입혀, 카탈로그를 "업무 언어"로 탐색하게 만든다.
- **lineage는 직접 PUT**: dbt 자동 매칭이 대소문자 문제로 실패해서(아래 이슈), manifest의 `depends_on`을 읽어 OM 테이블 간 엣지를 API로 직접 만들었다.

## 사용/실행법
서버 기동은 루트 `docker compose up -d --build` 에 포함된다(include). 아래는 **기동 후 1회 카탈로그 셋업** — 에어갭 `docker load` 반입 직후(볼륨 빈 상태)에도 동일하게 재수행한다.
```bash
curl localhost:8585/api/v1/system/version              # 서버 준비 확인 (루트 up 으로 이미 기동됨)

# Oracle 메타데이터 인제스트 (oracle_ingest.yaml 에 JWT·외부 호스트 채운 뒤)
MSYS_NO_PATHCONV=1 docker compose exec -T ingestion metadata ingest -c /tmp/oracle_ingest.yaml

# 7도메인 + 귀속 + 용어집, 그리고 lineage
PYTHONIOENCODING=utf-8 python om_setup_domains.py
PYTHONIOENCODING=utf-8 python om_add_lineage.py
```
> 에어갭 반입 절차(save/load)는 [`ops/README`](../ops/README.md).
UI: http://localhost:8585 (admin@open-metadata.org / admin)
- **Govern → Domains**에서 ❶/❷ 클릭 → 귀속 테이블
- 테이블 → **Lineage 탭**에서 연결 그래프

## 주의·겪은 이슈
- **포트 충돌**: OM 번들 ingestion(airflow)이 8080을 쓴다 → 우리 Airflow(8080)와 충돌. compose에서 **8088로 remap**.
- **OM은 멀티도메인**: 테이블 도메인 귀속 patch 경로는 `/domain`(단수)이 아니라 **`/domains`(배열)**. 단수로 하면 `500 Unrecognized field domain`.
- **dbt 자동 lineage 매칭 실패**: dbt manifest 스키마는 대문자(`PCS_GOLD`)인데 OM은 Oracle 스키마를 소문자(`pcs_gold`)로 저장 → 매칭 0건. → manifest 의존성을 직접 PUT(`om_add_lineage.py`)으로 우회.
- **REST 잔가시**: `?fields=domain`/`?fields=assets` 같은 무효 필드는 `400`. lineage 조회는 name 엔드포인트 말고 **table id** 기준이 확실. 절대경로 인자엔 `MSYS_NO_PATHCONV=1`.

↑ [최상위 README](../../../README.md) · 런타임 헬스는 Airflow UI + CTL 뷰(→ [quality/runbook](../../../quality/runbook.md))
