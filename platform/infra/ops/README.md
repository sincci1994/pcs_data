# `ops/` — 운영 스크립트

## `airgap_images.sh` — 폐쇄망 이미지 반입 (레지스트리 없음)

프록시 서버에서 빌드/pull 한 이미지를 `docker save` 타볼로 묶어, 파일로 폐쇄망 타겟에 옮겨 `docker load` 한다. `.env` 의 `COMPOSE_FILE` 이 OM 을 병합하므로 코어(빌드)·OM(pull) **6종이 한 번에** 번들된다.

| 이미지 | 출처 |
|---|---|
| `pcs-airflow-practice:latest` | 빌드 |
| `postgres:13` | pull |
| `openmetadata/db:1.13.1` · `elasticsearch:9.3.0` · `openmetadata/server:1.13.1` · `openmetadata/ingestion:1.13.1` | pull |

```bash
# ① 프록시 서버 (인터넷/미러 접근 가능)
platform/infra/ops/airgap_images.sh save      # → dist/pcs-images.tgz (+ manifest.txt)

# ② 전송
scp dist/pcs-images.tgz  <target>:/opt/pcs/dist/

# ③ 타겟 (폐쇄망) — 레포도 함께 반입돼 있어야 함
platform/infra/ops/airgap_images.sh load      # docker load
cp .env.example .env                           # 외부 DB 접속값·OM JWT 채우기
docker compose up -d                           # ★ --build 금지 (로드된 이미지 사용)
```

`list` 서브커맨드는 반입 대상 목록만 출력한다(검증용).

### 주의
- **아키텍처 일치**: 프록시 빌드 서버 == 타겟(대개 `linux/amd64`). 다르면 빌드/pull 에 `--platform linux/amd64`.
- **타겟은 빌드/네트워크 없음**: 로드된 이미지가 이미 있으므로 `docker compose up -d`. `--build`·`--pull always` 를 붙이면 폐쇄망에서 실패.
- **OM 병합 전제**: `.env` 의 `COMPOSE_FILE` 이 코어+OM 을 병합한다(구버전 Compose 도 지원). 이게 없으면 이 스크립트는 코어 이미지만 잡는다.
- **구버전 Compose 호환**: 빌드 프록시 서버가 Compose v2.5 라 신형 전용 플래그(`config --images`·`pull --ignore-buildable`)를 안 쓴다 — config 파싱 + `docker pull` 로 동작. 타겟(v2.29.1)도 동일 동작.
- **OM 로드 후 1회 셋업**: 볼륨은 빈 상태로 시작 → JWT 재발급·`oracle_ingest.yaml`·도메인 스크립트 재수행 필요. → [openmetadata/README](../openmetadata/README.md)
- **Oracle Thick 클라이언트**는 이미지 빌드 시 베이크(별개). → [design/08](../../../design/08_AIRGAP_BUILD.md)

↑ [최상위 README](../../../README.md)
