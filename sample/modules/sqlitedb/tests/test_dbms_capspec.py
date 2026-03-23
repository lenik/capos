"""sqlitedb implementation vs sample/caps/dbms.* CapSpecs."""

from __future__ import annotations

from pathlib import Path

import pytest

from sqlitedb.impl import SqliteDbBackend
from utils.captest.runner import run_capability_cases

REPO = Path(__file__).resolve().parents[4]


@pytest.fixture()
def sqlite_env(tmp_path: Path) -> dict[str, str]:
    return {"CAP_SQLITEDB_PATH": str(tmp_path / "t.db")}


def test_dbms_query_capspec(sqlite_env: dict[str, str]) -> None:
    db = SqliteDbBackend(sqlite_env)
    fails = run_capability_cases(
        REPO / "sample" / "caps" / "dbms.query",
        db.invoke,
        capability_name="dbms.query",
    )
    assert not fails, "\n".join(fails)


def test_dbms_update_capspec(sqlite_env: dict[str, str]) -> None:
    db = SqliteDbBackend(sqlite_env)
    fails = run_capability_cases(
        REPO / "sample" / "caps" / "dbms.update",
        db.invoke,
        capability_name="dbms.update",
    )
    assert not fails, "\n".join(fails)
