# Check: Phase 5 준비 — 프록시 빌드 → 폐쇄망 반입 경로 구축 (2026-07-10)

Plan = [instructions/phase5-airgap-build.md](../../instructions/phase5-airgap-build.md) · 절차 정본 = [platform/infra/ops/README.md](../../../platform/infra/ops/README.md)

## 완료 조건별 결과 (로컬 검증 — 프록시 서버 실행은 별건)

| # | 조건 | 결과 |
|---|---|---|
| 1 | no-op 빌드 (프록시/CA/vendor 전부 빈 상태) | ✅ CA `0 added`, vendor 블록 스킵 — 기존 집 환경 동작 불변 |
| 2 | `import oracledb` (airflow 본체 환경) | ✅ 4.0.1 |
| 3 | 번들러 `list`/`save`→`load` 왕복 | ✅ 이미지 5종, `dist/pcs-images.tgz` 3.2GB + manifest, load 5/5 |
| 4 | 기존 스택 E2E 회귀 (새 이미지로 ingestion 재기동 후 dbt build) | ✅ 54/54 PASS |
| 5 | design/05 체크리스트 7 실구현 링크 교체 | ✅ + 버전 핀 표에 oracledb 4.0.1 추가 |

운영DB(EES Oracle) 접속 스모크는 프록시 서버에서 수행 — **EES 계정 확보 선결** (design/09 §34 블로커).

## 계획과 달랐던 것 (근본 원인 포함)

1. **PyPI 패키지명은 `oracledb`** — `python-oracledb`는 제품명일 뿐 PyPI에 없음(404). 계획서의 `python-oracledb==<핀>`대로 썼으면 빌드 실패. Dockerfile 주석에 명기.
2. **base 는 Debian 12(bookworm)** 확인(`ca-certificates-java deb12u1`) — `libaio1` 이 정답이나 trixie 폴백(`libaio1t64`)은 유지(향후 base 업그레이드 대비).
3. **`.gitattributes` 신설** (`*.sh text eol=lf`) — `core.autocrlf=true` 환경에서 Windows 재체크아웃 시 셸 스크립트 CRLF 오염 방지. 기존 init/*.sh 는 Write 직후라 LF 였을 뿐 보호장치가 없었다.

## Act

- 다음 실행 지점: 프록시 서버에서 runbook ①(빌드+번들)~② 수행. CA `.crt`·Instant Client zip 은 그 서버에서 반입.
- 후속 코드 작업(별건): `extract/snapshot.py` Oracle 분기 — psycopg2 전용인 계약 체크(information_schema)·커서를 oracledb(ALL_TAB_COLUMNS)로 분기 + `init_oracle_client()` 호출 지점.
- SimpleAuthManager → FAB auth 전환 검토는 design/05 체크리스트 2 그대로 잔존.
