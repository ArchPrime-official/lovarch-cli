"""LovarchStorage — StorageClient via Supabase Storage API.

Uploads CLI deliverables to the existing 'user-assets' bucket under a
prefix `archprime-cli/{execution_id}/{filename}`. This avoids creating a
new bucket for the alpha; Story 5.x can spin up a dedicated bucket if
volume warrants.

Auth: Bearer user token (Supabase Storage RLS allows authenticated users
to write under their own paths if the bucket is configured for it).

NOTE: actual bucket-level RLS for archprime-cli prefix needs a follow-up
migration (Story 5.x). For alpha, we rely on user-assets being permissive
for authenticated writes. If RLS denies, surfaces as a clear 403 error.
"""
from __future__ import annotations

import mimetypes
import uuid
from datetime import datetime
from pathlib import Path

from archprime_cli.auth.session import LovarchSession, LovarchSessionError
from archprime_cli.clients.storage import StorageClient, StoredArtifact

DEFAULT_BUCKET = "user-assets"
PATH_PREFIX = "archprime-cli"


def _object_path(execution_id: str, filename: str) -> str:
    return f"{PATH_PREFIX}/{execution_id}/{filename}"


class LovarchStorage(StorageClient):
    """Premium-mode storage backend via Supabase Storage."""

    def __init__(
        self, session: LovarchSession, bucket: str = DEFAULT_BUCKET
    ) -> None:
        self._session = session
        self._bucket = bucket

    def _public_url(self, object_path: str) -> str:
        # Public URL pattern (does not require signing for public bucket;
        # private buckets need signed URLs but we use user-assets which is
        # configured for authenticated read in Lovarch).
        api_base = self._session._api_url  # noqa: SLF001 (intentional)
        return f"{api_base}/storage/v1/object/public/{self._bucket}/{object_path}"

    async def save_artifact(
        self,
        execution_id: str,
        filename: str,
        data: bytes | Path,
        mime_type: str | None = None,
    ) -> StoredArtifact:
        path = _object_path(execution_id, filename)
        if isinstance(data, Path):
            payload = data.read_bytes()
        else:
            payload = data

        mime = mime_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"

        upload_url = f"/storage/v1/object/{self._bucket}/{path}"
        response = await self._session.request(
            "POST",
            upload_url,
            content=payload,
            headers={
                "Content-Type": mime,
                "x-upsert": "true",
            },
        )

        if response.status_code >= 400:
            msg = (
                f"Supabase Storage upload failed: HTTP {response.status_code} "
                f"{response.text[:300]}"
            )
            raise LovarchSessionError(msg)

        return StoredArtifact(
            id=str(uuid.uuid4()),
            execution_id=execution_id,
            filename=filename,
            url=self._public_url(path),
            mime_type=mime,
            size_bytes=len(payload),
            created_at=datetime.utcnow(),
        )

    async def read_artifact(self, artifact_id_or_url: str) -> bytes:
        # If we got a Supabase URL, extract the object path; else treat as
        # raw object path (caller knows bucket).
        if artifact_id_or_url.startswith("http"):
            marker = f"/object/public/{self._bucket}/"
            idx = artifact_id_or_url.find(marker)
            if idx < 0:
                marker_priv = f"/object/{self._bucket}/"
                idx = artifact_id_or_url.find(marker_priv)
                if idx < 0:
                    msg = f"Cannot extract object path from URL: {artifact_id_or_url}"
                    raise LovarchSessionError(msg)
                path = artifact_id_or_url[idx + len(marker_priv) :]
            else:
                path = artifact_id_or_url[idx + len(marker) :]
        else:
            path = artifact_id_or_url

        response = await self._session.request(
            "GET", f"/storage/v1/object/{self._bucket}/{path}"
        )
        if response.status_code >= 400:
            msg = (
                f"Supabase Storage read failed: HTTP {response.status_code} "
                f"{response.text[:300]}"
            )
            raise LovarchSessionError(msg)
        return response.content

    async def list_artifacts(self, execution_id: str) -> list[StoredArtifact]:
        prefix_path = _object_path(execution_id, "").rstrip("/")
        response = await self._session.request(
            "POST",
            f"/storage/v1/object/list/{self._bucket}",
            json={"prefix": prefix_path, "limit": 1000, "offset": 0},
        )
        if response.status_code >= 400:
            msg = (
                f"Supabase Storage list failed: HTTP {response.status_code} "
                f"{response.text[:300]}"
            )
            raise LovarchSessionError(msg)
        items = response.json() or []
        artifacts: list[StoredArtifact] = []
        for item in items:
            name = item.get("name", "")
            if not name:
                continue
            full_path = f"{prefix_path}/{name}"
            artifacts.append(
                StoredArtifact(
                    id=str(item.get("id") or uuid.uuid4()),
                    execution_id=execution_id,
                    filename=name,
                    url=self._public_url(full_path),
                    mime_type=item.get("metadata", {}).get("mimetype"),
                    size_bytes=int(item.get("metadata", {}).get("size", 0)),
                    created_at=datetime.utcnow(),
                )
            )
        return artifacts

    async def delete_artifacts(self, execution_id: str) -> int:
        # List first, then bulk delete
        artifacts = await self.list_artifacts(execution_id)
        if not artifacts:
            return 0

        prefix_path = _object_path(execution_id, "").rstrip("/")
        paths = [f"{prefix_path}/{a.filename}" for a in artifacts]

        response = await self._session.request(
            "DELETE",
            f"/storage/v1/object/{self._bucket}",
            json={"prefixes": paths},
        )
        if response.status_code >= 400:
            msg = (
                f"Supabase Storage delete failed: HTTP {response.status_code} "
                f"{response.text[:300]}"
            )
            raise LovarchSessionError(msg)
        return len(paths)
