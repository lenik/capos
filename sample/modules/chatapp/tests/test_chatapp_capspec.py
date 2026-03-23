"""chat.ui contract tests against a full MemCOS stack (headless commands)."""

from __future__ import annotations

import json
from pathlib import Path

from chatapp.impl import ChatSessionMgr, build_contact_handlers
from contactbook.cap_impl import ContactBookAdapter
from sqlitedb.impl import build_handlers as build_sqlitedb_handlers
from memcos import MemCOS
from utils.captest.runner import run_capability_cases

REPO = Path(__file__).resolve().parents[4]


def _load_modulespec(rel: str) -> dict:
    return json.loads((REPO / rel).read_text(encoding="utf-8"))


def _deploy(tmp_path) -> MemCOS:
    db_path = tmp_path / "c.db"
    env = {"CAP_SQLITEDB_PATH": str(db_path)}
    cos = MemCOS(environment=env)
    cos.install_module(
        _load_modulespec("sample/modules/sqlitedb/modulespec.json"),
        build_sqlitedb_handlers(env),
    )
    adapter = ContactBookAdapter.with_demo_data()
    cos.install_module(
        _load_modulespec("sample/modules/contactbook/modulespec.json"),
        build_contact_handlers(adapter),
    )
    app = ChatSessionMgr(cos)
    cos.install_module(
        _load_modulespec("sample/modules/chatapp/modulespec.json"),
        {"chat.ui": app.handle},
        lifecycle=app.on_lifecycle,
    )
    return cos


def test_chat_ui_contract_cases(tmp_path) -> None:
    cos = _deploy(tmp_path)

    def invoke(cap: str, req: dict) -> dict:
        return cos.invoke(cap, req)

    fails = run_capability_cases(
        REPO / "sample/caps/chat.ui",
        invoke,
        capability_name="chat.ui",
    )
    assert not fails, "\n".join(fails)
