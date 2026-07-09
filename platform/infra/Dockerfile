# PCS 커스텀 ingestion 이미지 — OM 공식 ingestion(1.12.13) + dbt venv (→ design/05_INFRA.md)
# dbt 는 Airflow/OM 의존성과의 충돌 방지를 위해 전용 venv 에 격리 설치한다.
# 버전 핀: server/ingestion/postgresql 3태그 동일(1.12.13), dbt-core 1.11.12 / dbt-postgres 1.10.2.
FROM docker.getcollate.io/openmetadata/ingestion:1.12.13

# 사내 프록시·pip 미러 — 값은 .env → compose build.args 로만 주입(빈값이면 no-op, 런타임 미주입).
# 사설 CA 등록은 원격 이식 시 처리 — 방식은 git 히스토리(8716803) 참조.
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ARG PIP_INDEX_URL
ARG PIP_EXTRA_INDEX_URL

USER root
RUN python -m venv /opt/airflow/dbt_venv \
    && /opt/airflow/dbt_venv/bin/pip install --no-cache-dir \
        ${PIP_INDEX_URL:+--index-url $PIP_INDEX_URL} \
        ${PIP_EXTRA_INDEX_URL:+--extra-index-url $PIP_EXTRA_INDEX_URL} \
        dbt-core==1.11.12 dbt-postgres==1.10.2 \
    && chown -R airflow:0 /opt/airflow/dbt_venv
USER airflow
