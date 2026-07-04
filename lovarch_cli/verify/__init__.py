"""`lovarch verifica` — data-checking workflows for architects, interior
designers, geometri and engineers.

Design (Onda 2 · F10): deterministic code first (cheap, exact — ezdxf/regex),
LLM only where judgment is needed, using the ADVERSARIAL two-model pattern:
Sonnet 5 (executor) extracts/structures → Opus 4.8 (verifier) tries to refute
each claim independently. Credits are debited per real tokens via cli-ai-text;
deterministic checks are free.
"""
from lovarch_cli.verify.computo import verify_computo
from lovarch_cli.verify.contratto import verify_contratto
from lovarch_cli.verify.dossier import verify_dossier
from lovarch_cli.verify.misure import verify_misure
from lovarch_cli.verify.normativa import verify_normativa
from lovarch_cli.verify.pratica import verify_pratica
from lovarch_cli.verify.sicurezza import verify_sicurezza
from lovarch_cli.verify.accessibilita import verify_accessibilita

__all__ = [
    "verify_computo", "verify_contratto", "verify_dossier",
    "verify_misure", "verify_normativa", "verify_pratica",
    "verify_sicurezza", "verify_accessibilita",
]
