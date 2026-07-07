# ADR 0003 — 폐쇄망 패키징: PYTHONPATH-루트 (설치형 패키지 미사용)

- 상태: 채택
- 날짜: 2026-07-07

## 맥락
배포 대상은 **폐쇄망**이며, 빌드는 **프록시/사내 미러** 경유, **레포 전체를 하나의 단위로 반입**한다. 처음엔 `src/pcs_pipeline/` editable install 을 검토했으나 사내 캐논 레포(`coldchainservice_airflow`)는 PYTHONPATH-루트를 쓴다.

## 결정
첫party 코드(`extract/`·`common/`·`transform/`)를 **설치형 패키지로 만들지 않고** PYTHONPATH-루트로 import 한다. `pyproject.toml` 은 lint/format 설정 전용.

## 근거
- 프록시/폐쇄망 이슈는 *서드파티* 계층(requirements 핀 + 내부 인덱스)에서 해결되며 첫party 패키징과 무관.
- "레포 통째 반입" = 배포 단위가 레포 자체 → 배포 가능한 wheel 의 이점(공유 라이브러리) 부재.
- `pip install -e .` 는 빌드 백엔드/훅이라는 폐쇄망 실패 지점을 추가.
- 캐논 레포와 import 관례 100% 일치 → 인지 부하↓, 벤치마킹 노트 재사용.

## 결과
유닛테스트는 `dev/tests/conftest.py` 가 루트와 `platform/` 을 `sys.path` 에 주입해 회수. Airflow 를 모듈레벨 import 하는 dagfactory 는 컨테이너 DAG 파싱으로 검증.
