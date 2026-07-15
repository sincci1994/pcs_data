"""dbt docs 생성 DAG — Airflow UI 의 dbt Docs 메뉴(Cosmos 플러그인)가 서빙할 산출물을 만든다.

모델 변경·파이프라인 실행 후 수동 트리거하면 UI 문서(모델 설명·컬럼·계보 그래프)가 갱신된다.
산출 경로 = AIRFLOW__COSMOS__DBT_DOCS_DIR (/opt/airflow/dbt_docs — 컨테이너 로컬,
프로젝트 마운트는 root 소유라 쓰기 불가하므로 분리).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))   # 파서 프로세스 재사용 시 dags 폴더 누락 방어

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

from lib import notifier

with DAG(
    dag_id="dbt_docs",
    schedule=None,                      # 수동 트리거 — 모델 변경 후 갱신
    catchup=False,
    is_paused_upon_creation=False,
    default_args={"owner": "platform", "on_failure_callback": notifier.on_failure},
    tags=["dbt", "docs"],
    doc_md=__doc__,
) as dag:
    BashOperator(
        task_id="generate",
        bash_command=(
            "DBT_TARGET_PATH=/opt/airflow/dbt_docs DBT_LOG_PATH=/tmp/dbt_logs "
            "/opt/airflow/dbt_venv/bin/dbt docs generate "
            "--project-dir /opt/airflow/dbt --profiles-dir /opt/airflow/dbt"
        ),
    )
