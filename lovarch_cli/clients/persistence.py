"""DataPersistenceClient — abstract interface for execution tracking.

Mirrors the 3 Lovarch tables (pm_squad_executions, pm_squad_steps,
pm_squad_qa_checks) but lives behind an ABC so the CLI can run against:
- Free mode:    SQLite local (~/.lovarch/local.db)
- Premium mode: Lovarch Supabase (Epic 3)

The methods declared here are the MINIMUM surface needed for the squad
pipeline to track executions. Lead/CRM/billing methods from the original
LovarchClient (1.000+ lines, 25 methods) are NOT abstracted — they belong
to premium mode only and live in lovarch_supabase_extras.py (Epic 3).

Status state machine for steps mirrors the squad workflow:
    Triaged → Routed → InProgress → Returned → QA_Pending
    QA_Pending → QA_Pass | QA_Reject
    QA_Pass → Validated → Done
    QA_Reject → InProgress (retry)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class StepStatus(str, Enum):
    """Step lifecycle states (matches squad workflow contract)."""

    TRIAGED = "Triaged"
    ROUTED = "Routed"
    IN_PROGRESS = "InProgress"
    RETURNED = "Returned"
    QA_PENDING = "QA_Pending"
    QA_PASS = "QA_Pass"
    QA_REJECT = "QA_Reject"
    VALIDATED = "Validated"
    DONE = "Done"


class ExecutionMode(str, Enum):
    """Backend mode."""

    FREE = "free"
    PREMIUM = "premium"


class QaVerdict(str, Enum):
    """QA gate verdicts (mirrors Lovarch convention)."""

    PASS = "PASS"
    CONCERNS = "CONCERNS"
    FAIL = "FAIL"
    WAIVED = "WAIVED"


@dataclass(frozen=True)
class Execution:
    """Squad execution metadata."""

    id: str
    project_id: str
    workflow: str
    mode: ExecutionMode
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Step:
    """Single agent step within an execution."""

    id: str
    execution_id: str
    agent: str
    task: str | None
    status: StepStatus
    started_at: datetime
    completed_at: datetime | None = None
    artifact_url: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class QaCheck:
    """QA gate verdict on a step."""

    id: str
    execution_id: str
    qa_agent: str
    target_step_id: str | None
    verdict: QaVerdict
    findings: str | None
    checked_at: datetime


class DataPersistenceClient(ABC):
    """Abstract backend for execution + steps + QA tracking."""

    @abstractmethod
    async def create_execution(
        self,
        project_id: str,
        workflow: str,
        mode: ExecutionMode,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Create an execution row, return its id."""

    @abstractmethod
    async def update_execution(
        self,
        execution_id: str,
        status: str,
        completed_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Update execution status / completion / metadata."""

    @abstractmethod
    async def insert_step(
        self,
        execution_id: str,
        agent: str,
        task: str | None,
        status: StepStatus = StepStatus.TRIAGED,
    ) -> str:
        """Insert a new step, return its id."""

    @abstractmethod
    async def update_step(
        self,
        step_id: str,
        status: StepStatus,
        artifact_url: str | None = None,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Update step status / artifact / error / metadata."""

    @abstractmethod
    async def insert_qa_check(
        self,
        execution_id: str,
        qa_agent: str,
        target_step_id: str | None,
        verdict: QaVerdict,
        findings: str | None = None,
    ) -> str:
        """Record a QA gate verdict, return its id."""

    @abstractmethod
    async def get_execution(self, execution_id: str) -> Execution | None:
        """Fetch execution by id."""

    @abstractmethod
    async def list_steps(self, execution_id: str) -> list[Step]:
        """List all steps for an execution, ordered by started_at."""

    @abstractmethod
    async def list_qa_checks(self, execution_id: str) -> list[QaCheck]:
        """List all QA verdicts for an execution."""
