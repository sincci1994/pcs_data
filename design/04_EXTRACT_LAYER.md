# 04. Extract 레이어

외부 데이터를 **어떻게** 가져오나. ABC(재사용) + projects(구현) 2단계.

## Collector ABC — `run()` 템플릿
`platform/extract/modules/collectors/` 의 추상 베이스. 고정 실행 순서:

```
run(): fetch → pre_validate → preprocess → post_validate → load
```

| 단계 | 책임 |
|---|---|
| `fetch` | 원천에서 원형 데이터 취득 |
| `pre_validate` | 취득 직후 계약/스키마 검증 |
| `preprocess` | 정규화·타입 변환 |
| `post_validate` | 적재 전 최종 검증 |
| `load` | 타깃(LND 등) 적재 |

## 적재 패턴
| 패턴 | 흐름 | 상태 |
|---|---|---|
| **SCADA** | 원천 Oracle → `PCS_LND` (watermark 증분) | 구현됨 (참조용 척추) |
| **크로스 DB** | Oracle → Postgres (chunked fetch + bulk insert) | 기준 시나리오([09](09_SCENARIO_UTILITY_USAGE.md))에서 구현 예정 |

그 외 패턴(API/Catalog/FTP→S3)의 스텁은 두지 않는다 — 필요 시 실구현과 함께 추가.

## 구현 규약 — `platform/extract/projects/<소스>/`
- 엔티티별 수집기 파일로 분리(마스터/트레이스).
- 커넥션은 `platform/common/connectors` 팩토리에서 획득.
- 실행 설정은 `platform/dags/extract_dags/configs/<소스>/` YAML.

## 새 소스 추가 레시피
1. `platform/extract/projects/<소스>/` 폴더 생성.
2. 엔티티별 수집기 작성(ABC 상속 → 5단계 구현).
3. `platform/dags/extract_dags/configs/<소스>/` YAML config 추가.
4. CTL 기록(`ctl_start`/`ctl_end`) 연결.

## 참고
- SCADA 구현: `platform/extract/projects/scada/` · 저작 규칙: [platform/CLAUDE.md](../platform/CLAUDE.md)
