# `openmetadata/` — 비즈니스 온톨로지 / 데이터 카탈로그

## 목적
Marquez가 **기술 계보**(테이블/태스크)만 보여주는 반면, OpenMetadata(OM)는 그 위에 **비즈니스 해석**을 입힌다: "이 테이블은 ❶설비마스터 도메인", "이 흐름은 ❷가동성능". 팔란티어의 *Ontology*에 해당하는 레이어.

> Marquez = 기술 계보 + 런타임 헬스 / **OpenMetadata = 비즈니스 온톨로지 + 카탈로그**

## 파일·역할
| 파일 | 역할 |
|---|---|
| `docker-compose.yml` | OM 공식 1.13.1 스택(mysql + elasticsearch + server + ingestion) |
| `om_setup_domains.py` | 7도메인 등록 + 테이블 귀속 + 용어집(Glossary) 생성 (REST API) |
| `om_add_lineage.py` | dbt manifest 의존성을 읽어 OM 테이블 간 lineage 엣지를 직접 PUT |
| `oracle_ingest.yaml` | Oracle 메타데이터 인제스트 설정(생성됨) |
| `dbt_ingest.yaml` | dbt 인제스트 설정(생성됨, 참고용) |

## 왜 이렇게 (개념)
- **별도 compose**: OM 스택은 무겁고 자체 완결적이라 우리 파이프라인 compose와 분리해 `openmetadata/`에서 독립 기동한다.
- **Oracle은 `host.docker.internal:1521`로 인제스트**: OM 컨테이너는 다른 네트워크라 `oracle` 서비스명을 못 찾는다. 호스트에 노출된 1521 포트로 붙는다.
- **도메인 = 비즈니스 해석**: 인제스트된 테이블(기술적)에 7도메인(업무적)을 입혀, 카탈로그를 "업무 언어"로 탐색하게 만든다.
- **lineage는 직접 PUT**: dbt 자동 매칭이 대소문자 문제로 실패해서(아래 이슈), manifest의 `depends_on`을 읽어 OM 테이블 간 엣지를 API로 직접 만들었다.

## 사용/실행법
```bash
cd openmetadata
docker compose up -d                                   # 스택 기동(수 분)
curl localhost:8585/api/v1/system/version              # 서버 준비 확인

# Oracle 메타데이터 인제스트 (이미 컨테이너에 yaml 복사돼 있음)
MSYS_NO_PATHCONV=1 docker compose exec -T ingestion metadata ingest -c /tmp/oracle_ingest.yaml

# 7도메인 + 귀속 + 용어집, 그리고 lineage
PYTHONIOENCODING=utf-8 python om_setup_domains.py
PYTHONIOENCODING=utf-8 python om_add_lineage.py
```
UI: http://localhost:8585 (admin@open-metadata.org / admin)
- **Govern → Domains**에서 ❶/❷ 클릭 → 귀속 테이블
- 테이블 → **Lineage 탭**에서 연결 그래프

## 주의·겪은 이슈
- **포트 충돌**: OM 번들 ingestion(airflow)이 8080을 쓴다 → 우리 Airflow(8080)와 충돌. compose에서 **8088로 remap**.
- **OM은 멀티도메인**: 테이블 도메인 귀속 patch 경로는 `/domain`(단수)이 아니라 **`/domains`(배열)**. 단수로 하면 `500 Unrecognized field domain`.
- **dbt 자동 lineage 매칭 실패**: dbt manifest 스키마는 대문자(`PCS_GOLD`)인데 OM은 Oracle 스키마를 소문자(`pcs_gold`)로 저장 → 매칭 0건. → manifest 의존성을 직접 PUT(`om_add_lineage.py`)으로 우회.
- **REST 잔가시**: `?fields=domain`/`?fields=assets` 같은 무효 필드는 `400`. lineage 조회는 name 엔드포인트 말고 **table id** 기준이 확실. 절대경로 인자엔 `MSYS_NO_PATHCONV=1`.

↑ [최상위 README](../README.md) · 비교: Marquez(기술 계보)는 최상위 README의 옵저버빌리티 항목 참고
