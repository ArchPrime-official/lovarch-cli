"""Backend clients — abstract interfaces + concrete implementations.

Two backend modes:
- Free:    LocalSqliteClient + LocalFilesystemStorage (no Lovarch deps)
- Premium: LovarchSupabaseClient + LovarchS3Storage  (Epic 3 — Lovarch backend)

Use `get_clients(mode)` from factory.py to obtain the correct pair for the
current authentication state.
"""
from archprime_cli.clients.factory import get_clients
from archprime_cli.clients.persistence import (
    DataPersistenceClient,
    Execution,
    ExecutionMode,
    QaCheck,
    QaVerdict,
    Step,
    StepStatus,
)
from archprime_cli.clients.storage import StorageClient, StoredArtifact

__all__ = [
    "DataPersistenceClient",
    "Execution",
    "ExecutionMode",
    "QaCheck",
    "QaVerdict",
    "StepStatus",
    "StorageClient",
    "Step",
    "StoredArtifact",
    "get_clients",
]
