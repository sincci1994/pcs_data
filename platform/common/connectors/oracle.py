"""Oracle 커넥터 — thin/thick 양쪽 지원.

두 가지 생성 경로:
  1) from_airflow_conn("oracle_pcs"): Airflow OracleHook 래핑.
     현 파이프라인 동작을 '바이트 동일'로 보존(기존 oracle_etl 이 쓰던 hook.run/get_first 그대로).
  2) from_settings(...): oracledb 직접 연결. driver_mode="thick" 시 init_oracle_client(lib_dir)
     호출 → 버전 상이한 실타깃 Oracle(Thick 모드 필수) 경로. 폐쇄망에선 Instant Client 를
     이미지에 베이크해야 한다(런타임 다운로드 불가).
"""
from __future__ import annotations

from typing import Any, Iterable, Literal, Sequence

from .base import AbstractConnector, Params

DriverMode = Literal["thin", "thick"]

_THICK_INITIALIZED = False


class OracleConnector(AbstractConnector):
    name = "oracle"

    def __init__(
        self,
        *,
        hook: Any | None = None,
        dsn: str | None = None,
        user: str | None = None,
        password: str | None = None,
        driver_mode: DriverMode = "thin",
        lib_dir: str | None = None,
    ) -> None:
        self._hook = hook
        self._dsn = dsn
        self._user = user
        self._password = password
        self._driver_mode = driver_mode
        self._lib_dir = lib_dir
        self._conn = None  # oracledb Connection (direct 경로에서만)

    # ---------------------------------------------------------------- factory
    @classmethod
    def from_airflow_conn(cls, conn_id: str = "oracle_pcs") -> "OracleConnector":
        """Airflow OracleHook 을 래핑(현 운영 경로). thin 모드는 env 로 강제됨."""
        from airflow.providers.oracle.hooks.oracle import OracleHook

        return cls(hook=OracleHook(oracle_conn_id=conn_id))

    @classmethod
    def from_settings(
        cls,
        *,
        dsn: str,
        user: str,
        password: str,
        driver_mode: DriverMode = "thin",
        lib_dir: str | None = None,
    ) -> "OracleConnector":
        """oracledb 직접 연결(실타깃 Oracle/Thick 경로)."""
        return cls(
            dsn=dsn,
            user=user,
            password=password,
            driver_mode=driver_mode,
            lib_dir=lib_dir,
        )

    # ------------------------------------------------------------- lifecycle
    def connect(self) -> "OracleConnector":
        if self._hook is not None:
            return self  # hook 은 매 호출 시 자체적으로 연결을 관리
        global _THICK_INITIALIZED
        import oracledb

        if self._driver_mode == "thick" and not _THICK_INITIALIZED:
            oracledb.init_oracle_client(lib_dir=self._lib_dir)
            _THICK_INITIALIZED = True
        self._conn = oracledb.connect(
            user=self._user, password=self._password, dsn=self._dsn
        )
        return self

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # ------------------------------------------------------------- execution
    def execute(self, sql: str, params: Params = None) -> None:
        if self._hook is not None:
            self._hook.run(sql, parameters=params)
            return
        cur = self._require_conn().cursor()
        cur.execute(sql, params or [])
        self._conn.commit()

    def fetch_one(self, sql: str, params: Params = None) -> tuple | None:
        if self._hook is not None:
            return self._hook.get_first(sql, parameters=params)
        cur = self._require_conn().cursor()
        cur.execute(sql, params or [])
        return cur.fetchone()

    def fetch_all(self, sql: str, params: Params = None) -> list[tuple]:
        if self._hook is not None:
            return self._hook.get_records(sql, parameters=params)
        cur = self._require_conn().cursor()
        cur.execute(sql, params or [])
        return cur.fetchall()

    def bulk_insert(
        self, table: str, columns: Sequence[str], rows: Iterable[Sequence[Any]]
    ) -> int:
        cols = ", ".join(columns)
        binds = ", ".join(f":{i + 1}" for i in range(len(columns)))
        sql = f"INSERT INTO {table} ({cols}) VALUES ({binds})"
        data = list(rows)
        if self._hook is not None:
            self._hook.insert_rows(table=table, rows=data, target_fields=list(columns))
            return len(data)
        cur = self._require_conn().cursor()
        cur.executemany(sql, data)
        self._conn.commit()
        return len(data)

    def truncate(self, table: str) -> None:
        self.execute(f"TRUNCATE TABLE {table}")

    # ----------------------------------------------------------------- utils
    def _require_conn(self):
        if self._conn is None:
            self.connect()
        return self._conn
