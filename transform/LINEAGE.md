# LINEAGE — 전 경로 계보 (자동 생성 — 직접 수정 금지)

생성: `platform/infra/` 에서 `python ops/render_lineage.py` — manifest 갱신 시 함께 재생성한다.
실행 순서·의존은 Airflow `manager__pcs_transform` Graph, 테이블 계보는 OpenMetadata 리니지가 정본이고,
이 문서는 오프라인·코드리뷰용 스냅샷이다 (→ GUIDE.md §계보·의존성 어디서 보나).

```mermaid
flowchart LR
  subgraph SRC["소스 (운영 DB — 로컬 대역: src)"]
    src_pcs_sq_port_mst_2nd["src.pcs_sq_port_mst_2nd"]
  end
  subgraph BRZ["brz (원본 보존)"]
    source_pcs_transform_brz_ees_ees__portmaster2["brz.ees__portmaster2"]
    %% extract: ees_portmaster2
  end
  subgraph SLV["slv (표준화)"]
    model_pcs_transform_stg_ees__portmaster2["slv.stg_ees__portmaster2"]
    model_pcs_transform_stg_smdm__eqp_org_mapping["slv.stg_smdm__eqp_org_mapping"]
    seed_pcs_transform_seed_eqp_org_mapping["slv.seed_eqp_org_mapping"]
  end
  subgraph GLD["gld (데이터 제품)"]
    model_pcs_transform_dim_equipment["gld.dim_equipment"]
    model_pcs_transform_dim_pipe["gld.dim_pipe"]
    model_pcs_transform_dim_vendor["gld.dim_vendor"]
  end
  subgraph SRV["서빙 (Oracle — 소비 조회 단일 창구, → design/08 §1.1)"]
    srv_model_pcs_transform_dim_equipment["srv.equipment"]
    srv_model_pcs_transform_dim_pipe["srv.pipe"]
    srv_model_pcs_transform_dim_vendor["srv.vendor"]
    srv_model_pcs_transform_stg_ees__portmaster2["srv.stg_ees__portmaster2"]
    srv_model_pcs_transform_stg_smdm__eqp_org_mapping["srv.stg_smdm__eqp_org_mapping"]
  end
  src_pcs_sq_port_mst_2nd -->|extract__ees_portmaster2| source_pcs_transform_brz_ees_ees__portmaster2
  model_pcs_transform_stg_ees__portmaster2 --> model_pcs_transform_dim_equipment
  model_pcs_transform_stg_smdm__eqp_org_mapping --> model_pcs_transform_dim_equipment
  model_pcs_transform_stg_ees__portmaster2 --> model_pcs_transform_dim_pipe
  model_pcs_transform_stg_smdm__eqp_org_mapping --> model_pcs_transform_dim_pipe
  model_pcs_transform_stg_ees__portmaster2 --> model_pcs_transform_dim_vendor
  source_pcs_transform_brz_ees_ees__portmaster2 --> model_pcs_transform_stg_ees__portmaster2
  seed_pcs_transform_seed_eqp_org_mapping --> model_pcs_transform_stg_smdm__eqp_org_mapping
  model_pcs_transform_dim_equipment -->|publish| srv_model_pcs_transform_dim_equipment
  model_pcs_transform_dim_pipe -->|publish| srv_model_pcs_transform_dim_pipe
  model_pcs_transform_dim_vendor -->|publish| srv_model_pcs_transform_dim_vendor
  model_pcs_transform_stg_ees__portmaster2 -->|publish| srv_model_pcs_transform_stg_ees__portmaster2
  model_pcs_transform_stg_smdm__eqp_org_mapping -->|publish| srv_model_pcs_transform_stg_smdm__eqp_org_mapping
```
