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
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.text import Text

from archprime_cli.api import ApiClient, LovarchApiError
from archprime_cli.config import (
    DEFAULT_HOME,
    Credentials,
    clear_credentials,
    load_credentials,
)

console = Console()
err_console = Console(stderr=True)

app = typer.Typer(
    name="account",
    help="Gestione account (info, delete GDPR).",
    no_args_is_help=True,
)


# ════════════════════════════════════════════════════════════════════════════
# Localized strings (Story 2.3 — Epic 4 will extract)
# ════════════════════════════════════════════════════════════════════════════

I18N: dict[str, dict[str, str]] = {
    "no_account": {
        "it": "Nessun account configurato. Esegui 'arch signup' o 'arch login'.",
        "pt": "Nenhuma conta configurada. Execute 'arch signup' ou 'arch login'.",
        "en": "No account configured. Run 'arch signup' or 'arch login'.",
        "es": "Sin cuenta configurada. Ejecuta 'arch signup' o 'arch login'.",
    },
    "delete_warning_title": {
        "it": "⚠️  CANCELLAZIONE ACCOUNT — IRREVERSIBILE",
        "pt": "⚠️  EXCLUSÃO DE CONTA — IRREVERSÍVEL",
        "en": "⚠️  ACCOUNT DELETION — IRREVERSIBLE",
        "es": "⚠️  ELIMINACIÓN DE CUENTA — IRREVERSIBLE",
    },
    "delete_warning_body": {
        "it": (
            "Stai per cancellare il tuo account archprime-cli (modalità FREE).\n\n"
            "Cosa succede:\n"
            " • I tuoi dati personali (nome, email, telefono) saranno pseudonimizzati (GDPR Art. 17)\n"
            " • Il token verrà revocato — non potrai più usare archprime-cli con questo account\n"
            " • L'account ombra in Lovarch verrà eliminato\n"
            " • [bold]Opzionalmente[/bold] cancelliamo i progetti locali in ~/.archprime/projects/\n\n"
            "[red]Questa azione NON può essere annullata.[/red]"
        ),
        "pt": (
            "Você está prestes a excluir sua conta archprime-cli (modo FREE).\n\n"
            "O que acontece:\n"
            " • Seus dados pessoais (nome, email, telefone) serão pseudonimizados (GDPR/LGPD Art. 17)\n"
            " • O token será revogado — você não poderá mais usar archprime-cli com esta conta\n"
            " • A conta sombra na Lovarch será deletada\n"
            " • [bold]Opcionalmente[/bold] excluímos projetos locais em ~/.archprime/projects/\n\n"
            "[red]Esta ação NÃO pode ser desfeita.[/red]"
        ),
        "en": (
            "You are about to delete your archprime-cli account (FREE mode).\n\n"
            "What happens:\n"
            " • Your personal data (name, email, phone) will be pseudonymized (GDPR Art. 17)\n"
            " • Your token will be revoked — you won't be able to use archprime-cli with this account\n"
            " • The shadow account in Lovarch will be deleted\n"
            " • [bold]Optionally[/bold] we delete local projects in ~/.archprime/projects/\n\n"
            "[red]This action CANNOT be undone.[/red]"
        ),
        "es": (
            "Estás a punto de eliminar tu cuenta archprime-cli (modo FREE).\n\n"
            "Qué sucede:\n"
            " • Tus datos personales (nombre, email, teléfono) serán pseudonimizados (GDPR Art. 17)\n"
            " • El token será revocado — no podrás usar archprime-cli con esta cuenta\n"
            " • La cuenta sombra en Lovarch será eliminada\n"
            " • [bold]Opcionalmente[/bold] eliminamos proyectos locales en ~/.archprime/projects/\n\n"
            "[red]Esta acción NO se puede deshacer.[/red]"
        ),
    },
    "confirm_delete_remote": {
        "it": "Confermi la cancellazione dell'account remoto?",
        "pt": "Você confirma a exclusão da conta remota?",
        "en": "Confirm remote account deletion?",
        "es": "¿Confirmas la eliminación de la cuenta remota?",
    },
    "confirm_delete_local": {
        "it": "Vuoi anche cancellare i progetti locali in ~/.archprime/projects/?",
        "pt": "Deseja também excluir projetos locais em ~/.archprime/projects/?",
        "en": "Also delete local projects in ~/.archprime/projects/?",
        "es": "¿Eliminar también los proyectos locales en ~/.archprime/projects/?",
    },
    "deletion_aborted": {
        "it": "Cancellazione annullata. Nessun dato modificato.",
        "pt": "Exclusão cancelada. Nenhum dado modificado.",
        "en": "Deletion aborted. No data changed.",
        "es": "Eliminación cancelada. Ningún dato modificado.",
    },
    "deletion_success": {
        "it": "✓ Account cancellato. Grazie per aver provato archprime-cli.",
        "pt": "✓ Conta excluída. Obrigado por ter testado archprime-cli.",
        "en": "✓ Account deleted. Thanks for trying archprime-cli.",
        "es": "✓ Cuenta eliminada. Gracias por probar archprime-cli.",
    },
    "info_title": {
        "it": "Account corrente",
        "pt": "Conta atual",
        "en": "Current account",
        "es": "Cuenta actual",
    },
}


def t(key: str, lang: str = "it") -> str:
    return I18N.get(key, {}).get(lang) or I18N.get(key, {}).get("it") or key


@app.command(name="info", help="Mostra info dell'account corrente.")
def account_info() -> None:
    """Show currently logged-in account info."""
    creds = load_credentials()
    if creds.mode == "none":
        err_console.print(f"[yellow]{t('no_account', creds.language)}[/yellow]")
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
            title=f"[bold gold1]{t('info_title', creds.language)}[/bold gold1]",
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
            help="Keep ~/.archprime/projects/ local files after remote deletion.",
        ),
    ] = False,
) -> None:
    """Permanently delete CLI account (GDPR Art. 17 right-to-erasure)."""
    creds: Credentials = load_credentials()
    if creds.mode == "none" or not creds.free_token:
        err_console.print(f"[yellow]{t('no_account', creds.language)}[/yellow]")
        sys.exit(1)

    if creds.mode == "premium":
        err_console.print(
            "[yellow]Premium account deletion is handled in the Lovarch web app:\n"
            "  https://lovarch.com/settings/account/delete[/yellow]"
        )
        sys.exit(1)

    lang = creds.language

    # ─── Warning panel ───────────────────────────────────────────────────
    console.print()
    console.print(
        Panel(
            Text.from_markup(t("delete_warning_body", lang)),
            title=f"[bold red]{t('delete_warning_title', lang)}[/bold red]",
            border_style="red",
            padding=(1, 2),
        )
    )

    # ─── Confirmations ───────────────────────────────────────────────────
    if not yes:
        if not Confirm.ask(
            f"\n[bold red]{t('confirm_delete_remote', lang)}[/bold red]",
            default=False,
        ):
            console.print(f"\n[yellow]{t('deletion_aborted', lang)}[/yellow]")
            sys.exit(0)

    delete_local = not keep_local
    if not yes and not keep_local:
        delete_local = Confirm.ask(
            f"\n[yellow]{t('confirm_delete_local', lang)}[/yellow]", default=True
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

    console.print(f"\n[bold green]{t('deletion_success', lang)}[/bold green]\n")
