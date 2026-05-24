"""Codex app-server への stdio JSON-RPC 通信を担う共通トランスポート。

codex app-server --listen stdio:// をサブプロセスとして起動し、
JSON-RPC 2.0 プロトコルで LLM を呼び出す。
各 Quiz/Roadmap/Ingestion LLM アダプタがこのトランスポートを使う。
"""

from __future__ import annotations

import json
import queue
import subprocess
import threading
import time
from dataclasses import dataclass
from typing import Any


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


_MAX_RETRIES = 2
_RETRY_BACKOFF_BASE = 2.0


class CodexLlmTransport:
    """codex app-server サブプロセスを管理し、JSON-RPC で LLM を呼び出す。

    初回 call() 時にサブプロセスを lazy start し、close() で終了する。
    一過性エラー (CodexTransportHttpError) 発生時は最大 _MAX_RETRIES 回リトライする。
    """

    def __init__(self, *, timeout: float = 120.0) -> None:
        self._timeout = timeout
        self._process: subprocess.Popen[bytes] | None = None
        self._lock = threading.Lock()
        self._next_id = 1
        self._initialized = False
        self._line_queue: queue.Queue[str | None] = queue.Queue()
        self._reader_thread: threading.Thread | None = None
        self._notification_buffer: list[dict[str, Any]] = []

    def call(
        self,
        messages: list[CodexMessage],
        *,
        model: str = "default",
        temperature: float = 0.7,
    ) -> str:
        """LLM に messages を送信し、応答テキストを返す。

        CodexTransportHttpError (タイムアウト・プロセスエラー) 発生時は
        最大 _MAX_RETRIES 回リトライする。
        CodexTransportResponseError (パースエラー) はリトライしない。
        """
        last_error: CodexTransportHttpError | None = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                return self._call_once(messages, model=model, temperature=temperature)
            except CodexTransportHttpError as exc:
                last_error = exc
                if attempt < _MAX_RETRIES:
                    with self._lock:
                        self._close_unlocked()
                    time.sleep(_RETRY_BACKOFF_BASE ** (attempt + 1))
        assert last_error is not None  # noqa: S101
        raise last_error

    def _call_once(
        self,
        messages: list[CodexMessage],
        *,
        model: str = "default",
        temperature: float = 0.7,  # noqa: ARG002
    ) -> str:
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
        self._initialized = False
        self._notification_buffer.clear()
        # Sentinel で reader thread を停止
        self._line_queue.put(None)

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

    def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
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

            if "id" in parsed and parsed["id"] == req_id:
                if "error" in parsed:
                    error = parsed["error"]
                    msg = f"JSON-RPC error {error.get('code')}: {error.get('message')}"
                    raise CodexTransportHttpError(msg)
                return parsed.get("result", {})

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
        return result["thread"]["id"]

    def _start_turn(self, thread_id: str, user_text: str) -> str:
        result = self._request("turn/start", {
            "threadId": thread_id,
            "input": [{"type": "text", "text": user_text, "text_elements": []}],
        })
        turn = result.get("turn", {})
        if turn.get("status") == "failed":
            error = turn.get("error", {})
            msg = f"Turn failed: {error.get('message', 'unknown')}"
            raise CodexTransportHttpError(msg)
        return turn["id"]

    def _collect_turn_response(self, turn_id: str) -> str:
        item_buffers: dict[str, str] = {}
        completed_messages: list[dict[str, Any]] = []

        # Process buffered notifications first
        buffered = list(self._notification_buffer)
        self._notification_buffer.clear()

        for notification in buffered:
            if self._handle_notification(
                notification, turn_id, item_buffers, completed_messages,
            ):
                return self._build_response(completed_messages, item_buffers)

        # Read until turn/completed
        deadline = time.monotonic() + self._timeout
        while True:
            line = self._read_line(deadline)
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue

            if "method" in parsed and "id" not in parsed:
                if self._handle_notification(
                    parsed, turn_id, item_buffers, completed_messages,
                ):
                    return self._build_response(completed_messages, item_buffers)
            elif "method" in parsed and "id" in parsed:
                self._reply_unsupported(parsed["id"], parsed["method"])

    def _handle_notification(
        self,
        notification: dict[str, Any],
        turn_id: str,
        item_buffers: dict[str, str],
        completed_messages: list[dict[str, Any]],
    ) -> bool:
        """notification を処理する。turn 完了なら True を返す。"""
        method = notification.get("method", "")
        params = notification.get("params", {})

        # turn/completed は params.turn.id で turnId を持つ
        if method == "turn/completed":
            turn = params.get("turn", {})
            if turn.get("id") != turn_id:
                return False
            if turn.get("status") == "failed":
                error = turn.get("error", {})
                msg = f"Turn failed: {error.get('message', 'unknown')}"
                raise CodexTransportHttpError(msg)
            return True

        if params.get("turnId") != turn_id:
            return False

        if method == "item/agentMessage/delta":
            item_id = params.get("itemId", "")
            delta = params.get("delta", "")
            item_buffers[item_id] = item_buffers.get(item_id, "") + delta

        elif method == "item/completed":
            item = params.get("item", {})
            if item.get("type") == "agentMessage":
                completed_messages.append(item)

        return False

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
            msg = "Empty response from codex app-server"
            raise CodexTransportResponseError(msg)
        return result


__all__ = [
    "CodexLlmTransport",
    "CodexMessage",
    "CodexTransportError",
    "CodexTransportHttpError",
    "CodexTransportResponseError",
]
