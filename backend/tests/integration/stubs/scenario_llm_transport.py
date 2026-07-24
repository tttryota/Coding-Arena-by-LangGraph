"""ScenarioLlmTransport: インテグレーションテスト用 LLM スタブ。

CodexLlmTransport.call() と同じシグネチャを持ち、
シナリオ駆動で応答を返す。成功した呼び出しの履歴を CallRecord として記録する。
例外で終了した呼び出しは記録されない。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from infrastructure.llm.codex_transport import CodexMessage


@dataclass(frozen=True)
class CallRecord:
    """成功した 1 回の LLM 呼び出し記録。例外で終了した呼び出しは記録されない。"""

    messages: list[CodexMessage]
    model: str
    temperature: float
    response: str


@dataclass(frozen=True)
class PatternRule:
    """パターンマッチルール。user メッセージに pattern が含まれたら response を返す。"""

    pattern: str
    response: str


class ScenarioExhaustedError(Exception):
    """Sequential モードでレスポンスが枯渇した。"""


class NoPatternMatchError(Exception):
    """Pattern-matched モードでマッチするルールがない。"""


class ScenarioLlmTransport:
    """Sequential / Pattern-matched の 2 モードで応答を返すテスト用トランスポート。"""

    def __init__(self) -> None:
        self._sequential_responses: list[str] = []
        self._pattern_rules: list[PatternRule] = []
        self._call_index: int = 0
        self._records: list[CallRecord] = []

    def set_sequential_responses(self, responses: list[str]) -> None:
        """Sequential モード: N 回目の呼び出しに responses[N] を返す。パターンルールはクリアされる。"""
        self._sequential_responses = list(responses)
        self._pattern_rules.clear()
        self._call_index = 0

    def add_pattern_rule(self, pattern: str, response: str) -> None:
        """Pattern-matched モード: user メッセージに pattern が含まれたら response を返す。Sequential レスポンスはクリアされる。"""
        self._sequential_responses.clear()
        self._call_index = 0
        self._pattern_rules.append(PatternRule(pattern=pattern, response=response))

    def call(
        self,
        messages: list[CodexMessage],
        *,
        model: str = "default",
        temperature: float = 0.7,
        operation: str = "codex.call",
    ) -> str:
        """CodexLlmTransport.call() と同じシグネチャ。"""
        response = self._resolve_response(messages)
        self._records.append(
            CallRecord(
                messages=list(messages),
                model=model,
                temperature=temperature,
                response=response,
            ),
        )
        del operation
        return response

    @property
    def records(self) -> list[CallRecord]:
        """成功した呼び出しの履歴。例外で終了した呼び出しは含まれない。"""
        return list(self._records)

    @property
    def call_count(self) -> int:
        return len(self._records)

    def reset(self) -> None:
        """状態をリセット。"""
        self._sequential_responses.clear()
        self._pattern_rules.clear()
        self._call_index = 0
        self._records.clear()

    def _resolve_response(self, messages: list[CodexMessage]) -> str:
        """設定済みモードに応じてレスポンス決定戦略を切り替える。"""
        if self._pattern_rules:
            return self._resolve_pattern(messages)
        return self._resolve_sequential()

    def _resolve_sequential(self) -> str:
        """呼び出し順に応答を返す。"""
        if self._call_index >= len(self._sequential_responses):
            msg = (
                f"Sequential responses exhausted: "
                f"call #{self._call_index + 1}, "
                f"available={len(self._sequential_responses)}"
            )
            raise ScenarioExhaustedError(msg)
        response = self._sequential_responses[self._call_index]
        self._call_index += 1
        return response

    def _resolve_pattern(self, messages: list[CodexMessage]) -> str:
        """直近 user メッセージに基づいてパターンマッチする。"""
        user_content = self._extract_user_content(messages)
        for rule in self._pattern_rules:
            if rule.pattern in user_content:
                return rule.response
        msg = f"No pattern matched for user content: {user_content[:200]}"
        raise NoPatternMatchError(msg)

    def _extract_user_content(self, messages: list[CodexMessage]) -> str:
        """最新の user メッセージ本文だけを抜き出す。"""
        for msg in reversed(messages):
            if msg.role == "user":
                return msg.content
        return ""


__all__ = [
    "CallRecord",
    "NoPatternMatchError",
    "PatternRule",
    "ScenarioExhaustedError",
    "ScenarioLlmTransport",
]
