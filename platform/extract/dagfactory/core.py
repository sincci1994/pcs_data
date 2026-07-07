"""
경량 DagFactory — YAML 설정 파일을 Airflow DAG 으로 동적 변환.

레퍼런스(coldchainservice_airflow)의 DagBuilder 패턴을 축소·이식한 것.
핵심: operator/python_callable 를 '문자열 경로'로 적고 import_string 으로 동적 로드 →
      configs/*.yaml 만 추가하면 DAG/Task 가 코드 수정 없이 생성된다.

지원 키:
  default_args.start_date     : "YYYY-MM-DD" 문자열 허용
  default_args.retry_delay_sec: 초 → timedelta 변환
  schedule_interval, catchup, description, tags, max_active_runs
  tasks.<name>.operator       : 클래스 경로 (예: airflow.operators.python.PythonOperator)
  tasks.<name>.python_callable: 함수 경로 (예: extract.projects.scada.trace.extract_trace)
  tasks.<name>.success_check_lambda: SqlSensor 성공판정 람다 문자열
  tasks.<name>.dependencies   : 선행 task 이름 리스트
  그 외 키는 operator 생성자 인자로 그대로 전달.
"""
import datetime as dt
import glob
import os

import yaml
from airflow import DAG
from airflow.utils.module_loading import import_string

# operator 생성자 인자가 아닌, 팩토리 전용 메타 키
_META_KEYS = {"operator", "dependencies", "python_callable", "success_check_lambda"}


def _build_default_args(raw: dict) -> dict:
    args = dict(raw or {})
    sd = args.get("start_date")
    if isinstance(sd, str):
        args["start_date"] = dt.datetime.fromisoformat(sd)
    if "retry_delay_sec" in args:
        args["retry_delay"] = dt.timedelta(seconds=args.pop("retry_delay_sec"))
    return args


def build_dag(dag_id: str, cfg: dict) -> DAG:
    dag = DAG(
        dag_id=dag_id,
        default_args=_build_default_args(cfg.get("default_args")),
        schedule_interval=cfg.get("schedule_interval"),
        catchup=cfg.get("catchup", False),
        description=cfg.get("description"),
        max_active_runs=cfg.get("max_active_runs", 1),
        tags=cfg.get("tags", ["dagfactory"]),
    )

    deps: dict[str, list] = {}
    tasks: dict[str, object] = {}

    with dag:
        for tname, tcfg in cfg["tasks"].items():
            tcfg = dict(tcfg)
            op_class = import_string(tcfg["operator"])
            deps[tname] = tcfg.get("dependencies", [])

            kwargs = {k: v for k, v in tcfg.items() if k not in _META_KEYS}
            if "python_callable" in tcfg:
                kwargs["python_callable"] = import_string(tcfg["python_callable"])
            if "success_check_lambda" in tcfg:
                # 로컬 신뢰 설정에 한해 람다 문자열 허용
                kwargs["success"] = eval(tcfg["success_check_lambda"])  # noqa: S307

            tasks[tname] = op_class(task_id=tname, **kwargs)

    for tname, upstreams in deps.items():
        for up in upstreams:
            tasks[up] >> tasks[tname]

    return dag


def load_yaml_dags(globals_dict: dict, configs_dir: str) -> None:
    """configs_dir 하위 모든 *.yaml/*.yml 을 읽어 DAG 으로 등록."""
    patterns = ("**/*.yaml", "**/*.yml")
    for pattern in patterns:
        for path in glob.glob(os.path.join(configs_dir, pattern), recursive=True):
            with open(path, "r", encoding="utf-8") as f:
                doc = yaml.safe_load(f)
            for dag_id, cfg in (doc or {}).items():
                globals_dict[dag_id] = build_dag(dag_id, cfg)
