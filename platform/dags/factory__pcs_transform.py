"""Manager/Model DAG 팩토리 — 커밋된 dbt manifest.json 파싱 (→ design/03, adr/0002).

이 파일이 airflow dag 를 동적 생성한다:
  model__<이름>   : dbt run(or seed) → dbt test. 모델 단위 재시도·수동 백필 지점.
  manager__pcs_transform : extract Asset 이벤트로 기동, 의존 위상 순으로 Model DAG 트리거,
                           GOLD 성공 후 Publish 말단 (meta.publish_to 선언 기반).

결정론 원칙: 런타임 dbt 컴파일·LLM 금지 — 커밋된 manifest 파일만 읽는다.
실험(sbx) 필터 기준 [Phase 3 확정]: 모델 경로 models/sbx/ (승격 = 폴더 이동이므로 경로가 곧 상태).
복구 UX [Phase 3 확정]: 실패한 Manager run 안에서 실패 trigger 태스크만 clear —
  성공 태스크는 재실행되지 않는다(Airflow clear 의미론이 곧 "성공분 스킵").
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "/opt/airflow")

from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.sdk import DAG, Asset

from common import notifier, publish
from common.assets import MANAGER_TRIGGER_URIS

PROJECT = "pcs_transform"
MANIFEST_PATH = Path("/opt/airflow/transform/manifest.json")
DBT = "/opt/airflow/dbt_venv/bin/dbt"
DEFAULT_ARGS = {"owner": "platform", "retries": 0, "on_failure_callback": notifier.on_failure}

if not MANIFEST_PATH.exists():
    raise RuntimeError(
        "커밋된 manifest 부재: transform/manifest.json — 저작 절차(dbt compile 후 커밋) 확인"
    )

_manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _included(node: dict) -> bool:
    return node["resource_type"] in ("model", "seed") and node["package_name"] == PROJECT


def _is_sbx(node: dict) -> bool:
    return node["path"].replace("\\", "/").startswith("sbx/")


_nodes = {k: v for k, v in _manifest["nodes"].items() if _included(v)}

# 테스트 노드: 교차 모델 의존성의 원천 — relationships 등 generic 테스트가 다른 모델을 참조하면
# 그 모델이 먼저 빌드되어야 한다. Manager 위상에 이 간접 의존을 편입한다.
_tests = {
    k: v for k, v in _manifest["nodes"].items()
    if v["resource_type"] == "test" and v["package_name"] == PROJECT
}


def _attached_tests(node_key: str) -> list:
    """이 모델에 '소속'된 generic 테스트 노드명. dbt 기본 간접 선택(eager)은 모델을
    '건드리는' 타 모델 소속 테스트까지 끌어와 미빌드 참조로 죽는다 — 소속 기준으로 명시 선택.
    교차 모델 참조(relationships 등)의 빌드 순서는 Manager 의 테스트 유발 간선이 보장한다."""
    return sorted(
        t["name"] for t in _tests.values() if t.get("attached_node") == node_key
    )


def _dbt_task(key: str, node: dict) -> str:
    """모델 1개의 run→소속 테스트. test 실패 = Model DAG 실패 = 하류 미트리거 (규칙 3).
    교차 모델 singular 테스트는 여기가 아니라 Manager 말단(Publish 직전)에서 일괄 실행."""
    verb = "seed" if node["resource_type"] == "seed" else "run"
    name = node["name"]
    # 동시 실행 대비 run 별 산출물 격리 (repo 마운트엔 쓰지 않는다)
    env = f"DBT_TARGET_PATH=/tmp/dbt_run/{name} DBT_LOG_PATH=/tmp/dbt_run/{name}"
    cmd = f"cd /opt/airflow/transform && {env} {DBT} {verb} --select {name}"
    tests = _attached_tests(key)
    if tests:
        cmd += f" && {env} {DBT} test --select {' '.join(tests)} --indirect-selection=empty"
    return cmd


# ── Model DAG × N ──────────────────────────────────────────────────────────
for key, node in _nodes.items():
    name = node["name"]
    dag_id = f"model__{name}"
    with DAG(
        dag_id=dag_id,
        schedule=None,                     # 트리거는 Manager(또는 sbx 는 수동)만
        catchup=False,
        max_active_runs=1,
        is_paused_upon_creation=False,
        default_args=DEFAULT_ARGS,
        tags=["model", "sbx"] if _is_sbx(node) else ["model", node["path"].replace("\\", "/").split("/")[0]],
        doc_md=f"dbt {node['resource_type']} `{name}` 의 run→test. "
               f"개별 백필: 이 DAG 를 수동 트리거 (모델은 멱등 전제).",
    ) as model_dag:
        BashOperator(task_id="dbt_build", bash_command=_dbt_task(key, node))
    globals()[dag_id] = model_dag


# ── Manager DAG × 1 ────────────────────────────────────────────────────────
_operational = {k: v for k, v in _nodes.items() if not _is_sbx(v)}  # sbx 는 Manager 제외 (규칙 5)

with DAG(
    dag_id=f"manager__{PROJECT}",
    schedule=[Asset(uri) for uri in MANAGER_TRIGGER_URIS],  # extract 적재 완료 신호로 기동
    catchup=False,
    max_active_runs=1,
    is_paused_upon_creation=False,
    default_args=DEFAULT_ARGS,
    tags=["manager"],
    doc_md="dbt 의존 그래프 위상 순으로 Model DAG 트리거. 실패 시 하류 중단 — "
           "복구는 이 run 에서 실패 태스크 clear(성공분은 자동 스킵). "
           "백필도 Manager 단위로 수행 (→ design/08 §7).",
) as manager_dag:
    triggers = {}
    for key, node in _operational.items():
        triggers[key] = TriggerDagRunOperator(
            task_id=f"trigger__{node['name']}",
            trigger_dag_id=f"model__{node['name']}",
            wait_for_completion=True,
            poke_interval=10,
            allowed_states=["success"],
            failed_states=["failed"],
        )

    # 위상 간선 = 모델 직접 의존 + 테스트 유발 의존 (generic 테스트가 참조하는 타 모델)
    edges = {key: set(node["depends_on"].get("nodes", [])) for key, node in _operational.items()}
    for t in _tests.values():
        attached = t.get("attached_node")
        if attached in edges:
            edges[attached] |= {d for d in t["depends_on"].get("nodes", []) if d != attached}
    for key, parents in edges.items():
        for parent_key in parents:
            if parent_key in triggers:
                triggers[parent_key] >> triggers[key]

    # 교차 모델 정합(singular) 테스트 — 전 모델 빌드 후, Publish 직전 일괄 게이트
    singulars = [t for t in _tests.values() if not t.get("attached_node")]
    singular_gate = None
    if singulars:
        singular_gate = BashOperator(
            task_id="singular_tests",
            bash_command=(
                "cd /opt/airflow/transform && "
                "DBT_TARGET_PATH=/tmp/dbt_run/_singular DBT_LOG_PATH=/tmp/dbt_run/_singular "
                f"{DBT} test --select test_type:singular"
            ),
        )
        gate_parents = {d for t in singulars for d in t["depends_on"].get("nodes", [])}
        for parent_key in gate_parents:
            if parent_key in triggers:
                triggers[parent_key] >> singular_gate

    # Publish 말단 — GOLD 모델의 meta.publish_to 선언 기반 (분석가 셀프서비스 유지)
    for key, node in _operational.items():
        target = (node.get("config", {}).get("meta") or node.get("meta") or {}).get("publish_to")
        if not target:
            continue
        gold_relation = f"{node['schema']}.{node['name']}"
        publish_task = PythonOperator(
            task_id=f"publish__{node['name']}",
            python_callable=publish.publish_full_replace,
            op_kwargs={"gold_relation": gold_relation, "srv_relation": target},
        )
        triggers[key] >> publish_task
        if singular_gate is not None:
            singular_gate >> publish_task

globals()[manager_dag.dag_id] = manager_dag
