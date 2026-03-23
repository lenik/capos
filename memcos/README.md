# memcos — Memory Capability OS

Python reference implementation of the **memcos** specification (`spec/memcos.md`): an in-memory capability registry, **`invoke(capability, request)`** routing, synchronous **event bus**, and **module lifecycle** hooks (`module.installed`, …) for tests and demos.

## Layout

| Path | Role |
|------|------|
| `memcos/runtime.py` | `MemCOS`, `EventBus`, `PLATFORM_LIFECYCLE_EVENTS` |
| `memcos/tests/` | Pytest suite |
| `spec/memcos.md` | Normative behaviour and limitations |

## Usage

Run tests from the **repository root** with the project on `PYTHONPATH`:

```bash
cd /path/to/cap
PYTHONPATH=. python3 -m pytest memcos/tests/ -q
```

In code:

```python
from memcos import MemCOS

cos = MemCOS(environment={"CAP_SQLITEDB_PATH": "/tmp/app.db"})
cos.install_module(modulespec_dict, {"my.cap": handler_fn})
cos.invoke("my.cap", {"request": "payload"})
```

See `sample/modules/chatapp/tests/` for integration tests that deploy multiple modules on `MemCOS`.

For **HTTP + TypeScript MVVM** (chatweb Vitest against `POST /api/chat/ui` after the server starts), see `sample/modules/chatapp/README.md` and `tests/test_chatapp_web_e2e.py` (requires `npm install` under `sample/modules/chatapp/web/`).

## Related

- Capabilities: `sample/caps/`, `spec.md`
- Modules: `spec/modulespec.md`, `sample/modules/`
- Other tooling remains under `utils/` (e.g. caplint, captest).
