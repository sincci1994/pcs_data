# PCS 커스텀 ingestion 이미지 — OM 공식 ingestion(1.12.13) + 사설 CA + Oracle thick + dbt venv (→ design/05_INFRA.md)
# dbt 는 Airflow/OM 의존성과의 충돌 방지를 위해 전용 venv 에 격리 설치한다.
# 버전 핀: server/ingestion/postgresql 3태그 동일(1.12.13), dbt-core 1.11.12 / dbt-postgres 1.10.2, oracledb 4.0.1.
FROM docker.getcollate.io/openmetadata/ingestion:1.12.13

# 사내 프록시·pip 미러 — 값은 .env → compose build.args 로만 주입(빈값이면 no-op, 런타임 미주입).
# HTTP(S)_PROXY/NO_PROXY 는 Docker 예약 ARG — RUN 환경에 주입되고 이미지 레이어에 남지 않는다.
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ARG PIP_INDEX_URL
ARG PIP_EXTRA_INDEX_URL

USER root

# 사설 CA 등록 — certs/*.crt 없으면(집/일반망) no-op. pip 설치보다 먼저(SSL 가로채기 프록시 대응).
# PIP_CERT/REQUESTS_CA_BUNDLE 은 공개 CA 도 포함한 시스템 번들이라 일반망 PyPI 도 정상 (→ certs/README.md).
COPY certs/ /usr/local/share/ca-certificates/extra/
RUN update-ca-certificates
ENV PIP_CERT=/etc/ssl/certs/ca-certificates.crt \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# Oracle Instant Client (thick 모드) — vendor/ 에 basiclite zip 있을 때만 설치, 없으면 no-op (→ vendor/README.md).
# 실 EES 는 버전·인증 편차 대비 thick 필수, 폐쇄망은 런타임 다운로드 불가 → 이미지에 베이크.
# apt 는 소문자 http_proxy 만 인식하므로 명시 전달. libaio1t64 는 Debian trixie 폴백.
COPY vendor/ /tmp/vendor/
RUN if ls /tmp/vendor/instantclient-basiclite-*.zip >/dev/null 2>&1; then \
        export http_proxy="$HTTP_PROXY" https_proxy="$HTTPS_PROXY" no_proxy="$NO_PROXY" \
        && apt-get update \
        && { apt-get install -y --no-install-recommends libaio1 unzip \
             || apt-get install -y --no-install-recommends libaio1t64 unzip; } \
        && unzip -q /tmp/vendor/instantclient-basiclite-*.zip -d /opt/oracle \
        && echo /opt/oracle/instantclient* > /etc/ld.so.conf.d/oracle-instantclient.conf \
        && ldconfig \
        && apt-get clean && rm -rf /var/lib/apt/lists/*; \
    fi \
    && rm -rf /tmp/vendor

RUN python -m venv /opt/airflow/dbt_venv \
    && /opt/airflow/dbt_venv/bin/pip install --no-cache-dir \
        ${PIP_INDEX_URL:+--index-url $PIP_INDEX_URL} \
        ${PIP_EXTRA_INDEX_URL:+--extra-index-url $PIP_EXTRA_INDEX_URL} \
        dbt-core==1.11.12 dbt-postgres==1.10.2 \
    && chown -R airflow:0 /opt/airflow/dbt_venv
USER airflow

# oracledb 드라이버(제품명 python-oracledb, PyPI 패키지명은 oracledb) — 추출 로더(extract/snapshot.py)가
# 도는 airflow 본체 환경에 설치 (dbt venv 아님). thick 사용은 코드에서 init_oracle_client() 호출.
RUN pip install --no-cache-dir \
        ${PIP_INDEX_URL:+--index-url $PIP_INDEX_URL} \
        ${PIP_EXTRA_INDEX_URL:+--extra-index-url $PIP_EXTRA_INDEX_URL} \
        oracledb==4.0.1
