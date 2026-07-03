"""`lovarch verifica` — data-checking workflows for architects, interior
designers, geometri and engineers.

Design (Onda 2 · F10): deterministic code first (cheap, exact — ezdxf/regex),
LLM only where judgment is needed, using the ADVERSARIAL two-model pattern:
Sonnet 5 (executor) extracts/structures → Opus 4.8 (verifier) tries to refute
each claim independently. Credits are debited per real tokens via cli-ai-text;
deterministic checks are free.
"""
from lovarch_cli.verify.misure import verify_misure
from lovarch_cli.verify.normativa import verify_normativa

__all__ = ["verify_misure", "verify_normativa"]
