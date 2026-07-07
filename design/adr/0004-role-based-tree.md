# ADR 0004 — 역할 기반 트리 + 호스트/컨테이너 경로 분리

- 상태: 채택
- 날짜: 2026-07-07
- 대체: ADR 근거 일부(캐논 레포 구조 차용 결정)를 완화

## 맥락
목적기반(extract/transform/dags/common) 최상위 트리는 "기획한 사람에게만 이해된다"는 팀 피드백. 팀은 도메인 전문가·리소스 담당자·시스템 담당자·품질/모니터링 4역할로 나뉘어 **다 같이 배우며** 구성 중. "기능은 많되 단순해야."

## 결정
1. **호스트 트리를 역할 기반 7폴더로 재편**: `governance/`(도메인) · `transform/`(리소스) · `platform/`(시스템: dags·extract·common·infra) · `quality/`(품질) · `workspace/`(전원 공용) · `design/`(설계) · `dev/`(도구·테스트).
2. **컨테이너 경로는 관례 유지**: `/opt/airflow/{dags,extract,common,transform,tools}`. **번역은 docker-compose 볼륨 마운트가 담당.**
3. 결과: import 문자열(`extract.*`)·Cosmos DBT 경로·PYTHONPATH·YAML callable 은 **무변경**. 전면 재편이지만 런타임 파괴 위험 최소.

## 근거
- 역할↔폴더 1:1 이 체감 복잡도를 가장 크게 줄인다("자기 폴더 밖은 몰라도 된다").
- 물리 트리와 실행 환경을 마운트로 디커플링하면 "사람용 구조"와 "기계용 구조"를 동시에 최적화할 수 있다.
- 캐논 레포(coldchainservice)의 dags/extract/common 멘탈모델은 `platform/` **안에서** 그대로 보존된다.

## 결과/주의
- 호스트에서 테스트 시 `dev/tests/conftest.py` 가 `ROOT/platform` 을 sys.path 에 주입.
- **새 마운트를 추가할 때 반드시 컨테이너 쪽 경로를 관례(`/opt/airflow/...`)로 유지할 것.**
- 폐쇄망 이미지 빌드 시 소스 COPY 도 동일 매핑(`platform/extract → /opt/airflow/extract`)을 따른다(→ 08_AIRGAP_BUILD).
