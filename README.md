# cap — Capability OS, CapSpecs, ModuleSpecs, and memcos

This repository is a **specification and reference workspace** for a **capability operating system (Cap OS, COS)** idea: a runtime that **discovers** standardized **capabilities**, **routes** `invoke(capability, request)` to implementations, **assembles** modules, and may emit **platform lifecycle** events (`module.installed`, …). A production COS can be multi-process, multi-language (e.g. JVM JARs, native `.so`); this repo focuses on contracts, samples, and a tiny in-memory COS.

## Concepts (how they fit together)

| Concept | What it is | Where it lives in this repo |
|--------|------------|------------------------------|
| **Cap OS (COS)** | Abstract platform: capability registry, routing, module lifecycle, optional event bus. *Not* one installable binary here—**behaviour** you implement in a real deployment. | Described in prose in [`spec.md`](spec.md) and [`spec/memcos.md`](spec/memcos.md); illustrated by **memcos**. |
| **CapSpec** | Contract for **one** capability: name, version, type, signature (schemas), semantics, i18n `title` / `summary`, examples, contract tests. | [`spec.md`](spec.md), [`schemas/capspec.schema.json`](schemas/capspec.schema.json), packaged trees under [`sample/caps/<name>/`](sample/caps/). |
| **ModuleSpec** | Manifest for **one** implementation **module**: id, version, **`implements`** (which capability names it provides), **`requiresCapabilities`** (what it calls via the platform), runtime hints, optional lifecycle flags. | [`spec/modulespec.md`](spec/modulespec.md), [`schemas/modulespec.schema.json`](schemas/modulespec.schema.json), e.g. [`sample/modules/contactbook/modulespec.json`](sample/modules/contactbook/modulespec.json). |
| **memcos** | **Memory Capability OS** — a **minimal, in-process** reference COS for development and tests: `MemCOS.invoke`, module **install/remove/upgrade** hooks, **EventBus**, and the same lifecycle event names a full COS might emit. | Python package [`memcos/`](memcos/), normative text [`spec/memcos.md`](spec/memcos.md), [`memcos/README.md`](memcos/README.md). |

**Flow in one sentence:** a **module** (described by a **ModuleSpec**) **implements** one or more **CapSpecs**; the **COS** routes callers to the right implementation; **memcos** is a small COS you can run in tests without a real cluster.

## Documentation index

| Document | Purpose |
|----------|---------|
| [`spec.md`](spec.md) | Capability Description Specification (CapSpec details) |
| [`spec/modulespec.md`](spec/modulespec.md) | ModuleSpec field guide |
| [`spec/memcos.md`](spec/memcos.md) | memcos behaviour and limits |
| [`schemas/capspec.schema.json`](schemas/capspec.schema.json) | JSON Schema for `capability.json` |
| [`schemas/modulespec.schema.json`](schemas/modulespec.schema.json) | JSON Schema for `modulespec.json` |

## Repository layout

| Path | Role |
|------|------|
| `sample/caps/` | Packaged CapSpecs (`capability.json`, schemas, examples, contract tests) |
| `sample/caps/registry.json` | Sample capability registry |
| `sample/modules/` | Reference modules (ModuleSpec + code), e.g. `contactbook`, `sqlitedb`, `chatapp` |
| `memcos/` | Reference COS implementation (Python) |
| `utils/` | `caplint`, `captest` |
| `scripts/` | Generators, validators, [`scripts/data/capability_i18n.json`](scripts/data/capability_i18n.json) |

## Quick checks (from repo root)

```bash
python3 utils/caplint.py
python3 scripts/validate_capspecs.py
python3 scripts/validate_examples.py
```

## Tests

```bash
PYTHONPATH=. python3 -m pytest sample/modules/contactbook/tests/ -q

PYTHONPATH=.:sample/modules/chatapp:sample/modules/sqlitedb:sample/modules/contactbook \
  python3 -m pytest memcos/tests/ sample/modules/chatapp/tests/ -q
```

(`sample/modules/chatapp/web/` needs `npm install` for chatweb / Vitest integration tests.)

## More READMEs

- [`memcos/README.md`](memcos/README.md) — MemCOS API and tests  
- [`sample/modules/chatapp/README.md`](sample/modules/chatapp/README.md) — chatapp module (session mgr + Vue)
