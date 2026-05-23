"""IngestionFeedbackLlmClient Protocol の Codex app-server concrete 実装。"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from uuid import UUID

from infrastructure.llm.codex_transport import (
    CodexLlmTransport,
    CodexMessage,
)
from ingestion.domain.ingestion_feedback_types import (
    IngestionFeedbackLlmCallError,
    IngestionFeedbackLlmResponse,
    IngestionFeedbackResponseFormatError,
)

if TYPE_CHECKING:
    from ingestion.domain.ingestion_feedback_types import (
        IngestionFeedbackLlmRequest,
    )

_JSON_INSTRUCTION = "必ず JSON のみで回答してください。JSON の外にテキストを含めないでください。"


class CodexIngestionFeedbackLlm:
    def __init__(self, transport: CodexLlmTransport) -> None:
        self._transport = transport

    def analyze(  # noqa: PLR0915
        self,
        request: IngestionFeedbackLlmRequest,
    ) -> IngestionFeedbackLlmResponse:
        candidates_text = "\n".join(
            f"- {c.id}: {c.display_path}" for c in request.roadmap_candidates
        ) if request.roadmap_candidates else "(候補なし)"
        chunks_text = "\n---\n".join(request.chunk_texts)

        system = (
            "あなたはノート分析AIです。ノートの内容を分析し、"  # noqa: RUF001
            "関連するロードマップ項目の選定、正確性チェック、改善提案を行ってください。\n"
            f"{_JSON_INSTRUCTION}\n"
            '形式: {"selected_roadmap_item_id": "UUID or null", '
            '"accuracy_check": "正確性チェック結果", '
            '"improvement_suggestions": ["提案1", "提案2"]}'
        )
        user = (
            f"ファイル: {request.source_path}\n"
            f"ロードマップ候補:\n{candidates_text}\n"
            f"チャンク:\n{chunks_text}"
        )
        try:
            raw = self._transport.call([
                CodexMessage(role="system", content=system),
                CodexMessage(role="user", content=user),
            ])
        except Exception as exc:
            msg = f"ingestion feedback LLM call failed: {exc}"
            raise IngestionFeedbackLlmCallError(msg) from exc

        try:
            data = json.loads(raw)
            if "selected_roadmap_item_id" not in data:
                msg = "missing required field: selected_roadmap_item_id"
                raise IngestionFeedbackResponseFormatError(msg)
            item_id_raw = data["selected_roadmap_item_id"]
            if item_id_raw is None:
                selected_id = None
            elif isinstance(item_id_raw, str) and item_id_raw:
                selected_id = UUID(item_id_raw)
                valid_ids = {c.id for c in request.roadmap_candidates}
                if valid_ids and selected_id not in valid_ids:
                    msg = f"selected_roadmap_item_id {selected_id} not in candidates"
                    raise IngestionFeedbackResponseFormatError(msg)
            else:
                msg = f"invalid selected_roadmap_item_id: {item_id_raw!r}"
                raise IngestionFeedbackResponseFormatError(msg)

            accuracy_check = data["accuracy_check"]
            if not isinstance(accuracy_check, str):
                msg = f"accuracy_check must be str, got {type(accuracy_check).__name__}"
                raise IngestionFeedbackResponseFormatError(msg)

            suggestions = data["improvement_suggestions"]
            if not isinstance(suggestions, list) or not all(isinstance(s, str) for s in suggestions):
                msg = f"improvement_suggestions must be list[str], got {suggestions!r}"
                raise IngestionFeedbackResponseFormatError(msg)

            return IngestionFeedbackLlmResponse(
                selected_roadmap_item_id=selected_id,
                accuracy_check=accuracy_check,
                improvement_suggestions=suggestions,
            )
        except IngestionFeedbackResponseFormatError:
            raise
        except Exception as exc:
            msg = f"ingestion feedback response parse failed: {exc}"
            raise IngestionFeedbackResponseFormatError(msg) from exc


__all__ = ["CodexIngestionFeedbackLlm"]
