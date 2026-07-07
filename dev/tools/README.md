# `tools/` — 목데이터 생성기

## 목적
원천(`SRC_SCADA.TRACE_RAW`)에 **설비 센서 측정값을 하루치씩 채워 넣는** 스크립트. 실제 SCADA가 없으니, 파이프라인을 돌려볼 데이터를 만들어 준다.

## 파일·역할
| 파일 | 역할 |
|---|---|
| `gen_mock_trace.py` | 지정한 날짜의 분 단위 센서 trace를 생성해 `SRC_SCADA.TRACE_RAW`에 INSERT |

## 왜 이렇게 (개념)
- 센서 마스터(`SENSOR_MST`)의 **HI/LO_LIMIT**를 읽어, 정상값은 그 중앙 부근 정규분포로, 일부는 한계를 벗어나게(=알람) 생성한다 → 다운스트림에서 `ALARM_CNT`가 의미 있게 나온다.
- 일부 구간은 `STATUS='IDLE'`로 만들어 `UPTIME_RATIO`가 1보다 작게 나오게 한다.
- **날짜 기반 시드**라 같은 날짜는 항상 같은 데이터(재현성). 재실행 시 그 날짜 데이터를 먼저 지우고 다시 넣어 멱등.

## 사용/실행법
```bash
# 컨테이너 안에서 (Oracle 호스트명 = oracle). Windows는 MSYS_NO_PATHCONV=1 필수
MSYS_NO_PATHCONV=1 docker compose exec -T airflow-scheduler \
  python /opt/airflow/tools/gen_mock_trace.py --date 2026-06-01 --host oracle

# 호스트에서 직접 (pip install oracledb 필요, 기본 host=localhost)
python tools/gen_mock_trace.py --date 2026-06-01
```

### 파라미터
| 옵션 | 기본 | 설명 |
|---|---|---|
| `--date` | (필수) | 생성 날짜 `YYYY-MM-DD` |
| `--interval-min` | 10 | 측정 간격(분). 10이면 하루 144포인트/센서 |
| `--alarm-rate` | 0.03 | HI/LO 초과(알람) 비율 |
| `--host` | localhost | Oracle 호스트(컨테이너 안에선 `oracle`) |

## 워터마크와의 관계 (중요)
추출 DAG은 **워터마크 기반 증분**이라, 이미 적재한 시점 이후 데이터만 가져간다. 같은 날짜 데이터를 다시 만들어도 워터마크가 이미 그 날짜를 지났으면 재적재되지 않는다. 강제로 다시 적재하려면:
```sql
UPDATE PCS_CTL.C_SOURCE_WATERMARK
SET LAST_LOADED_TS = TIMESTAMP '2000-01-01 00:00:00'
WHERE SRC_SYS='SCADA' AND SRC_OBJ='TRACE_RAW';
```

↑ [최상위 README](../../README.md) · 관련: [`infra/init/`](../../platform/infra/init/README.md)(원천 테이블), [`platform/CLAUDE.md`](../../platform/CLAUDE.md)(추출 규칙)
