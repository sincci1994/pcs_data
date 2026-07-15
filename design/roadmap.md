# 로드맵 (보류·후속 항목)

| 항목 | 출처 | 트리거 조건 |
|---|---|---|
| PySpark·멀티엔진 변환, Partition 기반 의존성 | 요구 7 · [adr/0003](adr/0003-defer-pyspark-multi-engine.md) | 빈도값 분석 등 Postgres SQL로 어려운 워크로드가 실체화될 때 |
| CORE(스타 스키마) 중간 계층 | 舊 설계 | GOLD 모델 간 차원 중복이 관리 한계에 달할 때 |
| Publish 증분 전환 (전량 교체 → 증분) | [02_ARCHITECTURE.md](02_ARCHITECTURE.md) ② | 전량 교체 소요 시간이 서빙 SLA를 위협할 때 |
| OpenMetadata Glossary↔자산 연결 자동화 | 요구 4 온톨로지 | 용어집 항목이 수동 연결로 감당 안 될 만큼 늘 때 |
| Confluence 비즈니스 문서 연동 | 초기 기획 | 인테이크 문서가 팀 외부 공유 단계로 갈 때 |
| 레거시 실행SQL(ees/smdm/gpm→pipe-scheduler-db) 이관 시나리오 | 舊 계획수정안 | 첫 데이터 제품(06) 완료 후 — 시나리오 후보 |
| 결측 정책 정교화 (설비×일 결측률, 지표 신뢰도 플래그) | [08 §5](08_DATA_OPS.md) | 기본 0 취급으로 운영 후, 결측이 지표 신뢰를 실제로 흔들 때 |
| 서빙 DB GOLD 이력 보존 정책 협의 (5년) | [08 §1](08_DATA_OPS.md) | 서빙 DB(운영/별도) 확정 시 소유자와 협의 |
| Deadline Alerts (Airflow SLA 후속 기능) 검토 | [08 §7](08_DATA_OPS.md) | Airflow 버전이 해당 기능 안정화 시 |
| 크리덴셜 로테이션 절차 | 독립 리뷰 | 원격 운영 개시 |
| 소비자용 결측 가시화 (내 마트의 상류 상태 뷰) | [11 §6](11_TARGET_ARCHITECTURE.md) | OM 사용 정착 후, 소비자가 OM 리니지+freshness로 부족하다고 실증될 때 |
| DataLake 카탈로그 I/F 재평가 | [11 §2](11_TARGET_ARCHITECTURE.md) | Lake 안정화가 실증될 때 (현행은 시스템 I/F 지향) |
| GEMS·EAM 인입 시나리오 선정 | [11 §2](11_TARGET_ARCHITECTURE.md) | SMDM enrichment 정식화 이후 |
| watermark 추출 모드 구현 (증분+lookback+ctl.watermark) | [03 캐던스](03_DAG_DESIGN.md) · [08 §4](08_DATA_OPS.md) | 첫 누적형 소스(N2 등) 실명세 확보 시 |
| Manager 기동 AssetAny 전환 + 영향 하위그래프 선택 트리거 | [03 캐던스](03_DAG_DESIGN.md) | sources.yml 두 번째 소스(상이 캐던스) 추가 시 — AND 함정 발현 전 선행 |
