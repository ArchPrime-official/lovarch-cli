"""LocalSqliteClient + LocalFilesystemStorage — free-mode backend.

Stores execution tracking in ~/.archprime/local.db (SQLite) and artifacts in
~/.archprime/projects/{execution_id}/{filename}. Schema mirrors the relevant
subset of Lovarch's pm_squad_executions/steps/qa_checks tables.

Async API: stdlib sqlite3 is sync, but we wrap calls in asyncio.to_thread()
so the public interface matches the abstract contract. This avoids adding
aiosqlite as a dep for what is mostly low-volume tracking.

Threading note: each method opens its own connection (short-lived) — SQLite
file locking handles concurrent writers fine for our access pattern (one
pipeline_runner at a time, ~50 writes per execution).
"""
from __future__ import annotations

import asyncio
import json
import mimetypes
import shutil
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

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

DEFAULT_ARCHPRIME_HOME = Path.home() / ".archprime"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS executions (
    id           TEXT PRIMARY KEY,
    project_id   TEXT NOT NULL,
    workflow     TEXT NOT NULL,
    mode         TEXT NOT NULL CHECK (mode IN ('free','premium')),
    status       TEXT NOT NULL DEFAULT 'pending',
    started_at   TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    metadata     TEXT
);

CREATE TABLE IF NOT EXISTS steps (
    id            TEXT PRIMARY KEY,
    execution_id  TEXT NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    agent         TEXT NOT NULL,
    task          TEXT,
    status        TEXT NOT NULL,
    started_at    TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at  TEXT,
    artifact_url  TEXT,
    error         TEXT,
    metadata      TEXT
);

CREATE TABLE IF NOT EXISTS qa_checks (
    id              TEXT PRIMARY KEY,
    execution_id    TEXT NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    qa_agent        TEXT NOT NULL,
    target_step_id  TEXT REFERENCES steps(id),
    verdict         TEXT NOT NULL CHECK (verdict IN ('PASS','CONCERNS','FAIL','WAIVED')),
    findings        TEXT,
    checked_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS artifacts (
    id            TEXT PRIMARY KEY,
    execution_id  TEXT NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    filename      TEXT NOT NULL,
    path          TEXT NOT NULL,
    mime_type     TEXT,
    size_bytes    INTEGER NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_steps_execution    ON steps(execution_id);
CREATE INDEX IF NOT EXISTS idx_qa_execution       ON qa_checks(execution_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_execution ON artifacts(execution_id);
"""


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, isolation_level=None)  # autocommit
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _ensure_schema(db_path: Path) -> None:
    conn = _connect(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
    finally:
        conn.close()


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _parse_metadata(blob: str | None) -> dict[str, Any]:
    if not blob:
        return {}
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        return {}


# ════════════════════════════════════════════════════════════════════════════
# DataPersistenceClient — SQLite implementation
# ════════════════════════════════════════════════════════════════════════════


class LocalSqliteClient(DataPersistenceClient):
    """SQLite-backed execution/steps/QA tracker (free mode)."""

    def __init__(self, archprime_home: Path | None = None) -> None:
        self.home = archprime_home or DEFAULT_ARCHPRIME_HOME
        self.db_path = self.home / "local.db"
        _ensure_schema(self.db_path)

    def _execute(self, sql: str, params: tuple = ()) -> None:
        conn = _connect(self.db_path)
        try:
            conn.execute(sql, params)
        finally:
            conn.close()

    def _query(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        conn = _connect(self.db_path)
        try:
            return list(conn.execute(sql, params))
        finally:
            conn.close()

    async def create_execution(
        self,
        project_id: str,
        workflow: str,
        mode: ExecutionMode,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        execution_id = str(uuid.uuid4())
        await asyncio.to_thread(
            self._execute,
            "INSERT INTO executions(id, project_id, workflow, mode, status, metadata) "
            "VALUES (?, ?, ?, ?, 'pending', ?)",
            (execution_id, project_id, workflow, mode.value, json.dumps(metadata or {})),
        )
        return execution_id

    async def update_execution(
        self,
        execution_id: str,
        status: str,
        completed_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        sets = ["status = ?"]
        params: list[Any] = [status]
        if completed_at is not None:
            sets.append("completed_at = ?")
            params.append(completed_at.isoformat(timespec="seconds"))
        if metadata is not None:
            sets.append("metadata = ?")
            params.append(json.dumps(metadata))
        params.append(execution_id)
        await asyncio.to_thread(
            self._execute,
            f"UPDATE executions SET {', '.join(sets)} WHERE id = ?",
            tuple(params),
        )

    async def insert_step(
        self,
        execution_id: str,
        agent: str,
        task: str | None,
        status: StepStatus = StepStatus.TRIAGED,
    ) -> str:
        step_id = str(uuid.uuid4())
        await asyncio.to_thread(
            self._execute,
            "INSERT INTO steps(id, execution_id, agent, task, status) "
            "VALUES (?, ?, ?, ?, ?)",
            (step_id, execution_id, agent, task, status.value),
        )
        return step_id

    async def update_step(
        self,
        step_id: str,
        status: StepStatus,
        artifact_url: str | None = None,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        sets = ["status = ?"]
        params: list[Any] = [status.value]
        if status in {StepStatus.DONE, StepStatus.QA_PASS, StepStatus.VALIDATED}:
            sets.append("completed_at = ?")
            params.append(_now_iso())
        if artifact_url is not None:
            sets.append("artifact_url = ?")
            params.append(artifact_url)
        if error is not None:
            sets.append("error = ?")
            params.append(error)
        if metadata is not None:
            sets.append("metadata = ?")
            params.append(json.dumps(metadata))
        params.append(step_id)
        await asyncio.to_thread(
            self._execute,
            f"UPDATE steps SET {', '.join(sets)} WHERE id = ?",
            tuple(params),
        )

    async def insert_qa_check(
        self,
        execution_id: str,
        qa_agent: str,
        target_step_id: str | None,
        verdict: QaVerdict,
        findings: str | None = None,
    ) -> str:
        qa_id = str(uuid.uuid4())
        await asyncio.to_thread(
            self._execute,
            "INSERT INTO qa_checks(id, execution_id, qa_agent, target_step_id, "
            "verdict, findings) VALUES (?, ?, ?, ?, ?, ?)",
            (qa_id, execution_id, qa_agent, target_step_id, verdict.value, findings),
        )
        return qa_id

    async def get_execution(self, execution_id: str) -> Execution | None:
        rows = await asyncio.to_thread(
            self._query,
            "SELECT * FROM executions WHERE id = ?",
            (execution_id,),
        )
        if not rows:
            return None
        r = rows[0]
        return Execution(
            id=r["id"],
            project_id=r["project_id"],
            workflow=r["workflow"],
            mode=ExecutionMode(r["mode"]),
            status=r["status"],
            started_at=_parse_dt(r["started_at"]) or datetime.utcnow(),
            completed_at=_parse_dt(r["completed_at"]),
            metadata=_parse_metadata(r["metadata"]),
        )

    async def list_steps(self, execution_id: str) -> list[Step]:
        rows = await asyncio.to_thread(
            self._query,
            "SELECT * FROM steps WHERE execution_id = ? ORDER BY started_at ASC",
            (execution_id,),
        )
        return [
            Step(
                id=r["id"],
                execution_id=r["execution_id"],
                agent=r["agent"],
                task=r["task"],
                status=StepStatus(r["status"]),
                started_at=_parse_dt(r["started_at"]) or datetime.utcnow(),
                completed_at=_parse_dt(r["completed_at"]),
                artifact_url=r["artifact_url"],
                error=r["error"],
                metadata=_parse_metadata(r["metadata"]),
            )
            for r in rows
        ]

    async def list_qa_checks(self, execution_id: str) -> list[QaCheck]:
        rows = await asyncio.to_thread(
            self._query,
            "SELECT * FROM qa_checks WHERE execution_id = ? ORDER BY checked_at ASC",
            (execution_id,),
        )
        return [
            QaCheck(
                id=r["id"],
                execution_id=r["execution_id"],
                qa_agent=r["qa_agent"],
                target_step_id=r["target_step_id"],
                verdict=QaVerdict(r["verdict"]),
                findings=r["findings"],
                checked_at=_parse_dt(r["checked_at"]) or datetime.utcnow(),
            )
            for r in rows
        ]


# ════════════════════════════════════════════════════════════════════════════
# StorageClient — Filesystem implementation
# ════════════════════════════════════════════════════════════════════════════


class LocalFilesystemStorage(StorageClient):
    """Filesystem-backed artifact storage (free mode).

    Layout: {archprime_home}/projects/{execution_id}/{filename}
    Metadata is co-tracked in the SQLite `artifacts` table for fast listing.
    """

    def __init__(
        self,
        archprime_home: Path | None = None,
        sqlite_client: LocalSqliteClient | None = None,
    ) -> None:
        self.home = archprime_home or DEFAULT_ARCHPRIME_HOME
        self.projects_root = self.home / "projects"
        self.projects_root.mkdir(parents=True, exist_ok=True)
        # Reuse SQLite for artifact metadata
        self._db = sqlite_client or LocalSqliteClient(self.home)

    def _project_dir(self, execution_id: str) -> Path:
        d = self.projects_root / execution_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    async def save_artifact(
        self,
        execution_id: str,
        filename: str,
        data: bytes | Path,
        mime_type: str | None = None,
    ) -> StoredArtifact:
        target_dir = self._project_dir(execution_id)
        target = target_dir / filename
        if isinstance(data, Path):
            await asyncio.to_thread(shutil.copy2, data, target)
        else:
            await asyncio.to_thread(target.write_bytes, data)

        size = target.stat().st_size
        mime = mime_type or mimetypes.guess_type(filename)[0]
        artifact_id = str(uuid.uuid4())

        await asyncio.to_thread(
            self._db._execute,
            "INSERT INTO artifacts(id, execution_id, filename, path, mime_type, "
            "size_bytes) VALUES (?, ?, ?, ?, ?, ?)",
            (artifact_id, execution_id, filename, str(target), mime, size),
        )
        return StoredArtifact(
            id=artifact_id,
            execution_id=execution_id,
            filename=filename,
            url=f"file://{target}",
            mime_type=mime,
            size_bytes=size,
            created_at=datetime.utcnow(),
        )

    async def read_artifact(self, artifact_id_or_url: str) -> bytes:
        path: Path | None = None
        if artifact_id_or_url.startswith("file://"):
            path = Path(artifact_id_or_url[7:])
        else:
            rows = await asyncio.to_thread(
                self._db._query,
                "SELECT path FROM artifacts WHERE id = ?",
                (artifact_id_or_url,),
            )
            if rows:
                path = Path(rows[0]["path"])

        if not path or not path.exists():
            msg = f"Artifact not found: {artifact_id_or_url}"
            raise FileNotFoundError(msg)
        return await asyncio.to_thread(path.read_bytes)

    async def list_artifacts(self, execution_id: str) -> list[StoredArtifact]:
        rows = await asyncio.to_thread(
            self._db._query,
            "SELECT * FROM artifacts WHERE execution_id = ? ORDER BY created_at ASC",
            (execution_id,),
        )
        return [
            StoredArtifact(
                id=r["id"],
                execution_id=r["execution_id"],
                filename=r["filename"],
                url=f"file://{r['path']}",
                mime_type=r["mime_type"],
                size_bytes=r["size_bytes"],
                created_at=_parse_dt(r["created_at"]) or datetime.utcnow(),
            )
            for r in rows
        ]

    async def delete_artifacts(self, execution_id: str) -> int:
        # Delete files
        project_dir = self.projects_root / execution_id
        if project_dir.exists():
            await asyncio.to_thread(shutil.rmtree, project_dir, ignore_errors=True)
        # Delete metadata rows
        rows = await asyncio.to_thread(
            self._db._query,
            "SELECT COUNT(*) AS n FROM artifacts WHERE execution_id = ?",
            (execution_id,),
        )
        count = rows[0]["n"] if rows else 0
        await asyncio.to_thread(
            self._db._execute,
            "DELETE FROM artifacts WHERE execution_id = ?",
            (execution_id,),
        )
        return count
