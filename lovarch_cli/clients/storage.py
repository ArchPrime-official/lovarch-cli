"""StorageClient — abstract interface for artifact persistence.

Two implementations:
- Free:    LocalFilesystemStorage  → ~/.lovarch/projects/{execution_id}/
- Premium: LovarchS3Storage        → Lovarch S3 buckets (Epic 3)
                                       (user-assets, render-images, moodboard-sources)

The squad generates 27 deliverables per execution (DXF, IFC, PDF, XLSX, JSON,
HTML, ZIP). All go through this interface so the same pipeline_runner code
works in both modes.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class StoredArtifact:
    """Reference to a stored artifact."""

    id: str
    execution_id: str
    filename: str
    url: str
    mime_type: str | None
    size_bytes: int
    created_at: datetime


class StorageClient(ABC):
    """Abstract backend for artifact storage (deliverables)."""

    @abstractmethod
    async def save_artifact(
        self,
        execution_id: str,
        filename: str,
        data: bytes | Path,
        mime_type: str | None = None,
    ) -> StoredArtifact:
        """Save artifact bytes (or copy from Path) and return reference.

        Args:
            execution_id: scope artifact to this run
            filename: target filename (e.g. 'pianta-progetto.dxf')
            data: raw bytes OR Path to source file
            mime_type: optional MIME type (defaults to guess by extension)
        """

    @abstractmethod
    async def read_artifact(self, artifact_id_or_url: str) -> bytes:
        """Read an artifact by id or url and return its bytes."""

    @abstractmethod
    async def list_artifacts(self, execution_id: str) -> list[StoredArtifact]:
        """List all artifacts for an execution."""

    @abstractmethod
    async def delete_artifacts(self, execution_id: str) -> int:
        """Delete all artifacts for an execution (GDPR right-to-erasure).

        Returns number of artifacts deleted.
        """
