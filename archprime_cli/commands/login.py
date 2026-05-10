"""arch login — Authentication entry point (Free or Premium).

Subcommand structure:
  arch login              → interactive: choose Free or Premium
  arch login --free       → redirects to arch signup (free has no separate login)
  arch login --premium    → PKCE flow with Lovarch web

Premium PKCE flow:
  1. Generate verifier + challenge + state via PkceParams.generate()
  2. Spin up local HTTP server on 127.0.0.1:RANDOM/callback
  3. Open browser to https://lovarch.com/cli-auth?...
  4. Show "Waiting for browser..." spinner with timeout 5min
  5. On callback: validate state matches, POST cli-auth-exchange EF
  6. Save tokens via keyring_store.save_premium_session
  7. Show success panel with user info

Localized in 4 languages (Story 4.1 will extract to JSON).
"""
from __future__ import annotations

import asyncio
import sys
import webbrowser
from typing import Annotated
from urllib.parse import urlencode

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.spinner import Spinner
from rich.text import Text

from archprime_cli.api import ApiClient, LovarchApiError
from archprime_cli.auth import PkceParams, save_premium_session
from archprime_cli.auth.local_server import AuthServer
from archprime_cli.config import DEFAULT_API_URL

console = Console()
err_console = Console(stderr=True)

# https://lovarch.com host — ALWAYS the web app for /cli-auth, NOT the
# Supabase API URL (which is for EF calls). This is hardcoded because the
# /cli-auth React page only exists on lovarch.com.
LOVARCH_WEB_BASE = "https://lovarch.com"
PKCE_TIMEOUT_SECONDS = 300.0  # 5 minutes — matches DB code TTL

VALID_LANGUAGES = ["it", "pt", "en", "es"]


I18N: dict[str, dict[str, str]] = {
    "choose_mode_prompt": {
        "it": "Scegli modalità",
        "pt": "Escolha modalidade",
        "en": "Choose mode",
        "es": "Elige modalidad",
    },
    "free_redirect": {
        "it": "Per la modalità Free, esegui [bold cyan]arch signup[/bold cyan].",
        "pt": "Para o modo Free, execute [bold cyan]arch signup[/bold cyan].",
        "en": "For Free mode, run [bold cyan]arch signup[/bold cyan].",
        "es": "Para el modo Free, ejecuta [bold cyan]arch signup[/bold cyan].",
    },
    "opening_browser": {
        "it": "Apertura del browser per il login Lovarch...",
        "pt": "Abrindo o navegador para login Lovarch...",
        "en": "Opening browser for Lovarch login...",
        "es": "Abriendo navegador para login Lovarch...",
    },
    "manual_url_hint": {
        "it": "Se il browser non si apre, copia questo URL:",
        "pt": "Se o navegador não abrir, copie esta URL:",
        "en": "If the browser doesn't open, copy this URL:",
        "es": "Si el navegador no abre, copia esta URL:",
    },
    "waiting_callback": {
        "it": "In attesa dell'autorizzazione (timeout 5 min)...",
        "pt": "Aguardando autorização (timeout 5 min)...",
        "en": "Waiting for authorization (5 min timeout)...",
        "es": "Esperando autorización (timeout 5 min)...",
    },
    "callback_timeout": {
        "it": "Timeout: nessuna risposta dal browser in 5 minuti.",
        "pt": "Timeout: nenhuma resposta do navegador em 5 minutos.",
        "en": "Timeout: no response from browser in 5 minutes.",
        "es": "Timeout: ninguna respuesta del navegador en 5 minutos.",
    },
    "state_mismatch": {
        "it": "Errore di sicurezza: state non corrisponde (possibile CSRF). Riprova.",
        "pt": "Erro de segurança: state não corresponde (possível CSRF). Tente novamente.",
        "en": "Security error: state mismatch (possible CSRF). Try again.",
        "es": "Error de seguridad: state no coincide (posible CSRF). Intenta de nuevo.",
    },
    "auth_denied": {
        "it": "Autorizzazione negata dall'utente.",
        "pt": "Autorização negada pelo usuário.",
        "en": "Authorization denied by user.",
        "es": "Autorización denegada por el usuario.",
    },
    "login_success": {
        "it": "✓ Login Premium completato",
        "pt": "✓ Login Premium concluído",
        "en": "✓ Premium login complete",
        "es": "✓ Login Premium completado",
    },
}


def t(key: str, lang: str = "it") -> str:
    return I18N.get(key, {}).get(lang) or I18N.get(key, {}).get("it") or key


def _detect_language() -> str:
    import os

    env_lang = os.environ.get("LANG", "").split("_")[0].lower()
    return env_lang if env_lang in VALID_LANGUAGES else "it"


def login_command(
    free: Annotated[
        bool,
        typer.Option("--free", help="Free mode (redirects to arch signup)."),
    ] = False,
    premium: Annotated[
        bool,
        typer.Option(
            "--premium",
            help="Premium mode (PKCE flow with Lovarch login).",
        ),
    ] = False,
    lang_flag: Annotated[
        str | None,
        typer.Option("--lang", "-l", help="Override language (it/pt/en/es)."),
    ] = None,
) -> None:
    """Login al CLI (Free o Premium)."""
    lang = lang_flag if lang_flag in VALID_LANGUAGES else _detect_language()

    # Mutually exclusive flags
    if free and premium:
        err_console.print("[red]--free and --premium are mutually exclusive[/red]")
        sys.exit(2)

    if not free and not premium:
        # Interactive choice
        choice = Prompt.ask(
            f"[bold]{t('choose_mode_prompt', lang)}[/bold]",
            choices=["free", "premium"],
            default="free",
        )
        free = choice == "free"
        premium = choice == "premium"

    if free:
        console.print()
        console.print(t("free_redirect", lang))
        console.print()
        sys.exit(0)

    # ─── Premium PKCE flow ───────────────────────────────────────────────
    pkce = PkceParams.generate()
    server = AuthServer(port=0)
    server.start()

    auth_url = (
        f"{LOVARCH_WEB_BASE}/cli-auth?"
        + urlencode(
            {
                "state": pkce.state,
                "code_challenge": pkce.code_challenge,
                "code_challenge_method": pkce.code_challenge_method,
                "redirect_uri": server.callback_url,
                "lang": lang,
            }
        )
    )

    console.print()
    console.print(f"[gold1]→[/gold1] {t('opening_browser', lang)}")
    console.print(f"  [dim]{t('manual_url_hint', lang)}[/dim]")
    console.print(f"  [dim cyan]{auth_url}[/dim cyan]")
    console.print()

    webbrowser.open(auth_url, new=1, autoraise=True)

    with console.status(
        Text.from_markup(f"[gold1]{t('waiting_callback', lang)}[/gold1]"),
        spinner="dots",
    ):
        result = server.wait_for_callback(PKCE_TIMEOUT_SECONDS)

    server.shutdown()

    # ─── Validate callback ───────────────────────────────────────────────
    if result.error:
        if result.error == "timeout":
            err_console.print(f"\n[red]✗ {t('callback_timeout', lang)}[/red]")
        elif result.error == "access_denied":
            err_console.print(f"\n[yellow]✗ {t('auth_denied', lang)}[/yellow]")
        else:
            err_console.print(
                f"\n[red]✗ {result.error}: {result.error_description or ''}[/red]"
            )
        sys.exit(1)

    if not result.code or result.state != pkce.state:
        err_console.print(f"\n[red]✗ {t('state_mismatch', lang)}[/red]")
        sys.exit(1)

    # ─── Exchange code for tokens ────────────────────────────────────────
    api = ApiClient(base_url=DEFAULT_API_URL)
    try:
        response = asyncio.run(
            api.invoke_ef(
                "cli-auth-exchange",
                {
                    "code": result.code,
                    "code_verifier": pkce.code_verifier,
                    "language": lang,
                },
            )
        )
    except LovarchApiError as exc:
        err_console.print(f"\n[red]✗ {exc}[/red]")
        if exc.error_code:
            err_console.print(f"[dim](error_code: {exc.error_code})[/dim]")
        sys.exit(1)

    # ─── Save session ────────────────────────────────────────────────────
    user = response.get("user", {})
    expires_in = int(response.get("expires_in", 3600))
    from datetime import datetime, timedelta, timezone

    expires_at = (
        datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    ).isoformat(timespec="seconds")

    used_keyring, location = save_premium_session(
        user_id=user.get("id", ""),
        email=user.get("email", ""),
        full_name=user.get("full_name"),
        access_token=response["access_token"],
        refresh_token=response["refresh_token"],
        expires_at=expires_at,
        language=lang,
    )

    body = Text.assemble(
        ("Account: ", "dim"),
        (f"{user.get('email','')}\n", "bold"),
        ("User ID: ", "dim"),
        (f"{user.get('id','')}\n", "bold dim"),
        ("Expires: ", "dim"),
        (f"{expires_at}\n", "bold"),
        ("Storage: ", "dim"),
        (location, "bold" if used_keyring else "italic yellow"),
    )
    console.print()
    console.print(
        Panel(
            body,
            title=f"[bold green]{t('login_success', lang)}[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )
