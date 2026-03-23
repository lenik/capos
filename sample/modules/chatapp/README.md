# chatapp module

`chatapp` combines two parts:

| Part | Role | Location |
|------|------|----------|
| **chatsessionmgr** | Backend: `chat.ui` command handling, DB via `dbms.*`, contacts via `contact.*` | `chatsessionmgr/` (Python) |
| **chatweb** | Frontend: Vue 3 + TypeScript, MVVM command layer, Vite dev/build | `web/` |

## Python layout

- `chatsessionmgr/session.py` — `ChatSessionMgr` (core logic).
- `chatapp/impl.py` — `ChatApp` alias + `build_contact_handlers` for MemCOS.
- `chatapp/http_server.py` — `POST /api/chat/ui` + static files from `web/dist` (URL routing for embedded UIs).
- `chatapp/subprocess_router.py` — stub for future **out-of-process** module routing (JAR / `.so` / subprocess). MemCOS does not implement Java hosting today.

## Frontend (chatweb)

```bash
cd sample/modules/chatapp/web
npm install
npm run dev          # Vite dev server; proxy /api → configurable backend
npm run build        # output web/dist for static hosting
npm run test         # Vitest: MVVM command unit tests (no DOM)
npm run test:integration  # requires CHATAPP_TEST_URL (set by pytest)
```

- **MVVM**: UI logic lives in `web/src/commands/chatCommands.ts` (same module imports in `App.vue` and tests).
- Tests use **TypeScript** only; they do **not** simulate mouse/keyboard — they call the same command builders as the Vue app.

## MemCOS + HTTP + Vitest

From repo root (after `npm install` in `web/`):

```bash
PYTHONPATH=. python3 -m pytest sample/modules/chatapp/tests/test_chatapp_web_e2e.py -v
```

This starts MemCOS + `ChatHTTPServer`, then runs Vitest integration tests that `fetch` `/api/chat/ui`.

## Root `package.json`

`sample/modules/chatapp/package.json` delegates to `web/` (`npm run web:dev`, etc.).

## Deployment notes (COS)

- COS modules are intended to be **standalone runnable programs**. A full platform may spawn **one process per module** (or a **thread pool** / in-process calls for Python).
- **Java** modules would be deployed via a management API to load JARs; **native** `.so` modules similarly — **not** implemented in MemCOS yet.
- When Python backends are isolated in a **child process**, session routing would go through a router (see `subprocess_router.py` stub); the current MemCOS tests and HTTP server run **in-process** for simplicity.
