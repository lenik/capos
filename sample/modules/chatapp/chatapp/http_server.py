"""HTTP server for chatweb: serves built SPA and POST /api/chat/ui → ChatSessionMgr.handle()."""

from __future__ import annotations

import json
import mimetypes
from collections.abc import Callable, Mapping
from http import HTTPStatus
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any


class ChatHTTPServer(ThreadingHTTPServer):
    """Holds a chat.ui handler and optional static root for the Vue build."""

    chat_handler: Callable[[dict[str, Any]], dict[str, Any]] | None = None
    static_root: Path | None = None


class _ChatHTTPRequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: Any) -> None:
        return  # quiet for tests

    def _send_json(self, code: int, payload: Mapping[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self) -> None:
        if self.path != "/api/chat/ui":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return
        server: ChatHTTPServer = self.server  # type: ignore[assignment]
        if server.chat_handler is None:
            self._send_json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "no_handler"})
            return
        try:
            n = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(n) if n else b"{}"
            req = json.loads(raw.decode("utf-8"))
            out = server.chat_handler(req)
            self._send_json(HTTPStatus.OK, out)
        except Exception as e:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "bad_request", "message": str(e)},
            )

    def do_GET(self) -> None:
        server: ChatHTTPServer = self.server  # type: ignore[assignment]
        root = server.static_root
        if root is None or not root.is_dir():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "no_static"})
            return
        path = (self.path or "/").split("?", 1)[0]
        if path == "/":
            path = "/index.html"
        file_path = (root / path.lstrip("/")).resolve()
        try:
            if not str(file_path).startswith(str(root.resolve())):
                self.send_error(HTTPStatus.FORBIDDEN)
                return
        except FileNotFoundError:
            pass
        if not file_path.is_file():
            # SPA fallback
            file_path = root / "index.html"
        if not file_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        ctype, _ = mimetypes.guess_type(str(file_path))
        body = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", ctype or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


def serve(
    chat_handler: Callable[[dict[str, Any]], dict[str, Any]],
    *,
    host: str = "127.0.0.1",
    port: int = 0,
    static_root: Path | None = None,
) -> ChatHTTPServer:
    """Start a thread-safe HTTP server; return bound instance (use server_address for port)."""
    httpd = ChatHTTPServer((host, port), _ChatHTTPRequestHandler)
    httpd.chat_handler = chat_handler
    httpd.static_root = static_root
    return httpd


def main() -> None:
    """CLI placeholder: serve static + API (expects chat_handler injected by a harness in real use)."""
    import argparse

    p = argparse.ArgumentParser(description="chatapp HTTP (use tests/harness for full MemCOS stack)")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8787)
    p.add_argument("--static", type=Path, help="Path to web/dist")
    args = p.parse_args()
    static = args.static.resolve() if args.static else None

    def _fail(_req: dict[str, Any]) -> dict[str, Any]:
        return {"error": "no_cos", "hint": "Run via memcos test harness or wire chat_handler"}

    httpd = serve(_fail, host=args.host, port=args.port, static_root=static)
    print(f"chatapp http listening on http://{args.host}:{httpd.server_address[1]} (stub handler)")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
