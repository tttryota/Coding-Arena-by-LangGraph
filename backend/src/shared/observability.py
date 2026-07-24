"""Observability ports shared by graph runners and infrastructure adapters."""

from __future__ import annotations

from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class LlmCallMetrics:
    """Metrics collected after one logical LLM call."""

    response_chars: int
    child_rss_mb: int | None
    recycle_reason: str | None
    usage_details: dict[str, int] | None = None
    attempts: int = 1


class AttemptObservation(Protocol):
    """Mutable observation for one transport attempt."""

    def succeeded(self) -> None: ...

    def failed(self, error: Exception) -> None: ...


class LlmCallObservation(Protocol):
    """Mutable observation for one logical LLM call."""

    def attempt(
        self,
        number: int,
    ) -> AbstractContextManager[AttemptObservation]: ...

    def succeeded(self, output: str, metrics: LlmCallMetrics) -> None: ...

    def failed(self, error: Exception, *, attempts: int) -> None: ...


class Observability(Protocol):
    """Cross-cutting tracing boundary."""

    def llm_call(
        self,
        *,
        operation: str,
        model: str,
        temperature: float,
        messages: list[dict[str, str]],
    ) -> AbstractContextManager[LlmCallObservation]: ...

    def graph_scope(
        self,
        *,
        flow: str,
        operation: str,
        session_id: str,
    ) -> AbstractContextManager[None]: ...

    def graph_config(
        self,
        *,
        flow: str,
        operation: str,
        session_id: str,
    ) -> dict[str, Any]: ...

    def flush(self) -> None: ...

    def shutdown(self) -> None: ...


class _NoOpAttempt:
    def succeeded(self) -> None:
        return

    def failed(self, error: Exception) -> None:
        del error


class _NoOpCall:
    def attempt(
        self,
        number: int,
    ) -> AbstractContextManager[AttemptObservation]:
        del number
        return nullcontext(_NoOpAttempt())

    def succeeded(self, output: str, metrics: LlmCallMetrics) -> None:
        del output, metrics

    def failed(self, error: Exception, *, attempts: int) -> None:
        del error, attempts


class NoOpObservability:
    """Observability implementation that performs no I/O."""

    def llm_call(
        self,
        *,
        operation: str,
        model: str,
        temperature: float,
        messages: list[dict[str, str]],
    ) -> AbstractContextManager[LlmCallObservation]:
        del operation, model, temperature, messages
        return nullcontext(_NoOpCall())

    def graph_scope(
        self,
        *,
        flow: str,
        operation: str,
        session_id: str,
    ) -> AbstractContextManager[None]:
        del flow, operation, session_id
        return nullcontext()

    def graph_config(
        self,
        *,
        flow: str,
        operation: str,
        session_id: str,
    ) -> dict[str, Any]:
        del flow, operation, session_id
        return {}

    def flush(self) -> None:
        return

    def shutdown(self) -> None:
        return


__all__ = [
    "AttemptObservation",
    "LlmCallMetrics",
    "LlmCallObservation",
    "NoOpObservability",
    "Observability",
]
