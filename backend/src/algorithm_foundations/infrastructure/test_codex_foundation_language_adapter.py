from __future__ import annotations

import pytest

from algorithm_foundations.domain.foundation_types import (
    AlgorithmFoundationLanguageAdaptationError,
)
from algorithm_foundations.infrastructure.codex_foundation_language_adapter import (
    CodexAlgorithmFoundationLanguageAdapter,
)
from infrastructure.llm.codex_transport import CodexTransportHttpError


class _FakeTransport:
    def __init__(self, response: str = '{"reference_solution":"code"}') -> None:
        self.response = response
        self.error: Exception | None = None
        self.calls: list[dict[str, object]] = []

    def call(
        self,
        messages: list[object],
        *,
        model: str,
        temperature: float = 0.7,
        operation: str = "codex.call",
    ) -> str:
        self.calls.append(
            {
                "messages": messages,
                "model": model,
                "temperature": temperature,
            },
        )
        del operation
        if self.error is not None:
            raise self.error
        return self.response


def test_returns_canonical_solution_when_language_matches() -> None:
    transport = _FakeTransport()
    adapter = CodexAlgorithmFoundationLanguageAdapter(transport)  # type: ignore[arg-type]

    result = adapter.adapt_reference_solution(
        canonical_reference_solution="def solve():\n    print(1)\n",
        canonical_language="python",
        target_language="python",
        problem_statement="問題文",
        input_format="入力",
        output_format="出力",
        constraints="制約",
        examples=[{"input": "1", "output": "1"}],
    )

    assert result == "def solve():\n    print(1)\n"
    assert transport.calls == []


def test_adapts_solution_for_different_language() -> None:
    transport = _FakeTransport(
        response='{"reference_solution":"function solve(): void {\\n  console.log(1);\\n}"}',
    )
    adapter = CodexAlgorithmFoundationLanguageAdapter(transport)  # type: ignore[arg-type]

    result = adapter.adapt_reference_solution(
        canonical_reference_solution="def solve():\n    print(1)\n",
        canonical_language="python",
        target_language="typescript",
        problem_statement="問題文",
        input_format="入力",
        output_format="出力",
        constraints="制約",
        examples=[{"input": "1", "output": "1"}],
    )

    assert "function solve" in result
    assert len(transport.calls) == 1


def test_raises_parse_error_for_invalid_response() -> None:
    transport = _FakeTransport(response='{"reference_solution": 1}')
    adapter = CodexAlgorithmFoundationLanguageAdapter(transport)  # type: ignore[arg-type]

    with pytest.raises(AlgorithmFoundationLanguageAdaptationError) as exc_info:
        adapter.adapt_reference_solution(
            canonical_reference_solution="def solve():\n    print(1)\n",
            canonical_language="python",
            target_language="typescript",
            problem_statement="問題文",
            input_format="入力",
            output_format="出力",
            constraints="制約",
            examples=[{"input": "1", "output": "1"}],
        )
    assert exc_info.value.error_code == "llm_response_parse_failed"


def test_raises_request_failed_for_transport_error() -> None:
    transport = _FakeTransport()
    transport.error = CodexTransportHttpError("boom")
    adapter = CodexAlgorithmFoundationLanguageAdapter(transport)  # type: ignore[arg-type]

    with pytest.raises(AlgorithmFoundationLanguageAdaptationError) as exc_info:
        adapter.adapt_reference_solution(
            canonical_reference_solution="def solve():\n    print(1)\n",
            canonical_language="python",
            target_language="typescript",
            problem_statement="問題文",
            input_format="入力",
            output_format="出力",
            constraints="制約",
            examples=[{"input": "1", "output": "1"}],
        )
    assert exc_info.value.error_code == "llm_request_failed"
