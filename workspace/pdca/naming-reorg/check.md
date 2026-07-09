# Check: 명명·조직 전략 확정 + 재구성 + 온보딩 가이드 (2026-07-09)

서버 이전 직전 점검 — 사용자 지적 3건(온보딩 가이드 부재 / 계층·명명 전략 / 탐색성)에 대한 실행 기록.
Plan = design/10 (신설, 정본).

## 확정 결정 (사용자 Q&A)
- **어휘 = 메달리온 축약 통일**: `brz/slv/gld` + `sbx`(실험, 구 wrk) + ctl·srv. 구명칭(lnd/gold/wrk 혼합)은 참조 저장소 승계였고 비일관 — 전면 교체.
- **동작(clean/filter)은 폴더가 아니라** 계층 계약 + `int_<대상>_<동사구>` 모델명 + CTE명으로. 동작별 폴더는 모델 파편화라 배제.
- **접두사 축**: 소스명은 slv까지(`stg_<소스>__<엔티티>`), gld는 비즈니스명만(`dim_`/`fct_` + 도메인 폴더) — 소스 교체 시 mart 이름 불변(design/07 보장), 온톨로지 정합.
- 신규 소스 = **sources.yml 선언 1블록** (extract 팩토리) — 모델 셀프서비스와 대칭.

## 실행 결과
| 항목 | 결과 |
|---|---|
| design/10 신설 + 문서 15종 표기 개정 | ✅ (이력 문서는 당시 명칭 보존) |
| DB 스키마 rename (lnd→brz, gold→gld, wrk→sbx) + init 갱신 | ✅ |
| dbt 재구성: slv/<소스>·gld/<도메인> 폴더, stg_/dim_ 리네임, sbx 스모크 삭제 | ✅ manifest 재컴파일 6노드 |
| extract 선언형 팩토리 (sources.yml + snapshot.py + factory__extract.py) | ✅ 소스별 파이썬 모듈 제거 |
| GUIDE.md (트랙1 소스 온보딩 / 트랙2 모델 저작 + 치트시트·FAQ) | ✅ |
| E2E 재검증 | (하단 이력 — 체인·대사) |

## E2E (2026-07-09 통과)
- import 에러 0, 신규 DAG 전개(extract__ees_portmaster2, model__stg_*/dim_*), 구 dag_id 레코드 삭제.
- 체인 성공: extract → Asset → Manager → 모델 6종 → singular 게이트 → Publish 3종.
- **대사 5/5 PASS** — 카운트 완전 일치(94/89, 타입별, FK 0) = 리네임이 로직 불변임을 증명. brz 47행 유지(멱등).
- dbt build 55/55, OM 재인제스트 success — 리니지 brz.ees__portmaster2 → slv.stg_ees__portmaster2 → gld.dim_equipment.
- 잔존 구명칭 grep 0 (이력 문서·"구 wrk" 의도적 언급 제외), 링크 전수 검사 OK.
