# 03. 데이터 흐름 (메달리온)

## 스키마 스테이지
| 스테이지 | 스키마 | 역할 |
|---|---|---|
| Source | `SRC_SCADA` | 원천(SCADA) |
| Landing | `PCS_LND` | 수신 버퍼(원형 보존) |
| Silver | `PCS_SLV` | 정제/표준화 |
| Core | `PCS_CORE` | 차원·팩트(스타 스키마) |
| Gold | `PCS_GOLD` | 데이터 프로덕트(KPI) |

```
SRC_SCADA → PCS_LND → PCS_SLV → PCS_CORE → PCS_GOLD
 (extract)   (extract)  ───────── dbt ─────────
```

## Sensor 게이트 (transform DAG 진입)
Extract 완료를 확인한 뒤에만 dbt 를 돌린다.

```
ExternalTaskSensor  →  SqlSensor         →  DbtTaskGroup
(extract DAG 완료)    (LND watermark 확인)   (Cosmos 자동전개)
```

- **ExternalTaskSensor**: extract DAG 성공 대기.
- **SqlSensor**: `PCS_CTL` watermark/적재량 조건 충족 확인.
- **DbtTaskGroup**: Cosmos 가 dbt 모델을 Task 로 전개(slv→core→gold).

## 참고
- 지표 정의: [../governance/ontology/glossary.md](../governance/ontology/glossary.md) · 컬럼 설명의 단일 원천은 dbt `schema.yml`

> TODO: 실제 DAG id / 스케줄 확정 후 표 추가.
