"""arch account — User account management subcommands.

Currently exposes:
  arch account delete   GDPR right-to-erasure (free + premium)
  arch account info     Show currently logged-in account

For free users: hits cli-account-delete EF, pseudonymizes lead, deletes shadow
auth.user, clears local credentials + optionally local artifacts.

For premium users: TODO Epic 3 — chains to cli-premium-deactivate.
"""
from __future__ import annotations

import asyncio
import shutil
import sys
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.text import Text

from lovarch_cli.api import ApiClient, LovarchApiError
from lovarch_cli.config import (
    DEFAULT_HOME,
    Credentials,
    clear_credentials,
    load_credentials,
)
from lovarch_cli.i18n import t

console = Console()
err_console = Console(stderr=True)

app = typer.Typer(
    name="account",
    help="Gestione account (info, delete GDPR).",
    no_args_is_help=True,
)


@app.command(name="info", help="Mostra info dell'account corrente.")
def account_info() -> None:
    """Show currently logged-in account info."""
    creds = load_credentials()
    if creds.mode == "none":
        err_console.print(
            f"[yellow]{t('account.no_account', lang=creds.language)}[/yellow]"
        )
        sys.exit(1)

    body = Text.assemble(
        ("Mode:        ", "dim"),
        (f"{creds.mode}\n", "bold gold1"),
        ("Email:       ", "dim"),
        (f"{creds.email or '—'}\n", "bold"),
        ("Full name:   ", "dim"),
        (f"{creds.full_name or '—'}\n", "bold"),
        ("Country:     ", "dim"),
        (f"{creds.country or '—'}\n", "bold"),
        ("Language:    ", "dim"),
        (f"{creds.language}\n", "bold"),
        ("Signed up:   ", "dim"),
        (f"{creds.signed_up_at or '—'}\n", "bold"),
        ("Lead ID:     ", "dim"),
        (f"{creds.lead_id or '—'}\n", "bold dim"),
    )
    console.print(
        Panel(
            body,
            title=f"[bold gold1]{t('account.info_title', lang=creds.language)}[/bold gold1]",
            border_style="gold1",
            padding=(1, 2),
        )
    )


@app.command(name="delete", help="Cancella account (GDPR right-to-erasure).")
def account_delete(
    yes: Annotated[
        bool,
        typer.Option(
            "--yes", "-y", help="Skip confirmation prompts (CI/scripts only)."
        ),
    ] = False,
    keep_local: Annotated[
        bool,
        typer.Option(
            "--keep-local",
            help="Keep ~/.lovarch/projects/ local files after remote deletion.",
        ),
    ] = False,
) -> None:
    """Permanently delete CLI account (GDPR Art. 17 right-to-erasure)."""
    creds: Credentials = load_credentials()
    if creds.mode == "none" or not creds.free_token:
        err_console.print(
            f"[yellow]{t('account.no_account', lang=creds.language)}[/yellow]"
        )
        sys.exit(1)

    lang = creds.language

    if creds.mode == "premium":
        err_console.print(
            f"[yellow]{t('account.premium_delete_redirect', lang=lang)}[/yellow]"
        )
        sys.exit(1)

    # ─── Warning panel ───────────────────────────────────────────────────
    console.print()
    console.print(
        Panel(
            Text.from_markup(t("account.delete_warning_body", lang=lang)),
            title=f"[bold red]{t('account.delete_warning_title', lang=lang)}[/bold red]",
            border_style="red",
            padding=(1, 2),
        )
    )

    # ─── Confirmations ───────────────────────────────────────────────────
    if not yes:
        if not Confirm.ask(
            f"\n[bold red]{t('account.confirm_delete_remote', lang=lang)}[/bold red]",
            default=False,
        ):
            console.print(
                f"\n[yellow]{t('account.deletion_aborted', lang=lang)}[/yellow]"
            )
            sys.exit(0)

    delete_local = not keep_local
    if not yes and not keep_local:
        delete_local = Confirm.ask(
            f"\n[yellow]{t('account.confirm_delete_local', lang=lang)}[/yellow]",
            default=True,
        )

    # ─── Remote deletion ─────────────────────────────────────────────────
    api = ApiClient()
    try:
        asyncio.run(
            api.invoke_ef(
                "cli-account-delete",
                {
                    "free_token": creds.free_token,
                    "language": lang,
                    "confirm": True,
                },
            )
        )
    except LovarchApiError as exc:
        err_console.print(f"\n[red]✗ {exc}[/red]")
        if exc.error_code:
            err_console.print(f"[dim](error_code: {exc.error_code})[/dim]")
        sys.exit(1)

    # ─── Local cleanup ───────────────────────────────────────────────────
    clear_credentials()
    if delete_local:
        projects_dir = DEFAULT_HOME / "projects"
        if projects_dir.exists():
            shutil.rmtree(projects_dir, ignore_errors=True)
        db_path = DEFAULT_HOME / "local.db"
        if db_path.exists():
            db_path.unlink()

    console.print(
        f"\n[bold green]{t('account.deletion_success', lang=lang)}[/bold green]\n"
    )
