# PCS 비즈니스 도메인 (원천)

이 문서가 도메인 정의의 **source of truth**다. `infra/openmetadata/om_setup_domains.py` 는 이 정의를 OpenMetadata 에 *발행*할 뿐이다. (기존엔 정의가 스크립트 안에만 있었음 — 갭 해소)

| 코드 | 도메인 | 설명 | 대표 시스템 |
|---|---|---|---|
| 01 | EquipmentMaster | 설비 마스터·자산 | EAM·SMDM·AMS·EDCP·S5D·FRM·SETTI |
| 02 | EquipmentPerformance | 설비 가동·성능 | EES·FDC·TPSS·YMS·iEES·SIMAX·SMAS |
| 03 | WorkMaintenance | 작업·정비 | G-EMS·CPMS |
| 04 | SafetyEnvCompliance | 안전·환경·컴플라이언스 | EHS·SMCS·IDPS·iEES·인프라WP·PEPS |
| 05 | Procurement | 조달·협력사 | BQMS·GPMS·SETTI·PEPS |
| 06 | CostBudget | 비용·예산 | NERP·SMAS |
| 07 | StandardInnovation | 표준·혁신 | SMDM·S5D·FRM |

## 테이블→도메인 귀속 규칙 (이름 휴리스틱)
- 테이블명에 `SENSOR`/`TRACE`/`KPI` → 02 EquipmentPerformance
- 테이블명에 `EQP`/`LINE`/`MGMT` → 01 EquipmentMaster
- CTL/D_DATE 등 → 비귀속
