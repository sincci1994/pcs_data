# 용어집 (Glossary)

> 지표·용어 정의의 단일 원천. 항목 형식: 정의 / 산식 / 단위 / 관계 / 결측 정책 / 상태.
> 기준정보(엔티티) 항목은 산식 대신 **생성 규칙·키**를 기재한다.
> **관계**는 관련 용어를 `[[용어명]]`으로 링크한다 — OM Glossary 발행 시 related terms로 연결되고,
> 지식그래프(GraphRAG 등) 구축 시 이 문법이 용어 간 엣지의 원천이 된다.

## 설비 (Equipment)

- **정의**: 배관 스케줄러가 렌더링하는 설비 계층 노드. 레거시 EES **PortMaster2**(배관 구성 원장)에서 변환 생성한다. 8종: `MAIN`(메인설비) / `CHAMBER`(챔버) / `PUMP`(펌프) / `SCRUBBER`(스크러버) / `SCRUBBER_NOR_VALVE`·`SCRUBBER_BYP_VALVE`(밸브) / `SCRUBBER_MERGE`(합류) / `LATERAL_DUCT`(덕트).
- **생성 규칙**: 명명·챔버 분리(공정=경로 분리, TM/LL=단일)·NOR 소유 결정론 — 단일 원천: [인테이크 기록](intake/2026-07-09_equipment_pipe_portmaster2.md) §4 (레거시 변환규칙.md 준수 이식).
- **키**: `code` (전역 유일). 조직(팀/라인 등)은 enrichment — v1은 더미 시드, SMDM/GPM 연동은 후속.
- **관계**: [[배관]]의 양끝 노드 — Pipe의 `from/to/chamber/main`이 Equipment `code`를 참조한다.
- **결측 정책**: 소스 필수 컬럼 NULL/빈값 행은 slv(staging)에서 제외 (레거시 01 스크립트와 동일 기준).
- **상태**: **확정** (2026-07-09) — 레거시 검증 완료 로직의 이식이므로 대사 검증 게이트 적용.

## 배관 (Pipe)

- **정의**: 설비 노드 간 배관 연결(방향 있는 엣지). 6종: `FORELINE`(챔버→펌프) / `PS`(펌프→NOR밸브) / `SS`(NOR→BYP밸브) / `ALLBYPASS`(BYP밸브→BYP MERGE) / `SD1`(스크러버→자기 MERGE) / `SD2`(MERGE→덕트).
- **생성 규칙**: `code` = `{from}_{to}_{chamber}`. NOR-only 챔버는 SS/ALLBYPASS만 조건부 미생성, 나머지 4종 보존. 길이/MTBF 기본값은 종별 고정 상수 — [인테이크 기록](intake/2026-07-09_equipment_pipe_portmaster2.md) §4.
- **키**: `code` (전역 유일). FK 누락 0건이 품질 게이트.
- **관계**: [[설비]] 간 방향 있는 엣지 — `from/to/chamber/main`이 Equipment `code`를 참조한다.
- **결측 정책**: Equipment와 동일 (slv 필터 승계).
- **상태**: **확정** (2026-07-09).

## Utility 사용량 (UtilityUsage)

- **정의**: 설비별 하루 동안의 Utility 소비량. 소스는 레거시 EES 5분 Parameter 테이블 중 Utility 센서(명명 규칙으로 식별).
- **산식**: 구간값 합산 — 5분 값이 해당 구간의 사용량이며 일 단위로 합산한다 (누적계 차분 아님).
- **단위**: 미확정 (EES 실명세 확인 후).
- **관계**: [[설비]] 단위 일 지표 (설비 1 : 사용량 N).
- **결측 정책**: **기본 0 취급** — 일 합산에서는 결측 제외와 동일 결과. 정교화(결측률·신뢰도 플래그)는 roadmap (→ [design/08 §5](../design/08_DATA_OPS.md)).
- **일 경계**: Asia/Seoul 00:00 [기본값 — 확정 시 갱신].
- **상태**: 초안 (2026-07-09) — [design/06](../design/06_SCENARIO_UTILITY_USAGE.md)

## 현재 평균 사용량 (CurrentAvgUsage)

- **정의**: 설비별 당일 진행분 기준 Utility 평균 사용량.
- **산식**: 미확정 — 집계 윈도(당일 0시~현재 / 최근 N시간)와 갱신 주기 확정 필요.
- **단위**: 미확정.
- **관계**: [[Utility 사용량]]에서 파생 (윈도 평균).
- **결측 정책**: **분모 정의와 결합** — 평균의 분모를 경과 버킷 수(결측=0 취급)로 할지 수신 버킷 수(결측 제외)로 할지가 이 지표의 핵심 결정 (→ [design/08 §5](../design/08_DATA_OPS.md)).
- **상태**: 초안 (2026-07-09) — 구현 착수 전 확정 필수.
