"""Factory behavior for optional Langfuse tracing."""

from __future__ import annotations

from typing import Any

from infrastructure.config.settings import Settings
from infrastructure.observability import langfuse_client
from shared.observability import NoOpObservability


def test_disabled_tracing_returns_noop_without_constructing_sdk(
    monkeypatch: Any,
) -> None:
    def fail_if_called(settings: Settings) -> None:
        raise AssertionError(settings)

    monkeypatch.setattr(
        langfuse_client,
        "LangfuseObservability",
        fail_if_called,
    )

    observer = langfuse_client.create_observability(Settings())

    assert isinstance(observer, NoOpObservability)


def test_sdk_initialization_failure_is_fail_open(monkeypatch: Any) -> None:
    def fail_to_initialize(settings: Settings) -> None:
        raise ConnectionError(settings.langfuse_base_url)

    monkeypatch.setattr(
        langfuse_client,
        "LangfuseObservability",
        fail_to_initialize,
    )
    settings = Settings(
        langfuse_tracing_enabled=True,
        langfuse_public_key="pk-local",
        langfuse_secret_key="sk-local",  # noqa: S106
    )

    observer = langfuse_client.create_observability(settings)

    assert isinstance(observer, NoOpObservability)
