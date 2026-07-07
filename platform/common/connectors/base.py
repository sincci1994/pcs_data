"""스토리지 커넥터 추상 — 물리 엔진(Oracle/Postgres/S3) 위의 통일된 read/write 표면.

멀티엔진 전략의 린치핀. 현재는 Oracle 만 구현되어 있고 Postgres/S3 는 스텁이다.
Airflow 파싱 시점에 LLM 이 개입하지 않는 '결정론적 제어평면'의 일부다.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable, Mapping, Protocol, Sequence, runtime_checkable

Params = Sequence[Any] | Mapping[str, Any] | None


@runtime_checkable
class StorageConnector(Protocol):
    """관계형 엔진에 대한 최소 공통 실행 표면."""

    name: str

    def execute(self, sql: str, params: Params = None) -> None: ...
    def fetch_one(self, sql: str, params: Params = None) -> tuple | None: ...
    def fetch_all(self, sql: str, params: Params = None) -> list[tuple]: ...
    def bulk_insert(
        self, table: str, columns: Sequence[str], rows: Iterable[Sequence[Any]]
    ) -> int: ...
    def truncate(self, table: str) -> None: ...


class AbstractConnector(ABC):
    """연결 수명주기 + 컨텍스트 매니저. 구체 커넥터가 connect/close 를 구현한다."""

    name: str = "abstract"

    @abstractmethod
    def connect(self) -> "AbstractConnector": ...

    @abstractmethod
    def close(self) -> None: ...

    def __enter__(self) -> "AbstractConnector":
        return self.connect()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
