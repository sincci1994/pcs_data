# 08. 폐쇄망(air-gap) 빌드 전략

배포 현실: **폐쇄망 + 프록시 빌드 + 레포 통째 반입**. 이에 따라 패키징/의존성 전략이 결정된다.

## 서드파티 의존성
- `requirements.txt` / `requirements-dbt.txt` **완전 핀**(가능하면 해시 고정, `pip install --require-hashes`).
- Docker 빌드: `PIP_INDEX_URL`/`PIP_EXTRA_INDEX_URL`(사내 Nexus/Artifactory 미러) + `HTTP(S)_PROXY` 빌드 인자.
- **프록시·미러·사설 CA 는 최상위 `.env` + `certs/` 로 관리** → docker-compose `build.args` 로 이미지에 주입(빌드 시점 한정, 빈값이면 no-op). 사설 CA `.crt` 는 `certs/` 에 두면 빌드가 트러스트스토어 등록. → [.env.example](../.env.example) · [certs/README.md](../certs/README.md)
- dbt 패키지 허브 접근 불가 가정 → `packages.yml` 의존성은 벤더링하거나 회피.

## 첫party 코드
- **패키징/휠 불필요.** 소스를 이미지에 COPY(또는 마운트) + `PYTHONPATH=/opt/airflow`.
- 빌드 스텝 0 → 폐쇄망에서 실패 지점 최소. 근거: [ADR 0003](adr/0003-airgap-packaging.md).

## Oracle Thick 모드
- 실타깃 Oracle 은 버전 상이로 **Thick 필수**. Instant Client `.so` 를 이미지에 **베이크**(런타임 다운로드 불가).
- `ORA_PYTHON_DRIVER_TYPE=thick`, `OracleConnector.from_settings(driver_mode="thick", lib_dir=...)`.

## 컨테이너 이미지
- airflow·oracle·marquez·openmetadata 이미지는 사내 레지스트리 미러 경유로 pull.
