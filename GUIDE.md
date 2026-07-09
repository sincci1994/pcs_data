# GUIDE — 처음 쓰는 사람을 위한 사용·저작 안내

이 파이프라인으로 **①새 데이터를 들여오고 ②새 데이터 제품을 만드는** 두 가지 일의 순서를 안내한다.
개념 배경이 필요하면: 전체 그림 [README](README.md) · 계층·명명 규칙 [design/10](design/10_NAMING_ORGANIZATION.md).

## 큰 그림 — 데이터가 흐르는 길

```
운영 DB (신규 데이터가 쌓이는 곳)
   │  extract  ← sources.yml 선언이 만든 DAG가 주기 실행
   ▼
brz (bronze — 원본 그대로)
   │  ⚡ Asset 이벤트 = "적재 완료" 신호 — 이것이 '감지 센서' 역할.
   │     별도 센서 등록 없이 Manager DAG가 자동 기동된다
   ▼
slv (silver — 정제·표준화)  →  gld (gold — 비즈니스 제품)   ← dbt 모델 (SQL 파일)
   │  dbt test 통과 시
   ▼
Publish → 서빙 DB        (+ OpenMetadata: 카탈로그·리니지·용어집)
```

**어디에 뭘 만드나 — 치트시트** (명명 정본: [design/10](design/10_NAMING_ORGANIZATION.md))

| 하려는 일 | 만들 것 | 위치 | 이름 규칙 |
|---|---|---|---|
| 새 원천 데이터 들여오기 | YAML 블록 1개 | `platform/extract/sources.yml` | target = `brz.<소스>__<엔티티>` |
| 소스 정제·표준화 | staging 모델 | `transform/models/slv/<소스>/` | `stg_<소스>__<엔티티>.sql` |
| 복잡 변환의 중간 단계 | intermediate 모델 | slv/gld 해당 폴더 | `int_<대상>_<동사구>.sql` |
| 비즈니스 데이터 제품 | mart 모델 | `transform/models/gld/<도메인>/` | `dim_<엔티티>` / `fct_<지표>` |
| 실험·초안 | 아무 SQL | `transform/models/sbx/` | 자유 (헤더에 소유자·날짜 필수) |
| 지표·용어 정의 | glossary 항목 | `governance/glossary.md` | slv/gld 모델보다 **먼저** |

---

## 트랙 1 — 신규 소스 온보딩 (운영 DB에 새 데이터가 쌓이기 시작했다)

담당: 시스템(platform). 파이썬 코드 작업 없음 — 선언 1블록.

1. **소스 확인**: 운영 DB에서 테이블·컬럼·건수, 적재 주기, 접속 계정을 확인한다.
2. **접속 정보**: `platform/infra/.env`에 커넥션 env(`PCS_SRC_*` 또는 신규 접두사)를 채운다.
   시크릿은 `.env`로만 — 커밋 금지.
3. **선언 추가**: `platform/extract/sources.yml`에 블록 1개를 추가한다.
   ```yaml
   smdm_zte_equipment:                  # 소스 이름 (소문자 스네이크)
     conn: PCS_SRC                      # 접속 env 접두사
     table: smdm.zte_equipment          # 소스 테이블
     mode: snapshot                     # 전량 교체 (증분 watermark 는 후속)
     target: brz.smdm__zte_equipment    # bronze 테이블 (brz.<소스>__<엔티티>)
     schedule: "0 1 * * *"              # 매일 01:00 (Asia/Seoul)
     expected_columns: [eqp_id, csys_line_code, ...]   # 계약 체크 — 소스에 없으면 즉시 실패+알림
   ```
4. **자동 생성 확인**: 잠시 후(파싱 ~30초) Airflow UI(:8080)에 `extract__smdm_zte_equipment`
   DAG가 나타난다. 수동 트리거해 첫 적재를 확인한다.
5. **적재 확인**: warehouse에서 `select count(*) from brz.smdm__zte_equipment;`
6. **끝** — 이후는 자동이다: 매 적재 완료마다 Asset 이벤트가 발행되고, 이 소스를 쓰는
   staging 모델이 생기면 Manager가 신호를 받아 변환을 이어간다. **별도 센서 등록은 없다.**

> 자주 틀리는 것: bronze에는 dbt 모델을 만들지 않는다(extract 소유). 소스 컬럼이 바뀌면
> 계약 체크가 DAG를 즉시 실패시키고 알림을 보낸다 — `sources.yml`과 slv 모델을 함께 고치면 된다.

## 트랙 2 — 신규 데이터 제품 저작 (분석가)

담당: 분석가. SQL 파일 + 정의만 — DAG는 자동으로 생긴다.

1. **탐색·실험 (선택)**: `transform/models/sbx/`에 SQL을 만들어 자유롭게 실험한다.
   정의·테스트 불요, 헤더에 `-- owner: <이름> / date: <날짜>`만 필수.
   실행: Airflow에서 `model__<파일명>` DAG 수동 트리거 (Manager엔 편입되지 않는다).
2. **정의 확정**: `governance/glossary.md`에 지표 정의(산식·단위·결측 정책)를 확정한다.
   **정의 없이 slv/gld 모델 없다** — 이 순서가 규칙이다.
3. **모델 작성**:
   - 소스 정제가 필요하면 `models/slv/<소스>/stg_<소스>__<엔티티>.sql` (+ 같은 폴더 `_<소스>__sources.yml`에 brz 테이블 선언).
   - 제품은 `models/gld/<도메인>/dim_*.sql` 또는 `fct_*.sql` — **slv만 참조**(`ref()`), 소스 직접 참조 금지.
   - 서빙 반영이 필요하면 모델 첫 줄 config에 `meta={'publish_to': 'srv.<테이블>'}` 선언 — Publish 태스크가 자동 배선된다.
4. **테스트·설명**: 같은 폴더 `_<...>__models.yml`에 컬럼 설명(전부)과 테스트(키 unique/not_null + 도메인 range)를 쓴다.
5. **manifest 갱신** (DAG 자동 생성의 열쇠):
   ```bash
   cd platform/infra
   MSYS_NO_PATHCONV=1 docker exec openmetadata_ingestion bash -c \
     "cd /opt/airflow/transform && DBT_TARGET_PATH=/tmp/dbt_manifest DBT_LOG_PATH=/tmp/dbt_manifest /opt/airflow/dbt_venv/bin/dbt parse"
   docker cp openmetadata_ingestion:/tmp/dbt_manifest/manifest.json ../../transform/manifest.json
   ```
6. **확인**: Airflow에 `model__<모델명>` DAG가 생기고 Manager 위상에 편입된다.
   다음 extract 적재부터 자동 실행 — 급하면 Manager를 수동 트리거.
7. **커밋**: 모델 .sql + yml + glossary + manifest.json 을 함께 커밋한다.

## FAQ

- **"감지 센서는 어디서 등록하나?"** — 등록할 센서가 없다. extract가 적재를 마치면 **Asset
  이벤트**를 발행하고 Manager DAG가 그걸 구독해 자동 기동한다 (Airflow 3 data-aware scheduling).
- **"incremental 계층은 없나?"** — incremental은 계층이 아니라 dbt의 **적재 방식**(materialization)이다.
  대용량 모델에서 `{{ config(materialized='incremental') }}`로 쓴다. 계층은 brz/slv/gld뿐.
- **"모델이 많아지면 어떻게 찾나?"** — 비즈니스 개념은 OpenMetadata(:8585) 검색 → 용어집 → 리니지.
  저장소에서는 계층 폴더 → 소스/도메인 폴더 → 접두사 순으로 좁힌다.
- **"실행이 실패하면?"** — Manager run에서 실패한 태스크만 clear하면 성공분은 건너뛰고
  실패 지점부터 재개된다. 알림은 사내 메일·메신저로 온다(notifier).
- **"레거시 Excel 로직을 옮기려면?"** — [design/04 AS-IS 인테이크](design/04_AS_IS_INTAKE.md) 절차:
  인터뷰→논리 기록→SQL화→**대사 검증**→승격. 기록은 `governance/intake/`.
- **운영·장애 런북** — [platform/infra/README.md](platform/infra/README.md).
