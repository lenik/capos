from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

# Platform → module lifecycle (spec/memcos.md §3)
PLATFORM_LIFECYCLE_EVENTS: tuple[str, ...] = (
    "module.preinstall",
    "module.installed",
    "module.preremove",
    "module.removed",
    "module.preupgrade",
    "module.upgraded",
)

LifecycleFn = Callable[[str, Mapping[str, Any]], None]
CapabilityFn = Callable[[Mapping[str, Any]], Mapping[str, Any]]


class EventBus:
    """Simple synchronous pub/sub."""

    def __init__(self) -> None:
        self._subs: list[tuple[str | None, LifecycleFn]] = []

    def subscribe(self, event_name: str | None, fn: LifecycleFn) -> None:
        """Subscribe to one event name, or None as wildcard (all events)."""
        self._subs.append((event_name, fn))

    def publish(self, event_name: str, payload: Mapping[str, Any]) -> None:
        for pattern, fn in self._subs:
            if pattern is None or pattern == event_name:
                fn(event_name, payload)


class MemCOS:
    """In-memory capability registry with routing and module lifecycle."""

    def __init__(self, environment: Mapping[str, str] | None = None) -> None:
        self.environment: dict[str, str] = dict(environment or {})
        self.bus = EventBus()
        self._handlers: dict[str, CapabilityFn] = {}
        self._owner: dict[str, str] = {}

    def _lifecycle_payload(
        self,
        module_id: str,
        version: str,
        *,
        previous_version: str | None,
    ) -> dict[str, Any]:
        return {
            "moduleId": module_id,
            "version": version,
            "previousVersion": previous_version,
        }

    def _emit_platform_lifecycle(
        self,
        event_name: str,
        payload: Mapping[str, Any],
        *,
        lifecycle: LifecycleFn | None,
        handles_platform_lifecycle: bool,
    ) -> None:
        self.bus.publish(event_name, payload)
        if handles_platform_lifecycle and lifecycle is not None:
            lifecycle(event_name, payload)

    def invoke(self, capability_name: str, request: Mapping[str, Any]) -> Mapping[str, Any]:
        fn = self._handlers.get(capability_name)
        if fn is None:
            raise KeyError(f"No handler registered for capability {capability_name!r}")
        return fn(request)

    def register_capability(
        self,
        capability_name: str,
        fn: CapabilityFn,
        *,
        module_id: str,
        overwrite: bool = False,
    ) -> None:
        if not overwrite and capability_name in self._handlers:
            raise ValueError(
                f"Capability {capability_name!r} already registered by {self._owner.get(capability_name)}"
            )
        self._handlers[capability_name] = fn
        self._owner[capability_name] = module_id

    def unregister_module_capabilities(self, module_id: str) -> None:
        to_drop = [c for c, mid in self._owner.items() if mid == module_id]
        for c in to_drop:
            del self._handlers[c]
            del self._owner[c]

    def install_module(
        self,
        modulespec: Mapping[str, Any],
        handlers: Mapping[str, CapabilityFn],
        *,
        lifecycle: LifecycleFn | None = None,
    ) -> None:
        mod = modulespec["module"]
        mid: str = mod["id"]
        ver: str = mod["version"]
        handles = bool(mod.get("lifecycle", {}).get("handlesPlatformLifecycle"))
        pre = self._lifecycle_payload(mid, ver, previous_version=None)

        self._emit_platform_lifecycle(
            "module.preinstall",
            pre,
            lifecycle=lifecycle,
            handles_platform_lifecycle=handles,
        )
        for cap, fn in handlers.items():
            self.register_capability(cap, fn, module_id=mid, overwrite=True)
        self._emit_platform_lifecycle(
            "module.installed",
            pre,
            lifecycle=lifecycle,
            handles_platform_lifecycle=handles,
        )

    def remove_module(
        self,
        modulespec: Mapping[str, Any],
        *,
        lifecycle: LifecycleFn | None = None,
    ) -> None:
        mod = modulespec["module"]
        mid: str = mod["id"]
        ver: str = mod["version"]
        handles = bool(mod.get("lifecycle", {}).get("handlesPlatformLifecycle"))
        pre = self._lifecycle_payload(mid, ver, previous_version=None)

        self._emit_platform_lifecycle(
            "module.preremove",
            pre,
            lifecycle=lifecycle,
            handles_platform_lifecycle=handles,
        )
        self.unregister_module_capabilities(mid)
        self._emit_platform_lifecycle(
            "module.removed",
            pre,
            lifecycle=lifecycle,
            handles_platform_lifecycle=handles,
        )

    def upgrade_module(
        self,
        modulespec: Mapping[str, Any],
        handlers: Mapping[str, CapabilityFn],
        *,
        previous_version: str,
        lifecycle: LifecycleFn | None = None,
    ) -> None:
        mod = modulespec["module"]
        mid: str = mod["id"]
        ver: str = mod["version"]
        handles = bool(mod.get("lifecycle", {}).get("handlesPlatformLifecycle"))
        pre = self._lifecycle_payload(mid, ver, previous_version=previous_version)

        self._emit_platform_lifecycle(
            "module.preupgrade",
            pre,
            lifecycle=lifecycle,
            handles_platform_lifecycle=handles,
        )
        for cap, fn in handlers.items():
            self.register_capability(cap, fn, module_id=mid, overwrite=True)
        self._emit_platform_lifecycle(
            "module.upgraded",
            pre,
            lifecycle=lifecycle,
            handles_platform_lifecycle=handles,
        )
