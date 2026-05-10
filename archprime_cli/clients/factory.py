"""Client factory — returns the correct (DataPersistenceClient, StorageClient)
pair based on authentication mode.

Free mode  → LocalSqliteClient + LocalFilesystemStorage
Premium mode → LovarchSupabaseClient + LovarchStorage (uses keyring tokens)
"""
from __future__ import annotations

from pathlib import Path

from archprime_cli.clients.local_client import LocalFilesystemStorage, LocalSqliteClient
from archprime_cli.clients.persistence import DataPersistenceClient, ExecutionMode
from archprime_cli.clients.storage import StorageClient


def get_clients(
    mode: ExecutionMode,
    archprime_home: Path | None = None,
) -> tuple[DataPersistenceClient, StorageClient]:
    """Return (persistence_client, storage_client) for the given mode.

    Args:
        mode: free or premium
        archprime_home: override default ~/.archprime/ (mainly for tests)

    Raises:
        RuntimeError: premium requested but no session in keyring (user must
        run `arch login --premium` first).
    """
    if mode == ExecutionMode.FREE:
        persistence = LocalSqliteClient(archprime_home=archprime_home)
        # Reuse same SQLite handle for artifact metadata
        storage = LocalFilesystemStorage(
            archprime_home=archprime_home, sqlite_client=persistence
        )
        return persistence, storage

    if mode == ExecutionMode.PREMIUM:
        # Lazy imports — avoid loading httpx + Supabase modules in free flows
        from archprime_cli.auth.session import LovarchSession
        from archprime_cli.clients.lovarch_storage import LovarchStorage
        from archprime_cli.clients.lovarch_supabase import LovarchSupabaseClient

        session = LovarchSession.load()
        if session is None:
            msg = (
                "Premium mode requires authentication. Run "
                "'arch login --premium' first."
            )
            raise RuntimeError(msg)
        return LovarchSupabaseClient(session), LovarchStorage(session)

    msg = f"Unknown execution mode: {mode}"
    raise ValueError(msg)
