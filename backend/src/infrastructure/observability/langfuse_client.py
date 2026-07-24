"""Optional Langfuse-backed observability implementation."""

from __future__ import annotations

from contextlib import AbstractContextManager, contextmanager
from typing import TYPE_CHECKING, Any

import structlog

from shared.observability import LlmCallMetrics, NoOpObservability

if TYPE_CHECKING:
    from collections.abc import Iterator

    from infrastructure.config.settings import Settings

logger = structlog.get_logger(__name__)


class _LangfuseAttempt:
    def __init__(self, span: Any) -> None:
        self._span = span

    def succeeded(self) -> None:
        self._span.update(metadata={"status": "success"})

    def failed(self, error: Exception) -> None:
        self._span.update(
            level="ERROR",
            status_message=str(error),
            metadata={
                "status": "error",
                "error_type": type(error).__name__,
            },
        )


class _LangfuseCall:
    def __init__(self, generation: Any, *, capture_content: bool) -> None:
        self._generation = generation
        self._capture_content = capture_content

    @contextmanager
    def attempt(self, number: int) -> Iterator[_LangfuseAttempt]:
        with self._generation.start_as_current_observation(
            name="codex.attempt",
            as_type="span",
            metadata={"attempt": number},
        ) as span:
            yield _LangfuseAttempt(span)

    def succeeded(self, output: str, metrics: LlmCallMetrics) -> None:
        update: dict[str, Any] = {
            "output": (
                output
                if self._capture_content
                else {"response_chars": metrics.response_chars}
            ),
            "metadata": {
                "status": "success",
                "response_chars": metrics.response_chars,
                "child_rss_mb": metrics.child_rss_mb,
                "recycle_reason": metrics.recycle_reason,
                "attempts": metrics.attempts,
            },
        }
        if metrics.usage_details is not None:
            update["usage_details"] = metrics.usage_details
        self._generation.update(**update)

    def failed(self, error: Exception, *, attempts: int) -> None:
        self._generation.update(
            level="ERROR",
            status_message=str(error),
            metadata={
                "status": "error",
                "attempts": attempts,
                "error_type": type(error).__name__,
            },
        )


class LangfuseObservability:
    """Langfuse adapter with OpenTelemetry context propagation."""

    def __init__(self, settings: Settings) -> None:
        from langfuse import Langfuse
        from langfuse.langchain import CallbackHandler

        self._capture_content = settings.langfuse_capture_content
        self._client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            base_url=settings.langfuse_base_url,
            environment=settings.langfuse_tracing_environment,
            release=settings.langfuse_release,
            sample_rate=settings.langfuse_sample_rate,
            tracing_enabled=True,
        )
        self._callback = CallbackHandler()

    @contextmanager
    def llm_call(
        self,
        *,
        operation: str,
        model: str,
        temperature: float,
        messages: list[dict[str, str]],
    ) -> Iterator[_LangfuseCall]:
        input_value: object = messages if self._capture_content else {
            "message_count": len(messages),
        }
        with self._client.start_as_current_observation(
            name=operation,
            as_type="generation",
            model=model,
            model_parameters={"temperature": temperature},
            input=input_value,
        ) as generation:
            yield _LangfuseCall(
                generation,
                capture_content=self._capture_content,
            )

    def graph_scope(
        self,
        *,
        flow: str,
        operation: str,
        session_id: str,
    ) -> AbstractContextManager[None]:
        from langfuse import propagate_attributes

        return propagate_attributes(
            trace_name=f"{flow}.{operation}",
            session_id=session_id,
            tags=["langgraph", flow, operation],
            metadata={"flow": flow, "operation": operation},
        )

    def graph_config(
        self,
        *,
        flow: str,
        operation: str,
        session_id: str,
    ) -> dict[str, Any]:
        return {
            "callbacks": [self._callback],
            "run_name": f"{flow}.{operation}",
            "metadata": {
                "langfuse_session_id": session_id,
                "flow": flow,
                "operation": operation,
            },
        }

    def flush(self) -> None:
        try:
            self._client.flush()
        except Exception:
            logger.exception("langfuse_flush_failed")

    def shutdown(self) -> None:
        try:
            self._client.shutdown()
        except Exception:
            logger.exception("langfuse_shutdown_failed")


def create_observability(settings: Settings) -> NoOpObservability | LangfuseObservability:
    """Create tracing adapter; delivery failures remain fail-open."""
    if not settings.langfuse_tracing_enabled:
        return NoOpObservability()
    try:
        return LangfuseObservability(settings)
    except Exception:
        logger.exception("langfuse_initialization_failed")
        return NoOpObservability()


__all__ = ["LangfuseObservability", "create_observability"]
