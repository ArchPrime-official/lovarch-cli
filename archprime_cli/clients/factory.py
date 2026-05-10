"""Client factory — returns the correct (DataPersistenceClient, StorageClient)
pair based on authentication mode.

Free mode  → LocalSqliteClient + LocalFilesystemStorage
Premium mode → LovarchSupabaseClient + LovarchS3Storage (Epic 3)
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
        NotImplementedError: premium mode not yet implemented (Epic 3)
    """
    if mode == ExecutionMode.FREE:
        persistence = LocalSqliteClient(archprime_home=archprime_home)
        # Reuse same SQLite handle for artifact metadata
        storage = LocalFilesystemStorage(
            archprime_home=archprime_home, sqlite_client=persistence
        )
        return persistence, storage

    if mode == ExecutionMode.PREMIUM:
        msg = (
            "Premium mode requires Lovarch authentication (Epic 3 — not yet "
            "implemented). For now, use 'arch login --free' to run standalone "
            "with your own API keys."
        )
        raise NotImplementedError(msg)

    msg = f"Unknown execution mode: {mode}"
    raise ValueError(msg)
