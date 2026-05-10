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

Localized in 4 languages — keys live in archprime_cli/i18n/translations/*.json.
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
from rich.text import Text

from archprime_cli.api import ApiClient, LovarchApiError
from archprime_cli.auth import PkceParams, save_premium_session
from archprime_cli.auth.local_server import AuthServer
from archprime_cli.config import DEFAULT_API_URL
from archprime_cli.i18n import current_lang, set_current_lang, t

console = Console()
err_console = Console(stderr=True)

# https://lovarch.com host — ALWAYS the web app for /cli-auth, NOT the
# Supabase API URL (which is for EF calls). This is hardcoded because the
# /cli-auth React page only exists on lovarch.com.
LOVARCH_WEB_BASE = "https://lovarch.com"
PKCE_TIMEOUT_SECONDS = 300.0  # 5 minutes — matches DB code TTL


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
    if lang_flag is not None:
        set_current_lang(lang_flag)
    lang = current_lang()

    # Mutually exclusive flags
    if free and premium:
        err_console.print(f"[red]{t('login.modes_mutex', lang=lang)}[/red]")
        sys.exit(2)

    if not free and not premium:
        # Interactive choice
        choice = Prompt.ask(
            f"[bold]{t('login.choose_mode_prompt', lang=lang)}[/bold]",
            choices=["free", "premium"],
            default="free",
        )
        free = choice == "free"
        premium = choice == "premium"

    if free:
        console.print()
        console.print(t("login.free_redirect", lang=lang))
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
    console.print(f"[gold1]→[/gold1] {t('login.opening_browser', lang=lang)}")
    console.print(f"  [dim]{t('login.manual_url_hint', lang=lang)}[/dim]")
    console.print(f"  [dim cyan]{auth_url}[/dim cyan]")
    console.print()

    webbrowser.open(auth_url, new=1, autoraise=True)

    with console.status(
        Text.from_markup(f"[gold1]{t('login.waiting_callback', lang=lang)}[/gold1]"),
        spinner="dots",
    ):
        result = server.wait_for_callback(PKCE_TIMEOUT_SECONDS)

    server.shutdown()

    # ─── Validate callback ───────────────────────────────────────────────
    if result.error:
        if result.error == "timeout":
            err_console.print(
                f"\n[red]✗ {t('login.callback_timeout', lang=lang)}[/red]"
            )
        elif result.error == "access_denied":
            err_console.print(
                f"\n[yellow]✗ {t('login.auth_denied', lang=lang)}[/yellow]"
            )
        else:
            err_console.print(
                f"\n[red]✗ {result.error}: {result.error_description or ''}[/red]"
            )
        sys.exit(1)

    if not result.code or result.state != pkce.state:
        err_console.print(f"\n[red]✗ {t('login.state_mismatch', lang=lang)}[/red]")
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
            title=f"[bold green]{t('login.login_success', lang=lang)}[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )
