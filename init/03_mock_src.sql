-- [로컬 검증 전용] EES PortMaster2 목데이터 — 원격에선 실 EES(Oracle)가 소스라 이 스키마 자체가 없다.
-- 샘플: 레거시 검증 완료 3설비 47행 (pipe-scheduler-works/레거시전처리코드/검증샘플/sourcedata.md 그대로).
-- 적용: docker exec -i pcs_warehouse psql -U pcs_admin -d pcs_wh < platform/infra/mock/seed_src_portmaster2.sql

CREATE SCHEMA IF NOT EXISTS src;

DROP TABLE IF EXISTS src.pcs_sq_port_mst_2nd;
CREATE TABLE src.pcs_sq_port_mst_2nd (
    eqp_id           varchar(50)  NOT NULL,
    eqp_chamber_id   varchar(10)  NOT NULL,
    eqp_chamber_posn varchar(20)  NOT NULL,
    eqp_posn         varchar(10)  NOT NULL,
    seqp_type        varchar(20)  NOT NULL,
    seqp_maker       varchar(50)  NOT NULL,
    seqp_model_code  varchar(100),
    seqp_id          varchar(50)  NOT NULL,
    seqp_ch          varchar(10),
    seqp_port        varchar(10),
    db_user          varchar(30)  NOT NULL DEFAULT 'PF_PCS'
);

INSERT INTO src.pcs_sq_port_mst_2nd
    (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES
-- SLWB331 (PED/PRO 다중경로, Pair 스크러버)
('SLWB331','0','LL1','0','PUMP','EBARA','SLWB331_PP02','0','0'),
('SLWB331','0','TM','0','PUMP','EBARA','SLWB331_PP01','0','0'),
('SLWB331','A','PED','0','PUMP','LOT','SLWB331_PP03','0','0'),
('SLWB331','A','PED','BYP','SCRUBBER','UNISEM','SLWB331_SC02','1','3'),
('SLWB331','A','PED','NOR','SCRUBBER','UNISEM','SLWB331_SC01','1','1'),
('SLWB331','A','PRO','0','PUMP','LOT','SLWB331_PP04','0','0'),
('SLWB331','A','PRO','BYP','SCRUBBER','UNISEM','SLWB331_SC02','1','4'),
('SLWB331','A','PRO','NOR','SCRUBBER','UNISEM','SLWB331_SC01','1','2'),
('SLWB331','B','PED','0','PUMP','LOT','SLWB331_PP06','0','0'),
('SLWB331','B','PED','BYP','SCRUBBER','UNISEM','SLWB331_SC01','1','4'),
('SLWB331','B','PED','NOR','SCRUBBER','UNISEM','SLWB331_SC02','1','2'),
('SLWB331','B','PRO','0','PUMP','LOT','SLWB331_PP05','0','0'),
('SLWB331','B','PRO','BYP','SCRUBBER','UNISEM','SLWB331_SC01','1','3'),
('SLWB331','B','PRO','NOR','SCRUBBER','UNISEM','SLWB331_SC02','1','1'),
-- TBNP708 (PRO/DIVERT 경로별 독립)
('TBNP708','0','LL1','0','PUMP','KKT','TBNP708_PP01','0','0'),
('TBNP708','0','TM','0','PUMP','KKT','TBNP708_PP02','0','0'),
('TBNP708','1','DIVERT','0','PUMP','LOT','TBNP708_PP04','0','0'),
('TBNP708','1','DIVERT','BYP','SCRUBBER','UNISEM','TBNP708_SC06','1','3'),
('TBNP708','1','DIVERT','NOR','SCRUBBER','UNISEM','TBNP708_SC04','1','1'),
('TBNP708','1','PRO','0','PUMP','LOT','TBNP708_PP03','0','0'),
('TBNP708','1','PRO','BYP','SCRUBBER','UNISEM','TBNP708_SC03','1','3'),
('TBNP708','1','PRO','NOR','SCRUBBER','UNISEM','TBNP708_SC01','1','1'),
('TBNP708','2','DIVERT','0','PUMP','LOT','TBNP708_PP06','0','0'),
('TBNP708','2','DIVERT','BYP','SCRUBBER','UNISEM','TBNP708_SC04','1','3'),
('TBNP708','2','DIVERT','NOR','SCRUBBER','UNISEM','TBNP708_SC05','1','1'),
('TBNP708','2','PRO','0','PUMP','LOT','TBNP708_PP05','0','0'),
('TBNP708','2','PRO','BYP','SCRUBBER','UNISEM','TBNP708_SC01','1','3'),
('TBNP708','2','PRO','NOR','SCRUBBER','UNISEM','TBNP708_SC02','1','1'),
('TBNP708','3','DIVERT','0','PUMP','LOT','TBNP708_PP08','0','0'),
('TBNP708','3','DIVERT','BYP','SCRUBBER','UNISEM','TBNP708_SC05','1','3'),
('TBNP708','3','DIVERT','NOR','SCRUBBER','UNISEM','TBNP708_SC06','1','1'),
('TBNP708','3','PRO','0','PUMP','LOT','TBNP708_PP07','0','0'),
('TBNP708','3','PRO','BYP','SCRUBBER','UNISEM','TBNP708_SC02','1','3'),
('TBNP708','3','PRO','NOR','SCRUBBER','UNISEM','TBNP708_SC03','1','1'),
-- WTCB7G1 (NOR-only, BYP 스크러버 없음)
('WTCB7G1','0','TM','0','PUMP','KKT','WTCB7G1_PP01','0','0'),
('WTCB7G1','1','PRO','0','PUMP','EDWARDS','WTCB7G1_PP02','0','0'),
('WTCB7G1','1','PRO','NOR','SCRUBBER','CSK','WTCB7G1_SC01','1','1'),
('WTCB7G1','2','PRO','0','PUMP','EDWARDS','WTCB7G1_PP03','0','0'),
('WTCB7G1','2','PRO','NOR','SCRUBBER','CSK','WTCB7G1_SC01','1','1'),
('WTCB7G1','3','PRO','0','PUMP','EDWARDS','WTCB7G1_PP04','0','0'),
('WTCB7G1','3','PRO','NOR','SCRUBBER','CSK','WTCB7G1_SC02','1','1'),
('WTCB7G1','4','PRO','0','PUMP','EDWARDS','WTCB7G1_PP05','0','0'),
('WTCB7G1','4','PRO','NOR','SCRUBBER','CSK','WTCB7G1_SC02','1','1'),
('WTCB7G1','5','PRO','0','PUMP','EDWARDS','WTCB7G1_PP06','0','0'),
('WTCB7G1','5','PRO','NOR','SCRUBBER','CSK','WTCB7G1_SC03','1','1'),
('WTCB7G1','6','PRO','0','PUMP','EDWARDS','WTCB7G1_PP07','0','0'),
('WTCB7G1','6','PRO','NOR','SCRUBBER','CSK','WTCB7G1_SC03','1','1');

GRANT USAGE ON SCHEMA src TO dbt_exec;
GRANT SELECT ON ALL TABLES IN SCHEMA src TO dbt_exec;
