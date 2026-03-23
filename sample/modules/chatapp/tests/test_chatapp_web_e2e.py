"""Start MemCOS + HTTP server, then run chatweb Vitest integration (TypeScript MVVM, real fetch)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path

import pytest

from chatapp.http_server import serve
from chatapp.impl import ChatSessionMgr, build_contact_handlers
from contactbook.cap_impl import ContactBookAdapter
from memcos import MemCOS
from sqlitedb.impl import build_handlers as build_sqlitedb_handlers

REPO = Path(__file__).resolve().parents[4]
WEB = REPO / "sample" / "modules" / "chatapp" / "web"


def _load_spec(rel: str) -> dict:
    return json.loads((REPO / rel).read_text(encoding="utf-8"))


@pytest.mark.skipif(shutil.which("npm") is None, reason="npm not installed")
def test_memcos_chatapp_http_then_vitest_integration(tmp_path: Path) -> None:
    if not (WEB / "node_modules").is_dir():
        pytest.skip("run: cd sample/modules/chatapp/web && npm install")

    db_path = tmp_path / "chat.sqlite"
    env_py = {"CAP_SQLITEDB_PATH": str(db_path)}
    cos = MemCOS(environment=env_py)
    cos.install_module(_load_spec("sample/modules/sqlitedb/modulespec.json"), build_sqlitedb_handlers(env_py))
    adapter = ContactBookAdapter.with_demo_data()
    cos.install_module(_load_spec("sample/modules/contactbook/modulespec.json"), build_contact_handlers(adapter))
    mgr = ChatSessionMgr(cos)
    cos.install_module(
        _load_spec("sample/modules/chatapp/modulespec.json"),
        {"chat.ui": mgr.handle},
        lifecycle=mgr.on_lifecycle,
    )

    httpd = serve(mgr.handle, host="127.0.0.1", port=0, static_root=None)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.05)
    _, port = httpd.server_address
    base = f"http://127.0.0.1:{port}"
    try:
        env = {**os.environ, "CHATAPP_TEST_URL": base}
        r = subprocess.run(
            ["npm", "exec", "--", "vitest", "run", "tests/chatUi.integration.spec.ts"],
            cwd=WEB,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if r.returncode != 0:
            pytest.fail(f"vitest failed:\n{r.stdout}\n{r.stderr}")
    finally:
        httpd.shutdown()
        thread.join(timeout=2)
