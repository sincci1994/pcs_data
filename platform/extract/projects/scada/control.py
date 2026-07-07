"""SCADA 추출 DAG 의 CTL 통제 태스크 (ctl_start / ctl_end).

PythonOperator 가 실행 컨텍스트를 **context 로 주입(run_id / dag 등).
CTL 기록 로직 자체는 common.control.ctl.JobRunLogger 에 있다.
"""
from __future__ import annotations

from common.control.ctl import JobRunLogger

from .scada_base import connector

_LND_TRACE = "PCS_LND.L_SCADA_TRACE"


def ctl_start(**context) -> None:
    """C_JOB_RUN 에 실행 시작 기록."""
    logger = JobRunLogger(connector())
    logger.start(context["run_id"], context["dag"].dag_id, "ctl_start")


def ctl_end(**context) -> None:
    """C_JOB_RUN 에 완료 기록 + LND 적재 건수 집계."""
    c = connector()
    cnt = c.fetch_one(
        f"SELECT COUNT(*) FROM {_LND_TRACE} WHERE LOAD_ID = :1",
        [context["run_id"]],
    )[0]
    JobRunLogger(c).end(context["run_id"], context["dag"].dag_id, "ctl_end", cnt)
