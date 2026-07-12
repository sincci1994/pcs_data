# infra — 로컬 검증 스택 (Phase 2)

설계·버전 핀·원격 이식은 [design/05_INFRA.md](../../design/05_INFRA.md). 여기는 조작 절차만.
폐쇄망 반입(프록시 빌드 → tar → cloud load)은 [ops/README.md](ops/README.md).

## 기동

```bash
cp .env.example .env   # 비밀번호 채우기 (커밋 금지)
docker compose up -d --build
```

| 접점 | 주소 | 계정 |
|---|---|---|
| Airflow (ingestion 내장, 3.1.5) | http://localhost:8080 | admin / admin (SimpleAuthManager — 로컬 전용) |
| OpenMetadata 1.12.13 | http://localhost:8585 | admin@open-metadata.org / admin |
| warehouse Postgres 16 | localhost:5433 / `pcs_wh` | .env 참조 |

정상 상태: `docker compose ps -a` 에서 `execute_migrate_all` 만 Exited(0), 나머지 5개 Up(healthy).

## dbt 실행 (컨테이너 안)

```bash
MSYS_NO_PATHCONV=1 docker compose exec ingestion bash -c \
  "cd /opt/airflow/transform && /opt/airflow/dbt_venv/bin/dbt build"
```

산출물은 `DBT_TARGET_PATH`(컨테이너 로컬)에 쓰인다 — repo 마운트는 컨테이너에서 읽기 전제.

커밋용 manifest 갱신 (모델 추가·수정 시 — → design/03 규칙 1):
```bash
MSYS_NO_PATHCONV=1 docker exec openmetadata_ingestion bash -c \
  "cd /opt/airflow/transform && DBT_TARGET_PATH=/tmp/dbt_manifest DBT_LOG_PATH=/tmp/dbt_manifest /opt/airflow/dbt_venv/bin/dbt parse"
docker cp openmetadata_ingestion:/tmp/dbt_manifest/manifest.json ../../transform/manifest.json
```

## 로컬 목소스·ctl 적용 (기존 볼륨 — 최초 볼륨 생성 시엔 init/ 이 자동 수행)

```bash
docker exec -i pcs_warehouse psql -U pcs_admin -d pcs_wh < mock/seed_src_portmaster2.sql   # PortMaster2 47행
# ctl·srv 스키마: init/02_ctl_srv.sh 를 env 주입해 실행 (README 이력 참조)
```

## Oracle 실습 프로파일 (로컬 전용 — 오라클 왕복: Oracle 소스 → 변환 → Oracle 서빙)

운영 위상(소스도 서빙도 Oracle, warehouse 는 변환 계산 자원)을 로컬에서 재현한다 (→ design/08).

```bash
# .env 에 PCS_ORACLE_ADMIN_PASSWORD / PCS_ORA_SRC_PASSWORD / PCS_ORA_SRV_PASSWORD 채운 뒤
docker compose --profile practice-oracle up -d oracle   # 첫 부팅: init(사용자·47행 시드) 수 분
# 스모크: 47 출력 확인
docker exec pcs_oracle bash -c "sqlplus -s src/\$PCS_ORA_SRC_PASSWORD@localhost/FREEPDB1 <<< 'SELECT COUNT(*) FROM pcs_sq_port_mst_2nd;'"
```

전환: `.env` 에서 `PCS_SRC_DRIVER=oracle PCS_SRC_HOST=oracle PCS_SRC_PORT=1521 PCS_SRC_DB=FREEPDB1
PCS_SRC_USER=src PCS_SRC_PASSWORD=<PCS_ORA_SRC_PASSWORD 값>` + `PCS_SRV_DRIVER=oracle ...USER=pcs_srv`
→ `docker compose up -d ingestion` (env 반영 재생성). 원복은 값 되돌리고 같은 명령.

- Oracle Free 메모리 ~1.5–2.5GB 추가 — Docker Desktop 8GB 이상 권장.
- **폐쇄망 번들 반입 금지**: `./ops/airgap_images.sh list` 에 gvenzl 이미지가 보이면 실패로 간주 (가드가 COMPOSE_PROFILES 를 무효화한다).

## 구축 중 확인된 함정 (재발 방지)

1. **docker.getcollate.io 429**: compose 가 이미지들을 동시 pull 하면 rate limit. → `docker pull` 로 3개 OM 이미지를 순차 pull 후 `up`.
2. **Windows bind mount 는 컨테이너에서 root:755** — airflow(50000)가 마운트 루트에 쓰기 불가. 쓰기가 필요한 경로는 named volume 또는 컨테이너 로컬로: dags 루트는 named volume(OM 이 인제스천 DAG 를 씀), repo DAG 는 `/opt/airflow/dags/repo` 중첩 bind, dbt 산출물은 `DBT_TARGET_PATH`/`DBT_LOG_PATH`.
3. **`docker exec` 로 airflow CLI 쓸 때**: 초기화 체인이 DB 접속 env 를 프로세스에만 export 하므로 exec 세션은 sqlite 폴백("please run airflow db migrate" 오탐). → `-e AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow_user:airflow_pass@postgresql:5432/airflow_db` 명시.
4. **OM 파이프라인 deploy 직후 trigger 실패**: DAG 파일 생성 후 Airflow 파싱까지 ~30s 필요. 파싱 확인 후 트리거.
5. **舊 스택 잔재**: 재구축 전 컨테이너·네트워크(subnet 172.16.240.0/24)가 남아 있으면 network 생성 충돌. 舊 컨테이너·네트워크 제거 (볼륨은 별도 판단).
6. **`airflow dags trigger` 표 출력은 dag_id 를 잘라낸다** — 출력 grep 으로 성공 판정하는 재시도 루프를 짜면 영원히 재트리거된다(실측: 15초마다 190회). 성공 판정은 **exit code** 또는 `-o json` 으로. (extract 는 멱등이라 데이터 피해는 없었다 — brz 47행 유지.)

## 검증 이력

2026-07-09 design/05 시나리오 1·2·3·5·6 통과 (4=DAG 팩토리는 Phase 3 코드 필요) — 상세: [workspace/pdca/phase2-infra/](../../workspace/pdca/phase2-infra/check.md)
