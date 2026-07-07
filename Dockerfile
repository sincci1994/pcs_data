FROM apache/airflow:2.9.3-python3.11

# 사내 프록시/미러/CA 빌드 인자 — 값은 최상위 .env → docker-compose build.args 로 주입.
# HTTP_PROXY/HTTPS_PROXY/NO_PROXY 는 Docker 예약 ARG → RUN 환경에 자동 주입(apt·pip 자동 경유),
# 이미지 레이어/docker history 에 남지 않는다. 집 환경은 .env 를 비우면 전부 no-op.
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ARG PIP_INDEX_URL
ARG PIP_EXTRA_INDEX_URL

USER root
# 사내 사설 CA 신뢰 등록 후 빌드 도구 설치.
#  - certs/ 를 디렉토리째 COPY → .crt 없는 집 환경도 빈 폴더로 COPY 성공, update-ca-certificates 는 no-op.
COPY certs/ /usr/local/share/ca-certificates/extra/
RUN update-ca-certificates \
    && apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# pip 가 시스템 트러스트스토어(사설 CA 포함)를 쓰게 한다. 공개 CA 도 포함돼 집 환경 PyPI 도 정상.
ENV PIP_CERT=/etc/ssl/certs/ca-certificates.crt

USER airflow

# 1) dbt-oracle 는 Airflow 의존성과 충돌할 수 있으므로 전용 venv 에 격리 설치한다.
#    Cosmos 는 이 venv 의 dbt 실행파일 경로(dbt_executable_path)를 호출한다.
COPY requirements-dbt.txt /requirements-dbt.txt
RUN python -m venv /opt/airflow/dbt_venv \
    && . /opt/airflow/dbt_venv/bin/activate \
    && pip install --no-cache-dir --no-user \
        ${PIP_INDEX_URL:+--index-url $PIP_INDEX_URL} \
        ${PIP_EXTRA_INDEX_URL:+--extra-index-url $PIP_EXTRA_INDEX_URL} \
        -r /requirements-dbt.txt \
    && deactivate

# 2) Airflow 메인 환경 패키지 (미러 미설정 시 플래그 생략 → 기본 PyPI)
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir \
        ${PIP_INDEX_URL:+--index-url $PIP_INDEX_URL} \
        ${PIP_EXTRA_INDEX_URL:+--extra-index-url $PIP_EXTRA_INDEX_URL} \
        -r /requirements.txt

# 3) 모듈 경로 — 목적기반 최상위 패키지(extract / common / transform)를 루트에서 import.
#    폐쇄망 배포 시엔 볼륨 마운트 대신 소스를 이미지에 COPY 하고 동일 PYTHONPATH 를 쓴다.
ENV PYTHONPATH="/opt/airflow:${PYTHONPATH}"

# 4) python-oracledb 드라이버 모드.
#    - 로컬(gvenzl/oracle-free): thin 으로 충분(Instant Client 불필요).
#    - 실타깃 Oracle(버전 상이 → Thick 필수): ORA_PYTHON_DRIVER_TYPE=thick +
#      Instant Client .so 를 이미지에 베이크(폐쇄망은 런타임 다운로드 불가). docs/08_AIRGAP_BUILD.md 참고.
ENV ORA_PYTHON_DRIVER_TYPE=thin
