# 📐 design/ — 설계 문서 · ADR · 로드맵

"왜 이렇게 만들었나"의 기록. 일상 작업에는 필요 없고, 구조를 바꾸거나 깊이 이해할 때 본다.

## 설계 문서 (번호순)
- `00_OVERVIEW.md` · `01_TECH_STACK.md` · `02_DIRECTORY_STRUCTURE.md`
- `03_DATA_FLOW.md` · `04_EXTRACT_LAYER.md` · `05_TRANSFORM_LAYER.md`
- `06_COMMON_LAYER.md` · `07_OPERATIONS.md` · `08_AIRGAP_BUILD.md` ⭐폐쇄망
- `09_SCENARIO_UTILITY_USAGE.md` ⭐기준 시나리오 — 샘플 재작성의 기준 (Oracle 5min → Postgres → Utility 사용량)

## 결정 기록 ([adr/](adr))
- 0001 ADR 도입 · 0002 멀티엔진 어댑터 · 0003 폐쇄망 패키징(PYTHONPATH-루트) · **0004 역할 기반 트리(호스트/컨테이너 분리)** · **0005 슬림 토폴로지(외부 DB·Marquez 제거)**

## 로드맵 ([roadmap/](roadmap)) — 예약된 미래 기능
- [`contracts-engine.md`](roadmap/contracts-engine.md) — SQL-메타데이터 계약 → Task+Sensor 자동등록 엔진
- [`agent-authoring.md`](roadmap/agent-authoring.md) — 오프라인 Agent 저작 툴링

## 원본 기획서
- [`vision.md`](vision.md)
