"""extract DAG 팩토리 — 선언(sources.yml) 파싱으로 airflow dag 자동 생성 (→ design/03·10).

소스 블록 1개 = extract__<이름> DAG 1개. 완료 시 target 기반 Asset 이벤트 발행 →
manager__pcs_transform 이 구독(자동 기동). 신규 소스는 YAML 블록 추가로 끝 — GUIDE.md 트랙 1.
backfill: snapshot 모드는 과거 날짜 재실행 = 현재 스냅샷 재적재와 동일 (delete+insert 멱등) —
         catchup 없음, 필요 시 최신 run 만 clear.
"""
import sys

sys.path.insert(0, "/opt/airflow")

from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG, Asset

from common import notifier
from extract.config import asset_uri, load_sources


def _make_loader(source_name: str, src: dict):
    def _load(dag_run=None, dag=None, run_id=None, **_):
        if src["mode"] != "snapshot":
            raise NotImplementedError(
                f"mode={src['mode']!r} 미구현 — watermark(증분+lookback)는 센서 시나리오 재개 시 (design/06)"
            )
        from extract import snapshot
        return snapshot.load(
            source_name, src, dag.dag_id, dag_run.logical_date or dag_run.run_after, run_id
        )
    return _load


for _name, _src in load_sources().items():
    _dag_id = f"extract__{_name}"
    with DAG(
        dag_id=_dag_id,
        schedule=_src["schedule"],          # Asia/Seoul (compose 기본 TZ)
        catchup=False,
        max_active_runs=1,
        is_paused_upon_creation=False,
        default_args={"owner": "platform", "retries": 1, "on_failure_callback": notifier.on_failure},
        tags=["extract", _name],
        doc_md=f"`{_src['table']}` → `{_src['target']}` {_src['mode']} 적재 "
               f"(선언: extract/sources.yml [{_name}]). " + (__doc__ or ""),
    ) as _dag:
        PythonOperator(
            task_id="load",
            python_callable=_make_loader(_name, _src),
            outlets=[Asset(asset_uri(_src["target"]))],
        )
    globals()[_dag_id] = _dag
