# platform/ — 수집·오케스트레이션·인프라 (시스템 담당)

Phase 2(infra)·Phase 3(dags/extract/common)에서 코드가 들어올 자리.

| 폴더 | 무엇 |
|---|---|
| `dags/` | DAG 팩토리 2종 — `factory__extract.py`(sources.yml 파싱) · `factory__pcs_transform.py`(manifest 파싱) |
| `extract/` | `sources.yml`(소스 선언 — **신규 소스는 여기 블록 추가가 전부**) + 범용 로더(snapshot) |
| `common/` | pg(warehouse)·db(소스/서빙 방언 디스패치) 접속, ctl 기록, notifier, publish, Asset 파생 |
| `infra/` | OpenMetadata+Airflow compose 스택 (→ [design/05](../design/05_INFRA.md)) |

## 불변 규약
- **런타임 결정론**: DAG 파싱·실행 경로에 LLM 금지. DAG는 커밋된 manifest/YAML에서만 생성 — 수동 DAG 작성 금지 (→ [design/03](../design/03_DAG_DESIGN.md)).
- **호스트/컨테이너 경로 분리**: 컨테이너 안은 `/opt/airflow/...` 관례 고정, 번역은 compose 마운트 담당. import 문자열을 호스트 트리 기준으로 바꾸지 말 것.
- **시크릿은 `.env`만**: compose/profiles에 기본값 폴백 추가 금지.

## 저작 규칙 — 추출 코드를 쓰거나 고칠 때 (이전 구현에서 검증된 규칙 승계)
0. **신규 소스 추가는 `extract/sources.yml` 선언으로만** — 소스별 파이썬 모듈 복제 금지. 로더 자체를 고칠 때만 아래 규칙 적용 (절차: [GUIDE.md](../GUIDE.md) 트랙 1).
1. **적재 멱등성**: 적재와 워터마크 갱신은 단일 트랜잭션, 또는 delete-before-insert/MERGE. Airflow 재시도가 중복 행을 만들면 실패로 간주.
2. **이벤트타임 워터마크에는 lookback 윈도 필수**: 센서 데이터의 지연·역순 도착은 정상. `MAX(이벤트시각)`만으로 전진하면 지연분이 영구 유실된다.
3. **크로스 DB 적재(Oracle→Postgres)**: 단일 `INSERT...SELECT` 불가 — chunked fetch + bulk insert(COPY/executemany).
4. **동적 로드에 `eval()` 금지**: `import_string`까지만. config는 스키마 검증을 거친다.
5. **알림 없는 DAG 금지**: 모든 DAG default_args에 `on_failure_callback` 배선 — 반드시 **notifier 공통 모듈**(사내 메일·메신저 API 어댑터, → [design/08 §7](../design/08_DATA_OPS.md))을 통해서만. 개별 DAG에서 채널 API 직접 호출 금지.
6. **감사 기록은 재시도 안전**: `ctl.job_audit`에 run 단위 유니크 키(dag_id+logical_date)로 재시도 시 중복이 아닌 갱신. 워터마크는 `ctl.watermark`.
7. **backfill 경로를 설계에 포함**: catchup 정책과 과거 날짜 재적재 방법을 DAG docstring에 남긴다. 백필은 Manager 단위로 (→ [design/08 §7](../design/08_DATA_OPS.md)).
8. **Extract pre-flight 스키마 계약 체크**: 적재 전 소스 딕셔너리를 기대 스키마와 대조 — 불일치 시 fail-fast + 알림. 조용한 드리프트 금지 (→ [design/08 §6](../design/08_DATA_OPS.md)).

## 운영 팁
스택 조작·구축 함정(레지스트리 429, Windows bind 쓰기 불가, exec 세션 DB env, DAG 파싱 지연 등)은
[infra/README.md](infra/README.md) 런북 참조. 그 외:
- DAG이 안 보이면: Airflow safe_mode는 파일에 "airflow"+"dag" 문자열이 둘 다 있어야 파싱한다. (2.x 경험 — 3.x 재검증 필요)
- `docker compose exec`에 `/opt/...` 절대경로를 넘길 때 Windows Git-Bash는 `MSYS_NO_PATHCONV=1` 접두. (3.x 스택에서 재확인)
- 추출/변환 DAG 연계는 Asset 이벤트 기반(→ design/03) — 2.x 시절 `ExternalTaskSensor` logical date 매칭 팁은 폐기.
