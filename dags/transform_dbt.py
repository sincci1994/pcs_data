"""dbt 변환 DAG — Cosmos 가 dbt 프로젝트(/opt/airflow/dbt)를 파싱해 모델·테스트 태스크를 자동 생성.

- 기동: cron 이 아니라 extract DAG 가 발행하는 Asset 이벤트 구독 (데이터 도착 = 변환 시작).
- 그래프: 모델 간 의존은 SQL 의 ref()/source() 선언 하나에서 나온다 — 별도 배선 없음.
- 테스트: TestBehavior.AFTER_EACH(기본) — 모델 run 직후 소속 테스트, 실패 시 하류 차단.
- 계보: dbt docs generate 산출물이 그대로 리니지 문서 (→ README).
"""
from airflow.sdk import Asset
from cosmos import DbtDag, ExecutionConfig, ProfileConfig, ProjectConfig, RenderConfig
from cosmos.constants import LoadMode

from lib import notifier
from lib.config import asset_uri, load_sources

DBT_ROOT = "/opt/airflow/dbt"
DBT_BIN = "/opt/airflow/dbt_venv/bin/dbt"

dbt_pcs_transform = DbtDag(
    dag_id="dbt_pcs_transform",
    schedule=[Asset(asset_uri(s["target"])) for s in load_sources().values()],
    catchup=False,
    max_active_runs=1,
    default_args={"owner": "platform", "retries": 1, "on_failure_callback": notifier.on_failure},
    tags=["dbt", "transform"],
    project_config=ProjectConfig(DBT_ROOT),
    profile_config=ProfileConfig(
        profile_name="pcs_warehouse",
        target_name="dev",
        profiles_yml_filepath=f"{DBT_ROOT}/profiles.yml",   # env_var 기반 — .env 만 채우면 됨
    ),
    execution_config=ExecutionConfig(dbt_executable_path=DBT_BIN),
    render_config=RenderConfig(
        load_method=LoadMode.DBT_LS,        # 파싱 느려지면 DBT_MANIFEST 로 후퇴 (manifest 커밋 필요)
        dbt_executable_path=DBT_BIN,
    ),
)
