FROM apache/airflow:2.9.3-python3.11

USER root
# dbt/oracledb 빌드에 필요한 도구
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# 1) dbt-oracle 는 Airflow 의존성과 충돌할 수 있으므로 전용 venv 에 격리 설치한다.
#    Cosmos 는 이 venv 의 dbt 실행파일 경로(dbt_executable_path)를 호출한다.
RUN python -m venv /opt/airflow/dbt_venv \
    && . /opt/airflow/dbt_venv/bin/activate \
    && pip install --no-cache-dir --no-user "dbt-oracle==1.8.4" "dbt-core>=1.8,<1.9" \
    && deactivate

# 2) Airflow 메인 환경 패키지
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# 3) 모듈 경로 (common, dags 하위 패키지 import 가능하게)
ENV PYTHONPATH="/opt/airflow:/opt/airflow/common:/opt/airflow/dags:${PYTHONPATH}"

# 4) python-oracledb 를 thin 모드로 강제 (dbt-oracle / oracledb 공통)
ENV ORA_PYTHON_DRIVER_TYPE=thin
