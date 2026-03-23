"""Future: route chat.ui requests to a child process when the module runs out-of-process.

Full COS deployments may start each module as a separate OS process (or JVM for JARs,
or a shared library for .so). MemCOS currently runs Python handlers in-process only;
Java / native hosting is out of scope here until a management API exists.

This module is a placeholder for subprocess-based session routing.
"""

from __future__ import annotations

from typing import Any, Protocol


class CosInvoker(Protocol):
    def invoke(self, capability_name: str, request: dict[str, Any]) -> dict[str, Any]: ...


def route_session_stub(invoker: CosInvoker, capability_name: str, request: dict[str, Any]) -> dict[str, Any]:
    """Default: synchronous in-process invoke (same as MemCOS today)."""
    return invoker.invoke(capability_name, request)
