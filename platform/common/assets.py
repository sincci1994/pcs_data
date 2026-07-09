"""Asset URI 단일 원천 — extract(발행)와 Manager(구독)가 같은 문자열을 봐야 한다 (→ design/03).

URI 규칙과 소스 목록은 extract/sources.yml 에서 파생된다 — 소스가 늘면 Manager 구독도 자동 확장.
"""
from extract.config import asset_uri, load_sources

# Manager 기동 신호: 선언된 모든 extract 완료 Asset
MANAGER_TRIGGER_URIS = [asset_uri(src["target"]) for src in load_sources().values()]
