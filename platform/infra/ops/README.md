# ops/ — 폐쇄망 반입 런북 (프록시 빌드 → tar → cloud 서버 load)

프록시 연결된 사내 서버에서 이미지를 빌드/pull 해 `docker save` 타볼로 묶고, 파일로 폐쇄망
cloud 서버(pcs_data)에 옮겨 `docker load` 한다. 이미지 목록은 `docker compose config --images` 로
동적 도출 — compose 가 정본이므로 목록을 여기 중복 기재하지 않는다(`./ops/airgap_images.sh list` 로 확인).

## ① 프록시 서버 — 빌드 + 번들

1. **사전**: 아키텍처가 cloud 서버와 일치하는지 확인(대개 `linux/amd64` — 다르면 build/pull 에 `--platform linux/amd64`).
   Docker Engine + Compose v2, 리포 clone.
2. **준비** (`platform/infra/` 에서):
   - `cp .env.example .env` → 프록시·PIP 미러·시크릿 기입 ("사내 빌드 환경" 절).
   - 사설 CA `*.crt` → `certs/` (→ [certs/README.md](../certs/README.md)).
   - Instant Client basiclite zip → `vendor/` (→ [vendor/README.md](../vendor/README.md)).
3. **빌드 + 번들**:
   ```bash
   ./ops/airgap_images.sh save        # build → 순차 pull → dist/pcs-images.tgz (+ manifest.txt)
   ```
4. **검증 (수용 기준: 운영DB 연결까지)**:
   ```bash
   docker compose up -d               # execute_migrate_all Exited(0), 나머지 healthy (→ infra/README)
   # 운영DB(EES Oracle) 접속 스모크 테스트 — EES 계정 확보 선결 (design/09 §34)
   docker compose exec ingestion python -c "
   import oracledb
   oracledb.init_oracle_client()      # thick — Instant Client 베이크 확인 겸용
   with oracledb.connect(user='<EES_USER>', password='<EES_PW>', dsn='<host>:<port>/<service>') as c:
       print(c.cursor().execute('SELECT 1 FROM DUAL').fetchone())
   "
   ```
   pip 미러/사설 CA 동작은 빌드 성공 자체가 검증(dbt venv·oracledb 가 미러 경유 설치됨).

## ② 전송

```bash
scp dist/pcs-images.tgz <cloud>:/opt/pcs/platform/infra/dist/
```
리포도 함께 반입돼 있어야 한다 — cloud 서버도 clone (배포 동기화는 design/05 체크리스트 8).

## ③ cloud 서버 (폐쇄망) — load + 기동

```bash
./ops/airgap_images.sh load
cp .env.example .env                  # 비밀번호 전면 교체 + 실 EES 접속값 (PCS_SRC_*)
sudo chown -R 50000:0 ../../platform/dags ../../transform   # 리눅스 bind mount (design/05 체크리스트 3)
docker compose up -d                  # ★ --build/--pull 금지 — 로드된 이미지 사용
```

## 주의

- **타겟은 빌드/네트워크 없음**: `--build`·`--pull always` 를 붙이면 폐쇄망에서 실패.
- **이미지 태그 불변 전제**: save 는 로컬에 이미 있는 태그는 pull 을 생략한다 — 버전을 올리면 태그 핀을 바꿔라(latest 금지).
- **볼륨은 빈 상태로 시작**: OM/Airflow 초기화는 공식 entrypoint 체인이 수행. `vm.max_map_count`·포트 노출 차단 등 나머지는 [design/05 체크리스트](../../../design/05_INFRA.md) 준수.

↑ [infra README](../README.md) · [design/05_INFRA.md](../../../design/05_INFRA.md)
