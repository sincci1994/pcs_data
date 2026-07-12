# Check: Phase 6 — 운영 유사 로컬 Oracle 왕복 + 사용 가이드 (2026-07-11)

Plan = [instructions/phase6-oracle-roundtrip.md](../../instructions/phase6-oracle-roundtrip.md) · 서빙 경계 정본 = [design/08 §1.1](../../../design/08_DATA_OPS.md)

## 완료 조건별 결과

| # | 조건 | 결과 |
|---|---|---|
| 1 | 기본 경로 회귀 (새 env 없음) | ✅ extract(postgres src)→Asset→Manager→publish(warehouse srv) 전부 success — db.py 경유로도 기존 동작 불변 |
| 2 | 번들 제외 | ✅ `list`에 gvenzl 없음, `COMPOSE_PROFILES=practice-oracle` export 상태에서도 없음 (가드) |
| 3 | Oracle 왕복 | ✅ ALL_TAB_COLUMNS 계약 체크(thin), brz 47행 멱등(2회), Manager 완주, `PCS_SRV` 5종 건수 완전 일치 (94/89/6/47/3) |
| 4 | 소비자 증명 | ✅ `pcs_srv` 단독 EQUIPMENT×PIPE 조인 — 배관 26/38/25 = 대사 기지값, 설비 24/40/27+본체3 = 25/41/28 |
| 5 | 원자성 | ✅ 0행 게이트(서빙 미접촉 중단) + DELETE 후 INSERT 실패 주입(ORA-00904)→rollback으로 94행 보존 |
| 6 | 최종 회귀 (.env 원복) | ✅ postgres 경로 재통과 — publish__stg_* 포함 12태스크 success, `srv.stg_*` 뷰 publish 동작 |

부수 확인: 네거티브 계약 체크(가짜 기대 컬럼 → fail-fast), publish 재실행 멱등, `srv.` 외 접두 가드.

## 계획과 달랐던 것 (근본 원인 포함)

1. **`CREATE TABLE (LIKE <view>)`는 PG16에서 동작** — 우려했던 폴백(information_schema 기반 CREATE) 불필요. oracle 경로는 어차피 information_schema 로 타입맵을 만든다.
2. **compose 프로파일 서비스에 `:?` 필수화 금지** — 보간은 프로파일 비활성이어도 파일 전체에 적용되어 기본 `up`이 깨진다. `${VAR:-}` 빈 기본 + 컨테이너 fail-loud 로 대체 (크리덴셜 폴백 아님).
3. **잠복 버그 수정**: 로더가 `sources.yml`의 `conn:` 선언을 무시하고 `pg.src_conn()` 하드코딩 — db.py 경유로 선언이 실제로 존중된다. `pg.src_conn()` 제거(미사용).
4. gvenzl 이미지 핀 = `23.26.2-slim-faststart` (Docker Hub 태그 조회로 확정). healthy 도달 ~1분(faststart), init 1회 자동.

## Act

- 소비 조회 창구 전환의 실전 적용: 분석가 온보딩 시 "조회는 Oracle(:1521 pcs_srv), 저작은 warehouse(:5433)" 안내 — GUIDE §계보/역할 표 기준.
- window-replace publish 는 대규모 grain 프로덕트 등장 시 구현 (design/08 §3 손잡이 ②).
- 원격 전환 잔여는 조직 이슈 그대로: EES 계정(1순위)·실 서빙 DB 접속값 (design/09 미확정 1·3잔여).
- OM 리니지에 서빙(Oracle) 구간은 미노출 — OM에 Oracle 서비스 등록은 실서빙 확정 후 검토.
