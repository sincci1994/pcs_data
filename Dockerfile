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
COPY requirements-dbt.txt /requirements-dbt.txt
RUN python -m venv /opt/airflow/dbt_venv \
    && . /opt/airflow/dbt_venv/bin/activate \
    && pip install --no-cache-dir --no-user -r /requirements-dbt.txt \
    && deactivate

# 2) Airflow 메인 환경 패키지
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# 3) 모듈 경로 — 목적기반 최상위 패키지(extract / common / transform)를 루트에서 import.
#    폐쇄망 배포 시엔 볼륨 마운트 대신 소스를 이미지에 COPY 하고 동일 PYTHONPATH 를 쓴다.
ENV PYTHONPATH="/opt/airflow:${PYTHONPATH}"

# 4) python-oracledb 드라이버 모드.
#    - 로컬(gvenzl/oracle-free): thin 으로 충분(Instant Client 불필요).
#    - 실타깃 Oracle(버전 상이 → Thick 필수): ORA_PYTHON_DRIVER_TYPE=thick +
#      Instant Client .so 를 이미지에 베이크(폐쇄망은 런타임 다운로드 불가). docs/08_AIRGAP_BUILD.md 참고.
ENV ORA_PYTHON_DRIVER_TYPE=thin
