"""lovarch-cli — AI-powered architectural project execution CLI.

Agenti LLM reali per architetti, interior designer, geometri e ingegneri:
progetto di interni, direzione lavori, preventivi, catasto, sicurezza,
strutture/impianti/energia, capitolato, computo metrico — più 12 verifiche
(deterministiche o adversarial a 2 modelli), CAD 2D DXF, render e workflow
orchestrati dal @progetto-chief. Tutto advisory (BOZZA): firma e responsabilità
restano del professionista abilitato.

Two modes:
- Free: CAD DXF, verifica misure/computo offline, skill (il TUO modello)
- Premium: Lovarch-integrated (agenti server-side, render, crediti)

Powered by Lovarch — https://app.lovarch.com
"""
from lovarch_cli.version import __version__

__all__ = ["__version__"]
