"""Memory Capability OS — in-memory capability registry, routing, and lifecycle (see spec/memcos.md)."""

from memcos.runtime import (
    PLATFORM_LIFECYCLE_EVENTS,
    EventBus,
    MemCOS,
)

__all__ = [
    "PLATFORM_LIFECYCLE_EVENTS",
    "EventBus",
    "MemCOS",
]
