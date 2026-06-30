"""
변환 DAG (Python) — Sensor 게이트 + Cosmos DbtTaskGroup.

  wait_for_extract (ExternalTaskSensor)  ← 추출 DAG 완료(같은 logical date) 대기
        ↓
  wait_lnd_ready   (SqlSensor)           ← PCS_LND 에 데이터 도착 확인 (시간이 아닌 '데이터 기반' 트리거)
        ↓
  dbt_pcs          (DbtTaskGroup)        ← dbt 모델/seed/test 가 ref() 의존성대로 Task 자동 생성
                                            (.sql 추가 → Task 자동 등장, 병렬 가지는 동시 실행)
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.common.sql.sensors.sql import SqlSensor
from airflow.sensors.external_task import ExternalTaskSensor
from cosmos import (
    DbtTaskGroup,
    ExecutionConfig,
    ProfileConfig,
    ProjectConfig,
    RenderConfig,
)
from cosmos.constants import TestBehavior

DBT_PROJECT_DIR = "/opt/airflow/transform/dbt"
DBT_EXECUTABLE = "/opt/airflow/dbt_venv/bin/dbt"

profile_config = ProfileConfig(
    profile_name="pcs_oracle",
    target_name="dev",
    profiles_yml_filepath=f"{DBT_PROJECT_DIR}/profiles.yml",
)
project_config = ProjectConfig(DBT_PROJECT_DIR)
execution_config = ExecutionConfig(dbt_executable_path=DBT_EXECUTABLE)

with DAG(
    dag_id="sensor_daily_transform",
    schedule="@daily",                # 추출 DAG 과 동일 → ExternalTaskSensor 가 같은 logical date 매칭
    start_date=datetime(2026, 6, 1),
    catchup=False,
    tags=["transform", "dbt", "cosmos"],
    default_args={"retries": 1, "retry_delay": timedelta(minutes=2)},
) as dag:

    wait_for_extract = ExternalTaskSensor(
        task_id="wait_for_extract",
        external_dag_id="scada_extract_daily",
        external_task_id="ctl_end",
        allowed_states=["success"],
        failed_states=["failed"],
        mode="reschedule",            # 슬롯 점유 방지
        poke_interval=30,
        timeout=60 * 30,
    )

    # SqlSensor.success 는 '첫 행 첫 셀'을 인자로 받는다 → COUNT(*) > 0 이면 데이터 도착으로 판정
    wait_lnd_ready = SqlSensor(
        task_id="wait_lnd_ready",
        conn_id="oracle_pcs",
        sql="SELECT COUNT(*) FROM PCS_LND.L_SCADA_TRACE",
        success=lambda c: c is not None and int(c) > 0,
        mode="reschedule",
        poke_interval=30,
        timeout=60 * 10,
    )

    dbt_pcs = DbtTaskGroup(
        group_id="dbt_pcs",
        project_config=project_config,
        profile_config=profile_config,
        execution_config=execution_config,
        render_config=RenderConfig(
            emit_datasets=False,
            # relationships 테스트가 모델 빌드 순서보다 먼저 도는 문제 회피:
            # 모든 모델 빌드 후 dbt test 일괄 실행
            test_behavior=TestBehavior.AFTER_ALL,
        ),
        operator_args={"install_deps": False},
        default_args={"retries": 1},
    )

    wait_for_extract >> wait_lnd_ready >> dbt_pcs
