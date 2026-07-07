# 06. Common 레이어

extract·transform·dags 가 공유하는 함수/클래스. `platform/common/`.

## 서브패키지
| 패키지 | 책임 | 상태 |
|---|---|---|
| `connectors/` | 멀티엔진 커넥션 어댑터 | Oracle 구현. Postgres는 기준 시나리오([09](09_SCENARIO_UTILITY_USAGE.md)) 구현 시 신규 작성 |
| `control/` | CTL 제어평면(job/watermark 기록) | 구현 |

빈 네임스페이스 예약(operators/hooks/preprocessing/validation/error_handling)은 두지 않는다 — **필요해지는 시점에 실구현과 함께 추가**한다.

## Connectors (멀티엔진)
- `connectors/oracle.py` → `OracleConnector`: thin/thick 전환(`driver_mode`, `lib_dir`).
- 설계 근거: [ADR 0002 멀티엔진 어댑터](adr/0002-multi-engine-adapter-layer.md)

## Control (CTL)
- job 시작/종료·watermark 를 `PCS_CTL` 에 기록. 관측성 표면. → [07_OPERATIONS.md](07_OPERATIONS.md)
