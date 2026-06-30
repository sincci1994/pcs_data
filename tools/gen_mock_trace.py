#!/usr/bin/env python3
"""
설비 센서 trace 목데이터 생성기 (원천 SCADA 모사)

지정한 날짜 하루치를 분 단위(기본 10분 간격)로 SRC_SCADA.TRACE_RAW 에 적재한다.
센서 마스터의 HI/LO_LIMIT 를 기준으로 정상값을 만들고, 일부는 한계 초과(알람)로 생성.

사용 예:
  # 호스트(로컬)에서 직접 실행 (oracledb 설치 필요: pip install oracledb)
  python tools/gen_mock_trace.py --date 2026-06-01

  # 컨테이너 안에서 실행
  docker compose exec airflow-scheduler python /opt/airflow/tools/gen_mock_trace.py --date 2026-06-01
"""
import argparse
import datetime as dt
import os
import random

import oracledb  # thin 모드 (Instant Client 불필요)


def get_conn(args):
    return oracledb.connect(
        user=args.user,
        password=args.password,
        dsn=f"{args.host}:{args.port}/{args.service}",
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True, help="생성 대상 날짜 YYYY-MM-DD")
    p.add_argument("--interval-min", type=int, default=10, help="측정 간격(분)")
    p.add_argument("--alarm-rate", type=float, default=0.03, help="한계 초과 비율")
    p.add_argument("--host", default=os.getenv("ORA_HOST", "localhost"))
    p.add_argument("--port", default=os.getenv("ORA_PORT", "1521"))
    p.add_argument("--service", default=os.getenv("ORA_SERVICE", "FREEPDB1"))
    p.add_argument("--user", default=os.getenv("ORA_USER", "SRC_SCADA"))
    p.add_argument("--password", default=os.getenv("ORA_PASSWORD", "src_scada_pw"))
    args = p.parse_args()

    target_date = dt.datetime.strptime(args.date, "%Y-%m-%d").date()
    # 날짜 기반 시드 → 같은 날짜는 항상 같은 데이터(재현성)
    random.seed(int(target_date.strftime("%Y%m%d")))

    conn = get_conn(args)
    cur = conn.cursor()

    # 센서 마스터 로드
    cur.execute("SELECT SENSOR_ID, EQP_ID, HI_LIMIT, LO_LIMIT FROM SRC_SCADA.SENSOR_MST")
    sensors = cur.fetchall()
    if not sensors:
        raise SystemExit("SENSOR_MST 가 비어있습니다. init DDL 적재를 먼저 확인하세요.")

    # 해당 날짜 기존 데이터 제거(재실행 멱등성)
    start = dt.datetime.combine(target_date, dt.time.min)
    end = start + dt.timedelta(days=1)
    cur.execute(
        "DELETE FROM SRC_SCADA.TRACE_RAW WHERE MEAS_TS >= :1 AND MEAS_TS < :2",
        [start, end],
    )

    rows = []
    step = dt.timedelta(minutes=args.interval_min)
    for sensor_id, eqp_id, hi, lo in sensors:
        hi = float(hi)
        lo = float(lo)
        mid = (hi + lo) / 2.0
        span = hi - lo
        ts = start
        while ts < end:
            r = random.random()
            if r < args.alarm_rate / 2:                 # 상한 초과
                val = hi + abs(random.gauss(0, span * 0.1)) + 0.1
                status = "RUN"
            elif r < args.alarm_rate:                   # 하한 미만
                val = lo - abs(random.gauss(0, span * 0.1)) - 0.1
                status = "RUN"
            elif r < args.alarm_rate + 0.05:            # IDLE(가동 정지) 구간
                val = mid
                status = "IDLE"
            else:                                       # 정상
                val = random.gauss(mid, span * 0.12)
                status = "RUN"
            rows.append((eqp_id, sensor_id, ts, round(val, 3), status))
            ts += step

    cur.executemany(
        "INSERT INTO SRC_SCADA.TRACE_RAW (EQP_ID, SENSOR_ID, MEAS_TS, MEAS_VAL, STATUS_CD) "
        "VALUES (:1, :2, :3, :4, :5)",
        rows,
    )
    conn.commit()
    print(f"[OK] {args.date}: {len(rows)} rows inserted into SRC_SCADA.TRACE_RAW "
          f"({len(sensors)} sensors x {int(24*60/args.interval_min)} pts)")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
