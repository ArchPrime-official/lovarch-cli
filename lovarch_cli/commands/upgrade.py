"""arch upgrade — CTA from Free to Premium.

State-aware:
  - none    → instruct user to run `arch signup` first
  - free    → show benefits + open browser to /cli-upgrade
  - premium → already-premium acknowledgment + open /settings/credits

This is a thin CLI surface around a web page; no backend interaction. The
goal is to keep the upgrade funnel discoverable in-terminal and route the
user to the same web flow Lovarch uses for in-app upgrades.
"""
from __future__ import annotations

import sys
import webbrowser
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from lovarch_cli.config import load_credentials
from lovarch_cli.i18n import current_lang, set_current_lang, t

console = Console()
err_console = Console(stderr=True)

# Same web base used by `arch login --premium` for the PKCE flow.
LOVARCH_WEB_BASE = "https://lovarch.com"
UPGRADE_PATH = "/cli-upgrade"
PREMIUM_DASHBOARD_PATH = "/settings/credits"


def upgrade_command(
    no_browser: Annotated[
        bool,
        typer.Option(
            "--no-browser",
            help="Print the URL without opening the browser (for CI/SSH).",
        ),
    ] = False,
    lang_flag: Annotated[
        str | None,
        typer.Option("--lang", "-l", help="Override language (it/pt/en/es)."),
    ] = None,
) -> None:
    """Open the Premium upgrade flow in the browser (or print URL with --no-browser)."""
    if lang_flag is not None:
        set_current_lang(lang_flag)
    lang = current_lang()

    creds = load_credentials()

    # Prefer the language the user signed up with — falls back to runtime lang
    # so users who didn't sign up still get something localized.
    user_lang = creds.language if creds.mode != "none" else lang

    # ─── No account → tell user to signup first ──────────────────────────
    if creds.mode == "none":
        err_console.print(
            f"\n[yellow]{t('upgrade.no_account_hint', lang=user_lang)}[/yellow]\n"
        )
        sys.exit(1)

    # ─── Already Premium → acknowledge + open billing dashboard ──────────
    if creds.mode == "premium":
        url = f"{LOVARCH_WEB_BASE}{PREMIUM_DASHBOARD_PATH}"
        body = Text.from_markup(
            f"{t('upgrade.already_premium', lang=user_lang)}\n\n"
            f"[dim cyan]{url}[/dim cyan]"
        )
        console.print()
        console.print(
            Panel(
                body,
                title=f"[bold green]{t('upgrade.already_premium_title', lang=user_lang)}[/bold green]",
                border_style="green",
                padding=(1, 2),
            )
        )
        if not no_browser:
            webbrowser.open(url, new=1, autoraise=True)
        console.print()
        return

    # ─── Free → show benefits + open upgrade URL ─────────────────────────
    url = f"{LOVARCH_WEB_BASE}{UPGRADE_PATH}"
    body = Text.from_markup(
        f"{t('upgrade.body_free', lang=user_lang)}\n\n"
        f"[dim]{t('login.manual_url_hint', lang=user_lang)}[/dim]\n"
        f"[dim cyan]{url}[/dim cyan]"
    )
    console.print()
    console.print(
        Panel(
            body,
            title=f"[bold gold1]{t('upgrade.title', lang=user_lang)}[/bold gold1]",
            border_style="gold1",
            padding=(1, 2),
        )
    )
    if not no_browser:
        console.print(
            f"\n[gold1]→[/gold1] {t('login.opening_browser', lang=user_lang)}"
        )
        webbrowser.open(url, new=1, autoraise=True)
    console.print()
