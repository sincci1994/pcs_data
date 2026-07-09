# Check: Phase 3 코드 + 첫 데이터 제품 (2026-07-09)

Plan = design/03(DAG 설계)·09(시나리오). **시나리오 전환**: 착수 직전 사용자 결정으로 첫 제품이
Utility 사용량(06, 보류) → **Equipment/Pipe 기준정보(09, PortMaster2)** 로 교체됨 —
CurrentAvgUsage 정의 질문이 계기. 발굴 완료 로직(pipe-scheduler-works)의 이관 케이스라
AS-IS 인테이크 §6 대사 검증까지 Phase 3 에서 함께 완료.

## 결과

| 검증 | 결과 |
|---|---|
| DAG 팩토리 전개 (05 시나리오 4) | ✅ manifest → model__ 7개 + manager__ 1개, import 에러 0 |
| Asset 기동 | ✅ extract 성공 → Asset 이벤트 → Manager 자동 기동 (cron 없음) |
| 위상·차단 | ✅ 실패 지점 하류만 upstream_failed, 독립 브랜치 계속 |
| 복구 UX | ✅ 실패 trigger 만 clear → 성공분 보존·하류 재개 → run success |
| 멱등성 | ✅ extract 3회 후 lnd 47행 (중복 0) |
| dbt test | ✅ 전체 55/55 (relationships FK·accepted_values·singular 정합 포함) |
| **대사 검증** | ✅ **레거시 검증 수치 완전 일치** — quality/reconciliation/equipment_pipe |
| Publish 원자성 | ✅ 0행 주입 시 중단 + srv 이전 상태 보존 |
| OM | ✅ 10테이블 등재, dbt 리니지 lnd→slv→gold, 용어집 PCS.Equipment/Pipe 발행 |
| notifier | ✅ on_failure 콜백 전 DAG 배선 — 로컬은 로그 채널 (API env 주입만 남음) |

## 실패에서 배운 것 (원인 규명 후 수정)

1. **psycopg2 named cursor 는 트랜잭션 필수** — src 접속 autocommit 제거 (`pg.py`).
2. **dbt 간접 선택(eager)의 함정**: `--select 모델` 이 그 모델을 *건드리는* 타 소속 테스트까지 실행 →
   미빌드 참조로 사망. 해법 = manifest `attached_node` 기준 소속 테스트 명시 선택 +
   **테스트 유발 의존성을 Manager 위상에 편입** + singular 는 Publish 직전 일괄 게이트. (→ design/03 확정 기록)
3. Airflow 3 asset-triggered run 은 `logical_date=None` — extract 는 `run_after` 폴백 사용.
4. OM 파이프라인 deploy 직후 trigger 는 DAG 파싱(~30s) 전이면 실패 — 파싱 확인 후 트리거.

## Act
- 확정 결정 전부 design/03 에 반영 완료. wrk pool 격리·manifest CI 게이트는 후속 (design/03 보류 절).
- 원격 전환 선결: EES(pcsdb) 접속 권한 (09 미확정 1) — 확보 시 Oracle 드라이버 분기 구현.
- 조직 enrichment 실연동(SMDM/GPM) 시 seed→extract 교체가 design/07 자동 재정의의 첫 실사례가 된다.
