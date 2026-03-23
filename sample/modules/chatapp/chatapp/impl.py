"""chatapp module facade: MemCOS registration + contact.* handler helpers.

Core session logic lives in ``chatsessionmgr``; the Vue frontend lives in ``web/`` (chatweb).
"""

from __future__ import annotations

from typing import Any

from chatsessionmgr.session import ChatSessionMgr

# Backward-compatible name used in modulespec / tests
ChatApp = ChatSessionMgr

CONTACT_CAPS = (
    "contact.create",
    "contact.get",
    "contact.update",
    "contact.delete",
    "contact.search",
)


def build_contact_handlers(adapter: Any) -> dict[str, Any]:
    """Register one handler per contact.* capability for MemCOS."""

    def make_invoke(cap: str):
        def _fn(req: dict[str, Any]) -> dict[str, Any]:
            return adapter.invoke(cap, req)

        return _fn

    return {cap: make_invoke(cap) for cap in CONTACT_CAPS}


def chat_ui_handler(app: ChatSessionMgr, request: dict[str, Any]) -> dict[str, Any]:
    return app.handle(request)
