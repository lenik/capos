"""Deploy chatapp + contactbook + sqlitedb on MemCOS with env; headless chat.ui + lifecycle."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from chatapp.impl import ChatApp, build_contact_handlers
from contactbook.cap_impl import ContactBookAdapter
from sqlitedb.impl import build_handlers as build_sqlitedb_handlers
from memcos import MemCOS

REPO = Path(__file__).resolve().parents[4]


def _load_modulespec(rel: str) -> dict:
    return json.loads((REPO / rel).read_text(encoding="utf-8"))


def test_memcos_deploy_chatapp_sqlitedb_contactbook_headless_ui(tmp_path: Path) -> None:
    db_path = tmp_path / "chat.sqlite"
    env = {"CAP_SQLITEDB_PATH": str(db_path)}
    bus_events: list[str] = []

    def bus_tap(event_name: str, payload: object) -> None:
        bus_events.append(event_name)

    cos = MemCOS(environment=env)
    cos.bus.subscribe(None, bus_tap)

    cos.install_module(
        _load_modulespec("sample/modules/sqlitedb/modulespec.json"),
        build_sqlitedb_handlers(env),
    )
    adapter = ContactBookAdapter.with_demo_data()
    cos.install_module(
        _load_modulespec("sample/modules/contactbook/modulespec.json"),
        build_contact_handlers(adapter),
    )

    app = ChatApp(cos)
    cos.install_module(
        _load_modulespec("sample/modules/chatapp/modulespec.json"),
        {"chat.ui": app.handle},
        lifecycle=app.on_lifecycle,
    )

    assert bus_events.count("module.preinstall") == 3
    assert bus_events.count("module.installed") == 3
    assert "module.installed" in bus_events

    cx = sqlite3.connect(str(db_path))
    tables = {r[0] for r in cx.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "chat_sessions" in tables
    assert "chat_messages" in tables

    open_res = cos.invoke(
        "chat.ui",
        {
            "command": "chat.openWindow",
            "params": {
                "primaryContactId": "con-100",
                "context": {"kind": "supplier", "entityId": "sup-1"},
            },
        },
    )
    assert open_res["lastResult"]["ok"] is True
    assert open_res["viewModel"]["peerContact"]["contactId"] == "con-100"
    assert "supplier" in open_res["viewModel"]["title"].lower()

    send_res = cos.invoke(
        "chat.ui",
        {
            "command": "chat.sendMessage",
            "params": {"text": "Shipment ETA?"},
        },
    )
    assert send_res["lastResult"]["ok"] is True
    bodies = [m["body"] for m in send_res["viewModel"]["messages"]]
    assert "Shipment ETA?" in bodies

    refresh = cos.invoke(
        "chat.ui",
        {"command": "chat.refreshThread", "params": {}},
    )
    assert refresh["lastResult"]["ok"] is True
    assert len(refresh["viewModel"]["messages"]) >= 1


def test_chatapp_invokes_contact_not_raw_import() -> None:
    """Routing-only: session mgr must use cos.invoke for contact.get (no direct ContactBook import)."""
    import inspect

    from chatsessionmgr.session import ChatSessionMgr

    src = inspect.getsource(ChatSessionMgr._open_window)
    assert "ContactBook" not in src
    assert "invoke" in src
