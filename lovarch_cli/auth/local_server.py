"""Ephemeral HTTP server for capturing OAuth-style PKCE redirects.

Listens on 127.0.0.1:RANDOM_PORT. The Lovarch web /cli-auth page redirects
the browser to http://127.0.0.1:PORT/callback?code=X&state=Y after the user
authorizes the CLI. This module captures those query params and shuts down.

Threading: the server runs in a background thread so the CLI's main thread
can show a "Waiting for browser..." spinner. The result (code+state OR
error) is delivered via a threading.Event + a result holder.

Security notes:
- Bound to 127.0.0.1 only (not 0.0.0.0) — only the user's machine can hit
- One-shot: serves a single /callback request then shuts down
- Random port (port=0 lets OS pick) — defeats simple port-based attacks
- Ignores any path other than /callback (returns 404)
"""
from __future__ import annotations

import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional
from urllib.parse import parse_qs, urlparse

CALLBACK_PATH = "/callback"

SUCCESS_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>lovarch-cli login</title>
<style>
  body { font-family: -apple-system, system-ui, sans-serif;
         display: flex; align-items: center; justify-content: center;
         height: 100vh; margin: 0; background: #FAF9F7; color: #09090B; }
  .card { text-align: center; padding: 2rem 3rem;
          border: 1px solid rgba(0,0,0,0.08); border-radius: 12px;
          background: #fff; box-shadow: 0 1px 4px rgba(0,0,0,0.04); }
  h1 { color: #A16207; margin: 0 0 0.5rem; font-weight: 600; }
  p { margin: 0.5rem 0 0; color: #71717a; }
</style>
</head>
<body>
  <div class="card">
    <h1>✓ lovarch-cli</h1>
    <p>Login completato. Puoi chiudere questa scheda.</p>
    <p style="margin-top:1rem;font-size:0.85rem">Login complete — you can close this tab.</p>
  </div>
</body>
</html>
"""

ERROR_HTML = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>lovarch-cli login error</title></head>
<body style="font-family:sans-serif;padding:2rem;background:#FAF9F7">
<h1 style="color:#dc2626">lovarch-cli login failed</h1>
<p>{error}</p>
<p>Torna al terminale per maggiori dettagli. Return to the terminal for details.</p>
</body>
</html>
"""


@dataclass
class CallbackResult:
    """Result captured from the browser redirect."""

    code: Optional[str] = None
    state: Optional[str] = None
    error: Optional[str] = None
    error_description: Optional[str] = None


class _Handler(BaseHTTPRequestHandler):
    """Per-request handler. Stores result on the parent server."""

    server_version = "lovarch-cli/0.1"

    def log_message(self, format: str, *args: object) -> None:  # type: ignore[override]
        # Suppress default stderr logging — we capture via spinner
        return

    def do_GET(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler API)
        parsed = urlparse(self.path)
        if parsed.path != CALLBACK_PATH:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            return

        params = parse_qs(parsed.query, keep_blank_values=True)
        result: CallbackResult = self.server.callback_result  # type: ignore[attr-defined]

        if "error" in params:
            result.error = params["error"][0]
            result.error_description = params.get(
                "error_description", [""]
            )[0]
            html = ERROR_HTML.format(error=result.error)
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
        elif "code" in params and "state" in params:
            result.code = params["code"][0]
            result.state = params["state"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(SUCCESS_HTML.encode("utf-8"))
        else:
            result.error = "missing_params"
            result.error_description = "neither code/state nor error returned"
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing parameters")

        # Signal main thread that we got the redirect
        self.server.done_event.set()  # type: ignore[attr-defined]


class AuthServer:
    """Single-shot localhost HTTP server for PKCE callback capture."""

    def __init__(self, port: int = 0) -> None:
        self._httpd = HTTPServer(("127.0.0.1", port), _Handler)
        # Attach result holder + event to the server instance for handler access
        self._httpd.callback_result = CallbackResult()  # type: ignore[attr-defined]
        self._httpd.done_event = threading.Event()  # type: ignore[attr-defined]
        self._thread: Optional[threading.Thread] = None

    @property
    def port(self) -> int:
        return self._httpd.server_address[1]

    @property
    def callback_url(self) -> str:
        return f"http://127.0.0.1:{self.port}{CALLBACK_PATH}"

    def start(self) -> None:
        """Start serving in a background thread."""
        self._thread = threading.Thread(
            target=self._httpd.serve_forever,
            daemon=True,
            name="lovarch-cli-auth-server",
        )
        self._thread.start()

    def wait_for_callback(self, timeout_seconds: float) -> CallbackResult:
        """Block until the browser hits /callback or timeout elapses."""
        got_it = self._httpd.done_event.wait(timeout=timeout_seconds)  # type: ignore[attr-defined]
        if not got_it:
            self._httpd.callback_result.error = "timeout"  # type: ignore[attr-defined]
            self._httpd.callback_result.error_description = (  # type: ignore[attr-defined]
                f"No callback within {timeout_seconds}s"
            )
        return self._httpd.callback_result  # type: ignore[attr-defined,return-value]

    def shutdown(self) -> None:
        """Stop the HTTP server and wait for thread to join."""
        self._httpd.shutdown()
        self._httpd.server_close()
        if self._thread:
            self._thread.join(timeout=2.0)
