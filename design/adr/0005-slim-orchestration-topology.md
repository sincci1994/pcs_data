# ADR 0005 — 오케스트레이션 서버 슬림 토폴로지 (외부 DB + Marquez 제거)

- 상태: 채택
- 날짜: 2026-07-07

## 맥락
레포 목적이 "집 연습용 end-to-end"에서 **운영 오케스트레이션 서버**로 전환. 데이터 DB(소스 Oracle·웨어하우스 Postgres)는 별도 DB 서버에 이미 존재한다. 사내 빌드 테스트에서 컨테이너 46개가 관측돼 구성 재검토 — 조사 결과 이 레포의 정의는 최대 13개(코어 8 + OM 5)였고, 초과분은 호스트에 쌓인 잔여물(고아/중지 컨테이너·타 프로젝트)이었다. 이를 계기로 서버 역할에 맞게 스택을 슬림화한다.

## 결정
1. **코어 compose = 4서비스**: `postgres`(Airflow 메타DB, 로컬 유지 — 인프라성 DB라 자급자족) + `airflow-init`(1회성)·`airflow-webserver`·`airflow-scheduler`. 실행 중 3개.
2. **데이터 DB 컨테이너 제거**: 소스 Oracle·웨어하우스 Postgres 는 컨테이너로 띄우지 않는다. 접속은 `.env`(`PCS_ORACLE_*`, `PCS_WH_*`) → `AIRFLOW_CONN_ORACLE_PCS` / `AIRFLOW_CONN_POSTGRES_WH` 로만.
3. **Marquez 스택(3컨테이너) 제거 + OpenLineage 전역 비활성**(`AIRFLOW__OPENLINEAGE__DISABLED=true`). 관측 역할 재배치:
   - 테이블/컬럼 계보 → OpenMetadata dbt ingestion
   - 파이프라인 실행 상태 → Airflow UI (+ 필요 시 OM Airflow 커넥터)
   - 병목·신선도·볼륨 → CTL 헬스뷰(`V_FRESHNESS`/`V_BOTTLENECK`/`V_VOLUME_ANOMALY`)
4. **OpenMetadata 스택(5서비스)은 `.env` 의 `COMPOSE_FILE` 로 루트에 병합** — 별도 기동이 아니라 `docker compose up -d --build` 한 번에 코어(빌드)와 함께 준비·기동된다. 근거: 폐쇄망 반입이 단일 명령 + 단일 이미지 번들(`platform/infra/ops/airgap_images.sh`)로 끝난다. `include:` 대신 `COMPOSE_FILE` 병합을 쓰는 이유는 구버전 Compose(<v2.20, `include` 미지원) 호환. (OM 파일 자체는 그대로 — standalone 기동도 가능.)
5. **로컬 Oracle 제거**: 개발 환경도 외부 Oracle(`.env` `PCS_ORACLE_*`)에 접속한다. dev 오버레이 없이 단일 `up` 경로. SCADA 샘플 원천 DDL·목데이터(`platform/infra/init`·`dev/tools`)는 어떤 compose 에도 배선되지 않는 참조물로만 잔존 — design/09 정착 시 폴더째 삭제.

## 근거
- Marquez 가 주던 것 중 이 프로젝트가 실제로 쓰는 것(계보 탐색·병목 확인)은 OM + CTL 뷰 + Airflow UI 로 전부 대체된다. 유일한 손실은 OpenLineage 이벤트 단위의 런 계보인데, 현 운영 요구에 없다.
- 관측 백엔드 2개(Marquez/OM)는 "동일한 내용을 두 곳에서 관리"하는 중복 — 정의 표준화라는 레포 목적과 상충.
- 컨테이너 -4개(oracle, marquez×3), 이미지 -3종 → 폐쇄망 반입 아티팩트와 장애 표면 축소(→ 08_AIRGAP_BUILD).

## 결과/주의
- 재도입 경로: 런 단위 계보가 필요해지면 marquez 3서비스 + `AIRFLOW__OPENLINEAGE__TRANSPORT` env 복원이면 끝(openlineage provider 핀은 requirements.txt 에 유지 중).
- 운영 기동에는 `.env` 의 외부 DB 접속값이 필수 — 비면 커넥션 사용 시점에 실패한다(파싱은 통과).
- 컨테이너 개수 기대값(단일 프로젝트, COMPOSE_FILE 병합): 실행 7(코어 3 + OM 4) + exited 2(airflow-init·execute-migrate-all). 이보다 많으면 레포 밖 잔여물 — 진단 명령은 README "컨테이너 구성" 절.
