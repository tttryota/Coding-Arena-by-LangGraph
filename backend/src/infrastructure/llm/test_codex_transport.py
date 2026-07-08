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
