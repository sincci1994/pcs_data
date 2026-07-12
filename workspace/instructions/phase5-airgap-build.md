# 지시서 — Phase 5: 프록시 서버 빌드 → 폐쇄망 반입 준비

## 목표
프록시 연결된 사내 서버에서 이미지를 빌드하고 `.tar`로 말아 폐쇄망 cloud 서버(pcs_data)로
반입하는 경로를 리포에 갖춘다. 수용 기준: **프록시 서버에서 빌드된 스택이 운영DB(EES Oracle)와
연결되면 설정 완료**로 본다.

## 범위
- 사설 CA 재이식 (`certs/` → 트러스트스토어, 히스토리 8716803 방식 승계).
- Oracle **thick** 준비: oracledb 드라이버 베이크 + Instant Client `vendor/` 반입 시 설치.
- 이미지 번들러 (`ops/airgap_images.sh` — 히스토리 352edb3 재이식, 순차 pull로 429 회피).
- 프록시 빌드 → 전송 → load 런북 (`platform/infra/ops/README.md`).

## 제약
- 집/일반망 빌드는 전부 no-op — certs/vendor/프록시 비워두면 기존과 동일하게 동작해야 한다.
- CA·Instant Client 실파일은 환경별 반입물 — 커밋 금지(gitignore).
- 타겟(폐쇄망)에서는 build/pull 금지 — 로드된 이미지 태그만 사용.

## 완료 조건
1. no-op 로컬 빌드 성공 + `import oracledb` 확인.
2. 번들러 `list`/`save`→`load` 왕복 확인.
3. 기존 스택 E2E(dbt) 회귀 없음.
4. design/05 체크리스트 7 실구현 링크로 교체.
5. 운영DB 접속 스모크는 프록시 서버에서 — EES 계정 확보 선결 (design/09 §34, 조직 이슈).
