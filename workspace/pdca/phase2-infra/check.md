# Check: Phase 2 인프라 — compose 스택 로컬 구축·검증 (2026-07-09)

Plan = [design/05_INFRA.md](../../../design/05_INFRA.md) (설계 확정본). 이 문서는 검증 결과만 기록.

## 시나리오별 결과

| # | 시나리오 | 결과 |
|---|---|---|
| 1 | `config` → `up -d --build` → ps | ✅ execute_migrate_all Exited(0), 나머지 5개 healthy |
| 2 | ingestion 초기화 체인 (원격 문제 1 체크포인트) | ✅ `Database migrating done!` → SimpleAuthManager admin 설정 → 스케줄러 기동 — 수동 개입 0회 |
| 3 | Airflow(:8080)·OM(:8585) 로그인 | ✅ 둘 다 200, Airflow `/api/v2/version` = 3.1.5 |
| 4 | DAG 팩토리 manifest 전개 | ⏭ Phase 3 코드 필요 (설계상 명시 유보) |
| 5 | 샘플 모델 빌드 → warehouse 조회 | ✅ `wrk.wrk_infra_smoke` 12행 (dbt 1.11.12 / dbt-postgres 1.10.2, venv 격리) |
| 6 | OM 통합: Postgres 서비스 + dbt | ✅ 메타데이터 인제스천 success → 테이블 등재, dbt 인제스천 success → dataModel(DBT) 부착. 리니지 엣지는 스모크 모델에 ref() 없어 당연히 0 — 실검증은 Phase 3 slv→gold 체인에서 |

## 계획과 달랐던 것 (근본 원인 포함)

1. `.wslconfig` 12GB 설정 **불필요** — 호스트 32GB, WSL 기본 50%=15.9GB 로 이미 충분. `vm.max_map_count` 도 충족 상태.
2. getcollate 레지스트리 429 → 순차 pull 로 해소 (동시 pull 이 트리거).
3. Windows bind mount 쓰기 불가(root:755) 2건 파급:
   - dbt 가 무출력 exit 2 → `DBT_TARGET_PATH`/`DBT_LOG_PATH` 를 컨테이너 로컬로 (설계에 없던 결정 — 오히려 원격 이식에 유리한 방향).
   - OM 인제스천 DAG 배포 Permission denied → dags 루트를 공식 named volume 으로 복원, repo DAG 는 `/opt/airflow/dags/repo` 중첩 bind (**설계 수정점**: design/05 의 "dags bind mount" 서술).
4. 舊 스택 잔재(컨테이너 9개·네트워크 2개)가 subnet·포트 선점 → 컨테이너·네트워크만 제거, 舊 볼륨은 보존 중 (`openmetadata_*`, `pcs_airflow_practice_*` prefix — 불요 확정 시 삭제).

## Act

- 함정 5건 → [platform/infra/README.md](../../../platform/infra/README.md) 런북에 수록.
- design/05 후속 반영 필요: dags 마운트 서술(중첩 bind), .wslconfig 항목을 "확인만" 으로 완화.
- OM 인제스천 스케줄: metadata 04:00 / dbt 05:00 (일 1회, → design/02 온톨로지 절) — Phase 3 에서 Manager 완주 후로 재조정 검토.
