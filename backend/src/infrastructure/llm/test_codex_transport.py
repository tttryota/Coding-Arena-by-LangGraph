"""CodexLlmTransport のリトライロジックのテスト。"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from infrastructure.llm.codex_transport import (
    CodexLlmTransport,
    CodexMessage,
    CodexTransportHttpError,
    CodexTransportResponseError,
)
from shared.observability import LlmCallMetrics, NoOpObservability


def test_extract_usage_details_normalizes_known_app_server_fields() -> None:
    usage = CodexLlmTransport._extract_usage_details(
        {
            "usage": {
                "inputTokens": 12,
                "outputTokens": 8,
                "totalTokens": 20,
                "cachedInputTokens": 4,
            },
        },
    )

    assert usage == {
        "input": 12,
        "output": 8,
        "total": 20,
        "cache_read_input_tokens": 4,
    }


def test_extract_usage_details_does_not_invent_missing_usage() -> None:
    assert CodexLlmTransport._extract_usage_details({}) == {}


def test_noop_observability_performs_no_network_or_stateful_work() -> None:
    observer = NoOpObservability()

    with observer.llm_call(
        operation="quiz.answer_evaluation",
        model="test",
        temperature=0.0,
        messages=[],
    ) as call:
        with call.attempt(1) as attempt:
            attempt.succeeded()
        call.succeeded(
            "ok",
            LlmCallMetrics(
                response_chars=2,
                child_rss_mb=None,
                recycle_reason=None,
            ),
        )

    assert observer.graph_config(
        flow="quiz",
        operation="start",
        session_id="session-1",
    ) == {}


class TestCallRetry:
    """call() のリトライ動作を検証する。"""

    @patch.object(CodexLlmTransport, "_call_once")
    @patch("infrastructure.llm.codex_transport.time.sleep")
    def test_first_attempt_succeeds(
        self,
        mock_sleep: MagicMock,
        mock_call_once: MagicMock,
    ) -> None:
        """テスト対象: call_with_retry 関数。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        mock_call_once.return_value = "ok"
        transport = CodexLlmTransport()
        messages = [CodexMessage(role="user", content="hello")]

        result = transport.call(messages)

        assert result == "ok"
        mock_call_once.assert_called_once()
        mock_sleep.assert_not_called()

    @patch.object(CodexLlmTransport, "_close_unlocked")
    @patch.object(CodexLlmTransport, "_call_once")
    @patch("infrastructure.llm.codex_transport.time.sleep")
    def test_retry_on_http_error_then_success(
        self,
        mock_sleep: MagicMock,
        mock_call_once: MagicMock,
        mock_close_unlocked: MagicMock,
    ) -> None:
        """テスト対象: call_with_retry 関数。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        mock_call_once.side_effect = [
            CodexTransportHttpError("timeout"),
            "ok",
        ]
        transport = CodexLlmTransport()
        messages = [CodexMessage(role="user", content="hello")]

        result = transport.call(messages)

        assert result == "ok"
        assert mock_call_once.call_count == 2
        mock_sleep.assert_called_once()
        mock_close_unlocked.assert_called_once()

    @patch.object(CodexLlmTransport, "_close_unlocked")
    @patch.object(CodexLlmTransport, "_call_once")
    @patch("infrastructure.llm.codex_transport.time.sleep")
    def test_all_retries_exhausted_raises(
        self,
        mock_sleep: MagicMock,
        mock_call_once: MagicMock,
        mock_close_unlocked: MagicMock,
    ) -> None:
        """テスト対象: call_with_retry 関数。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        error = CodexTransportHttpError("timeout")
        mock_call_once.side_effect = [error, error, error]
        transport = CodexLlmTransport()
        messages = [CodexMessage(role="user", content="hello")]

        with pytest.raises(CodexTransportHttpError) as exc_info:
            transport.call(messages)

        assert exc_info.value is error
        assert mock_call_once.call_count == 3
        assert mock_sleep.call_count == 2
        assert mock_close_unlocked.call_count == 2

    @patch.object(CodexLlmTransport, "_close_unlocked")
    @patch.object(CodexLlmTransport, "_call_once")
    @patch("infrastructure.llm.codex_transport.time.sleep")
    def test_response_error_not_retried(
        self,
        mock_sleep: MagicMock,
        mock_call_once: MagicMock,
        mock_close_unlocked: MagicMock,
    ) -> None:
        """テスト対象: call_with_retry 関数。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        error = CodexTransportResponseError("parse error")
        mock_call_once.side_effect = error
        transport = CodexLlmTransport()
        messages = [CodexMessage(role="user", content="hello")]

        with pytest.raises(CodexTransportResponseError) as exc_info:
            transport.call(messages)

        assert exc_info.value is error
        mock_call_once.assert_called_once()
        mock_sleep.assert_not_called()
        mock_close_unlocked.assert_not_called()

    @patch.object(CodexLlmTransport, "_close_unlocked")
    @patch.object(CodexLlmTransport, "_call_once")
    @patch("infrastructure.llm.codex_transport.time.sleep")
    def test_backoff_timing(
        self,
        mock_sleep: MagicMock,
        mock_call_once: MagicMock,
        mock_close_unlocked: MagicMock,
    ) -> None:
        """テスト対象: call_with_retry 関数。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        error = CodexTransportHttpError("timeout")
        mock_call_once.side_effect = [error, error, error]
        transport = CodexLlmTransport()
        messages = [CodexMessage(role="user", content="hello")]

        with pytest.raises(CodexTransportHttpError):
            transport.call(messages)

        calls = mock_sleep.call_args_list
        assert len(calls) == 2
        assert calls[0].args[0] == pytest.approx(2.0)  # 2^1
        assert calls[1].args[0] == pytest.approx(4.0)  # 2^2

    @patch.object(CodexLlmTransport, "_close_unlocked")
    @patch.object(CodexLlmTransport, "_call_once")
    @patch("infrastructure.llm.codex_transport.time.sleep")
    def test_second_retry_succeeds(
        self,
        mock_sleep: MagicMock,
        mock_call_once: MagicMock,
        mock_close_unlocked: MagicMock,
    ) -> None:
        """テスト対象: call_with_retry 関数。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        error = CodexTransportHttpError("timeout")
        mock_call_once.side_effect = [error, error, "ok"]
        transport = CodexLlmTransport()
        messages = [CodexMessage(role="user", content="hello")]

        result = transport.call(messages)

        assert result == "ok"
        assert mock_call_once.call_count == 3
        assert mock_sleep.call_count == 2
        assert mock_close_unlocked.call_count == 2


class TestCallObservability:
    @patch.object(CodexLlmTransport, "_close_unlocked")
    @patch.object(CodexLlmTransport, "_call_once")
    @patch("infrastructure.llm.codex_transport.time.sleep")
    def test_retry_success_records_attempts_and_logical_generation(
        self,
        mock_sleep: MagicMock,
        mock_call_once: MagicMock,
        mock_close_unlocked: MagicMock,
    ) -> None:
        del mock_sleep, mock_close_unlocked
        observer = MagicMock()
        logical_call = observer.llm_call.return_value.__enter__.return_value
        attempt = logical_call.attempt.return_value.__enter__.return_value
        mock_call_once.side_effect = [CodexTransportHttpError("timeout"), "ok"]
        transport = CodexLlmTransport(observability=observer)

        result = transport.call(
            [CodexMessage(role="user", content="hello")],
            operation="quiz.answer_evaluation",
        )

        assert result == "ok"
        assert [item.args[0] for item in logical_call.attempt.call_args_list] == [1, 2]
        attempt.failed.assert_called_once()
        attempt.succeeded.assert_called_once()
        metrics = logical_call.succeeded.call_args.args[1]
        assert metrics.attempts == 2
        logical_call.failed.assert_not_called()
        observer.llm_call.assert_called_once()

    @patch.object(CodexLlmTransport, "_call_once")
    def test_parse_failure_marks_logical_generation_as_error(
        self,
        mock_call_once: MagicMock,
    ) -> None:
        observer = MagicMock()
        logical_call = observer.llm_call.return_value.__enter__.return_value
        mock_call_once.side_effect = CodexTransportResponseError("parse error")
        transport = CodexLlmTransport(observability=observer)

        with pytest.raises(CodexTransportResponseError):
            transport.call([CodexMessage(role="user", content="hello")])

        logical_call.failed.assert_called_once()
        assert logical_call.failed.call_args.kwargs == {"attempts": 1}


class TestSendOsError:
    """_send() が OSError を CodexTransportHttpError に変換することを検証する。"""

    def test_broken_pipe_becomes_http_error(self) -> None:
        """テスト対象: CodexTransport._send 関連処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        transport = CodexLlmTransport()
        mock_stdin = MagicMock()
        mock_stdin.write.side_effect = BrokenPipeError("broken pipe")
        mock_process = MagicMock()
        mock_process.stdin = mock_stdin
        transport._process = mock_process
        with pytest.raises(CodexTransportHttpError, match="Failed to write"):
            transport._send({"test": "data"})

    def test_os_error_becomes_http_error(self) -> None:
        """テスト対象: CodexTransport._send 関連処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        transport = CodexLlmTransport()
        mock_stdin = MagicMock()
        mock_stdin.write.side_effect = OSError("I/O error")
        mock_process = MagicMock()
        mock_process.stdin = mock_stdin
        transport._process = mock_process
        with pytest.raises(CodexTransportHttpError, match="Failed to write"):
            transport._send({"test": "data"})


class TestRecycle:
    """成功した call 後の codex app-server recycle を検証する。"""

    @patch.object(CodexLlmTransport, "_close_unlocked")
    @patch.object(CodexLlmTransport, "_call_once")
    def test_recycles_after_max_calls(
        self,
        mock_call_once: MagicMock,
        mock_close_unlocked: MagicMock,
    ) -> None:
        mock_call_once.return_value = "ok"
        transport = CodexLlmTransport(max_calls=2, max_rss_mb=0)
        messages = [CodexMessage(role="user", content="hello")]

        assert transport.call(messages) == "ok"
        assert transport.call(messages) == "ok"

        mock_close_unlocked.assert_called_once()

    @patch.object(CodexLlmTransport, "_child_rss_mb", return_value=2048)
    @patch.object(CodexLlmTransport, "_close_unlocked")
    @patch.object(CodexLlmTransport, "_call_once")
    def test_recycles_after_max_rss(
        self,
        mock_call_once: MagicMock,
        mock_close_unlocked: MagicMock,
        mock_child_rss_mb: MagicMock,
    ) -> None:
        mock_call_once.return_value = "ok"
        transport = CodexLlmTransport(max_calls=0, max_rss_mb=1024)
        transport._process = SimpleNamespace(pid=123)  # type: ignore[assignment]

        assert transport.call([CodexMessage(role="user", content="hello")]) == "ok"

        mock_close_unlocked.assert_called_once()
        mock_child_rss_mb.assert_called_once_with(123)

    @patch.object(CodexLlmTransport, "_child_rss_mb", return_value=2048)
    @patch.object(CodexLlmTransport, "_close_unlocked")
    @patch.object(CodexLlmTransport, "_call_once")
    def test_zero_thresholds_disable_recycle(
        self,
        mock_call_once: MagicMock,
        mock_close_unlocked: MagicMock,
        mock_child_rss_mb: MagicMock,
    ) -> None:
        mock_call_once.return_value = "ok"
        transport = CodexLlmTransport(max_calls=0, max_rss_mb=0)
        transport._process = SimpleNamespace(pid=123)  # type: ignore[assignment]

        assert transport.call([CodexMessage(role="user", content="hello")]) == "ok"
        assert transport.call([CodexMessage(role="user", content="hello")]) == "ok"

        mock_close_unlocked.assert_not_called()
        assert mock_child_rss_mb.call_count == 2

    def test_next_call_starts_new_process_after_recycle(self) -> None:
        class FakeProcess:
            def __init__(self, pid: int) -> None:
                self.pid = pid

            def kill(self) -> None:
                pass

            def wait(self) -> None:
                pass

        class FakeTransport(CodexLlmTransport):
            def __init__(self) -> None:
                super().__init__(max_calls=1, max_rss_mb=0)
                self.starts = 0

            def _call_once(
                self,
                messages: list[CodexMessage],
                *,
                model: str = "default",
                temperature: float = 0.7,
            ) -> str:
                if self._process is None:
                    self.starts += 1
                    self._process = FakeProcess(self.starts)  # type: ignore[assignment]
                return "ok"

        transport = FakeTransport()

        assert transport.call([CodexMessage(role="user", content="hello")]) == "ok"
        assert transport.call([CodexMessage(role="user", content="hello")]) == "ok"

        assert transport.starts == 2
