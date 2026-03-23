# memcos — Memory Capability OS (specification)

**memcos** is a **minimal in-memory** reference “capability operating system” for development and tests. It is **not** a production orchestrator; it models how a platform might:

- keep a **registry** of which module implements which capability;
- **route** `invoke(capabilityName, request)` to the registered handler;
- expose an **event bus** for **platform → module** lifecycle notifications and optional cross-module events;
- **assemble** modules in dependency order (basic form).

Implementations live under `util/memcos/` (Python). Other language ports should preserve the **behaviour** described here.

---

## 1. Goals

| Goal | Description |
|------|-------------|
| G1 | Register capability handlers and resolve them by name. |
| G2 | Install/remove modules atomically with defined lifecycle ordering. |
| G3 | Deliver **platform lifecycle events** to modules that opt in. |
| G4 | Support **routing** so a module can call `requiresCapabilities` without importing another module’s code directly. |

---

## 2. Core concepts

- **Capability handler** — Callable `handler(request: dict) -> dict` conforming to the CapSpec for that name (errors as exceptions or structured error; memcos Python API uses exceptions mapping to `{code, message}`).
- **Module** — Described by **ModuleSpec** (`modulespec.json`). On install, handlers for each `implements` entry are registered.
- **Router** — Resolves `capabilityName` → handler. If missing, `KeyError` / `ROUTING_UNAVAILABLE`.
- **Event bus** — Publish/subscribe strings `eventName` with `payload: dict`. Used for lifecycle and optional domain events.

---

## 3. Platform lifecycle events

When a module declares `module.lifecycle.handlesPlatformLifecycle: true`, the **platform** (here: memcos) **must** emit the following events in the defined phases. Handlers are **synchronous** in memcos; real platforms may use async queues.

| Event name | When | Typical module work |
|------------|------|---------------------|
| `module.preinstall` | Before handlers are registered | Validate config, reserve migrations lock |
| `module.installed` | After handlers are registered and module is active | Create tables, seed defaults |
| `module.preremove` | Before handlers are unregistered | Drain connections, stop consumers |
| `module.removed` | After handlers are removed | Drop temp resources (optional) |
| `module.preupgrade` | Before replacing handlers with new version | Expand-schema compatible migrations |
| `module.upgraded` | After new version active | Backfill, compact indexes |

**Payload shape (minimum):**

```json
{
  "moduleId": "<module id>",
  "version": "<semver or target version>",
  "previousVersion": "<semver|null>"
}
```

Events `module.preupgrade` / `module.upgraded` should include `previousVersion` when applicable.

**Delivery (memcos Python):** each lifecycle event is **published** on the shared **event bus** (so tests or observers can `subscribe`). If `handlesPlatformLifecycle` is true and a **lifecycle callback** is passed to `install_module` / `remove_module` / `upgrade_module`, memcos also invokes that callback with `(event_name, payload)` for each event in the sequence.

---

## 4. Install / remove / upgrade sequences

### Install

1. Emit `module.preinstall`.
2. Register all capability handlers for `implements`.
3. Emit `module.installed`.

### Remove

1. Emit `module.preremove`.
2. Unregister handlers for that module’s capabilities.
3. Emit `module.removed`.

### Upgrade (same module id, new version)

1. Emit `module.preupgrade` with `previousVersion`.
2. Replace handlers with new callables.
3. Emit `module.upgraded`.

---

## 5. Routing

- `invoke(capability_name, request)` uses the **single** registered handler for that name (last install wins if overlapping — **undefined** in production; memcos may warn).
- A module that **requires** `other.cap` must obtain it only via **router.invoke** (dependency injection style), not static imports of another implementation package.

---

## 6. Limitations (memcos)

- In-memory only; no persistence, no clustering.
- No authz; no network.
- Intended for **captest** integration and demos.

---

## 7. Versioning

This document is **memcos spec 1.0**. Breaking changes to event ordering or payload fields bump the major version.
