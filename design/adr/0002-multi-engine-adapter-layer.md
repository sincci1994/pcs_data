# ADR 0002 — 멀티엔진 어댑터 계층

- 상태: 채택 (인터페이스만, Oracle 구현)
- 날짜: 2026-07-07

## 맥락
저장소가 Postgres·Oracle(thick)·S3 로 다양하고, 적재 경로도 API 직접/Catalog→DB/FTP→S3 로 나뉜다. 현 코드는 Oracle-thin 단일이라 확장 시 결합도가 문제된다.

## 결정
- **커넥션 추상화**를 `platform/common/connectors/` 에 둔다: `StorageConnector` Protocol + `AbstractConnector`. Oracle 구현(`OracleConnector`, thin/thick), Postgres/S3 스텁.
- **적재 패턴**을 `platform/extract/modules/collectors/` 에 ABC 로 둔다: `Collector.run()` 템플릿(fetch→validate→preprocess→validate→load). api/catalog/ftp_s3 스텁.
- **Load 오퍼레이터**는 `platform/common/operators/`.

## 결과
새 엔진/소스는 어댑터 추가로 흡수. SCADA 는 현재 flat 콜러블을 유지하되 내부적으로 `OracleConnector`+`platform/common/control` 사용 → 향후 `CatalogCollector.run()` 위임으로 무중단 전환 가능.
