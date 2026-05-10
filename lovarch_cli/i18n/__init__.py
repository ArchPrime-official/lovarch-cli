"""lovarch-cli i18n — bundled translations + lookup loader.

4 languages supported (CLAUDE.md MANDATORY: 4 langs always):
- it (Italiano) — DEFAULT
- pt (Português)
- en (English)
- es (Español)

Usage in subcommands:

    from lovarch_cli.i18n import t, current_lang

    print(t("signup.welcome_title"))
    print(t("signup.invalid_email", lang="pt"))

Detection chain (in current_lang()):
  1. Explicit override via set_current_lang(...) (set by --lang flag in cli.py)
  2. LOVARCH_LANG env var
  3. LANG env var (e.g. 'it_IT.UTF-8' → 'it')
  4. Default: 'it'

Fallback chain on missing key:
  requested_lang → 'it' → 'en' → key itself (returned as-is for visibility)
"""
from lovarch_cli.i18n.loader import current_lang, set_current_lang, t

__all__ = ["t", "current_lang", "set_current_lang"]
