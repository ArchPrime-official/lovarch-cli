"""arch signup — Free mode interactive registration with lead capture.

Flow:
  1. Welcome banner (4-language)
  2. Interactive prompts: full_name, email, phone, country, language
  3. GDPR consent (mandatory — Italian/EU compliance)
  4. POST → cli-signup EF (validates server-side, creates shadow user, lead)
  5. Save returned token to ~/.archprime/credentials.json (chmod 0600)
  6. Success message + next-steps (arch init, arch run)

Localization: hardcoded IT + PT + EN + ES strings here for Story 2.2.
Epic 4 Story 4.1 will extract into i18n/translations/*.json.
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

from archprime_cli.api import ApiClient, LovarchApiError
from archprime_cli.config import Credentials, save_credentials

console = Console()
err_console = Console(stderr=True)

EMAIL_RX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_RX = re.compile(r"^\+?[1-9]\d{6,14}$")
COUNTRY_RX = re.compile(r"^[A-Z]{2}$")

VALID_LANGUAGES = ["it", "pt", "en", "es"]


# ════════════════════════════════════════════════════════════════════════════
# Localized strings (Story 2.2 hardcoded — Epic 4 Story 4.1 extracts to JSON)
# ════════════════════════════════════════════════════════════════════════════

I18N: dict[str, dict[str, str]] = {
    "welcome_title": {
        "it": "Benvenuto in archprime-cli",
        "pt": "Bem-vindo ao archprime-cli",
        "en": "Welcome to archprime-cli",
        "es": "Bienvenido a archprime-cli",
    },
    "welcome_body": {
        "it": (
            "Modalità FREE — registrazione richiesta.\n\n"
            "Ti chiederemo nome, email, telefono e paese. Useremo queste "
            "informazioni solo per:\n"
            " • Confermare la tua identità\n"
            " • Inviarti aggiornamenti su archprime-cli (opt-out in qualsiasi momento)\n"
            " • Permetterti l'upgrade futuro a Premium con stesso account\n\n"
            "I tuoi dati sono protetti dal GDPR. Puoi cancellarli con "
            "[bold]arch account delete[/bold] in ogni momento."
        ),
        "pt": (
            "Modo FREE — cadastro obrigatório.\n\n"
            "Vamos pedir nome, email, telefone e país. Usaremos essas "
            "informações apenas para:\n"
            " • Confirmar sua identidade\n"
            " • Enviar atualizações sobre archprime-cli (opt-out a qualquer momento)\n"
            " • Permitir upgrade futuro para Premium com mesmo cadastro\n\n"
            "Seus dados são protegidos pelo GDPR/LGPD. Você pode deletar com "
            "[bold]arch account delete[/bold] a qualquer momento."
        ),
        "en": (
            "FREE Mode — registration required.\n\n"
            "We'll ask for name, email, phone, and country. We'll use this "
            "information only to:\n"
            " • Confirm your identity\n"
            " • Send archprime-cli updates (opt-out anytime)\n"
            " • Enable future Premium upgrade with the same account\n\n"
            "Your data is GDPR-protected. You can delete it with "
            "[bold]arch account delete[/bold] anytime."
        ),
        "es": (
            "Modo FREE — registro obligatorio.\n\n"
            "Pediremos nombre, email, teléfono y país. Usaremos esta "
            "información solo para:\n"
            " • Confirmar tu identidad\n"
            " • Enviar actualizaciones sobre archprime-cli (opt-out cuando quieras)\n"
            " • Permitir upgrade futuro a Premium con la misma cuenta\n\n"
            "Tus datos están protegidos por GDPR. Puedes eliminarlos con "
            "[bold]arch account delete[/bold] cuando quieras."
        ),
    },
    "prompt_language": {
        "it": "Lingua preferita",
        "pt": "Idioma preferido",
        "en": "Preferred language",
        "es": "Idioma preferido",
    },
    "prompt_full_name": {
        "it": "Nome completo",
        "pt": "Nome completo",
        "en": "Full name",
        "es": "Nombre completo",
    },
    "prompt_email": {
        "it": "Email",
        "pt": "Email",
        "en": "Email",
        "es": "Email",
    },
    "prompt_phone": {
        "it": "Telefono (formato internazionale, es. +39 123 456 7890)",
        "pt": "Telefone (formato internacional, ex. +55 11 98765-4321)",
        "en": "Phone (international format, e.g. +1 415 555 2671)",
        "es": "Teléfono (formato internacional, ej. +34 612 345 678)",
    },
    "prompt_country": {
        "it": "Codice paese ISO 3166 (es. IT, BR, US, ES)",
        "pt": "Código país ISO 3166 (ex. BR, IT, US, ES)",
        "en": "Country code ISO 3166 (e.g. US, IT, BR, ES)",
        "es": "Código país ISO 3166 (ej. ES, IT, US, BR)",
    },
    "prompt_consent": {
        "it": "Accetti i Termini di Servizio e la Privacy Policy (GDPR)?",
        "pt": "Você aceita os Termos de Serviço e Política de Privacidade (GDPR/LGPD)?",
        "en": "Do you accept the Terms of Service and Privacy Policy (GDPR)?",
        "es": "¿Aceptas los Términos de Servicio y Política de Privacidad (GDPR)?",
    },
    "tos_url_label": {
        "it": "TOS:",
        "pt": "TOS:",
        "en": "TOS:",
        "es": "TOS:",
    },
    "consent_required": {
        "it": "Il consenso GDPR è obbligatorio. Cadastro annullato.",
        "pt": "Consentimento GDPR é obrigatório. Cadastro cancelado.",
        "en": "GDPR consent is required. Signup cancelled.",
        "es": "Consentimiento GDPR es obligatorio. Registro cancelado.",
    },
    "invalid_email": {
        "it": "Email non valida.",
        "pt": "Email inválido.",
        "en": "Invalid email.",
        "es": "Email no válido.",
    },
    "invalid_phone": {
        "it": "Telefono deve essere in formato internazionale (es. +391234567890).",
        "pt": "Telefone deve estar em formato internacional (ex. +5511987654321).",
        "en": "Phone must be in international format (e.g. +14155552671).",
        "es": "Teléfono debe estar en formato internacional (ej. +34612345678).",
    },
    "invalid_country": {
        "it": "Codice paese deve essere 2 lettere (ISO 3166 alpha-2).",
        "pt": "Código país deve ser 2 letras (ISO 3166 alpha-2).",
        "en": "Country code must be 2 letters (ISO 3166 alpha-2).",
        "es": "Código país debe ser 2 letras (ISO 3166 alpha-2).",
    },
    "submitting": {
        "it": "Invio in corso...",
        "pt": "Enviando...",
        "en": "Submitting...",
        "es": "Enviando...",
    },
    "next_steps": {
        "it": (
            "[bold green]✓ Cadastro completato[/bold green]\n\n"
            "Prossimi passi:\n"
            " 1. [cyan]arch init <progetto>[/cyan] — crea un nuovo progetto\n"
            " 2. [cyan]arch audit <progetto>[/cyan] — verifica gli input\n"
            " 3. [cyan]arch run dal-brief-al-cantiere[/cyan] — esegui workflow\n\n"
            "Per upgrade a Premium (crediti inclusi): [link]https://lovarch.com/cli-upgrade[/link]"
        ),
        "pt": (
            "[bold green]✓ Cadastro concluído[/bold green]\n\n"
            "Próximos passos:\n"
            " 1. [cyan]arch init <projeto>[/cyan] — cria novo projeto\n"
            " 2. [cyan]arch audit <projeto>[/cyan] — verifica inputs\n"
            " 3. [cyan]arch run dal-brief-al-cantiere[/cyan] — executa workflow\n\n"
            "Upgrade pra Premium (créditos inclusos): [link]https://lovarch.com/cli-upgrade[/link]"
        ),
        "en": (
            "[bold green]✓ Signup complete[/bold green]\n\n"
            "Next steps:\n"
            " 1. [cyan]arch init <project>[/cyan] — create a new project\n"
            " 2. [cyan]arch audit <project>[/cyan] — verify inputs\n"
            " 3. [cyan]arch run dal-brief-al-cantiere[/cyan] — run workflow\n\n"
            "Upgrade to Premium (credits included): [link]https://lovarch.com/cli-upgrade[/link]"
        ),
        "es": (
            "[bold green]✓ Registro completado[/bold green]\n\n"
            "Próximos pasos:\n"
            " 1. [cyan]arch init <proyecto>[/cyan] — crea un nuevo proyecto\n"
            " 2. [cyan]arch audit <proyecto>[/cyan] — verifica inputs\n"
            " 3. [cyan]arch run dal-brief-al-cantiere[/cyan] — ejecuta workflow\n\n"
            "Upgrade a Premium (créditos incluidos): [link]https://lovarch.com/cli-upgrade[/link]"
        ),
    },
}


def t(key: str, lang: str = "it") -> str:
    """Lookup localized string with fallback chain: lang → it → key."""
    return I18N.get(key, {}).get(lang) or I18N.get(key, {}).get("it") or key


def detect_default_language() -> str:
    """Detect user's language from $LANG env var, fallback to 'it'."""
    import os

    env_lang = os.environ.get("LANG", "").split("_")[0].lower()
    return env_lang if env_lang in VALID_LANGUAGES else "it"


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
    lang = lang_flag if lang_flag in VALID_LANGUAGES else detect_default_language()

    # ─── Welcome banner ──────────────────────────────────────────────────
    console.print()
    console.print(
        Panel(
            Text.from_markup(t("welcome_body", lang)),
            title=f"[bold gold1]🎓 {t('welcome_title', lang)}[/bold gold1]",
            border_style="gold1",
            padding=(1, 2),
        )
    )
    console.print()

    # ─── Confirm/select language ─────────────────────────────────────────
    lang = Prompt.ask(
        f"[bold]{t('prompt_language', lang)}[/bold]",
        choices=VALID_LANGUAGES,
        default=lang,
    )

    # ─── Collect inputs ──────────────────────────────────────────────────
    while True:
        full_name = Prompt.ask(f"[bold]{t('prompt_full_name', lang)}[/bold]").strip()
        if len(full_name) >= 3:
            break
        err_console.print("[red]Min 3 caratteri[/red]")

    while True:
        email = Prompt.ask(f"[bold]{t('prompt_email', lang)}[/bold]").strip().lower()
        if EMAIL_RX.match(email):
            break
        err_console.print(f"[red]{t('invalid_email', lang)}[/red]")

    while True:
        phone = Prompt.ask(f"[bold]{t('prompt_phone', lang)}[/bold]").strip()
        if PHONE_RX.match(phone):
            break
        err_console.print(f"[red]{t('invalid_phone', lang)}[/red]")

    while True:
        country = (
            Prompt.ask(f"[bold]{t('prompt_country', lang)}[/bold]").strip().upper()
        )
        if COUNTRY_RX.match(country):
            break
        err_console.print(f"[red]{t('invalid_country', lang)}[/red]")

    # ─── GDPR consent (mandatory) ────────────────────────────────────────
    if not yes:
        console.print(
            f"\n[dim]{t('tos_url_label', lang)} https://lovarch.com/legal/cli-tos[/dim]"
        )
        accept = Confirm.ask(
            f"[bold yellow]{t('prompt_consent', lang)}[/bold yellow]", default=False
        )
        if not accept:
            err_console.print(f"\n[red]✗ {t('consent_required', lang)}[/red]")
            raise typer.Exit(1)

    # ─── Submit to EF ────────────────────────────────────────────────────
    console.print(f"\n[dim]{t('submitting', lang)}[/dim]")
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
            Text.from_markup(t("next_steps", lang)),
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print(f"\n[dim]Credentials: {creds_path}[/dim]")
