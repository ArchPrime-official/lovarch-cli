"""arch signup — Free mode interactive registration with lead capture.

Flow:
  1. Welcome banner (4-language)
  2. Interactive prompts: full_name, email, phone, country, language
  3. GDPR consent (mandatory — Italian/EU compliance)
  4. POST → cli-signup EF (validates server-side, creates shadow user, lead)
  5. Save returned token to ~/.lovarch/credentials.json (chmod 0600)
  6. Success message + next-steps (arch init, arch run)

Localization: i18n keys live in lovarch_cli/i18n/translations/{it,pt,en,es}.json.
"""
from __future__ import annotations

import asyncio
import re
import sys
from datetime import datetime, timezone
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.text import Text

from lovarch_cli.api import ApiClient, LovarchApiError
from lovarch_cli.config import Credentials, save_credentials
from lovarch_cli.i18n import current_lang, set_current_lang, t
from lovarch_cli.i18n.loader import VALID_LANGUAGES

console = Console()
err_console = Console(stderr=True)

EMAIL_RX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_RX = re.compile(r"^\+?[1-9]\d{6,14}$")
COUNTRY_RX = re.compile(r"^[A-Z]{2}$")


def signup_command(
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Auto-accept TOS (skip GDPR consent prompt — for CI only).",
        ),
    ] = False,
    lang_flag: Annotated[
        str | None,
        typer.Option(
            "--lang",
            help="Force language (it/pt/en/es). Default: detect from $LANG.",
        ),
    ] = None,
) -> None:
    """Cadastro Free interativo (interactive Free signup).

    Use --yes to auto-accept TOS for non-interactive (CI/Docker) flows.
    """
    # ─── Language detection ──────────────────────────────────────────────
    if lang_flag is not None:
        set_current_lang(lang_flag)
    lang = current_lang()

    # ─── Welcome banner ──────────────────────────────────────────────────
    console.print()
    console.print(
        Panel(
            Text.from_markup(t("signup.welcome_body", lang=lang)),
            title=f"[bold gold1]🎓 {t('signup.welcome_title', lang=lang)}[/bold gold1]",
            border_style="gold1",
            padding=(1, 2),
        )
    )
    console.print()

    # ─── Confirm/select language ─────────────────────────────────────────
    lang = Prompt.ask(
        f"[bold]{t('signup.prompt_language', lang=lang)}[/bold]",
        choices=list(VALID_LANGUAGES),
        default=lang,
    )
    set_current_lang(lang)

    # ─── Collect inputs ──────────────────────────────────────────────────
    while True:
        full_name = Prompt.ask(
            f"[bold]{t('signup.prompt_full_name', lang=lang)}[/bold]"
        ).strip()
        if len(full_name) >= 3:
            break
        err_console.print(f"[red]{t('signup.name_too_short', lang=lang)}[/red]")

    while True:
        email = (
            Prompt.ask(f"[bold]{t('signup.prompt_email', lang=lang)}[/bold]")
            .strip()
            .lower()
        )
        if EMAIL_RX.match(email):
            break
        err_console.print(f"[red]{t('signup.invalid_email', lang=lang)}[/red]")

    while True:
        phone = Prompt.ask(
            f"[bold]{t('signup.prompt_phone', lang=lang)}[/bold]"
        ).strip()
        if PHONE_RX.match(phone):
            break
        err_console.print(f"[red]{t('signup.invalid_phone', lang=lang)}[/red]")

    while True:
        country = (
            Prompt.ask(f"[bold]{t('signup.prompt_country', lang=lang)}[/bold]")
            .strip()
            .upper()
        )
        if COUNTRY_RX.match(country):
            break
        err_console.print(f"[red]{t('signup.invalid_country', lang=lang)}[/red]")

    # ─── GDPR consent (mandatory) ────────────────────────────────────────
    if not yes:
        console.print(
            f"\n[dim]{t('signup.tos_url_label', lang=lang)} "
            f"https://lovarch.com/terms-of-service[/dim]"
        )
        accept = Confirm.ask(
            f"[bold yellow]{t('signup.prompt_consent', lang=lang)}[/bold yellow]",
            default=False,
        )
        if not accept:
            err_console.print(
                f"\n[red]✗ {t('signup.consent_required', lang=lang)}[/red]"
            )
            raise typer.Exit(1)

    # ─── Submit to EF ────────────────────────────────────────────────────
    console.print(f"\n[dim]{t('signup.submitting', lang=lang)}[/dim]")
    api = ApiClient()
    payload = {
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "country": country,
        "language": lang,
        "source": "cli-free",
        "accept_tos": True,
        "cli_version": "0.1.0",
    }

    try:
        response = asyncio.run(api.invoke_ef("cli-signup", payload))
    except LovarchApiError as exc:
        err_console.print(f"\n[red]✗ {exc}[/red]")
        if exc.error_code:
            err_console.print(f"[dim](error_code: {exc.error_code})[/dim]")
        sys.exit(1)

    # ─── Save credentials ────────────────────────────────────────────────
    creds = Credentials(
        mode="free",
        lead_id=response["lead_id"],
        user_id=response["user_id"],
        free_token=response["free_token"],
        email=email,
        full_name=full_name,
        country=country,
        language=lang,
        signed_up_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        upgrade_url=response.get("upgrade_url"),
    )
    creds_path = save_credentials(creds)

    # ─── Success ─────────────────────────────────────────────────────────
    console.print()
    console.print(
        Panel(
            Text.from_markup(t("signup.next_steps", lang=lang)),
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print(f"\n[dim]Credentials: {creds_path}[/dim]")
