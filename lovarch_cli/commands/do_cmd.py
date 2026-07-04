"""`lovarch do` — run platform workflows from the terminal (premium).

    lovarch do render "soggiorno minimal, luce naturale" -o render.png
    lovarch do render "attico" --mode plan_to_3d --ref pianta.png
    lovarch do colors --style natural
    lovarch do copy "consegna ristrutturazione attico Brera"

Credits are debited server-side by the platform (same as the web app); costs
are always expressed in the user's credits.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import typer
from rich.console import Console
from lovarch_cli.upsell import not_authenticated

console = Console()
err_console = Console(stderr=True)

do_app = typer.Typer(
    help="Esegui i workflow della piattaforma Lovarch (premium).",
    no_args_is_help=True,
)


def _workflows():
    from lovarch_cli.auth.session import LovarchSession
    from lovarch_cli.workflows import PlatformWorkflows

    session = LovarchSession.load()
    if session is None:
        not_authenticated()
        raise typer.Exit(1)
    return PlatformWorkflows(session)


def _lang(language: str | None) -> str:
    if language:
        return language
    from lovarch_cli.i18n import current_lang

    return current_lang()


@do_app.command("render")
def render_command(
    description: str = typer.Argument(..., help="Descrizione della scena da renderizzare."),
    output: Path = typer.Option(Path("render.png"), "--output", "-o", help="File di destinazione."),
    mode: str = typer.Option(None, "--mode", help="room_render | render_3d | plan_to_3d | lighting_only | closeup_detail | closeup_angle (vuoto = sketch/testo→render 2D)."),
    style: str = typer.Option("moderno", "--style", "-s", help="Stile del render."),
    aspect: str = typer.Option("16:9", "--aspect", help="Aspect ratio (16:9, 9:16, 1:1, 4:3, 3:4)."),
    ref: Path = typer.Option(None, "--ref", help="Immagine di riferimento (sketch/foto/pianta)."),
    language: str = typer.Option(None, "--language", help="Lingua dell'output (default: configurata)."),
) -> None:
    """Render fotorealistico via Render Studio (crediti addebitati dalla piattaforma)."""
    from lovarch_cli.mcp.tools import tool_render

    out = asyncio.run(tool_render(
        _workflows(), description=description, output_path=str(output),
        mode=mode or None, render_style=style, aspect_ratio=aspect,
        reference_image_path=str(ref) if ref else None, language=_lang(language),
    ))
    if not out.get("ok"):
        err_console.print(f"[red]✗ {out.get('error')}[/red]")
        raise typer.Exit(1)
    if out.get("saved_to"):
        console.print(f"[green]✓[/green] Render salvato: [bold]{out['saved_to']}[/bold]")
    if out.get("image_url"):
        console.print(f"[dim]Nel tuo account Lovarch: {out['image_url']}[/dim]")


@do_app.command("colors")
def colors_command(
    style: str = typer.Option("modern", "--style", "-s", help="modern | vintage | natural | bold | custom."),
    base: str = typer.Option(None, "--base", help="Colori base separati da virgola (es. '#A16207,#09090B')."),
    image_url: str = typer.Option(None, "--from-image", help="URL immagine da cui estrarre la palette."),
    language: str = typer.Option(None, "--language", help="Lingua dell'output."),
) -> None:
    """Palette colori brand via piattaforma."""
    wf = _workflows()
    from lovarch_cli.workflows import WorkflowError

    try:
        out = asyncio.run(wf.colors(
            style=style,
            base_colors=[c.strip() for c in base.split(",")] if base else None,
            image_url=image_url, language=_lang(language),
        ))
    except WorkflowError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)
    console.print_json(json.dumps(out, ensure_ascii=False))


@do_app.command("copy")
def copy_command(
    brief: str = typer.Argument(..., help="Brief del contenuto (min 5 caratteri)."),
    mode: str = typer.Option("post", "--mode", help="post | story | carousel."),
    slides: int = typer.Option(5, "--slides", help="Numero slide (solo carousel)."),
    language: str = typer.Option(None, "--language", help="Lingua dell'output."),
) -> None:
    """Copy di marketing (caption + hashtags) via piattaforma."""
    wf = _workflows()
    from lovarch_cli.workflows import WorkflowError

    try:
        out = asyncio.run(wf.copy(brief, mode=mode, slide_count=slides, language=_lang(language)))
    except WorkflowError as exc:
        err_console.print(f"[red]✗ {exc}[/red]")
        raise typer.Exit(1)
    if out.get("caption"):
        console.print(f"\n[bold gold1]Caption[/bold gold1]\n{out['caption']}\n")
    if out.get("hashtags"):
        console.print("[bold gold1]Hashtags[/bold gold1]\n" + " ".join(out["hashtags"]) + "\n")
    rest = {k: v for k, v in out.items() if k not in ("caption", "hashtags")}
    if rest:
        console.print_json(json.dumps(rest, ensure_ascii=False))


@do_app.command("logo")
def logo_command(
    prompt: str = typer.Argument(..., help="Descrizione del logo / brand."),
    output: Path = typer.Option(Path("logo.png"), "--output", "-o"),
    ref: Path = typer.Option(None, "--ref", help="Immagine di riferimento."),
    language: str = typer.Option(None, "--language"),
) -> None:
    """Logo pack del brand via piattaforma."""
    from lovarch_cli.mcp.tools import tool_logo

    out = asyncio.run(tool_logo(_workflows(), prompt=prompt, output_path=str(output),
                                reference_image_path=str(ref) if ref else None, language=_lang(language)))
    if not out.get("ok"):
        err_console.print(f"[red]✗ {out.get('error')}[/red]"); raise typer.Exit(1)
    if out.get("saved_to"):
        console.print(f"[green]✓[/green] Logo: [bold]{out['saved_to']}[/bold]")
    if out.get("image_url"):
        console.print(f"[dim]Nel tuo account: {out['image_url']}[/dim]")


@do_app.command("site")
def site_command(
    prompt: str = typer.Argument(..., help="Descrizione del sito web."),
    output: Path = typer.Option(Path("site.html"), "--output", "-o"),
    language: str = typer.Option(None, "--language"),
) -> None:
    """Genera un sito web (HTML) via piattaforma."""
    from lovarch_cli.mcp.tools import tool_site

    out = asyncio.run(tool_site(_workflows(), prompt=prompt, output_path=str(output), language=_lang(language)))
    if not out.get("ok"):
        err_console.print(f"[red]✗ {out.get('error')}[/red]"); raise typer.Exit(1)
    console.print(f"[green]✓[/green] Sito: [bold]{out['saved_to']}[/bold] ({out.get('bytes', 0)} bytes)")


@do_app.command("script")
def script_command(
    topic: str = typer.Argument(..., help="Argomento dello script."),
    type: str = typer.Option("reel", "--type", help="reel | post | carousel | video…"),
    goal: str = typer.Option("educare", "--goal", help="Obiettivo del contenuto."),
    tone: str = typer.Option("professionale", "--tone", help="Tono di voce."),
    cta: str = typer.Option("", "--cta", help="Call-to-action."),
    output: Path = typer.Option(None, "--output", "-o", help="Salva lo script su file."),
    language: str = typer.Option(None, "--language"),
) -> None:
    """Script di contenuto strutturato via piattaforma (addebita crediti)."""
    wf = _workflows()
    from lovarch_cli.workflows import WorkflowError

    try:
        s = asyncio.run(wf.script(topic, type=type, goal=goal, tone=tone, cta=cta,
                                  language=_lang(language)))
    except WorkflowError as exc:
        err_console.print(f"[red]✗ {exc}[/red]"); raise typer.Exit(1)

    title = s.get("title") or topic
    content = s.get("content") or ""
    console.print(f"\n[bold gold1]{title}[/bold gold1]\n")
    if content:
        console.print(content)
    if s.get("keywords"):
        console.print("\n[dim]" + " ".join(s["keywords"]) + "[/dim]")
    if not s.get("persisted", True):
        console.print("\n[yellow]⚠ Non salvato nel tuo account (crediti rimborsati).[/yellow]")
    if output:
        Path(output).expanduser().write_text(content or title, encoding="utf-8")
        console.print(f"\n[green]✓[/green] salvato: {output}")

