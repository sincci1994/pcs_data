-- 일상 헬스 점검 (PCS_CTL) — quality/runbook.md 의 ① 절차
-- 실행 예: docker compose exec -T oracle bash -lc \
--   "sqlplus -s system/oracle@localhost:1521/FREEPDB1 @/dev/stdin" < quality/queries/health_check.sql

-- 1) 최신성/끊김: STALE 이 있으면 조치
SELECT * FROM PCS_CTL.V_FRESHNESS ORDER BY STATUS DESC, HOURS_SINCE DESC;

-- 2) 병목: 평균 소요시간 상위 10
SELECT * FROM (
  SELECT * FROM PCS_CTL.V_BOTTLENECK ORDER BY AVG_SEC DESC
) WHERE ROWNUM <= 10;

-- 3) 건수 이상: EMPTY / DROP 만
SELECT * FROM PCS_CTL.V_VOLUME_ANOMALY WHERE FLAG <> 'OK' ORDER BY START_TS DESC;

-- 4) DQ 실패: 최근 테스트 실패 (PASS_YN='N')
SELECT * FROM (
  SELECT * FROM PCS_CTL.A_DQ_RESULT WHERE PASS_YN = 'N' ORDER BY CHECKED_AT DESC
) WHERE ROWNUM <= 20;
