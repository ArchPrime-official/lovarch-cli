"""LovarchSupabaseClient — DataPersistenceClient via Supabase REST API.

Mirrors LocalSqliteClient but talks to the Lovarch Supabase via PostgREST
(/rest/v1/{table}) using a user Bearer token managed by LovarchSession
(auto-refresh on 401).

Tables:
- pm_squad_executions
- pm_squad_steps
- pm_squad_qa_checks

These are the same tables the Lovarch web app writes to — admin pages at
/admin/squad-execution/{id}/live read them in real time (Story 1.5 will
verify CLI executions appear in the dashboard alongside web ones).
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from archprime_cli.auth.session import LovarchSession, LovarchSessionError
from archprime_cli.clients.persistence import (
    DataPersistenceClient,
    Execution,
    ExecutionMode,
    QaCheck,
    QaVerdict,
    Step,
    StepStatus,
)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    # Supabase returns "2026-05-10T12:00:00.123456+00:00" — Python 3.11+ parses
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _parse_metadata(value: Any) -> dict[str, Any]:
    if not value:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}
    return {}


class LovarchSupabaseClient(DataPersistenceClient):
    """Premium-mode persistence backend via Supabase REST."""

    def __init__(self, session: LovarchSession) -> None:
        self._session = session

    # ─── Helper ───────────────────────────────────────────────────────────

    async def _post(self, table: str, body: dict[str, Any]) -> dict[str, Any]:
        path = f"/rest/v1/{table}"
        response = await self._session.request(
            "POST",
            path,
            json=body,
            headers={
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            },
        )
        if response.status_code >= 400:
            msg = (
                f"Supabase POST {table} failed: HTTP {response.status_code} "
                f"{response.text[:300]}"
            )
            raise LovarchSessionError(msg)
        data = response.json()
        if isinstance(data, list):
            return data[0] if data else {}
        return data

    async def _patch(
        self, table: str, filters: dict[str, str], body: dict[str, Any]
    ) -> None:
        path = f"/rest/v1/{table}"
        response = await self._session.request(
            "PATCH",
            path,
            params=filters,
            json=body,
            headers={"Content-Type": "application/json"},
        )
        if response.status_code >= 400:
            msg = (
                f"Supabase PATCH {table} failed: HTTP {response.status_code} "
                f"{response.text[:300]}"
            )
            raise LovarchSessionError(msg)

    async def _get(
        self, table: str, params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        path = f"/rest/v1/{table}"
        response = await self._session.request("GET", path, params=params)
        if response.status_code >= 400:
            msg = (
                f"Supabase GET {table} failed: HTTP {response.status_code} "
                f"{response.text[:300]}"
            )
            raise LovarchSessionError(msg)
        data = response.json()
        return data if isinstance(data, list) else []

    # ─── DataPersistenceClient impl ───────────────────────────────────────

    async def create_execution(
        self,
        project_id: str,
        workflow: str,
        mode: ExecutionMode,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        execution_id = str(uuid.uuid4())
        # Schema reference: pm_squad_executions has columns id, project_id,
        # workflow, status, started_at, completed_at, metadata. CLI rows
        # tagged with metadata.source='cli-{free,premium}' for filtering.
        meta = dict(metadata or {})
        meta.setdefault("source", f"cli-{mode.value}")
        meta.setdefault("cli_user_id", self._session.user_id)

        await self._post(
            "pm_squad_executions",
            {
                "id": execution_id,
                "project_id": project_id,
                "workflow": workflow,
                "status": "pending",
                "metadata": meta,
            },
        )
        return execution_id

    async def update_execution(
        self,
        execution_id: str,
        status: str,
        completed_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        body: dict[str, Any] = {"status": status}
        if completed_at is not None:
            body["completed_at"] = completed_at.isoformat(timespec="seconds")
        if metadata is not None:
            body["metadata"] = metadata
        await self._patch(
            "pm_squad_executions",
            {"id": f"eq.{execution_id}"},
            body,
        )

    async def insert_step(
        self,
        execution_id: str,
        agent: str,
        task: str | None,
        status: StepStatus = StepStatus.TRIAGED,
    ) -> str:
        step_id = str(uuid.uuid4())
        await self._post(
            "pm_squad_steps",
            {
                "id": step_id,
                "execution_id": execution_id,
                "agent": agent,
                "task": task,
                "status": status.value,
            },
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
        body: dict[str, Any] = {"status": status.value}
        if status in {StepStatus.DONE, StepStatus.QA_PASS, StepStatus.VALIDATED}:
            body["completed_at"] = datetime.utcnow().isoformat(timespec="seconds")
        if artifact_url is not None:
            body["artifact_url"] = artifact_url
        if error is not None:
            body["error"] = error
        if metadata is not None:
            body["metadata"] = metadata
        await self._patch("pm_squad_steps", {"id": f"eq.{step_id}"}, body)

    async def insert_qa_check(
        self,
        execution_id: str,
        qa_agent: str,
        target_step_id: str | None,
        verdict: QaVerdict,
        findings: str | None = None,
    ) -> str:
        qa_id = str(uuid.uuid4())
        await self._post(
            "pm_squad_qa_checks",
            {
                "id": qa_id,
                "execution_id": execution_id,
                "qa_agent": qa_agent,
                "target_step_id": target_step_id,
                "verdict": verdict.value,
                "findings": findings,
            },
        )
        return qa_id

    async def get_execution(self, execution_id: str) -> Execution | None:
        rows = await self._get(
            "pm_squad_executions",
            {"id": f"eq.{execution_id}", "select": "*"},
        )
        if not rows:
            return None
        r = rows[0]
        meta = _parse_metadata(r.get("metadata"))
        # Mode is implied by metadata.source='cli-{free,premium}'; default premium
        source = str(meta.get("source", "cli-premium"))
        mode = (
            ExecutionMode.FREE if source.endswith("free") else ExecutionMode.PREMIUM
        )
        return Execution(
            id=r["id"],
            project_id=r["project_id"],
            workflow=r["workflow"],
            mode=mode,
            status=r["status"],
            started_at=_parse_dt(r.get("started_at")) or datetime.utcnow(),
            completed_at=_parse_dt(r.get("completed_at")),
            metadata=meta,
        )

    async def list_steps(self, execution_id: str) -> list[Step]:
        rows = await self._get(
            "pm_squad_steps",
            {
                "execution_id": f"eq.{execution_id}",
                "select": "*",
                "order": "started_at.asc",
            },
        )
        return [
            Step(
                id=r["id"],
                execution_id=r["execution_id"],
                agent=r["agent"],
                task=r.get("task"),
                status=StepStatus(r["status"]),
                started_at=_parse_dt(r.get("started_at")) or datetime.utcnow(),
                completed_at=_parse_dt(r.get("completed_at")),
                artifact_url=r.get("artifact_url"),
                error=r.get("error"),
                metadata=_parse_metadata(r.get("metadata")),
            )
            for r in rows
        ]

    async def list_qa_checks(self, execution_id: str) -> list[QaCheck]:
        rows = await self._get(
            "pm_squad_qa_checks",
            {
                "execution_id": f"eq.{execution_id}",
                "select": "*",
                "order": "checked_at.asc",
            },
        )
        return [
            QaCheck(
                id=r["id"],
                execution_id=r["execution_id"],
                qa_agent=r["qa_agent"],
                target_step_id=r.get("target_step_id"),
                verdict=QaVerdict(r["verdict"]),
                findings=r.get("findings"),
                checked_at=_parse_dt(r.get("checked_at")) or datetime.utcnow(),
            )
            for r in rows
        ]
