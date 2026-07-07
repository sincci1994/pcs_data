# certs/ — 사내 사설 CA

사내 루트/중간 CA를 `*.crt`(PEM)로 이 폴더에 두면 이미지 빌드가 시스템 트러스트스토어에 등록한다
(Dockerfile: `COPY certs/` → `update-ca-certificates`, pip 는 `PIP_CERT` 로 이 번들 사용).

- 실파일(`*.crt`)은 gitignore — 환경별 산출물이라 커밋하지 않는다. 집 환경은 비워두면 됨.
- 프록시/pip 미러 값은 최상위 `.env` 에서 설정(→ `.env.example`).
