# PCS 로컬 스택 이미지 — Airflow 3.1.5 + Cosmos + dbt 전용 venv
# 사내 프록시·pip 미러는 .env → compose build.args 로만 주입 (빈값이면 no-op, 런타임 미주입).
FROM apache/airflow:3.1.5

ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ARG PIP_INDEX_URL
ARG PIP_EXTRA_INDEX_URL

RUN pip install --no-cache-dir \
        ${PIP_INDEX_URL:+--index-url $PIP_INDEX_URL} \
        ${PIP_EXTRA_INDEX_URL:+--extra-index-url $PIP_EXTRA_INDEX_URL} \
        astronomer-cosmos==1.15.0

# dbt docs 산출 대역 — named volume 이 이 소유권(airflow)을 물려받는다
RUN mkdir -p /opt/airflow/dbt_docs

# dbt 는 Airflow 의존성과의 충돌 방지를 위해 전용 venv 에 격리 (Cosmos ExecutionMode.LOCAL)
RUN python -m venv /opt/airflow/dbt_venv \
    && /opt/airflow/dbt_venv/bin/pip install --no-cache-dir \
        ${PIP_INDEX_URL:+--index-url $PIP_INDEX_URL} \
        ${PIP_EXTRA_INDEX_URL:+--extra-index-url $PIP_EXTRA_INDEX_URL} \
        dbt-core==1.11.12 dbt-postgres==1.10.2
