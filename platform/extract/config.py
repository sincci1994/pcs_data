"""sources.yml 로더 + 스키마 검증 — extract 팩토리와 Asset 파생의 공용 진입점.

결정론 원칙: 선언 파일만 읽는다. 동적 로드에 eval 금지 (platform/CLAUDE.md 규칙 4) —
필드는 화이트리스트 검증을 거친 리터럴 값으로만 쓰인다.
"""
import re
from pathlib import Path

import yaml

SOURCES_PATH = Path("/opt/airflow/extract/sources.yml")

_REQUIRED = {"conn", "table", "mode", "target", "schedule", "expected_columns"}
_MODES = {"snapshot", "watermark"}
_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
_RELATION = re.compile(r"^[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*$")
_COLUMN = re.compile(r"^[a-z_][a-z0-9_]*$")


def load_sources() -> dict:
    cfg = yaml.safe_load(SOURCES_PATH.read_text(encoding="utf-8")) or {}
    for name, src in cfg.items():
        missing = _REQUIRED - set(src)
        if missing:
            raise ValueError(f"sources.yml [{name}]: 필수 키 누락 {sorted(missing)}")
        if not _NAME.match(name):
            raise ValueError(f"sources.yml [{name}]: 소스 이름은 소문자 스네이크만")
        if src["mode"] not in _MODES:
            raise ValueError(f"sources.yml [{name}]: mode 는 {_MODES} 중 하나")
        for key in ("table", "target"):
            if not _RELATION.match(src[key]):
                raise ValueError(f"sources.yml [{name}]: {key} 형식 위반 ({src[key]!r})")
        for col in src["expected_columns"] + src.get("select_columns", []):
            if not _COLUMN.match(col):
                raise ValueError(f"sources.yml [{name}]: 컬럼명 형식 위반 ({col!r})")
    return cfg


def asset_uri(target: str) -> str:
    """bronze 테이블 → Asset URI (extract 발행 = Manager 구독, 규칙은 design/10)."""
    schema, table = target.split(".")
    return f"postgresql://warehouse/pcs_wh/{schema}/{table}"
