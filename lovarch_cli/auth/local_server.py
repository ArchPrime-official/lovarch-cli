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

# ── Lovarch brand mark — hexagon node-mesh, recreated as inline SVG so the
# served page stays self-contained (no external image, no JS). ──────────────
_SYMBOL_SVG = (
    '<svg viewBox="0 0 100 100" width="34" height="34" aria-hidden="true" '
    'style="color:#18181B">'
    '<g stroke="currentColor" stroke-width="1.1" fill="none" stroke-linecap="round">'
    '<line x1="50" y1="10" x2="84.6" y2="30"/><line x1="84.6" y1="30" x2="84.6" y2="70"/>'
    '<line x1="84.6" y1="70" x2="50" y2="90"/><line x1="50" y1="90" x2="15.4" y2="70"/>'
    '<line x1="15.4" y1="70" x2="15.4" y2="30"/><line x1="15.4" y1="30" x2="50" y2="10"/>'
    '<line x1="50" y1="10" x2="50" y2="90"/><line x1="15.4" y1="30" x2="84.6" y2="70"/>'
    '<line x1="84.6" y1="30" x2="15.4" y2="70"/><line x1="50" y1="10" x2="15.4" y2="70"/>'
    '<line x1="50" y1="10" x2="84.6" y2="70"/><line x1="50" y1="90" x2="15.4" y2="30"/>'
    '<line x1="50" y1="90" x2="84.6" y2="30"/></g>'
    '<g fill="currentColor">'
    '<circle cx="50" cy="10" r="2.7"/><circle cx="84.6" cy="30" r="2.7"/>'
    '<circle cx="84.6" cy="70" r="2.7"/><circle cx="50" cy="90" r="2.7"/>'
    '<circle cx="15.4" cy="70" r="2.7"/><circle cx="15.4" cy="30" r="2.7"/>'
    '<circle cx="50" cy="50" r="2.7"/></g></svg>'
)

_CHECK_SVG = (
    '<svg viewBox="0 0 24 24" width="30" height="30" fill="none" stroke="currentColor" '
    'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">'
    '<polyline points="20 6 9 17 4 12"/></svg>'
)
_X_SVG = (
    '<svg viewBox="0 0 24 24" width="30" height="30" fill="none" stroke="currentColor" '
    'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">'
    '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>'
)

# Single-language copy (the CLI knows the user's language and passes it in).
_SUCCESS_TEXT = {
    "it": ("Accesso completato", "Puoi chiudere questa scheda e tornare al terminale."),
    "pt": ("Login concluído", "Você pode fechar esta aba e voltar ao terminal."),
    "en": ("You're signed in", "You can close this tab and return to your terminal."),
    "es": ("Sesión iniciada", "Puedes cerrar esta pestaña y volver a la terminal."),
}
_ERROR_TEXT = {
    "it": ("Accesso non riuscito", "Torna al terminale per i dettagli e riprova."),
    "pt": ("Login não concluído", "Volte ao terminal para ver os detalhes e tente de novo."),
    "en": ("Sign-in failed", "Return to your terminal for details and try again."),
    "es": ("Error al iniciar sesión", "Vuelve a la terminal para ver los detalles e inténtalo de nuevo."),
}

_SHELL = """<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>lovarch-cli</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500&family=Outfit:wght@300;500;600&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; min-height: 100vh; display: flex; align-items: center;
          justify-content: center; padding: 24px;
          background: #FAF9F7; color: #18181B;
          font-family: 'DM Sans', -apple-system, system-ui, sans-serif;
          -webkit-font-smoothing: antialiased; }}
  .card {{ background: #fff; border: 1px solid rgba(24,24,27,.10);
           border-radius: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.05);
           padding: 34px 30px; max-width: 380px; width: 100%; text-align: center; }}
  .brand {{ display: flex; align-items: center; justify-content: center;
            gap: 11px; margin-bottom: 22px; }}
  .word {{ font-family: 'Outfit', system-ui, sans-serif; font-size: 20px;
           font-weight: 300; letter-spacing: .34em; padding-left: .34em; color: #18181B; }}
  .badge {{ width: 60px; height: 60px; border-radius: 50%; display: flex;
            align-items: center; justify-content: center; margin: 6px auto 18px; }}
  .badge.ok {{ background: rgba(21,128,61,.09); color: #15803D; }}
  .badge.err {{ background: rgba(185,28,28,.08); color: #B91C1C; }}
  h1 {{ font-family: 'Outfit', system-ui, sans-serif; font-size: 20px;
        font-weight: 600; letter-spacing: -.01em; margin: 0 0 8px; color: #18181B; }}
  p {{ font-size: 14px; line-height: 1.55; color: #71717A; margin: 0; }}
  .errbox {{ margin-top: 16px; background: rgba(185,28,28,.08);
             border: 1px solid rgba(185,28,28,.16); border-radius: 9px;
             padding: 10px 12px; font-family: ui-monospace, Menlo, monospace;
             font-size: 12px; color: #B91C1C; word-break: break-word; }}
  .foot {{ margin-top: 22px; padding-top: 16px; border-top: 1px solid rgba(24,24,27,.10);
           font-size: 11.5px; color: #a1a1aa; letter-spacing: .02em; }}
</style>
</head>
<body>
  <div class="card">
    <div class="brand">{symbol}<span class="word">LOVARCH</span></div>
    <div class="badge {badge_cls}">{badge_svg}</div>
    <h1>{title}</h1>
    <p>{body}</p>
    {extra}
    <p class="foot">lovarch-cli</p>
  </div>
</body>
</html>
"""


def _normalize_lang(lang: str) -> str:
    lang = (lang or "it").lower()[:2]
    return lang if lang in _SUCCESS_TEXT else "it"


def success_html(lang: str = "it") -> str:
    """Branded, single-language 'login complete' page."""
    lang = _normalize_lang(lang)
    title, body = _SUCCESS_TEXT[lang]
    return _SHELL.format(
        lang=lang, symbol=_SYMBOL_SVG, badge_cls="ok", badge_svg=_CHECK_SVG,
        title=title, body=body, extra="",
    )


def error_html(error: str, lang: str = "it") -> str:
    """Branded, single-language 'login failed' page (shows the error code)."""
    lang = _normalize_lang(lang)
    title, body = _ERROR_TEXT[lang]
    from html import escape
    errbox = f'<div class="errbox">{escape(error or "unknown")}</div>'
    return _SHELL.format(
        lang=lang, symbol=_SYMBOL_SVG, badge_cls="err", badge_svg=_X_SVG,
        title=title, body=body, extra=errbox,
    )


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

        lang: str = getattr(self.server, "lang", "it")  # type: ignore[attr-defined]

        if "error" in params:
            result.error = params["error"][0]
            result.error_description = params.get(
                "error_description", [""]
            )[0]
            html = error_html(result.error, lang)
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
            self.wfile.write(success_html(lang).encode("utf-8"))
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

    def __init__(self, port: int = 0, lang: str = "it") -> None:
        self._httpd = HTTPServer(("127.0.0.1", port), _Handler)
        # Attach result holder + event to the server instance for handler access
        self._httpd.callback_result = CallbackResult()  # type: ignore[attr-defined]
        self._httpd.done_event = threading.Event()  # type: ignore[attr-defined]
        # Language for the branded success/error pages (single-language render).
        self._httpd.lang = lang  # type: ignore[attr-defined]
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
