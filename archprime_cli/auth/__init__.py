"""archprime-cli auth — premium PKCE flow + token storage.

Three modules:
- pkce.py            → verifier/challenge generation (RFC 7636)
- local_server.py    → ephemeral HTTP listener on 127.0.0.1:RANDOM/callback
- keyring_store.py   → OS-native secure storage (macOS Keychain, Windows
                       Credential Manager, Linux Secret Service)

The flow (orchestrated in commands/login.py):
1. Generate verifier + challenge via pkce.PkceParams.generate()
2. Spin up local_server.AuthServer on 127.0.0.1:RANDOM_PORT
3. Open browser to https://lovarch.com/cli-auth?...&redirect_uri=http://127.0.0.1:PORT/callback
4. User authorizes on lovarch.com → web POSTs to cli-auth-store EF →
   web redirects browser back to local server with ?code=X&state=Y
5. Local server captures code+state, validates state, calls cli-auth-exchange
6. Tokens returned → stored via keyring_store.save_premium_session()
"""
from archprime_cli.auth.keyring_store import (
    PremiumSession,
    clear_premium_session,
    load_premium_session,
    save_premium_session,
)
from archprime_cli.auth.pkce import PkceParams

__all__ = [
    "PkceParams",
    "PremiumSession",
    "clear_premium_session",
    "load_premium_session",
    "save_premium_session",
]
