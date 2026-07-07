# 작업 지시: 센서 알람율 KPI 추가

- 상태: 진행중
- 요청자: 데이터 거버넌스 담당
- 작성일: 2026-07-07
- 대응 PDCA: `workspace/pdca/sensor-alarm-kpi/`

## 목표
설비×센서×일 단위 **알람율(Alarm Ratio)** 지표를 GOLD 마트에 추가한다. 담당자마다 다르게 계산하던 "알람" 정의를 표준화한다.

## 배경
- 용어 정의: [governance/ontology/glossary.md](../../governance/ontology/glossary.md) 의 `Alarm`(HI/LO 한계 이탈 건수).
- 대상 마트: `PCS_GOLD.G_WP_EQP_SENSOR_KPI_D` (컬럼 정의: `transform/dbt/models/core/schema.yml`).
- 소스 Fact: `PCS_CORE.F_SENSOR_DAILY`.

## 범위
- 포함: dbt 모델 컬럼 추가(알람율), schema.yml 테스트, 용어집 반영.
- 제외: 대시보드/화면 변경, 신규 소스 수집.

## 제약
- Airflow 파싱 경로에 LLM 개입 금지(결정론적).
- 지표 정의는 용어집을 **단일 원천**으로 참조.

## 완료조건 (acceptance)
- [ ] `G_WP_EQP_SENSOR_KPI_D` 에 알람율 컬럼 존재 + 0~1 범위 테스트 통과.
- [ ] glossary 에 `AlarmRatio` 항목 추가.
- [ ] Cosmos 로 dbt Task 정상 전개(파싱 에러 없음).

## 참고문서
- [design/05_TRANSFORM_LAYER.md](../../design/05_TRANSFORM_LAYER.md)
