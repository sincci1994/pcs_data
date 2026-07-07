# PCS 업무 용어집 (원천)

`infra/openmetadata/om_setup_domains.py` 가 이 용어를 OM Glossary(`PCS_Terms`)로 발행한다.

| 용어 | 표기 | 정의 |
|---|---|---|
| Equipment | 설비 | 공정 설비(Etcher/CVD/Scrubber 등). 마스터 = SMDM/EAM |
| Sensor | 센서 | 설비에 부착된 측정 포인트(온도/압력/유량). 상·하한 보유 |
| UptimeRatio | 가동률 | RUN 상태 측정 비율 = RUN건수 / 전체건수 |
| Alarm | 알람 | 센서값이 HI/LO 한계를 벗어난 건수 |

> 새 지표를 추가할 때는 여기 정의를 먼저 확정한 뒤(담당자 간 정의 통일), 코드/대시보드가 이를 참조하도록 한다. 이것이 프로젝트의 핵심 목적(지표 정의 표준화)이다.
