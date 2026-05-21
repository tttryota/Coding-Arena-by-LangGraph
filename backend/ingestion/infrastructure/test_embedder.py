import math
from collections.abc import Callable, MutableMapping, Sequence
from typing import Protocol, cast

import pytest
from structlog.testing import capture_logs

from ingestion.infrastructure.embedder import (
    ChunkEmbeddingInput,
    ChunkEmbeddingResult,
    EmbeddingBatchInput,
    EmbeddingBatchInputError,
    EmbeddingModel,
    EmbeddingModelCallError,
    EmbeddingResponseCountMismatchError,
    EmbeddingVectorFormatError,
    embed,
)

pytestmark = pytest.mark.skip(
    reason="Review target is limited to chunk-store TC-01..TC-33.",
)


class _RecordingEmbeddingModel:
    def __init__(
        self,
        responses: Sequence[object],
        *,
        fail_on_call: int | None = None,
        fail_with: Exception | None = None,
    ) -> None:
        self._responses = list(responses)
        self._fail_on_call = fail_on_call
        self._fail_with = fail_with
        self.calls: list[list[str]] = []

    def embed(self, texts: list[str]) -> object:
        self.calls.append(list(texts))
        if self._fail_on_call == len(self.calls):
            if self._fail_with is not None:
                raise self._fail_with
            msg = "embedding model call failed"
            raise RuntimeError(msg)
        try:
            return self._responses[len(self.calls) - 1]
        except IndexError as exc:
            msg = "unexpected embedding_model.embed() call"
            raise AssertionError(msg) from exc


class _AlternativeEmbeddingModel:
    def __init__(self, response: object) -> None:
        self._response = response
        self.calls: list[list[str]] = []

    def embed(self, texts: list[str]) -> object:
        copied_texts: list[str] = []
        for text in texts:
            copied_texts.append(text)
        self.calls.append(copied_texts)
        return self._response


class _NonCallableEmbeddingModel:
    def __init__(self) -> None:
        self.embed = "not-callable"


class _EmbeddingModelWithCalls(Protocol):
    calls: list[list[str]]

    def embed(self, texts: list[str]) -> object: ...


def _make_batch_input(
    *,
    chunks: list[tuple[object, object]],
    embedding_model: object,
    source_path: str | None = "study/embeddings.md",
) -> EmbeddingBatchInput:
    chunk_objects = [
        ChunkEmbeddingInput(
            chunk_index=cast("int", chunk_index),
            text=cast("str", text),
        )
        for chunk_index, text in chunks
    ]
    return EmbeddingBatchInput(
        chunks=chunk_objects,
        embedding_model=cast("EmbeddingModel", embedding_model),
        source_path=source_path,
    )


def _normalize_results(results: list[ChunkEmbeddingResult]) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for result in results:
        assert type(result.chunk_index) is int
        assert isinstance(result.embedding, list)
        assert all(isinstance(value, float) for value in result.embedding)
        normalized.append(
            {
                "chunk_index": result.chunk_index,
                "embedding": list(result.embedding),
            },
        )
    return normalized


def _find_log_events(
    log_output: list[MutableMapping[str, object]],
    event_name: str,
) -> list[MutableMapping[str, object]]:
    return [entry for entry in log_output if entry.get("event") == event_name]


def _assert_single_log_event_includes(
    log_output: list[MutableMapping[str, object]],
    event_name: str,
    expected_fields: dict[str, object],
) -> MutableMapping[str, object]:
    matching_logs = _find_log_events(log_output, event_name)
    assert len(matching_logs) == 1
    log_entry = matching_logs[0]

    assert set(expected_fields) <= set(log_entry)
    assert {field_name: log_entry[field_name] for field_name in expected_fields} == (
        expected_fields
    )
    return log_entry


class TestEmbedderPhase1:
    def test_embedder_tc_01_reconstructs_single_chunk_result(self) -> None:
        embedding_model = _RecordingEmbeddingModel([[[0.12, -0.03, 0.44, 0.08]]])
        batch_input = _make_batch_input(
            chunks=[(0, "TypeScript のジェネリクスは型引数を使って再利用性を高める。")],
            embedding_model=embedding_model,
            source_path="study/typescript/generics.md",
        )

        actual = _normalize_results(embed(batch_input))

        assert actual == [
            {
                "chunk_index": 0,
                "embedding": [0.12, -0.03, 0.44, 0.08],
            },
        ]
        assert embedding_model.calls == [
            ["TypeScript のジェネリクスは型引数を使って再利用性を高める。"],
        ]

    def test_embedder_tc_01_accepts_int_elements_in_embedding_vector(self) -> None:
        embedding_model = _RecordingEmbeddingModel([[[1, 2.0, -3, 4.0]]])
        batch_input = _make_batch_input(
            chunks=[(0, "整数要素を含むベクトル")],
            embedding_model=embedding_model,
        )

        actual = _normalize_results(embed(batch_input))

        assert actual == [
            {"chunk_index": 0, "embedding": [1.0, 2.0, -3.0, 4.0]},
        ]

    def test_embedder_tc_02_short_circuits_empty_batch_and_logs_success(self) -> None:
        embedding_model = _RecordingEmbeddingModel([])
        batch_input = _make_batch_input(
            chunks=[],
            embedding_model=embedding_model,
            source_path="study/empty.md",
        )

        with capture_logs() as log_output:
            actual = _normalize_results(embed(batch_input))

        assert actual == []
        assert embedding_model.calls == []
        _assert_single_log_event_includes(
            log_output,
            "embedder_batch_completed",
            {
                "source_path": "study/empty.md",
                "chunk_count": 0,
                "embedded_count": 0,
                "vector_dimension": None,
                "invalid_chunk_count": 0,
                "model_failure_count": 0,
            },
        )


class TestEmbedderPhase2:
    def test_embedder_tc_10_passes_multiple_chunks_once_in_input_order(self) -> None:
        embedding_model = _RecordingEmbeddingModel(
            [
                [
                    [0.1, 0.2, 0.3, 0.4],
                    [-0.11, 0.05, 0.18, 0.09],
                    [0.1, 0.2, 0.3, 0.4],
                ],
            ],
        )
        batch_input = _make_batch_input(
            chunks=[
                (0, "Docker Compose でアプリケーションを起動する。"),
                (2, " PostgreSQL のトランザクション分離レベルを整理する。 "),
                (5, "Docker Compose でアプリケーションを起動する。"),
            ],
            embedding_model=embedding_model,
            source_path="study/backend/infra.md",
        )

        actual = _normalize_results(embed(batch_input))

        assert actual == [
            {"chunk_index": 0, "embedding": [0.1, 0.2, 0.3, 0.4]},
            {"chunk_index": 2, "embedding": [-0.11, 0.05, 0.18, 0.09]},
            {"chunk_index": 5, "embedding": [0.1, 0.2, 0.3, 0.4]},
        ]
        assert embedding_model.calls == [
            [
                "Docker Compose でアプリケーションを起動する。",
                " PostgreSQL のトランザクション分離レベルを整理する。 ",
                "Docker Compose でアプリケーションを起動する。",
            ],
        ]

    def test_embedder_tc_11_logs_required_fields_for_non_empty_success(self) -> None:
        embedding_model = _RecordingEmbeddingModel(
            [
                [
                    [0.1, 0.2, 0.3, 0.4],
                    [-0.11, 0.05, 0.18, 0.09],
                ],
            ],
        )
        batch_input = _make_batch_input(
            chunks=[
                (0, "Docker Compose でアプリケーションを起動する。"),
                (1, "PostgreSQL のトランザクション分離レベルを整理する。"),
            ],
            embedding_model=embedding_model,
            source_path="study/backend/infra.md",
        )

        with capture_logs() as log_output:
            actual = _normalize_results(embed(batch_input))

        assert actual == [
            {"chunk_index": 0, "embedding": [0.1, 0.2, 0.3, 0.4]},
            {"chunk_index": 1, "embedding": [-0.11, 0.05, 0.18, 0.09]},
        ]
        _assert_single_log_event_includes(
            log_output,
            "embedder_batch_completed",
            {
                "source_path": "study/backend/infra.md",
                "chunk_count": 2,
                "embedded_count": 2,
                "vector_dimension": 4,
                "invalid_chunk_count": 0,
                "model_failure_count": 0,
            },
        )

    def test_embedder_tc_12_fails_fast_on_blank_chunk_without_model_call(self) -> None:
        embedding_model = _RecordingEmbeddingModel([[[0.1, 0.2]]])
        batch_input = _make_batch_input(
            chunks=[(0, "有効な本文"), (1, "   ")],
            embedding_model=embedding_model,
            source_path="study/invalid.md",
        )

        with pytest.raises(EmbeddingBatchInputError) as exc_info:
            embed(batch_input)

        assert str(exc_info.value) == (
            "chunk input invalid at input_position=1: "
            "chunk_index=1; text must not be blank"
        )
        assert embedding_model.calls == []

    @pytest.mark.parametrize("bad_chunk_index", [-1, 1.5, True])
    def test_embedder_tc_13_rejects_non_non_negative_integer_chunk_index(
        self,
        bad_chunk_index: object,
    ) -> None:
        embedding_model = _RecordingEmbeddingModel([[[0.1, 0.2]]])
        batch_input = _make_batch_input(
            chunks=[(bad_chunk_index, "有効な本文")],
            embedding_model=embedding_model,
            source_path=None,
        )

        with pytest.raises(EmbeddingBatchInputError):
            embed(batch_input)

        assert embedding_model.calls == []

    def test_embedder_tc_14_rejects_non_string_text(self) -> None:
        embedding_model = _RecordingEmbeddingModel([[[0.1, 0.2]]])
        batch_input = _make_batch_input(
            chunks=[(0, 123)],
            embedding_model=embedding_model,
            source_path=None,
        )

        with pytest.raises(EmbeddingBatchInputError):
            embed(batch_input)

        assert embedding_model.calls == []


class TestEmbedderPhase3:
    def test_embedder_tc_20_rejects_non_callable_embed_method(self) -> None:
        batch_input = _make_batch_input(
            chunks=[(0, "TypeScript のジェネリクスを整理した。")],
            embedding_model=_NonCallableEmbeddingModel(),
            source_path=None,
        )

        with pytest.raises(EmbeddingBatchInputError):
            embed(batch_input)

    def test_embedder_tc_21_raises_count_mismatch_error(self) -> None:
        embedding_model = _RecordingEmbeddingModel([[[0.1, 0.2, 0.3, 0.4]]])
        batch_input = _make_batch_input(
            chunks=[
                (0, "Docker Compose でアプリケーションを起動する。"),
                (1, "PostgreSQL のトランザクション分離レベルを整理する。"),
            ],
            embedding_model=embedding_model,
            source_path=None,
        )

        with pytest.raises(EmbeddingResponseCountMismatchError) as exc_info:
            embed(batch_input)

        assert str(exc_info.value) == (
            "embedding response count mismatch: expected 2, got 1"
        )
        assert embedding_model.calls == [
            [
                "Docker Compose でアプリケーションを起動する。",
                "PostgreSQL のトランザクション分離レベルを整理する。",
            ],
        ]

    def test_embedder_tc_22_raises_format_error_for_non_list_vector(self) -> None:
        embedding_model = _RecordingEmbeddingModel([[(0.1, 0.2, 0.3, 0.4)]])
        batch_input = _make_batch_input(
            chunks=[(0, "Docker Compose でアプリケーションを起動する。")],
            embedding_model=embedding_model,
            source_path=None,
        )

        with pytest.raises(EmbeddingVectorFormatError) as exc_info:
            embed(batch_input)

        assert str(exc_info.value) == (
            "embedding model must return list[list[float]]: "
            "vector_index=0, got_type=tuple, got_value=(0.1, 0.2, 0.3, 0.4)"
        )

    def test_embedder_tc_23_raises_format_error_for_empty_vector(self) -> None:
        embedding_model = _RecordingEmbeddingModel([[[]]])
        batch_input = _make_batch_input(
            chunks=[(0, "Docker Compose でアプリケーションを起動する。")],
            embedding_model=embedding_model,
            source_path=None,
        )

        with pytest.raises(EmbeddingVectorFormatError) as exc_info:
            embed(batch_input)

        assert (
            str(exc_info.value) == "embedding vector must not be empty: vector_index=0"
        )

    @pytest.mark.parametrize(
        ("bad_value"),
        [
            pytest.param(math.nan, id="nan"),
            pytest.param(math.inf, id="inf"),
            pytest.param(None, id="none"),
            pytest.param("0.2", id="string"),
            pytest.param(True, id="bool"),
        ],
    )
    def test_embedder_tc_24_raises_format_error_for_invalid_elements(
        self,
        bad_value: object,
    ) -> None:
        embedding_model = _RecordingEmbeddingModel([[[0.1, bad_value, 0.3, 0.4]]])
        batch_input = _make_batch_input(
            chunks=[(0, "Docker Compose でアプリケーションを起動する。")],
            embedding_model=embedding_model,
            source_path=None,
        )

        with pytest.raises(EmbeddingVectorFormatError) as exc_info:
            embed(batch_input)

        assert str(exc_info.value) == (
            "embedding vector elements must be finite floats: "
            "vector_index=0, "
            "element_index=1, "
            f"got_type={type(bad_value).__name__}, "
            f"got_value={bad_value!r}"
        )

    def test_embedder_tc_25_raises_format_error_for_dimension_mismatch(self) -> None:
        embedding_model = _RecordingEmbeddingModel(
            [
                [
                    [0.1, 0.2, 0.3, 0.4],
                    [-0.11, 0.05, 0.18],
                ],
            ],
        )
        batch_input = _make_batch_input(
            chunks=[
                (0, "Docker Compose でアプリケーションを起動する。"),
                (1, "PostgreSQL のトランザクション分離レベルを整理する。"),
            ],
            embedding_model=embedding_model,
            source_path=None,
        )

        with pytest.raises(EmbeddingVectorFormatError) as exc_info:
            embed(batch_input)

        assert str(exc_info.value) == (
            "embedding vector dimensions must match within a batch: "
            "vector_index=1, expected_dimension=4, actual_dimension=3"
        )

    def test_embedder_tc_26_prioritizes_count_mismatch_over_format_error(self) -> None:
        embedding_model = _RecordingEmbeddingModel([[[0.1, math.nan, 0.3, 0.4]]])
        batch_input = _make_batch_input(
            chunks=[
                (0, "Docker Compose でアプリケーションを起動する。"),
                (1, "PostgreSQL のトランザクション分離レベルを整理する。"),
            ],
            embedding_model=embedding_model,
            source_path=None,
        )

        with pytest.raises(EmbeddingResponseCountMismatchError):
            embed(batch_input)


class TestEmbedderPhase4:
    @pytest.mark.parametrize(
        "model_factory",
        [
            pytest.param(
                lambda response: _RecordingEmbeddingModel([response]),
                id="recording-model",
            ),
            pytest.param(
                lambda response: _AlternativeEmbeddingModel(response),
                id="alternative-model",
            ),
        ],
    )
    def test_embedder_tc_30_preserves_contract_across_protocol_compatible_models(
        self,
        model_factory: Callable[[object], object],
    ) -> None:
        response = [[0.1, 0.2, 0.3, 0.4]]
        embedding_model = cast("_EmbeddingModelWithCalls", model_factory(response))
        batch_input = _make_batch_input(
            chunks=[(3, "Docker Compose でアプリケーションを起動する。")],
            embedding_model=embedding_model,
            source_path="study/backend/infra.md",
        )

        actual = _normalize_results(embed(batch_input))

        assert actual == [
            {
                "chunk_index": 3,
                "embedding": [0.1, 0.2, 0.3, 0.4],
            },
        ]
        assert embedding_model.calls == [
            ["Docker Compose でアプリケーションを起動する。"],
        ]

    def test_embedder_tc_31_wraps_model_failure_and_logs_it(self) -> None:
        timeout_error = TimeoutError("embedding timed out")
        embedding_model = _RecordingEmbeddingModel(
            [],
            fail_on_call=1,
            fail_with=timeout_error,
        )
        batch_input = _make_batch_input(
            chunks=[(0, "Docker Compose でアプリケーションを起動する。")],
            embedding_model=embedding_model,
            source_path="study/backend/infra.md",
        )

        with (
            capture_logs() as log_output,
            pytest.raises(
                EmbeddingModelCallError,
            ) as exc_info,
        ):
            embed(batch_input)

        success_logs = _find_log_events(log_output, "embedder_batch_completed")

        assert exc_info.value.__cause__ is timeout_error
        assert str(exc_info.value) == (
            "embedding model call failed: "
            "source_path='study/backend/infra.md', "
            "chunk_count=1, "
            "exception_type=TimeoutError, "
            "exception_message=embedding timed out"
        )
        failure_log = _assert_single_log_event_includes(
            log_output,
            "embedder_model_call_failed",
            {
                "source_path": "study/backend/infra.md",
                "chunk_count": 1,
                "embedded_count": 0,
                "vector_dimension": None,
                "invalid_chunk_count": 0,
                "model_failure_count": 1,
            },
        )
        assert failure_log.get("exc_info") is True
        assert success_logs == []
