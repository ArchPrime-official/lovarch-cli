"""archprime-cli — AI-powered architectural project execution CLI.

Squad di 17 agenti specializzati (mind clones di Schumacher, Baldwin, Mazria,
Deming, Juran, English, Dodds) che esegue audit, briefing, normativa IT, CAD,
BIM/IFC, computo metrico, capitolato, pratiche edilizie, contratto CNAPPC, energy/LCA
preliminare, dossier consolidato.

Two modes:
- Free: standalone (your own API keys, SQLite local, filesystem storage)
- Premium: Lovarch-integrated (Supabase + S3 + Edge Functions + credits)

Powered by Lovarch — https://lovarch.com
"""
from archprime_cli.version import __version__

__all__ = ["__version__"]
