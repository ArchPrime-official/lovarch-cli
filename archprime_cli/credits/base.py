"""Credits — abstract base + value types."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class CreditsBalance:
    """Snapshot of a user's credit standing at a point in time.

    Attributes:
        balance: total credits granted (monthly + bonus).
        monthly_used: credits consumed since the start of the cycle.
        credits_remaining: max(0, balance - monthly_used).
        is_admin: admins bypass credit gates entirely.
        required: threshold the caller asked us to compare against, or None.
        sufficient: is_admin OR credits_remaining >= required (True when
            required is None — i.e. caller just wants the balance).
    """

    balance: int
    monthly_used: int
    credits_remaining: int
    is_admin: bool
    required: int | None
    sufficient: bool

    @property
    def deficit(self) -> int:
        """How many extra credits the user needs to cross `required`.

        Returns 0 when sufficient or when no required threshold was given.
        """
        if self.sufficient or self.required is None:
            return 0
        return max(0, self.required - self.credits_remaining)


class InsufficientCreditsError(Exception):
    """Raised when a pipeline cannot proceed because of credit shortage.

    Carries the full balance so callers can render rich error UI.
    """

    def __init__(self, balance: CreditsBalance) -> None:
        self.balance = balance
        super().__init__(
            f"Insufficient credits: have {balance.credits_remaining}, "
            f"need {balance.required} (deficit: {balance.deficit})"
        )


class CreditsClient(ABC):
    """Backend-agnostic credits interface.

    Free mode returns an unlimited no-op; Premium calls cli-credits-check.
    """

    @abstractmethod
    async def check(self, required: int | None = None) -> CreditsBalance:
        """Fetch the user's current balance.

        Args:
            required: if given, server compares and sets `sufficient`.

        Returns:
            CreditsBalance snapshot.

        Raises:
            RuntimeError: backend communication failure.
        """
        raise NotImplementedError

    async def check_or_raise(self, required: int) -> CreditsBalance:
        """Fetch balance and raise InsufficientCreditsError if not sufficient.

        Convenience wrapper around `check()` for callers that just want to
        gate an operation.
        """
        balance = await self.check(required=required)
        if not balance.sufficient:
            raise InsufficientCreditsError(balance)
        return balance
