"""PostgreSQL implementation of dbms.query and dbms.update (requires psycopg)."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from typing import Any

from utils.captest.runner import CapError


def _pg_url(env: Mapping[str, str]) -> str:
    u = env.get("CAP_POSTGRESDB_URL") or env.get("DATABASE_URL") or env.get("POSTGRESDB_URL")
    if not u:
        raise CapError("CONFIG_MISSING", "Set CAP_POSTGRESDB_URL for postgresdb")
    return u


def _to_psycopg_sql(sql: str) -> str:
    """Map SQLite-style :name placeholders to psycopg %(name)s."""
    return re.sub(r":([a-zA-Z_][a-zA-Z0-9_]*)", r"%(\1)s", sql)


def _is_read_sql(sql: str) -> bool:
    s = sql.strip()
    if not s:
        return False
    u = s.upper()
    return u.startswith("SELECT") or u.startswith("WITH")


class PostgresDbBackend:
    def __init__(self, env: Mapping[str, str]) -> None:
        self._url = _pg_url(env)
        self._conn = None

    def _connect(self):
        if self._conn is None:
            try:
                import psycopg
            except ImportError as e:
                raise CapError(
                    "NOT_AVAILABLE",
                    "postgresdb requires the psycopg package (pip install psycopg[binary])",
                ) from e
            self._conn = psycopg.connect(self._url)
        return self._conn

    def query(self, req: Mapping[str, Any]) -> dict[str, Any]:
        if not _is_read_sql(req.get("sql") or ""):
            raise CapError("INVALID_REQUEST", "dbms.query allows SELECT / WITH only")
        sql = _to_psycopg_sql((req.get("sql") or "").strip())
        params = dict(req.get("parameters") or {})
        max_rows = int(req.get("maxRows") or 1000)
        cx = self._connect()
        try:
            with cx.cursor() as cur:
                cur.execute(sql, params)
                cols = [d.name for d in cur.description] if cur.description else []
                rows_raw = cur.fetchmany(max_rows + 1)
        except Exception as e:
            raise CapError("INVALID_REQUEST", str(e)) from e
        truncated = len(rows_raw) > max_rows
        if truncated:
            rows_raw = rows_raw[:max_rows]
        rows = []
        for r in rows_raw:
            rows.append(dict(zip(cols, r)))
        return {"columns": cols, "rows": rows, "truncated": truncated}

    def update(self, req: Mapping[str, Any]) -> dict[str, Any]:
        sql_raw = (req.get("sql") or "").strip()
        if not sql_raw:
            raise CapError("INVALID_REQUEST", "sql is required")
        if _is_read_sql(sql_raw):
            raise CapError("INVALID_REQUEST", "dbms.update does not execute SELECT; use dbms.query")
        sql = _to_psycopg_sql(sql_raw)
        params = dict(req.get("parameters") or {})
        cx = self._connect()
        try:
            with cx.cursor() as cur:
                cur.execute(sql, params)
                n = cur.rowcount
            cx.commit()
        except Exception as e:
            raise CapError("INVALID_REQUEST", str(e)) from e
        return {"affectedRows": n if n is not None and n >= 0 else 0}

    def invoke(self, capability_name: str, request: dict[str, Any]) -> dict[str, Any]:
        if capability_name == "dbms.query":
            return self.query(request)
        if capability_name == "dbms.update":
            return self.update(request)
        raise CapError("INVALID_REQUEST", f"unknown capability {capability_name}")


def build_handlers(env: Mapping[str, str]) -> dict[str, Callable[[Mapping[str, Any]], Mapping[str, Any]]]:
    db = PostgresDbBackend(env)

    def q(req: Mapping[str, Any]) -> Mapping[str, Any]:
        return db.query(req)

    def u(req: Mapping[str, Any]) -> Mapping[str, Any]:
        return db.update(req)

    return {"dbms.query": q, "dbms.update": u}
