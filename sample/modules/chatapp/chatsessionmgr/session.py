"""Chat session manager — backend half of chatapp (chatweb is the Vue frontend)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from utils.captest.runner import CapError


class ChatSessionMgr:
    """Implements chat.ui via platform routing (contact.*, dbms.*). Used by MemCOS and by HTTP workers."""

    def __init__(self, cos: Any) -> None:
        self._cos = cos
        self._last_session_id: str | None = None
        self._schema_ready = False

    def on_lifecycle(self, event_name: str, payload: dict[str, Any]) -> None:
        if event_name == "module.installed" and payload.get("moduleId") == "chatapp":
            self.ensure_schema()

    def ensure_schema(self) -> None:
        if self._schema_ready:
            return
        ddl_sessions = """
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            contact_id TEXT NOT NULL,
            context_kind TEXT,
            entity_id TEXT,
            created_at TEXT NOT NULL
        )
        """.strip()
        ddl_messages = """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            body TEXT NOT NULL,
            direction TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """.strip()
        self._cos.invoke("dbms.update", {"sql": ddl_sessions, "parameters": {}})
        self._cos.invoke("dbms.update", {"sql": ddl_messages, "parameters": {}})
        self._schema_ready = True

    def handle(self, request: dict[str, Any]) -> dict[str, Any]:
        self.ensure_schema()
        cmd = request.get("command")
        params = request.get("params") or {}
        if cmd == "chat.openWindow":
            return self._open_window(request, params)
        if cmd == "chat.sendMessage":
            return self._send_message(request, params)
        if cmd == "chat.refreshThread":
            return self._refresh(request, params)
        raise CapError("INVALID_REQUEST", f"unknown command {cmd!r}")

    def _now(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    def _title(self, ctx: dict[str, Any], contact: dict[str, Any]) -> str:
        kind = (ctx.get("kind") or "chat") if isinstance(ctx, dict) else "chat"
        name = contact.get("displayName") or contact.get("contactId") or "?"
        return f"{kind} — {name}"

    def _peer(self, contact: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {
            "contactId": contact["contactId"],
            "displayName": contact["displayName"],
        }
        for k in ("email", "phone", "companyName", "tags", "version"):
            if k in contact and contact[k] is not None:
                out[k] = contact[k]
        return out

    def _load_messages(self, session_id: str) -> list[dict[str, Any]]:
        q = """
        SELECT id AS messageId, body, direction, created_at AS createdAt
        FROM chat_messages
        WHERE session_id = :sid
        ORDER BY created_at
        """
        res = self._cos.invoke(
            "dbms.query",
            {"sql": q.strip(), "parameters": {"sid": session_id}},
        )
        rows = res.get("rows") or []
        out: list[dict[str, Any]] = []
        for r in rows:
            out.append(
                {
                    "messageId": str(r.get("messageId")),
                    "body": str(r.get("body") or ""),
                    "direction": str(r.get("direction") or "outbound"),
                    "createdAt": str(r.get("createdAt") or ""),
                }
            )
        return out

    def _open_window(self, request: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
        pid = (params.get("primaryContactId") or "").strip()
        if not pid:
            raise CapError("INVALID_REQUEST", "primaryContactId is required")
        ctx = params.get("context") if isinstance(params.get("context"), dict) else {}
        contact = self._cos.invoke("contact.get", {"contactId": pid})

        sid = str(uuid.uuid4())
        now = self._now()
        self._cos.invoke(
            "dbms.update",
            {
                "sql": """
                INSERT INTO chat_sessions (id, contact_id, context_kind, entity_id, created_at)
                VALUES (:id, :cid, :ck, :eid, :ca)
                """.strip(),
                "parameters": {
                    "id": sid,
                    "cid": pid,
                    "ck": ctx.get("kind"),
                    "eid": ctx.get("entityId"),
                    "ca": now,
                },
            },
        )
        self._last_session_id = sid
        msgs = self._load_messages(sid)
        return {
            "viewModel": {
                "windowId": sid,
                "sessionId": sid,
                "title": self._title(ctx, contact),
                "context": ctx,
                "peerContact": self._peer(contact),
                "messages": msgs,
            },
            "lastResult": {"ok": True},
        }

    def _session_id(self, request: dict[str, Any]) -> str:
        sid = (request.get("sessionId") or self._last_session_id or "").strip()
        if not sid:
            raise CapError("INVALID_REQUEST", "sessionId is required (or run chat.openWindow first)")
        return sid

    def _send_message(self, request: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
        sid = self._session_id(request)
        text = (params.get("text") or "").strip()
        if not text:
            raise CapError("INVALID_REQUEST", "text is required")
        mid = str(uuid.uuid4())
        now = self._now()
        self._cos.invoke(
            "dbms.update",
            {
                "sql": """
                INSERT INTO chat_messages (id, session_id, body, direction, created_at)
                VALUES (:id, :sid, :body, :dir, :ca)
                """.strip(),
                "parameters": {
                    "id": mid,
                    "sid": sid,
                    "body": text,
                    "dir": "outbound",
                    "ca": now,
                },
            },
        )
        self._last_session_id = sid
        row = self._cos.invoke(
            "dbms.query",
            {
                "sql": "SELECT contact_id FROM chat_sessions WHERE id = :id",
                "parameters": {"id": sid},
            },
        )
        rows = row.get("rows") or []
        if not rows:
            raise CapError("NOT_FOUND", "session not found")
        cid = str(rows[0].get("contact_id"))
        contact = self._cos.invoke("contact.get", {"contactId": cid})
        ctx_q = self._cos.invoke(
            "dbms.query",
            {
                "sql": "SELECT context_kind, entity_id FROM chat_sessions WHERE id = :id",
                "parameters": {"id": sid},
            },
        )
        cr = (ctx_q.get("rows") or [{}])[0]
        ctx = {}
        if cr.get("context_kind"):
            ctx["kind"] = cr.get("context_kind")
        if cr.get("entity_id"):
            ctx["entityId"] = cr.get("entity_id")
        msgs = self._load_messages(sid)
        return {
            "viewModel": {
                "windowId": sid,
                "sessionId": sid,
                "title": self._title(ctx, contact),
                "context": ctx,
                "peerContact": self._peer(contact),
                "messages": msgs,
            },
            "lastResult": {"ok": True, "detail": "message sent"},
        }

    def _refresh(self, request: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
        sid = self._session_id(request)
        row = self._cos.invoke(
            "dbms.query",
            {
                "sql": "SELECT contact_id, context_kind, entity_id FROM chat_sessions WHERE id = :id",
                "parameters": {"id": sid},
            },
        )
        rows = row.get("rows") or []
        if not rows:
            raise CapError("NOT_FOUND", "session not found")
        r0 = rows[0]
        cid = str(r0.get("contact_id"))
        contact = self._cos.invoke("contact.get", {"contactId": cid})
        ctx: dict[str, Any] = {}
        if r0.get("context_kind"):
            ctx["kind"] = r0.get("context_kind")
        if r0.get("entity_id"):
            ctx["entityId"] = r0.get("entity_id")
        msgs = self._load_messages(sid)
        return {
            "viewModel": {
                "windowId": sid,
                "sessionId": sid,
                "title": self._title(ctx, contact),
                "context": ctx,
                "peerContact": self._peer(contact),
                "messages": msgs,
            },
            "lastResult": {"ok": True, "detail": "refreshed"},
        }
