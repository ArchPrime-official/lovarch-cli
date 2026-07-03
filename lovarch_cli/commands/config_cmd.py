"""`lovarch config` — manage user preferences and BYO API keys.

    lovarch config show
    lovarch config set language it
    lovarch config set openai_key sk-...
    lovarch config get storage_path
    lovarch config unset mapbox_token
"""
from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from lovarch_cli import config_store

console = Console()
err_console = Console(stderr=True)

config_app = typer.Typer(
    help="Configurazione utente (lingua, storage, API keys per il modo Free).",
    no_args_is_help=True,
)


@config_app.command("show")
def show_command() -> None:
    """Mostra la configurazione attuale (le chiavi segrete sono mascherate)."""
    table = Table(title="lovarch config", show_header=True, header_style="bold gold1")
    table.add_column("Chiave", style="cyan")
    table.add_column("Valore")
    table.add_column("Segreto", justify="center")
    for key, masked, is_secret in config_store.display_items():
        table.add_row(key, masked, "🔒" if is_secret else "")
    console.print(table)
    console.print(f"[dim]{config_store.config_path()}[/dim]")


@config_app.command("set")
def set_command(
    key: str = typer.Argument(..., help="language | storage_path | openai_key | mapbox_token"),
    value: str = typer.Argument(..., help="Il valore da impostare"),
) -> None:
    """Imposta una chiave di configurazione."""
    try:
        config_store.set_value(key, value)
    except config_store.ConfigError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)
    shown = config_store.mask(key, value)
    console.print(f"[green]✓[/green] {key} = {shown}")


@config_app.command("get")
def get_command(
    key: str = typer.Argument(..., help="La chiave da leggere"),
) -> None:
    """Legge il valore di una chiave (mascherato se segreto)."""
    try:
        value = config_store.get_value(key)
    except config_store.ConfigError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)
    console.print(config_store.mask(key, value))


@config_app.command("unset")
def unset_command(
    key: str = typer.Argument(..., help="La chiave da rimuovere"),
) -> None:
    """Rimuove una chiave di configurazione."""
    try:
        removed = config_store.unset_value(key)
    except config_store.ConfigError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)
    if removed:
        console.print(f"[green]✓[/green] rimosso: {key}")
    else:
        console.print(f"[dim]{key} non era impostato[/dim]")
