"""Codex app-server への stdio JSON-RPC 通信を担う共通トランスポート。

codex app-server --listen stdio:// をサブプロセスとして起動し、
JSON-RPC 2.0 プロトコルで LLM を呼び出す。
各 Quiz/Roadmap/Ingestion LLM アダプタがこのトランスポートを使う。
"""

from __future__ import annotations

import json
import os
import queue
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import structlog

from shared.observability import (
    LlmCallMetrics,
    NoOpObservability,
    Observability,
)


class CodexTransportError(Exception):
    pass


class CodexTransportHttpError(CodexTransportError):
    """通信・プロセスエラー。名前は既存アダプターとの互換性のため維持。"""


class CodexTransportResponseError(CodexTransportError):
    pass


@dataclass(frozen=True)
class CodexMessage:
    role: str
    content: str


@dataclass(frozen=True)
class _CallPayload:
    text: str
    usage_details: dict[str, int] | None = None


@dataclass
class _TurnCollection:
    item_buffers: dict[str, str]
    completed_messages: list[dict[str, Any]]
    usage_details: dict[str, int]


_MAX_RETRIES = 2
_RETRY_BACKOFF_BASE = 2.0
_DEFAULT_MAX_CALLS = 20
_DEFAULT_MAX_RSS_MB = 1536

logger = structlog.get_logger(__name__)


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning("invalid integer environment value", name=name, value=raw)
        return default


class CodexLlmTransport:
    """codex app-server サブプロセスを管理し、JSON-RPC で LLM を呼び出す。

    初回 call() 時にサブプロセスを lazy start し、close() で終了する。
    一過性エラー (CodexTransportHttpError) 発生時は最大 _MAX_RETRIES 回リトライする。
    """

    def __init__(
        self,
        *,
        timeout: float = 120.0,
        max_calls: int | None = None,
        max_rss_mb: int | None = None,
        observability: Observability | None = None,
    ) -> None:
        self._timeout = timeout
        self._max_calls = (
            _env_int("CODEX_TRANSPORT_MAX_CALLS", _DEFAULT_MAX_CALLS)
            if max_calls is None
            else max_calls
        )
        self._max_rss_mb = (
            _env_int("CODEX_TRANSPORT_MAX_RSS_MB", _DEFAULT_MAX_RSS_MB)
            if max_rss_mb is None
            else max_rss_mb
        )
        self._process: subprocess.Popen[bytes] | None = None
        self._lock = threading.Lock()
        self._next_id = 1
        self._process_call_count = 0
        self._initialized = False
        self._line_queue: queue.Queue[str | None] = queue.Queue()
        self._reader_thread: threading.Thread | None = None
        self._notification_buffer: list[dict[str, Any]] = []
        self._observability = observability or NoOpObservability()

    def call(  # noqa: PLR0915
        self,
        messages: list[CodexMessage],
        *,
        model: str = "default",
        temperature: float = 0.7,
        operation: str = "codex.call",
    ) -> str:
        """LLM に messages を送信し、応答テキストを返す。

        CodexTransportHttpError (タイムアウト・プロセスエラー) 発生時は
        最大 _MAX_RETRIES 回リトライする。
        CodexTransportResponseError (パースエラー) はリトライしない。
        """
        observed_messages = [
            {"role": message.role, "content": message.content}
            for message in messages
        ]
        with self._observability.llm_call(
            operation=operation,
            model=model,
            temperature=temperature,
            messages=observed_messages,
        ) as observation:
            last_error: CodexTransportHttpError | None = None
            for attempt_index in range(_MAX_RETRIES + 1):
                attempt_number = attempt_index + 1
                try:
                    with observation.attempt(attempt_number) as attempt_observation:
                        result = self._call_once(
                            messages,
                            model=model,
                            temperature=temperature,
                        )
                        payload = (
                            result
                            if isinstance(result, _CallPayload)
                            else _CallPayload(text=result)
                        )
                        attempt_observation.succeeded()
                    metrics = self._after_successful_call(
                        payload.text,
                        usage_details=payload.usage_details,
                        attempts=attempt_number,
                    )
                    observation.succeeded(payload.text, metrics)
                    return payload.text
                except CodexTransportHttpError as exc:
                    attempt_observation.failed(exc)
                    last_error = exc
                    if attempt_index < _MAX_RETRIES:
                        with self._lock:
                            self._close_unlocked()
                        time.sleep(_RETRY_BACKOFF_BASE ** attempt_number)
                except Exception as exc:
                    attempt_observation.failed(exc)
                    observation.failed(exc, attempts=attempt_number)
                    raise
            assert last_error is not None  # noqa: S101
            observation.failed(last_error, attempts=_MAX_RETRIES + 1)
            raise last_error

    def _call_once(
        self,
        messages: list[CodexMessage],
        *,
        model: str = "default",
        temperature: float = 0.7,  # noqa: ARG002
    ) -> _CallPayload:
        """単一試行で LLM を呼び出す。"""
        with self._lock:
            self._ensure_started()
            if not self._initialized:
                self._do_initialize()

            system_parts = [m.content for m in messages if m.role == "system"]
            user_parts = [m.content for m in messages if m.role == "user"]
            system_text = "\n".join(system_parts) if system_parts else None
            user_text = "\n".join(user_parts) if user_parts else ""

            thread_id = self._create_thread(system_text, model)
            turn_id = self._start_turn(thread_id, user_text)
            return self._collect_turn_response(turn_id)

    def close(self) -> None:
        """サブプロセスを終了する。"""
        with self._lock:
            self._close_unlocked()

    def _close_unlocked(self) -> None:
        """lock 取得済みの状態でサブプロセスを終了する。"""
        if self._process is not None:
            self._process.kill()
            self._process.wait()
            self._process = None
        self._process_call_count = 0
        self._initialized = False
        self._notification_buffer.clear()
        # Sentinel で reader thread を停止
        self._line_queue.put(None)

    def _after_successful_call(
        self,
        response: str,
        *,
        usage_details: dict[str, int] | None = None,
        attempts: int = 1,
    ) -> LlmCallMetrics:
        """成功した call の計測と、必要なら子プロセス recycle を行う。"""
        with self._lock:
            proc = self._process
            pid = proc.pid if proc is not None else None
            self._process_call_count += 1
            call_count = self._process_call_count
            child_rss_mb = self._child_rss_mb(pid) if pid is not None else None
            recycle_reason = self._recycle_reason(call_count, child_rss_mb)
            logger.info(
                "codex_transport_call_completed",
                pid=pid,
                call_count=call_count,
                child_rss_mb=child_rss_mb,
                response_chars=len(response),
                recycle_reason=recycle_reason,
            )
            if recycle_reason is not None:
                self._close_unlocked()
            return LlmCallMetrics(
                response_chars=len(response),
                child_rss_mb=child_rss_mb,
                recycle_reason=recycle_reason,
                usage_details=usage_details,
                attempts=attempts,
            )

    def _recycle_reason(
        self,
        call_count: int,
        child_rss_mb: int | None,
    ) -> str | None:
        if self._max_calls > 0 and call_count >= self._max_calls:
            return "max_calls"
        if (
            self._max_rss_mb > 0
            and child_rss_mb is not None
            and child_rss_mb >= self._max_rss_mb
        ):
            return "max_rss_mb"
        return None

    @staticmethod
    def _child_rss_mb(pid: int) -> int | None:
        try:
            with Path(f"/proc/{pid}/status").open(encoding="utf-8") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        parts = line.split()
                        if len(parts) >= 2:
                            return int(parts[1]) // 1024
        except (FileNotFoundError, OSError, ValueError):
            pass
        try:
            result = subprocess.run(  # noqa: S603
                ["ps", "-o", "rss=", "-p", str(pid)],  # noqa: S607
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip()) // 1024
        except (OSError, ValueError):
            pass
        return None

    # ------------------------------------------------------------------
    # Subprocess lifecycle
    # ------------------------------------------------------------------

    def _ensure_started(self) -> None:
        if self._process is not None and self._process.poll() is None:
            return

        self._process = subprocess.Popen(
            ["codex", "app-server", "--listen", "stdio://"],  # noqa: S607
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        self._process_call_count = 0
        self._initialized = False
        self._notification_buffer.clear()
        self._line_queue = queue.Queue()
        self._start_reader()

    def _start_reader(self) -> None:
        proc = self._process
        line_queue = self._line_queue

        def _reader() -> None:
            if proc is None or proc.stdout is None:
                return
            while True:
                raw = proc.stdout.readline()
                if not raw:
                    break
                line = raw.decode("utf-8").strip()
                if line:
                    line_queue.put(line)
            # EOF reached — send sentinel
            line_queue.put(None)

        self._reader_thread = threading.Thread(target=_reader, daemon=True)
        self._reader_thread.start()

    # ------------------------------------------------------------------
    # JSON-RPC primitives
    # ------------------------------------------------------------------

    def _send(self, message: dict[str, Any]) -> None:
        if self._process is None or self._process.stdin is None:
            msg = "codex app-server is not running"
            raise CodexTransportHttpError(msg)
        raw = json.dumps(message) + "\n"
        try:
            self._process.stdin.write(raw.encode("utf-8"))
            self._process.stdin.flush()
        except OSError as exc:
            msg = f"Failed to write to codex app-server stdin: {exc}"
            raise CodexTransportHttpError(msg) from exc

    def _read_line(self, deadline: float) -> str:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            msg = "Timeout reading from codex app-server"
            raise CodexTransportHttpError(msg)
        try:
            line = self._line_queue.get(timeout=remaining)
        except queue.Empty:
            msg = "Timeout reading from codex app-server"
            raise CodexTransportHttpError(msg) from None
        if line is None:
            code = self._process.returncode if self._process else "unknown"
            msg = f"codex app-server exited unexpectedly (code {code})"
            raise CodexTransportHttpError(msg)
        return line

    def _request(  # noqa: PLR0915
        self, method: str, params: dict[str, Any],
    ) -> dict[str, Any]:
        req_id = self._next_id
        self._next_id += 1

        self._send({
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params,
        })

        deadline = time.monotonic() + self._timeout
        while True:
            line = self._read_line(deadline)
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(parsed, dict):
                continue

            if "id" in parsed and parsed["id"] == req_id:
                if "error" in parsed:
                    error = parsed["error"]
                    if not isinstance(error, dict):
                        msg = "JSON-RPC error payload must be an object"
                        raise CodexTransportResponseError(msg)
                    msg = f"JSON-RPC error {error.get('code')}: {error.get('message')}"
                    raise CodexTransportHttpError(msg)
                result = parsed.get("result", {})
                if not isinstance(result, dict):
                    msg = "JSON-RPC result must be an object"
                    raise CodexTransportResponseError(msg)
                return cast("dict[str, Any]", result)

            if "method" in parsed and "id" not in parsed:
                self._notification_buffer.append(parsed)
            elif "method" in parsed and "id" in parsed:
                self._reply_unsupported(parsed["id"], parsed["method"])

    def _reply_unsupported(self, req_id: int, method: str) -> None:
        self._send({
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32000,
                "message": f"client cannot handle app-server request: {method}",
            },
        })

    # ------------------------------------------------------------------
    # Protocol flow
    # ------------------------------------------------------------------

    def _do_initialize(self) -> None:
        self._request("initialize", {
            "clientInfo": {
                "name": "obsidian-backend",
                "title": "Obsidian Backend",
                "version": "0.1.0",
            },
            "capabilities": {
                "experimentalApi": True,
            },
        })
        self._initialized = True

    def _create_thread(
        self, system_text: str | None, model: str,
    ) -> str:
        params: dict[str, Any] = {
            "approvalPolicy": "never",
            "sandbox": "read-only",
            "ephemeral": True,
        }
        if system_text:
            params["developerInstructions"] = system_text
        if model != "default":
            params["model"] = model

        result = self._request("thread/start", params)
        thread = result.get("thread")
        if not isinstance(thread, dict):
            msg = "thread/start response must include thread"
            raise CodexTransportResponseError(msg)
        thread_id = thread.get("id")
        if not isinstance(thread_id, str):
            msg = "thread/start response must include thread.id"
            raise CodexTransportResponseError(msg)
        return thread_id

    def _start_turn(self, thread_id: str, user_text: str) -> str:
        result = self._request("turn/start", {
            "threadId": thread_id,
            "input": [{"type": "text", "text": user_text, "text_elements": []}],
        })
        turn = result.get("turn", {})
        if not isinstance(turn, dict):
            msg = "turn/start response must include turn"
            raise CodexTransportResponseError(msg)
        if turn.get("status") == "failed":
            error = turn.get("error", {})
            if not isinstance(error, dict):
                msg = "turn/start error payload must be an object"
                raise CodexTransportResponseError(msg)
            msg = f"Turn failed: {error.get('message', 'unknown')}"
            raise CodexTransportHttpError(msg)
        turn_id = turn.get("id")
        if not isinstance(turn_id, str):
            msg = "turn/start response must include turn.id"
            raise CodexTransportResponseError(msg)
        return turn_id

    def _collect_turn_response(self, turn_id: str) -> _CallPayload:
        collection = _TurnCollection(
            item_buffers={},
            completed_messages=[],
            usage_details={},
        )

        # Process buffered notifications first
        buffered = list(self._notification_buffer)
        self._notification_buffer.clear()

        for notification in buffered:
            if self._handle_notification(
                notification,
                turn_id,
                collection,
            ):
                return _CallPayload(
                    text=self._build_response(
                        collection.completed_messages,
                        collection.item_buffers,
                    ),
                    usage_details=collection.usage_details or None,
                )

        # Read until turn/completed
        deadline = time.monotonic() + self._timeout
        while True:
            line = self._read_line(deadline)
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(parsed, dict):
                continue

            if "method" in parsed and "id" not in parsed:
                if self._handle_notification(
                    parsed,
                    turn_id,
                    collection,
                ):
                    return _CallPayload(
                        text=self._build_response(
                            collection.completed_messages,
                            collection.item_buffers,
                        ),
                        usage_details=collection.usage_details or None,
                    )
            elif "method" in parsed and "id" in parsed:
                self._reply_unsupported(parsed["id"], parsed["method"])

    def _handle_notification(  # noqa: C901, PLR0915
        self,
        notification: dict[str, Any],
        turn_id: str,
        collection: _TurnCollection,
    ) -> bool:
        """notification を処理する。turn 完了なら True を返す。"""
        method = notification.get("method", "")
        params = notification.get("params", {})

        # turn/completed は params.turn.id で turnId を持つ
        if method == "turn/completed":
            turn = params.get("turn", {})
            if not isinstance(turn, dict):
                return False
            if turn.get("id") != turn_id:
                return False
            if turn.get("status") == "failed":
                error = turn.get("error", {})
                if not isinstance(error, dict):
                    msg = "turn/completed error payload must be an object"
                    raise CodexTransportResponseError(msg)
                msg = f"Turn failed: {error.get('message', 'unknown')}"
                raise CodexTransportHttpError(msg)
            collection.usage_details.update(self._extract_usage_details(turn))
            return True

        if params.get("turnId") != turn_id:
            return False

        if method == "item/agentMessage/delta":
            item_id = params.get("itemId", "")
            delta = params.get("delta", "")
            collection.item_buffers[item_id] = (
                collection.item_buffers.get(item_id, "") + delta
            )

        elif method == "item/completed":
            item = params.get("item", {})
            if not isinstance(item, dict):
                return False
            if item.get("type") == "agentMessage":
                collection.completed_messages.append(cast("dict[str, Any]", item))

        return False

    @staticmethod
    def _extract_usage_details(turn: dict[str, Any]) -> dict[str, int]:
        """Normalize token usage if the app-server includes it."""
        raw = turn.get("usage") or turn.get("tokenUsage")
        if not isinstance(raw, dict):
            return {}
        aliases = {
            "input": ("input_tokens", "inputTokens", "prompt_tokens", "promptTokens"),
            "output": (
                "output_tokens",
                "outputTokens",
                "completion_tokens",
                "completionTokens",
            ),
            "total": ("total_tokens", "totalTokens"),
            "cache_read_input_tokens": (
                "cached_input_tokens",
                "cachedInputTokens",
                "cacheReadInputTokens",
            ),
        }
        normalized: dict[str, int] = {}
        for target, source_names in aliases.items():
            value = next((raw.get(name) for name in source_names if name in raw), None)
            if isinstance(value, int) and value >= 0:
                normalized[target] = value
        return normalized

    @staticmethod
    def _build_response(
        completed_messages: list[dict[str, Any]],
        item_buffers: dict[str, str],
    ) -> str:
        texts: list[str] = []
        for msg in completed_messages:
            text = msg.get("text", "")
            if not text:
                text = item_buffers.get(msg.get("id", ""), "")
            if text:
                texts.append(text)

        if not texts:
            texts = [t for t in item_buffers.values() if t]

        result = "\n\n".join(texts)
        if not result:
            error_message = "Empty response from codex app-server"
            raise CodexTransportResponseError(error_message)
        return result


__all__ = [
    "CodexLlmTransport",
    "CodexMessage",
    "CodexTransportError",
    "CodexTransportHttpError",
    "CodexTransportResponseError",
]
