#!/usr/bin/env bash
# [로컬 실습 전용] EES PortMaster2 목데이터 — mock/seed_src_portmaster2.sql 의 Oracle 이식 (동일 47행).
# 비인용 식별자는 대문자 폴딩 → SRC.PCS_SQ_PORT_MST_2ND. sources.yml 은 그대로 동작 (UPPER 매칭).
set -euo pipefail

sqlplus -s src/"$PCS_ORA_SRC_PASSWORD"@localhost/FREEPDB1 <<'EOF'
WHENEVER SQLERROR EXIT SQL.SQLCODE
CREATE TABLE pcs_sq_port_mst_2nd (
    eqp_id           VARCHAR2(50 CHAR)   NOT NULL,
    eqp_chamber_id   VARCHAR2(10 CHAR)   NOT NULL,
    eqp_chamber_posn VARCHAR2(20 CHAR)   NOT NULL,
    eqp_posn         VARCHAR2(10 CHAR)   NOT NULL,
    seqp_type        VARCHAR2(20 CHAR)   NOT NULL,
    seqp_maker       VARCHAR2(50 CHAR)   NOT NULL,
    seqp_model_code  VARCHAR2(100 CHAR),
    seqp_id          VARCHAR2(50 CHAR)   NOT NULL,
    seqp_ch          VARCHAR2(10 CHAR),
    seqp_port        VARCHAR2(10 CHAR),
    db_user          VARCHAR2(30 CHAR)   DEFAULT 'PF_PCS' NOT NULL
);

INSERT ALL
-- SLWB331 (PED/PRO 다중경로, Pair 스크러버)
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('SLWB331','0','LL1','0','PUMP','EBARA','SLWB331_PP02','0','0')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('SLWB331','0','TM','0','PUMP','EBARA','SLWB331_PP01','0','0')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('SLWB331','A','PED','0','PUMP','LOT','SLWB331_PP03','0','0')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('SLWB331','A','PED','BYP','SCRUBBER','UNISEM','SLWB331_SC02','1','3')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('SLWB331','A','PED','NOR','SCRUBBER','UNISEM','SLWB331_SC01','1','1')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('SLWB331','A','PRO','0','PUMP','LOT','SLWB331_PP04','0','0')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('SLWB331','A','PRO','BYP','SCRUBBER','UNISEM','SLWB331_SC02','1','4')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('SLWB331','A','PRO','NOR','SCRUBBER','UNISEM','SLWB331_SC01','1','2')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('SLWB331','B','PED','0','PUMP','LOT','SLWB331_PP06','0','0')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('SLWB331','B','PED','BYP','SCRUBBER','UNISEM','SLWB331_SC01','1','4')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('SLWB331','B','PED','NOR','SCRUBBER','UNISEM','SLWB331_SC02','1','2')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('SLWB331','B','PRO','0','PUMP','LOT','SLWB331_PP05','0','0')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('SLWB331','B','PRO','BYP','SCRUBBER','UNISEM','SLWB331_SC01','1','3')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('SLWB331','B','PRO','NOR','SCRUBBER','UNISEM','SLWB331_SC02','1','1')
-- TBNP708 (PRO/DIVERT 경로별 독립)
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('TBNP708','0','LL1','0','PUMP','KKT','TBNP708_PP01','0','0')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('TBNP708','0','TM','0','PUMP','KKT','TBNP708_PP02','0','0')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('TBNP708','1','DIVERT','0','PUMP','LOT','TBNP708_PP04','0','0')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('TBNP708','1','DIVERT','BYP','SCRUBBER','UNISEM','TBNP708_SC06','1','3')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('TBNP708','1','DIVERT','NOR','SCRUBBER','UNISEM','TBNP708_SC04','1','1')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('TBNP708','1','PRO','0','PUMP','LOT','TBNP708_PP03','0','0')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('TBNP708','1','PRO','BYP','SCRUBBER','UNISEM','TBNP708_SC03','1','3')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('TBNP708','1','PRO','NOR','SCRUBBER','UNISEM','TBNP708_SC01','1','1')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('TBNP708','2','DIVERT','0','PUMP','LOT','TBNP708_PP06','0','0')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('TBNP708','2','DIVERT','BYP','SCRUBBER','UNISEM','TBNP708_SC04','1','3')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('TBNP708','2','DIVERT','NOR','SCRUBBER','UNISEM','TBNP708_SC05','1','1')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('TBNP708','2','PRO','0','PUMP','LOT','TBNP708_PP05','0','0')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('TBNP708','2','PRO','BYP','SCRUBBER','UNISEM','TBNP708_SC01','1','3')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('TBNP708','2','PRO','NOR','SCRUBBER','UNISEM','TBNP708_SC02','1','1')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('TBNP708','3','DIVERT','0','PUMP','LOT','TBNP708_PP08','0','0')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('TBNP708','3','DIVERT','BYP','SCRUBBER','UNISEM','TBNP708_SC05','1','3')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('TBNP708','3','DIVERT','NOR','SCRUBBER','UNISEM','TBNP708_SC06','1','1')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('TBNP708','3','PRO','0','PUMP','LOT','TBNP708_PP07','0','0')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('TBNP708','3','PRO','BYP','SCRUBBER','UNISEM','TBNP708_SC02','1','3')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('TBNP708','3','PRO','NOR','SCRUBBER','UNISEM','TBNP708_SC03','1','1')
-- WTCB7G1 (NOR-only, BYP 스크러버 없음)
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('WTCB7G1','0','TM','0','PUMP','KKT','WTCB7G1_PP01','0','0')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('WTCB7G1','1','PRO','0','PUMP','EDWARDS','WTCB7G1_PP02','0','0')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('WTCB7G1','1','PRO','NOR','SCRUBBER','CSK','WTCB7G1_SC01','1','1')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('WTCB7G1','2','PRO','0','PUMP','EDWARDS','WTCB7G1_PP03','0','0')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('WTCB7G1','2','PRO','NOR','SCRUBBER','CSK','WTCB7G1_SC01','1','1')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('WTCB7G1','3','PRO','0','PUMP','EDWARDS','WTCB7G1_PP04','0','0')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('WTCB7G1','3','PRO','NOR','SCRUBBER','CSK','WTCB7G1_SC02','1','1')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('WTCB7G1','4','PRO','0','PUMP','EDWARDS','WTCB7G1_PP05','0','0')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('WTCB7G1','4','PRO','NOR','SCRUBBER','CSK','WTCB7G1_SC02','1','1')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('WTCB7G1','5','PRO','0','PUMP','EDWARDS','WTCB7G1_PP06','0','0')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('WTCB7G1','5','PRO','NOR','SCRUBBER','CSK','WTCB7G1_SC03','1','1')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('WTCB7G1','6','PRO','0','PUMP','EDWARDS','WTCB7G1_PP07','0','0')
INTO pcs_sq_port_mst_2nd (eqp_id, eqp_chamber_id, eqp_chamber_posn, eqp_posn, seqp_type, seqp_maker, seqp_id, seqp_ch, seqp_port) VALUES ('WTCB7G1','6','PRO','NOR','SCRUBBER','CSK','WTCB7G1_SC03','1','1')
SELECT 1 FROM dual;

COMMIT;
SELECT 'PCS seed rows: ' || COUNT(*) FROM pcs_sq_port_mst_2nd;
EOF
echo "PCS: PortMaster2 목데이터 시드 완료"
