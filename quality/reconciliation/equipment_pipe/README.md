# 대사 검증 — Equipment/Pipe (PortMaster2 이관)

- 대상: `gold_equipment` / `gold_pipe` — [인테이크 기록](../../../governance/intake/2026-07-09_equipment_pipe_portmaster2.md)
- 기준 스냅샷: 레거시 검증 완료 수치 (외부 저장소 `pipe-scheduler-works/레거시전처리코드/문서/변환규칙.md` §6, 샘플 3설비 47행 입력)
- 실행: [reconcile.sql](reconcile.sql) 머리말 참조 — **모든 쿼리 0행 = PASS**
- 결과 이력:

| 일자 | 입력 | 결과 |
|---|---|---|
| 2026-07-09 | src 목데이터 47행 (검증샘플 3설비) | **PASS** — 5개 쿼리 전부 0행 (equipment 25/41/28, pipe 26/38/25, 타입별 일치, FK 누락 0) |
| 2026-07-09 (명명 재구성 후) | 동일 47행 — gold_*→dim_* 리네임 검증 | **PASS** — 동일 수치 재통과 (리네임 로직 불변 증명) |
