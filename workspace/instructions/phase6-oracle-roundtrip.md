# 지시서 — Phase 6: 운영 유사 로컬 (Oracle 왕복) + 사용법 체득

## 목표
로컬을 운영 위상에 맞춘다: **Oracle이 소스이자 서빙 DB**, warehouse Postgres는 변환 계산
자원. Oracle Free 컨테이너로 소스→변환→서빙 왕복을 로컬에서 실증하고, 이 구조를 쓰는 법
(Agent 지시·계보 보는 법)을 가이드로 남긴다.

## 범위
- `platform/common/db.py`(신규 방언 계층) + `snapshot.py`·`publish.py` 드라이버 분기.
- `platform/infra/` compose practice-oracle 프로파일 + `oracle-init/` + 번들러 가드.
- SLV 2개 모델 `publish_to` 선언 + manifest 재컴파일 (**SLV+GOLD 모두 서빙** — 사용자 결정).
- `design/08` 개정(서빙 대상 SLV 추가, 질의 경계, 규모 손잡이 3개) + design/09 미확정 3 갱신.
- `GUIDE.md` 트랙 0(Agent에게 시키기)·계보 절 + `instructions/TEMPLATE.md` + `ops/render_lineage.py`.
- 범위 밖: watermark 증분 모드, window-replace publish, 실 EES/서빙 접속(조직 이슈).

## 제약
- 드라이버 선택은 env 전용(`PCS_SRC_DRIVER`/`PCS_SRV_DRIVER`) — 새 env 없으면 기존 postgres
  경로 그대로(no-op 안전). 선언·factory는 환경 불변.
- Oracle Free는 **로컬 전용** — 폐쇄망 번들에 절대 미포함 (번들러 가드로 강제).
- 시크릿은 `.env`만, compose에 크리덴셜 기본값 폴백 금지 (→ platform/CLAUDE.md).
- 분석가 셀프서비스 유지: 서빙 추가 = 모델 `meta.publish_to` 한 줄 + manifest.

## 완료 조건
1. 기본 경로(새 env 없음): extract→Manager→publish(warehouse srv)가 기존과 동일하게 success.
2. `ops/airgap_images.sh list`에 gvenzl 이미지 없음 — `COMPOSE_PROFILES` 오염 상태에서도.
3. Oracle 전환 후: ALL_TAB_COLUMNS 계약 체크 통과, brz 47행 멱등, Manager 완주,
   `PCS_SRV`에 서빙 테이블 5종 생성·warehouse와 건수 일치.
4. 소비자 증명: `pcs_srv` 계정 단독 질의로 대사 기지 수치 재현 (Oracle만 필요).
5. 실패 주입 시 rollback으로 서빙 이전 상태 보존 + 0행 게이트 동작.
6. `.env` 원복 후 1번 재통과 (전 변경의 no-op 안전).
