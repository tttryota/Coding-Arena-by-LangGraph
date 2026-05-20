from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

import pytest
from structlog.testing import capture_logs

from core.ingestion.infrastructure.ingestion_feedback import generate_for_file
from core.ingestion.infrastructure.ingestion_feedback_types import (
    IngestionFeedbackChunkInput,
    IngestionFeedbackGenerateInput,
    IngestionFeedbackGenerateResult,
    IngestionFeedbackInputError,
    IngestionFeedbackLlmCallError,
    IngestionFeedbackLlmRequest,
    IngestionFeedbackLlmResponse,
    IngestionFeedbackPersistenceError,
    IngestionFeedbackResponseFormatError,
    IngestionFeedbackRoadmapLookupError,
    NewIngestionFeedbackRecord,
    RoadmapCandidate,
    StoredIngestionFeedback,
)

if TYPE_CHECKING:
    from collections.abc import MutableMapping

_ROADMAP_ID = UUID("11111111-1111-1111-1111-111111111111")
_SECOND_ROADMAP_ID = UUID("22222222-2222-2222-2222-222222222222")
_FEEDBACK_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_SECOND_FEEDBACK_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_THIRD_FEEDBACK_ID = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_OUTSIDE_ROADMAP_ID = UUID("99999999-9999-9999-9999-999999999999")


class _RecordingRoadmapReader:
    def __init__(
        self,
        *,
        items: list[RoadmapCandidate] | None = None,
        error: Exception | None = None,
    ) -> None:
        self._items = list(items or [])
        self._error = error
        self.calls = 0

    def list_items(self) -> list[RoadmapCandidate]:
        self.calls += 1
        if self._error is not None:
            raise self._error
        return list(self._items)


class _RecordingLlmClient:
    def __init__(
        self,
        *,
        response: object | None = None,
        error: Exception | None = None,
        event_log: list[str] | None = None,
    ) -> None:
        self._response = response
        self._error = error
        self._event_log = event_log
        self.calls: list[IngestionFeedbackLlmRequest] = []

    def analyze(
        self,
        request: IngestionFeedbackLlmRequest,
    ) -> IngestionFeedbackLlmResponse:
        self.calls.append(request)
        if self._event_log is not None:
            self._event_log.append("llm.analyze")
        if self._error is not None:
            raise self._error
        assert self._response is not None
        return cast("IngestionFeedbackLlmResponse", self._response)


class _RecordingWriter:
    def __init__(
        self,
        *,
        stored_feedback: object | None = None,
        error: Exception | None = None,
        event_log: list[str] | None = None,
    ) -> None:
        self._stored_feedback = stored_feedback
        self._error = error
        self._event_log = event_log
        self.calls: list[NewIngestionFeedbackRecord] = []

    def create(
        self,
        record: NewIngestionFeedbackRecord,
    ) -> StoredIngestionFeedback:
        self.calls.append(record)
        if self._event_log is not None:
            self._event_log.append("writer.create")
        if self._error is not None:
            raise self._error
        assert self._stored_feedback is not None
        return cast("StoredIngestionFeedback", self._stored_feedback)


class _AppendingWriter:
    def __init__(
        self,
        *,
        existing_records: list[StoredIngestionFeedback],
        next_feedback_id: UUID,
    ) -> None:
        self.records = list(existing_records)
        self._next_feedback_id = next_feedback_id
        self.calls: list[NewIngestionFeedbackRecord] = []

    def create(
        self,
        record: NewIngestionFeedbackRecord,
    ) -> StoredIngestionFeedback:
        self.calls.append(record)
        stored_feedback = StoredIngestionFeedback(
            id=self._next_feedback_id,
            source_path=record.source_path,
            roadmap_item_id=record.roadmap_item_id,
            title=record.title,
            body=record.body,
            is_read=record.is_read,
            created_at=record.created_at,
            read_at=record.read_at,
        )
        self.records.append(stored_feedback)
        return stored_feedback


class _MissingAccuracyCheckResponse:
    def __init__(
        self,
        *,
        selected_roadmap_item_id: UUID | None,
        improvement_suggestions: list[str],
    ) -> None:
        self.selected_roadmap_item_id = selected_roadmap_item_id
        self.improvement_suggestions = improvement_suggestions


class _MissingSelectedRoadmapResponse:
    def __init__(
        self,
        *,
        accuracy_check: str,
        improvement_suggestions: list[str],
    ) -> None:
        self.accuracy_check = accuracy_check
        self.improvement_suggestions = improvement_suggestions


class _MissingImprovementSuggestionsResponse:
    def __init__(
        self,
        *,
        selected_roadmap_item_id: UUID | None,
        accuracy_check: str,
    ) -> None:
        self.selected_roadmap_item_id = selected_roadmap_item_id
        self.accuracy_check = accuracy_check


def _chunk(*, chunk_index: int, text: str) -> IngestionFeedbackChunkInput:
    return IngestionFeedbackChunkInput(chunk_index=chunk_index, text=text)


def _make_input(
    *,
    source_path: str = "study/typescript/generics.md",
    chunks: list[IngestionFeedbackChunkInput] | None = None,
    minimum_chunk_characters: int = 10,
    generated_at: str = "2026-05-20T21:30:00+09:00",
) -> IngestionFeedbackGenerateInput:
    return IngestionFeedbackGenerateInput(
        source_path=source_path,
        chunks=list(chunks or []),
        minimum_chunk_characters=minimum_chunk_characters,
        generated_at=generated_at,
    )


def _make_roadmap_candidates() -> list[RoadmapCandidate]:
    return [
        RoadmapCandidate(
            id=_ROADMAP_ID,
            display_path="TypeScript > 基礎 > ジェネリクス",
        ),
        RoadmapCandidate(
            id=_SECOND_ROADMAP_ID,
            display_path="TypeScript > 応用 > Conditional Types",
        ),
    ]


def _make_success_response(
    *,
    selected_roadmap_item_id: UUID | None = _ROADMAP_ID,
    accuracy_check: str = (
        "ジェネリクスを型安全性の文脈で説明できており、大きな誤りはない。"
    ),
    improvement_suggestions: list[str] | None = None,
) -> IngestionFeedbackLlmResponse:
    return IngestionFeedbackLlmResponse(
        selected_roadmap_item_id=selected_roadmap_item_id,
        accuracy_check=accuracy_check,
        improvement_suggestions=list(
            improvement_suggestions
            if improvement_suggestions is not None
            else [
                "関数だけでなくクラスやインターフェースにも適用できる点を追記する。",
                "型推論と明示的な型引数指定の違いを例で補う。",
            ],
        ),
    )


def _make_stored_feedback(
    *,
    feedback_id: UUID = _FEEDBACK_ID,
    source_path: str = "study/typescript/generics.md",
    roadmap_item_id: UUID | None = _ROADMAP_ID,
    title: str = "study/typescript/generics.md の取り込みフィードバック",
    body: str,
    created_at: str = "2026-05-20T21:30:00+09:00",
) -> StoredIngestionFeedback:
    return StoredIngestionFeedback(
        id=feedback_id,
        source_path=source_path,
        roadmap_item_id=roadmap_item_id,
        title=title,
        body=body,
        is_read=False,
        created_at=created_at,
        read_at=None,
    )


def _serialize_request(
    request: IngestionFeedbackLlmRequest,
) -> dict[str, object]:
    return {
        "source_path": request.source_path,
        "chunk_texts": list(request.chunk_texts),
        "roadmap_candidates": [
            {
                "id": str(candidate.id),
                "display_path": candidate.display_path,
            }
            for candidate in request.roadmap_candidates
        ],
    }


def _serialize_record(
    record: NewIngestionFeedbackRecord,
) -> dict[str, object]:
    return {
        "source_path": record.source_path,
        "roadmap_item_id": (
            None if record.roadmap_item_id is None else str(record.roadmap_item_id)
        ),
        "title": record.title,
        "body": record.body,
        "is_read": record.is_read,
        "created_at": record.created_at,
        "read_at": record.read_at,
    }


def _serialize_feedback(
    feedback: StoredIngestionFeedback,
) -> dict[str, object]:
    return {
        "id": str(feedback.id),
        "source_path": feedback.source_path,
        "roadmap_item_id": (
            None if feedback.roadmap_item_id is None else str(feedback.roadmap_item_id)
        ),
        "title": feedback.title,
        "body": feedback.body,
        "is_read": feedback.is_read,
        "created_at": feedback.created_at,
        "read_at": feedback.read_at,
    }


def _serialize_result(result: IngestionFeedbackGenerateResult) -> dict[str, object]:
    created_feedback = result.created_feedback
    return {
        "status": result.status,
        "used_chunk_count": result.used_chunk_count,
        "skipped_chunk_count": result.skipped_chunk_count,
        "created_feedback": (
            None if created_feedback is None else _serialize_feedback(created_feedback)
        ),
        "skip_reason": result.skip_reason,
    }


def _assert_created_result_matches_persisted_record(
    result: IngestionFeedbackGenerateResult,
    *,
    persisted_record: NewIngestionFeedbackRecord,
    stored_feedback: StoredIngestionFeedback,
) -> None:
    assert result.status == "created"
    assert result.created_feedback is not None
    assert _serialize_feedback(result.created_feedback) == _serialize_feedback(
        stored_feedback,
    )
    assert result.created_feedback.source_path == persisted_record.source_path
    assert result.created_feedback.roadmap_item_id == persisted_record.roadmap_item_id
    assert result.created_feedback.title == persisted_record.title
    assert result.created_feedback.body == persisted_record.body
    assert result.created_feedback.is_read == persisted_record.is_read
    assert result.created_feedback.created_at == persisted_record.created_at
    assert result.created_feedback.read_at == persisted_record.read_at


def _find_log_events(
    log_output: list[MutableMapping[str, Any]],
    event_name: str,
) -> list[MutableMapping[str, Any]]:
    return [entry for entry in log_output if entry.get("event") == event_name]


def _assert_single_log_event_includes(
    log_output: list[MutableMapping[str, Any]],
    event_name: str,
    expected_fields: dict[str, object],
) -> MutableMapping[str, Any]:
    events = _find_log_events(log_output, event_name)
    assert len(events) == 1
    event = events[0]

    for field_name, expected_value in expected_fields.items():
        assert field_name in event
        actual_value = event[field_name]
        if field_name == "feedback_id" and actual_value is not None:
            assert str(actual_value) == expected_value
            continue
        assert actual_value == expected_value

    return event


def _assert_no_log_event(
    log_output: list[MutableMapping[str, Any]],
    event_name: str,
) -> None:
    assert _find_log_events(log_output, event_name) == []


class TestIngestionFeedbackGeneration:
    def test_tc_01_creates_feedback_with_roadmap_and_logs_success(self) -> None:
        expected_body = (
            "反映先ロードマップ: TypeScript > 基礎 > ジェネリクス\n\n"
            "正確性チェック:\n"
            "ジェネリクスを型安全性の文脈で説明できており、大きな誤りはない。\n\n"
            "改善提案:\n"
            "- 関数だけでなくクラスやインターフェースにも適用できる点を追記する。\n"
            "- 型推論と明示的な型引数指定の違いを例で補う。"
        )
        input_data = _make_input(
            chunks=[
                _chunk(
                    chunk_index=1,
                    text="T は型パラメータとして使え、extends で制約も付けられる。",
                ),
                _chunk(
                    chunk_index=0,
                    text=(
                        "TypeScript のジェネリクスは型安全性を保ちながら再利用可能な"
                        "関数や型を表現する仕組み。"
                    ),
                ),
                _chunk(chunk_index=2, text="補足"),
            ],
        )
        roadmap_reader = _RecordingRoadmapReader(items=_make_roadmap_candidates())
        llm_client = _RecordingLlmClient(response=_make_success_response())
        writer = _RecordingWriter(
            stored_feedback=_make_stored_feedback(body=expected_body),
        )

        with capture_logs() as log_output:
            result = generate_for_file(
                input_data,
                llm_client=llm_client,
                roadmap_reader=roadmap_reader,
                writer=writer,
            )

        assert _serialize_result(result) == {
            "status": "created",
            "used_chunk_count": 2,
            "skipped_chunk_count": 1,
            "created_feedback": {
                "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "source_path": "study/typescript/generics.md",
                "roadmap_item_id": "11111111-1111-1111-1111-111111111111",
                "title": "study/typescript/generics.md の取り込みフィードバック",
                "body": expected_body,
                "is_read": False,
                "created_at": "2026-05-20T21:30:00+09:00",
                "read_at": None,
            },
            "skip_reason": None,
        }
        assert roadmap_reader.calls == 1
        assert [_serialize_request(request) for request in llm_client.calls] == [
            {
                "source_path": "study/typescript/generics.md",
                "chunk_texts": [
                    (
                        "TypeScript のジェネリクスは型安全性を保ちながら再利用可能な"
                        "関数や型を表現する仕組み。"
                    ),
                    "T は型パラメータとして使え、extends で制約も付けられる。",
                ],
                "roadmap_candidates": [
                    {
                        "id": "11111111-1111-1111-1111-111111111111",
                        "display_path": "TypeScript > 基礎 > ジェネリクス",
                    },
                    {
                        "id": "22222222-2222-2222-2222-222222222222",
                        "display_path": "TypeScript > 応用 > Conditional Types",
                    },
                ],
            },
        ]
        assert [_serialize_record(record) for record in writer.calls] == [
            {
                "source_path": "study/typescript/generics.md",
                "roadmap_item_id": "11111111-1111-1111-1111-111111111111",
                "title": "study/typescript/generics.md の取り込みフィードバック",
                "body": expected_body,
                "is_read": False,
                "created_at": "2026-05-20T21:30:00+09:00",
                "read_at": None,
            },
        ]
        _assert_single_log_event_includes(
            log_output,
            "ingestion_feedback_created",
            {
                "source_path": "study/typescript/generics.md",
                "input_chunk_count": 3,
                "used_chunk_count": 2,
                "skipped_chunk_count": 1,
                "roadmap_candidate_count": 2,
                "feedback_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            },
        )

    def test_tc_02_creates_feedback_without_roadmap_candidates(self) -> None:
        expected_body = (
            "正確性チェック:\n"
            "概要説明としては妥当だが、ネットワークや volume の観点が省略されている。\n\n"
            "改善提案:\n"
            "- service 間通信の説明を 1 文追加する。"
        )
        input_data = _make_input(
            source_path="study/docker/compose.md",
            chunks=[
                _chunk(
                    chunk_index=0,
                    text="Docker Compose では複数コンテナの起動設定をまとめて管理できる。",
                ),
            ],
            generated_at="2026-05-20T21:35:00+09:00",
        )
        roadmap_reader = _RecordingRoadmapReader(items=[])
        llm_client = _RecordingLlmClient(
            response=_make_success_response(
                selected_roadmap_item_id=None,
                accuracy_check=(
                    "概要説明としては妥当だが、ネットワークや volume の観点が"
                    "省略されている。"
                ),
                improvement_suggestions=[
                    "service 間通信の説明を 1 文追加する。",
                ],
            ),
        )
        writer = _RecordingWriter(
            stored_feedback=_make_stored_feedback(
                feedback_id=_SECOND_FEEDBACK_ID,
                source_path="study/docker/compose.md",
                roadmap_item_id=None,
                title="study/docker/compose.md の取り込みフィードバック",
                body=expected_body,
                created_at="2026-05-20T21:35:00+09:00",
            ),
        )

        with capture_logs() as log_output:
            result = generate_for_file(
                input_data,
                llm_client=llm_client,
                roadmap_reader=roadmap_reader,
                writer=writer,
            )

        assert roadmap_reader.calls == 1
        assert _serialize_result(result) == {
            "status": "created",
            "used_chunk_count": 1,
            "skipped_chunk_count": 0,
            "created_feedback": {
                "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                "source_path": "study/docker/compose.md",
                "roadmap_item_id": None,
                "title": "study/docker/compose.md の取り込みフィードバック",
                "body": expected_body,
                "is_read": False,
                "created_at": "2026-05-20T21:35:00+09:00",
                "read_at": None,
            },
            "skip_reason": None,
        }
        assert [_serialize_request(request) for request in llm_client.calls] == [
            {
                "source_path": "study/docker/compose.md",
                "chunk_texts": [
                    "Docker Compose では複数コンテナの起動設定をまとめて管理できる。",
                ],
                "roadmap_candidates": [],
            },
        ]
        assert [_serialize_record(record) for record in writer.calls] == [
            {
                "source_path": "study/docker/compose.md",
                "roadmap_item_id": None,
                "title": "study/docker/compose.md の取り込みフィードバック",
                "body": expected_body,
                "is_read": False,
                "created_at": "2026-05-20T21:35:00+09:00",
                "read_at": None,
            },
        ]
        assert "反映先ロードマップ:" not in writer.calls[0].body
        assert writer.calls[0].body.startswith("正確性チェック:")
        _assert_single_log_event_includes(
            log_output,
            "ingestion_feedback_created",
            {
                "source_path": "study/docker/compose.md",
                "input_chunk_count": 1,
                "used_chunk_count": 1,
                "skipped_chunk_count": 0,
                "roadmap_candidate_count": 0,
                "feedback_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            },
        )

    def test_tc_03_skips_when_all_chunks_are_too_short(self) -> None:
        input_data = _make_input(
            source_path="daily/2026-05-20.md",
            chunks=[
                _chunk(chunk_index=0, text="会議"),
                _chunk(chunk_index=1, text="後で調べる"),
            ],
            generated_at="2026-05-20T21:40:00+09:00",
        )
        roadmap_reader = _RecordingRoadmapReader(items=_make_roadmap_candidates())
        llm_client = _RecordingLlmClient(response=_make_success_response())
        writer = _RecordingWriter(
            stored_feedback=_make_stored_feedback(body="unused"),
        )

        with capture_logs() as log_output:
            result = generate_for_file(
                input_data,
                llm_client=llm_client,
                roadmap_reader=roadmap_reader,
                writer=writer,
            )

        assert _serialize_result(result) == {
            "status": "skipped",
            "used_chunk_count": 0,
            "skipped_chunk_count": 2,
            "created_feedback": None,
            "skip_reason": "no_analyzable_chunks",
        }
        assert roadmap_reader.calls == 0
        assert llm_client.calls == []
        assert writer.calls == []
        log_entry = _assert_single_log_event_includes(
            log_output,
            "ingestion_feedback_skipped",
            {
                "source_path": "daily/2026-05-20.md",
                "input_chunk_count": 2,
                "used_chunk_count": 0,
                "skipped_chunk_count": 2,
                "roadmap_candidate_count": 0,
            },
        )
        assert "feedback_id" not in log_entry

    def test_tc_10_uses_strip_length_for_threshold_and_sorts_chunks(self) -> None:
        event_log: list[str] = []
        roadmap_candidates = _make_roadmap_candidates()[:1]
        input_data = _make_input(
            source_path="study/python/decorators.md",
            chunks=[
                _chunk(chunk_index=2, text="  descriptor  "),
                _chunk(chunk_index=0, text=" decorator "),
                _chunk(chunk_index=1, text=" short "),
            ],
            minimum_chunk_characters=9,
            generated_at="2026-05-20T22:00:00+09:00",
        )
        roadmap_reader = _RecordingRoadmapReader(items=roadmap_candidates)
        stored_feedback = _make_stored_feedback(
            feedback_id=_SECOND_FEEDBACK_ID,
            source_path="study/python/decorators.md",
            roadmap_item_id=None,
            title="study/python/decorators.md の取り込みフィードバック",
            body=(
                "正確性チェック:\n"
                "要点は押さえている。\n\n"
                "改善提案:\n"
                "- 具体例を追加する。"
            ),
            created_at="2026-05-20T22:00:00+09:00",
        )
        llm_client = _RecordingLlmClient(
            response=_make_success_response(
                selected_roadmap_item_id=None,
                accuracy_check="要点は押さえている。",
                improvement_suggestions=["具体例を追加する。"],
            ),
            event_log=event_log,
        )
        writer = _RecordingWriter(
            stored_feedback=stored_feedback,
            event_log=event_log,
        )

        result = generate_for_file(
            input_data,
            llm_client=llm_client,
            roadmap_reader=roadmap_reader,
            writer=writer,
        )

        assert len(writer.calls) == 1
        _assert_created_result_matches_persisted_record(
            result,
            persisted_record=writer.calls[0],
            stored_feedback=stored_feedback,
        )
        assert result.used_chunk_count == 2
        assert result.skipped_chunk_count == 1
        assert result.status == "created"
        assert roadmap_reader.calls == 1
        assert [_serialize_request(request) for request in llm_client.calls] == [
            {
                "source_path": "study/python/decorators.md",
                "chunk_texts": [
                    " decorator ",
                    "  descriptor  ",
                ],
                "roadmap_candidates": [
                    {
                        "id": "11111111-1111-1111-1111-111111111111",
                        "display_path": "TypeScript > 基礎 > ジェネリクス",
                    },
                ],
            },
        ]
        assert event_log == ["llm.analyze", "writer.create"]

    def test_tc_11_omits_roadmap_line_when_llm_returns_null_selection(self) -> None:
        expected_body = (
            "正確性チェック:\n"
            "候補はあるが、特定のロードマップ項目へはまだ紐付かない。\n\n"
            "改善提案:\n"
            "- 具体例を補い、どの学習項目に対応するかを明確にする。"
        )
        input_data = _make_input(
            source_path="study/misc/note.md",
            chunks=[
                _chunk(
                    chunk_index=0,
                    text="概念の概要はあるが、どのロードマップ項目かはまだ曖昧である。",
                ),
            ],
            generated_at="2026-05-20T22:05:00+09:00",
        )
        roadmap_candidates = _make_roadmap_candidates()
        roadmap_reader = _RecordingRoadmapReader(items=roadmap_candidates)
        llm_client = _RecordingLlmClient(
            response=_make_success_response(
                selected_roadmap_item_id=None,
                accuracy_check=(
                    "候補はあるが、特定のロードマップ項目へはまだ紐付かない。"
                ),
                improvement_suggestions=[
                    "具体例を補い、どの学習項目に対応するかを明確にする。",
                ],
            ),
        )
        stored_feedback = _make_stored_feedback(
            feedback_id=_SECOND_FEEDBACK_ID,
            source_path="study/misc/note.md",
            roadmap_item_id=None,
            title="study/misc/note.md の取り込みフィードバック",
            body=expected_body,
            created_at="2026-05-20T22:05:00+09:00",
        )
        writer = _RecordingWriter(
            stored_feedback=stored_feedback,
        )

        result = generate_for_file(
            input_data,
            llm_client=llm_client,
            roadmap_reader=roadmap_reader,
            writer=writer,
        )

        assert len(writer.calls) == 1
        _assert_created_result_matches_persisted_record(
            result,
            persisted_record=writer.calls[0],
            stored_feedback=stored_feedback,
        )
        assert roadmap_reader.calls == 1
        assert [_serialize_request(request) for request in llm_client.calls] == [
            {
                "source_path": "study/misc/note.md",
                "chunk_texts": [
                    "概念の概要はあるが、どのロードマップ項目かはまだ曖昧である。",
                ],
                "roadmap_candidates": [
                    {
                        "id": str(candidate.id),
                        "display_path": candidate.display_path,
                    }
                    for candidate in roadmap_candidates
                ],
            },
        ]
        assert result.created_feedback is not None
        assert result.created_feedback.roadmap_item_id is None
        assert writer.calls[0].roadmap_item_id is None
        assert writer.calls[0].body == expected_body
        assert "反映先ロードマップ:" not in writer.calls[0].body

    def test_tc_12_aggregates_four_analyzable_chunks_per_file(self) -> None:
        input_data = _make_input(
            source_path="study/rust/ownership.md",
            chunks=[
                _chunk(
                    chunk_index=2,
                    text="三つ目の分析対象チャンクは所有権移動時の注意点を述べる。",
                ),
                _chunk(
                    chunk_index=0,
                    text="一つ目の分析対象チャンクは所有権の基本概念を定義する。",
                ),
                _chunk(
                    chunk_index=3,
                    text="四つ目の分析対象チャンクは借用との違いを補足する。",
                ),
                _chunk(
                    chunk_index=1,
                    text="二つ目の分析対象チャンクはムーブの挙動を例で示す。",
                ),
            ],
            generated_at="2026-05-20T22:10:00+09:00",
        )
        roadmap_reader = _RecordingRoadmapReader(items=_make_roadmap_candidates())
        llm_client = _RecordingLlmClient(response=_make_success_response())
        writer = _RecordingWriter(
            stored_feedback=_make_stored_feedback(
                feedback_id=_SECOND_FEEDBACK_ID,
                source_path="study/rust/ownership.md",
                title="study/rust/ownership.md の取り込みフィードバック",
                body=(
                    "反映先ロードマップ: TypeScript > 基礎 > ジェネリクス\n\n"
                    "正確性チェック:\n"
                    "ジェネリクスを型安全性の文脈で説明できており、大きな誤りはない。\n\n"
                    "改善提案:\n"
                    "- 関数だけでなくクラスやインターフェースにも適用できる点を追記する。\n"
                    "- 型推論と明示的な型引数指定の違いを例で補う。"
                ),
                created_at="2026-05-20T22:10:00+09:00",
            ),
        )

        result = generate_for_file(
            input_data,
            llm_client=llm_client,
            roadmap_reader=roadmap_reader,
            writer=writer,
        )

        assert result.status == "created"
        assert result.used_chunk_count == 4
        assert result.skipped_chunk_count == 0
        assert result.created_feedback is not None
        assert roadmap_reader.calls == 1
        assert len(llm_client.calls) == 1
        assert list(llm_client.calls[0].chunk_texts) == [
            "一つ目の分析対象チャンクは所有権の基本概念を定義する。",
            "二つ目の分析対象チャンクはムーブの挙動を例で示す。",
            "三つ目の分析対象チャンクは所有権移動時の注意点を述べる。",
            "四つ目の分析対象チャンクは借用との違いを補足する。",
        ]
        assert len(writer.calls) == 1

    def test_tc_13_appends_new_record_for_same_source_path(self) -> None:
        expected_body = (
            "反映先ロードマップ: TypeScript > 基礎 > ジェネリクス\n\n"
            "正確性チェック:\n"
            "追記内容に大きな誤りはない。\n\n"
            "改善提案:\n"
            "- 推論規則の具体例を追加する。"
        )
        source_path = "study/typescript/generics.md"
        input_data = _make_input(
            source_path=source_path,
            chunks=[
                _chunk(
                    chunk_index=0,
                    text="ジェネリクスの基本に加えて、型引数の推論規則も追記した。",
                ),
            ],
            generated_at="2026-05-21T08:00:00+09:00",
        )
        roadmap_reader = _RecordingRoadmapReader(items=_make_roadmap_candidates())
        llm_client = _RecordingLlmClient(
            response=_make_success_response(
                accuracy_check="追記内容に大きな誤りはない。",
                improvement_suggestions=["推論規則の具体例を追加する。"],
            ),
        )
        existing_feedback = _make_stored_feedback(
            feedback_id=_FEEDBACK_ID,
            source_path=source_path,
            body="既存フィードバック本文",
            created_at="2026-05-19T09:00:00+09:00",
        )
        writer = _AppendingWriter(
            existing_records=[existing_feedback],
            next_feedback_id=_THIRD_FEEDBACK_ID,
        )

        result = generate_for_file(
            input_data,
            llm_client=llm_client,
            roadmap_reader=roadmap_reader,
            writer=writer,
        )

        assert result.status == "created"
        assert result.created_feedback is not None
        assert str(result.created_feedback.id) == "cccccccc-cccc-cccc-cccc-cccccccccccc"
        assert result.created_feedback.created_at == "2026-05-21T08:00:00+09:00"
        assert len(writer.calls) == 1
        assert [str(record.id) for record in writer.records] == [
            "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "cccccccc-cccc-cccc-cccc-cccccccccccc",
        ]
        assert [record.source_path for record in writer.records] == [
            source_path,
            source_path,
        ]
        assert writer.records[0].body == "既存フィードバック本文"
        assert writer.records[1].body == expected_body
        assert writer.records[1].source_path == source_path
        assert (
            len(
                [
                    record
                    for record in writer.records
                    if record.source_path == source_path
                ],
            )
            == 2
        )

    def test_tc_20_skips_empty_chunk_list_without_external_calls(self) -> None:
        input_data = _make_input(
            source_path="study/empty.md",
            chunks=[],
            generated_at="2026-05-20T22:15:00+09:00",
        )
        roadmap_reader = _RecordingRoadmapReader(items=_make_roadmap_candidates())
        llm_client = _RecordingLlmClient(response=_make_success_response())
        writer = _RecordingWriter(
            stored_feedback=_make_stored_feedback(body="unused"),
        )

        with capture_logs() as log_output:
            result = generate_for_file(
                input_data,
                llm_client=llm_client,
                roadmap_reader=roadmap_reader,
                writer=writer,
            )

        assert _serialize_result(result) == {
            "status": "skipped",
            "used_chunk_count": 0,
            "skipped_chunk_count": 0,
            "created_feedback": None,
            "skip_reason": "no_analyzable_chunks",
        }
        assert roadmap_reader.calls == 0
        assert llm_client.calls == []
        assert writer.calls == []
        log_entry = _assert_single_log_event_includes(
            log_output,
            "ingestion_feedback_skipped",
            {
                "source_path": "study/empty.md",
                "input_chunk_count": 0,
                "used_chunk_count": 0,
                "skipped_chunk_count": 0,
                "roadmap_candidate_count": 0,
            },
        )
        assert "feedback_id" not in log_entry

    @pytest.mark.parametrize(
        "input_data",
        [
            _make_input(
                source_path="",
                chunks=[_chunk(chunk_index=0, text="valid enough text")],
            ),
            _make_input(
                chunks=[_chunk(chunk_index=0, text="valid enough text")],
                minimum_chunk_characters=0,
            ),
            _make_input(
                chunks=[_chunk(chunk_index=0, text="valid enough text")],
                generated_at="2026/05/20 22:20",
            ),
            _make_input(
                chunks=[_chunk(chunk_index=-1, text="valid enough text")],
            ),
            _make_input(
                chunks=[
                    _chunk(chunk_index=0, text="valid enough text A"),
                    _chunk(chunk_index=0, text="valid enough text B"),
                ],
            ),
        ],
    )
    def test_tc_21_rejects_invalid_input_before_external_calls(
        self,
        input_data: IngestionFeedbackGenerateInput,
    ) -> None:
        roadmap_reader = _RecordingRoadmapReader(items=_make_roadmap_candidates())
        llm_client = _RecordingLlmClient(response=_make_success_response())
        writer = _RecordingWriter(
            stored_feedback=_make_stored_feedback(body="unused"),
        )

        with pytest.raises(IngestionFeedbackInputError):
            generate_for_file(
                input_data,
                llm_client=llm_client,
                roadmap_reader=roadmap_reader,
                writer=writer,
            )

        assert roadmap_reader.calls == 0
        assert llm_client.calls == []
        assert writer.calls == []

    @pytest.mark.parametrize(
        ("roadmap_candidates", "llm_response"),
        [
            (
                _make_roadmap_candidates(),
                _make_success_response(
                    selected_roadmap_item_id=_OUTSIDE_ROADMAP_ID,
                    improvement_suggestions=["候補外の ID は拒否する。"],
                ),
            ),
            (
                [],
                _make_success_response(
                    selected_roadmap_item_id=_ROADMAP_ID,
                    improvement_suggestions=["候補ゼロ時は null を返す。"],
                ),
            ),
            (
                _make_roadmap_candidates(),
                _make_success_response(improvement_suggestions=[]),
            ),
            (
                _make_roadmap_candidates(),
                _MissingAccuracyCheckResponse(
                    selected_roadmap_item_id=None,
                    improvement_suggestions=["accuracy_check は必須である。"],
                ),
            ),
            (
                _make_roadmap_candidates(),
                _make_success_response(
                    selected_roadmap_item_id=None,
                    accuracy_check="   ",
                    improvement_suggestions=["空白だけの正確性チェックは不可。"],
                ),
            ),
            (
                _make_roadmap_candidates(),
                _MissingSelectedRoadmapResponse(
                    accuracy_check="正確性チェック内容。",
                    improvement_suggestions=["selected_roadmap_item_id が欠落。"],
                ),
            ),
            (
                _make_roadmap_candidates(),
                _MissingImprovementSuggestionsResponse(
                    selected_roadmap_item_id=None,
                    accuracy_check="improvement_suggestions が欠落。",
                ),
            ),
        ],
    )
    def test_tc_22_rejects_invalid_llm_response_without_persisting(
        self,
        roadmap_candidates: list[RoadmapCandidate],
        llm_response: object,
    ) -> None:
        input_data = _make_input(
            chunks=[_chunk(chunk_index=0, text="分析可能な十分長いチャンク本文です。")],
        )
        roadmap_reader = _RecordingRoadmapReader(items=roadmap_candidates)
        llm_client = _RecordingLlmClient(response=llm_response)
        writer = _RecordingWriter(
            stored_feedback=_make_stored_feedback(body="unused"),
        )

        with (
            capture_logs() as log_output,
            pytest.raises(
                IngestionFeedbackResponseFormatError,
            ),
        ):
            generate_for_file(
                input_data,
                llm_client=llm_client,
                roadmap_reader=roadmap_reader,
                writer=writer,
            )

        assert len(llm_client.calls) == 1
        assert writer.calls == []
        _assert_no_log_event(log_output, "ingestion_feedback_created")

    def test_tc_30_works_with_protocol_only_dependency_objects(self) -> None:
        expected_body = (
            "正確性チェック:\n"
            "Protocol を満たす依存だけで処理できる。\n\n"
            "改善提案:\n"
            "- 具体的な実装クラスに結び付けない。"
        )
        input_data = _make_input(
            source_path="study/protocol.md",
            chunks=[
                _chunk(
                    chunk_index=0,
                    text="Protocol DI の意図を説明する十分長い本文。",
                ),
            ],
            generated_at="2026-05-20T22:25:00+09:00",
        )
        call_counts = {
            "roadmap_reader": 0,
            "llm_client": 0,
            "writer": 0,
        }
        event_log: list[str] = []

        class LocalRoadmapReader:
            __slots__ = ()

            def list_items(self) -> list[RoadmapCandidate]:
                call_counts["roadmap_reader"] += 1
                event_log.append("roadmap_reader.list_items")
                return []

        class LocalLlmClient:
            __slots__ = ()

            def analyze(
                self,
                request: IngestionFeedbackLlmRequest,
            ) -> IngestionFeedbackLlmResponse:
                call_counts["llm_client"] += 1
                event_log.append("llm_client.analyze")
                assert request.source_path == "study/protocol.md"
                return _make_success_response(
                    selected_roadmap_item_id=None,
                    accuracy_check="Protocol を満たす依存だけで処理できる。",
                    improvement_suggestions=["具体的な実装クラスに結び付けない。"],
                )

        class LocalWriter:
            __slots__ = ()

            def create(
                self,
                record: NewIngestionFeedbackRecord,
            ) -> StoredIngestionFeedback:
                call_counts["writer"] += 1
                event_log.append("writer.create")
                return _make_stored_feedback(
                    feedback_id=_SECOND_FEEDBACK_ID,
                    source_path=record.source_path,
                    roadmap_item_id=record.roadmap_item_id,
                    title=record.title,
                    body=expected_body,
                    created_at=record.created_at,
                )

        roadmap_reader = LocalRoadmapReader()
        llm_client = LocalLlmClient()
        writer = LocalWriter()

        result = generate_for_file(
            input_data,
            llm_client=llm_client,
            roadmap_reader=roadmap_reader,
            writer=writer,
        )

        assert result.status == "created"
        assert result.created_feedback is not None
        assert result.created_feedback.body == expected_body
        assert call_counts == {
            "roadmap_reader": 1,
            "llm_client": 1,
            "writer": 1,
        }
        assert event_log == [
            "roadmap_reader.list_items",
            "llm_client.analyze",
            "writer.create",
        ]

    def test_tc_31_raises_when_roadmap_lookup_fails(self) -> None:
        input_data = _make_input(
            chunks=[_chunk(chunk_index=0, text="分析可能な十分長いチャンク本文です。")],
        )
        roadmap_reader = _RecordingRoadmapReader(error=TimeoutError("roadmap timeout"))
        llm_client = _RecordingLlmClient(response=_make_success_response())
        writer = _RecordingWriter(
            stored_feedback=_make_stored_feedback(body="unused"),
        )

        with (
            capture_logs() as log_output,
            pytest.raises(
                IngestionFeedbackRoadmapLookupError,
            ),
        ):
            generate_for_file(
                input_data,
                llm_client=llm_client,
                roadmap_reader=roadmap_reader,
                writer=writer,
            )

        assert roadmap_reader.calls == 1
        assert len(llm_client.calls) == 0
        assert writer.calls == []
        _assert_single_log_event_includes(
            log_output,
            "ingestion_feedback_roadmap_lookup_failed",
            {
                "source_path": "study/typescript/generics.md",
                "input_chunk_count": 1,
                "used_chunk_count": 1,
                "skipped_chunk_count": 0,
                "roadmap_candidate_count": 0,
                "error_type": "TimeoutError",
            },
        )
        _assert_no_log_event(log_output, "ingestion_feedback_created")
        _assert_no_log_event(log_output, "ingestion_feedback_skipped")

    def test_tc_32_raises_when_llm_call_fails(self) -> None:
        input_data = _make_input(
            chunks=[
                _chunk(chunk_index=0, text="一つ目の分析可能チャンク本文です。"),
                _chunk(chunk_index=1, text="二つ目の分析可能チャンク本文です。"),
            ],
        )
        roadmap_reader = _RecordingRoadmapReader(items=_make_roadmap_candidates())
        llm_client = _RecordingLlmClient(error=ConnectionError("llm unavailable"))
        writer = _RecordingWriter(
            stored_feedback=_make_stored_feedback(body="unused"),
        )

        with (
            capture_logs() as log_output,
            pytest.raises(
                IngestionFeedbackLlmCallError,
            ),
        ):
            generate_for_file(
                input_data,
                llm_client=llm_client,
                roadmap_reader=roadmap_reader,
                writer=writer,
            )

        assert roadmap_reader.calls == 1
        assert len(llm_client.calls) == 1
        assert writer.calls == []
        _assert_single_log_event_includes(
            log_output,
            "ingestion_feedback_llm_failed",
            {
                "source_path": "study/typescript/generics.md",
                "input_chunk_count": 2,
                "used_chunk_count": 2,
                "skipped_chunk_count": 0,
                "roadmap_candidate_count": 2,
                "error_type": "ConnectionError",
            },
        )
        _assert_no_log_event(log_output, "ingestion_feedback_created")
        _assert_no_log_event(log_output, "ingestion_feedback_skipped")

    def test_tc_33_raises_when_persistence_fails(self) -> None:
        input_data = _make_input(
            chunks=[
                _chunk(
                    chunk_index=0,
                    text="保存直前まで進む十分長いチャンク本文です。",
                ),
            ],
        )
        roadmap_reader = _RecordingRoadmapReader(items=_make_roadmap_candidates())
        llm_client = _RecordingLlmClient(response=_make_success_response())
        writer = _RecordingWriter(error=RuntimeError("insert failed"))

        with (
            capture_logs() as log_output,
            pytest.raises(
                IngestionFeedbackPersistenceError,
            ),
        ):
            generate_for_file(
                input_data,
                llm_client=llm_client,
                roadmap_reader=roadmap_reader,
                writer=writer,
            )

        assert roadmap_reader.calls == 1
        assert len(llm_client.calls) == 1
        assert len(writer.calls) == 1
        _assert_single_log_event_includes(
            log_output,
            "ingestion_feedback_persist_failed",
            {
                "source_path": "study/typescript/generics.md",
                "input_chunk_count": 1,
                "used_chunk_count": 1,
                "skipped_chunk_count": 0,
                "roadmap_candidate_count": 2,
                "error_type": "RuntimeError",
            },
        )
        _assert_no_log_event(log_output, "ingestion_feedback_created")
        _assert_no_log_event(log_output, "ingestion_feedback_skipped")
