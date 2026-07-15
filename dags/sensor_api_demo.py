"""API 데이터 감지 sensor 예시 — deferrable HttpSensor.

데모는 Airflow 자신의 health API 를 감지 대상으로 쓴다(외부망·추가 컨테이너 불필요).
실전: http_conn_id/endpoint 를 사내 데이터 수신 API 로, response_check 를
"신규 데이터 존재" 판정으로 교체하고 process 자리에 적재 태스크를 잇는다.
연결은 compose env 한 줄: AIRFLOW_CONN_DEMO_API=http://localhost:8080
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))   # 파서 프로세스 재사용 시 dags 폴더 누락 방어

from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG

from lib import notifier

with DAG(
    dag_id="sensor_api_demo",
    schedule=None,                      # 수동 트리거 데모
    catchup=False,
    default_args={"owner": "platform", "on_failure_callback": notifier.on_failure},
    tags=["sensor", "demo"],
    doc_md=__doc__,
) as dag:
    wait_for_api = HttpSensor(
        task_id="wait_for_api",
        http_conn_id="demo_api",
        endpoint="/api/v2/monitor/health",
        response_check=lambda r: r.json().get("scheduler", {}).get("status") == "healthy",
        deferrable=True,                # 대기 중 워커 슬롯 점유 없음 (triggerer 가 폴링)
        poke_interval=10,
        timeout=120,
    )
    process = PythonOperator(
        task_id="process",
        python_callable=lambda: print("데이터 감지됨 — 실전에선 여기서 적재/트리거"),
    )
    wait_for_api >> process
