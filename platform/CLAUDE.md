# platform/ — 수집·오케스트레이션·인프라 (시스템 담당)

| 폴더 | 무엇 |
|---|---|
| `dags/` | `extract_dags/`(YAML→DAG 자동 생성) + `transform_dags/`(Cosmos) |
| `extract/` | `dagfactory/`(경량 팩토리) + `modules/collectors/`(ABC) + `projects/<소스>/`(구현) |
| `common/` | 커넥터(`connectors/`)·CTL 제어(`control/`) |
| `infra/` | Oracle 초기화 DDL(`init/`) + OpenMetadata 스택(`openmetadata/`) |

## 불변 규약
- **호스트/컨테이너 경로 분리**: 컨테이너 안은 `/opt/airflow/{dags,extract,common,transform,tools}` 고정 — 번역은 docker-compose 마운트 담당. import 문자열(`extract.projects...`)·Cosmos 경로를 호스트 트리 기준으로 바꾸지 말 것. → [adr/0004](../design/adr/0004-role-based-tree.md)
- **시크릿은 `.env`만**: compose/profiles에 기본값 폴백(`:-password`) 새로 추가 금지. 커밋 금지.

## 저작 규칙 — 추출 코드를 쓰거나 고칠 때 (필수)
1. **적재 멱등성**: 적재와 워터마크 갱신은 단일 트랜잭션, 또는 LOAD_ID 기준 delete-before-insert/MERGE. Airflow 재시도가 중복 행을 만들면 실패로 간주한다.
2. **이벤트타임 워터마크에는 lookback 윈도 필수**: 센서/설비 데이터의 지연·역순 도착은 정상이다. `MAX(이벤트시각)`만으로 전진하면 지연분이 영구 유실된다. 겹침 구간은 1의 규칙으로 dedup.
3. **크로스 DB 적재(Oracle→Postgres)**: 단일 `INSERT...SELECT` 불가 — chunked fetch + bulk insert(COPY/executemany)로 구현.
4. **DAG 팩토리 YAML에 `eval()` 금지**: 동적 로드는 `import_string`까지만. config는 스키마 검증을 거친다.
5. **알림 없는 DAG 금지**: 모든 DAG default_args에 `on_failure_callback` 배선.
6. **감사 기록은 재시도 안전**: `C_JOB_RUN`류는 run 단위 유니크 키를 갖고, 재시도 시 중복 행이 아닌 갱신이 되게 한다. 행수 집계는 해당 run의 전체 대상 테이블을 포함.
7. **backfill 경로를 설계에 포함**: `catchup`/스냅샷 정책을 정하고, 과거 날짜 재적재 방법을 DAG docstring에 남긴다.

## 새 소스 추가 레시피
1. `extract/projects/<소스>/`에 수집 함수 작성(collector ABC 또는 callable, 위 규칙 준수).
2. `dags/extract_dags/configs/<소스>/*.yaml` 추가 → DAG 자동 등장.
3. CTL 기록(`common/control/ctl.py`) 연결.

## 운영 팁 (겪은 이슈)
- DAG이 안 보이면: Airflow safe_mode는 파일에 "airflow"+"dag" 문자열이 둘 다 있어야 파싱한다.
- `docker compose exec`에 `/opt/...` 절대경로를 넘길 때 Windows Git-Bash는 `MSYS_NO_PATHCONV=1` 접두.
- 추출/변환 DAG은 같은 logical date로 트리거해야 `ExternalTaskSensor`가 매칭된다.
- Cosmos는 LOCAL 실행모드(`dbt_executable_path`)에서만 OpenLineage 이벤트를 emit한다 — 단, 현재 OpenLineage 는 전역 비활성(`AIRFLOW__OPENLINEAGE__DISABLED`, → adr/0005). 계보는 OM dbt ingestion 이 담당.

상세 설계: [design/04](../design/04_EXTRACT_LAYER.md) · [design/06](../design/06_COMMON_LAYER.md) · 기준 시나리오: [design/09](../design/09_SCENARIO_UTILITY_USAGE.md)
