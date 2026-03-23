# cap — Capability Description Specification

This repository defines **CapSpecs** (callable capability contracts), sample capabilities under `sample/caps/`, reference **modules** under `sample/modules/`, and a minimal in-memory runtime (**memcos**) for routing and tests.

## Documentation

| Document | Purpose |
|----------|---------|
| [`spec.md`](spec.md) | Capability Description Specification (naming, signatures, tests, i18n `title` / `summary`) |
| [`spec/modulespec.md`](spec/modulespec.md) | Module metadata (`modulespec.json`) |
| [`spec/memcos.md`](spec/memcos.md) | Memory Capability OS behaviour |
| [`schemas/capspec.schema.json`](schemas/capspec.schema.json) | JSON Schema for `capability.json` |

## Layout

| Path | Role |
|------|------|
| `sample/caps/` | Packaged capabilities (`capability.json`, schemas, examples, contract tests) |
| `sample/caps/registry.json` | Sample registry of capability names |
| `sample/modules/` | Reference implementations (e.g. `contactbook`, `sqlitedb`, `chatapp`) |
| `memcos/` | Python: `MemCOS` registry, lifecycle events, event bus ([`memcos/README.md`](memcos/README.md)) |
| `utils/` | `caplint`, `captest` |
| `scripts/` | Generators (`generate_erp_modules.py`), validators, [`scripts/data/capability_i18n.json`](scripts/data/capability_i18n.json) for localized titles/summaries |

## Quick checks (from repo root)

```bash
python3 utils/caplint.py
python3 scripts/validate_capspecs.py
python3 scripts/validate_examples.py
```

## Tests

```bash
# CapSpec contract tests for a reference module (example)
PYTHONPATH=. python3 -m pytest sample/modules/contactbook/tests/ -q

# memcos + chatapp (Python); chatweb needs npm install under sample/modules/chatapp/web/
PYTHONPATH=.:sample/modules/chatapp:sample/modules/sqlitedb:sample/modules/contactbook \
  python3 -m pytest memcos/tests/ sample/modules/chatapp/tests/ -q
```

## Related READMEs

- [`memcos/README.md`](memcos/README.md) — MemCOS usage
- [`sample/modules/chatapp/README.md`](sample/modules/chatapp/README.md) — chatapp (chatsessionmgr + Vue chatweb)
