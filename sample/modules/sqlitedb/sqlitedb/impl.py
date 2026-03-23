"""SQLite implementation of dbms.query and dbms.update."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Mapping
from typing import Any

from utils.captest.runner import CapError


def _db_path(env: Mapping[str, str]) -> str:
    p = env.get("CAP_SQLITEDB_PATH") or env.get("SQLITEDB_PATH")
    if not p:
        raise CapError("CONFIG_MISSING", "Set CAP_SQLITEDB_PATH for sqlitedb")
    return p


def _is_read_sql(sql: str) -> bool:
    s = sql.strip()
    if not s:
        return False
    u = s.upper()
    return u.startswith("SELECT") or u.startswith("WITH")


def _is_mutation_sql(sql: str) -> bool:
    s = sql.strip()
    if not s:
        return False
    return not _is_read_sql(s)


class SqliteDbBackend:
    """One connection per backend instance (captest / memcos adapter lifetime)."""

    def __init__(self, env: Mapping[str, str]) -> None:
        self._path = _db_path(env)
        self._conn: sqlite3.Connection | None = None

    def _cx(self) -> sqlite3.Connection:
        if self._conn is None:
            # Allow use from worker threads (e.g. chatapp HTTP server + MemCOS).
            self._conn = sqlite3.connect(self._path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def query(self, req: Mapping[str, Any]) -> dict[str, Any]:
        sql = (req.get("sql") or "").strip()
        if not _is_read_sql(sql):
            raise CapError("INVALID_REQUEST", "dbms.query allows SELECT / WITH only")
        params = dict(req.get("parameters") or {})
        max_rows = int(req.get("maxRows") or 1000)
        cx = self._cx()
        try:
            cur = cx.execute(sql, params)
        except sqlite3.Error as e:
            raise CapError("INVALID_REQUEST", str(e)) from e
        rows_raw = cur.fetchmany(max_rows + 1)
        truncated = len(rows_raw) > max_rows
        if truncated:
            rows_raw = rows_raw[:max_rows]
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = []
        for r in rows_raw:
            rows.append({cols[i]: r[i] for i in range(len(cols))})
        return {"columns": cols, "rows": rows, "truncated": truncated}

    def update(self, req: Mapping[str, Any]) -> dict[str, Any]:
        sql = (req.get("sql") or "").strip()
        if not sql:
            raise CapError("INVALID_REQUEST", "sql is required")
        if not _is_mutation_sql(sql):
            raise CapError("INVALID_REQUEST", "dbms.update does not execute SELECT; use dbms.query")
        params = dict(req.get("parameters") or {})
        cx = self._cx()
        try:
            cur = cx.execute(sql, params)
            cx.commit()
        except sqlite3.Error as e:
            raise CapError("INVALID_REQUEST", str(e)) from e
        out: dict[str, Any] = {"affectedRows": cur.rowcount if cur.rowcount >= 0 else 0}
        if cur.lastrowid is not None and cur.lastrowid > 0:
            out["lastInsertId"] = str(cur.lastrowid)
        return out

    def invoke(self, capability_name: str, request: dict[str, Any]) -> dict[str, Any]:
        if capability_name == "dbms.query":
            return self.query(request)
        if capability_name == "dbms.update":
            return self.update(request)
        raise CapError("INVALID_REQUEST", f"unknown capability {capability_name}")


def build_handlers(env: Mapping[str, str]) -> dict[str, Callable[[Mapping[str, Any]], Mapping[str, Any]]]:
    db = SqliteDbBackend(env)

    def q(req: Mapping[str, Any]) -> Mapping[str, Any]:
        return db.query(req)

    def u(req: Mapping[str, Any]) -> Mapping[str, Any]:
        return db.update(req)

    return {"dbms.query": q, "dbms.update": u}


def build_invoke(env: Mapping[str, str]) -> Callable[[str, dict[str, Any]], dict[str, Any]]:
    db = SqliteDbBackend(env)

    def invoke(capability_name: str, request: dict[str, Any]) -> dict[str, Any]:
        return db.invoke(capability_name, request)

    return invoke
