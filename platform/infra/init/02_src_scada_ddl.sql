-- =====================================================================
-- 02_src_scada_ddl.sql : 원천(SCADA 모사) 테이블 + 마스터 시드
-- =====================================================================
SET DEFINE OFF;

-- 설비 마스터
CREATE TABLE SRC_SCADA.EQP_MST (
  EQP_ID    VARCHAR2(20) PRIMARY KEY,
  EQP_NM    VARCHAR2(100),
  LINE_CD   VARCHAR2(20),
  MODEL_CD  VARCHAR2(40),
  USE_YN    CHAR(1) DEFAULT 'Y'
);

-- 센서 마스터 (상/하한 포함 → 알람 판정 기준)
CREATE TABLE SRC_SCADA.SENSOR_MST (
  SENSOR_ID  VARCHAR2(20) PRIMARY KEY,
  EQP_ID     VARCHAR2(20),
  SENSOR_NM  VARCHAR2(100),
  UNIT       VARCHAR2(20),
  HI_LIMIT   NUMBER,
  LO_LIMIT   NUMBER
);

-- 고빈도 센서 측정값 (목데이터 생성기가 분 단위로 적재)
CREATE TABLE SRC_SCADA.TRACE_RAW (
  EQP_ID     VARCHAR2(20),
  SENSOR_ID  VARCHAR2(20),
  MEAS_TS    TIMESTAMP,
  MEAS_VAL   NUMBER,
  STATUS_CD  VARCHAR2(10)
);
CREATE INDEX SRC_SCADA.IX_TRACE_TS ON SRC_SCADA.TRACE_RAW (MEAS_TS);

-- ---- 마스터 시드 ----
INSERT INTO SRC_SCADA.EQP_MST VALUES ('EQP001', 'Etcher #1',   'L01', 'ETCH-A', 'Y');
INSERT INTO SRC_SCADA.EQP_MST VALUES ('EQP002', 'Etcher #2',   'L01', 'ETCH-A', 'Y');
INSERT INTO SRC_SCADA.EQP_MST VALUES ('EQP003', 'CVD #1',      'L02', 'CVD-B',  'Y');
INSERT INTO SRC_SCADA.EQP_MST VALUES ('EQP004', 'Scrubber #1', 'L03', 'SCR-C',  'Y');

-- 설비별 센서 2종(온도/압력)
INSERT INTO SRC_SCADA.SENSOR_MST VALUES ('S001', 'EQP001', 'Chamber Temp', 'degC', 85, 55);
INSERT INTO SRC_SCADA.SENSOR_MST VALUES ('S002', 'EQP001', 'Chamber Pres', 'Torr', 12, 4);
INSERT INTO SRC_SCADA.SENSOR_MST VALUES ('S003', 'EQP002', 'Chamber Temp', 'degC', 85, 55);
INSERT INTO SRC_SCADA.SENSOR_MST VALUES ('S004', 'EQP002', 'Chamber Pres', 'Torr', 12, 4);
INSERT INTO SRC_SCADA.SENSOR_MST VALUES ('S005', 'EQP003', 'Deposit Temp', 'degC', 420, 380);
INSERT INTO SRC_SCADA.SENSOR_MST VALUES ('S006', 'EQP003', 'Gas Flow',     'sccm', 200, 120);
INSERT INTO SRC_SCADA.SENSOR_MST VALUES ('S007', 'EQP004', 'pH',           'pH',   9, 6);
INSERT INTO SRC_SCADA.SENSOR_MST VALUES ('S008', 'EQP004', 'Exhaust Pres', 'Pa',   50, 20);

COMMIT;
EXIT;
