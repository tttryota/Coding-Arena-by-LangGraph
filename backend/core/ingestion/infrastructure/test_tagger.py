import logging
from collections.abc import Sequence

import pytest

from core.ingestion.infrastructure.tagger import (
    ChunkTaggingInput,
    ChunkTaggingResult,
    TaggingBatchInput,
    TaggingLlmCallError,
    TaggingPromptBuildError,
    TaggingResponseFormatError,
    tag,
)


class _RecordingPromptStrategy:
    def __init__(self, *, fail_on_call: int | None = None) -> None:
        self._fail_on_call = fail_on_call
        self.calls: list[dict[str, object]] = []

    def build_prompt(self, chunk_text: str, existing_tags: list[str]) -> object:
        self.calls.append(
            {
                "chunk_text": chunk_text,
                "existing_tags": list(existing_tags),
            },
        )
        if self._fail_on_call == len(self.calls):
            msg = "prompt build failed"
            raise RuntimeError(msg)
        return {
            "chunk_text": chunk_text,
            "existing_tags": list(existing_tags),
            "call_index": len(self.calls) - 1,
        }


class _QueueLlmClient:
    def __init__(
        self,
        responses: Sequence[object],
        *,
        fail_on_call: int | None = None,
    ) -> None:
        self._responses = list(responses)
        self._fail_on_call = fail_on_call
        self.calls: list[object] = []

    def classify(self, prompt: object) -> object:
        self.calls.append(prompt)
        if self._fail_on_call == len(self.calls):
            msg = "llm call failed"
            raise RuntimeError(msg)
        try:
            return self._responses[len(self.calls) - 1]
        except IndexError as exc:
            msg = "unexpected llm classify() call"
            raise AssertionError(msg) from exc


def _make_batch_input(
    *,
    chunks: list[tuple[int, str]],
    existing_tags: list[str],
    prompt_strategy: _RecordingPromptStrategy | object,
    llm_client: _QueueLlmClient | object,
    source_path: str | None = None,
) -> TaggingBatchInput:
    chunk_objects = [
        ChunkTaggingInput(chunk_index=chunk_index, text=text)
        for chunk_index, text in chunks
    ]
    return TaggingBatchInput(
        chunks=chunk_objects,
        existing_tags=existing_tags,
        prompt_strategy=prompt_strategy,  # type: ignore[arg-type]
        llm_client=llm_client,  # type: ignore[arg-type]
        source_path=source_path,
    )


def _normalize_results(results: list[ChunkTaggingResult]) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for result in results:
        assert type(result.chunk_index) is int
        assert isinstance(result.tags, list)
        assert all(isinstance(t, str) for t in result.tags)
        normalized.append(
            {
                "chunk_index": result.chunk_index,
                "tags": list(result.tags),
            },
        )
    return normalized


def _find_log_records_with_observability_fields(
    caplog: pytest.LogCaptureFixture,
) -> list[logging.LogRecord]:
    observability_fields = (
        "source_path",
        "chunk_index",
        "existing_tag_count",
        "generated_tag_count",
        "empty_result_count",
        "llm_failure_count",
    )
    return [
        record
        for record in caplog.records
        if any(hasattr(record, field_name) for field_name in observability_fields)
    ]


def _collect_int_field_values(
    records: list[logging.LogRecord],
    field_name: str,
) -> set[int]:
    values: set[int] = set()
    for record in records:
        value = getattr(record, field_name, None)
        if type(value) is int:
            values.add(value)
    return values


class TestTaggerPhase1:
    def test_tagger_tc_01_returns_minimal_single_chunk_result(self) -> None:
        prompt_strategy = _RecordingPromptStrategy()
        llm_client = _QueueLlmClient([["TypeScript"]])
        batch_input = _make_batch_input(
            chunks=[(0, "TypeScript のジェネリクスを整理した。")],
            existing_tags=["TypeScript", "React", "Docker"],
            prompt_strategy=prompt_strategy,
            llm_client=llm_client,
        )

        actual = _normalize_results(tag(batch_input))

        assert actual == [{"chunk_index": 0, "tags": ["TypeScript"]}]
        assert prompt_strategy.calls == [
            {
                "chunk_text": "TypeScript のジェネリクスを整理した。",
                "existing_tags": ["TypeScript", "React", "Docker"],
            },
        ]
        assert len(llm_client.calls) == 1

    def test_tagger_tc_02_returns_empty_tags_for_unclassifiable_chunk(self) -> None:
        prompt_strategy = _RecordingPromptStrategy()
        llm_client = _QueueLlmClient([[]])
        batch_input = _make_batch_input(
            chunks=[(5, "今日は学習メモを見直し、次に何を読むか考えた。")],
            existing_tags=["TypeScript", "React", "Docker"],
            prompt_strategy=prompt_strategy,
            llm_client=llm_client,
        )

        actual = _normalize_results(tag(batch_input))

        assert actual == [{"chunk_index": 5, "tags": []}]
        assert len(prompt_strategy.calls) == 1
        assert len(llm_client.calls) == 1

    def test_tagger_tc_03_returns_empty_list_without_calling_dependencies(self) -> None:
        prompt_strategy = _RecordingPromptStrategy()
        llm_client = _QueueLlmClient([])
        batch_input = _make_batch_input(
            chunks=[],
            existing_tags=["TypeScript"],
            prompt_strategy=prompt_strategy,
            llm_client=llm_client,
        )

        actual = _normalize_results(tag(batch_input))

        assert actual == []
        assert prompt_strategy.calls == []
        assert llm_client.calls == []


class TestTaggerPhase2:
    def test_tagger_tc_10_processes_chunks_independently_and_preserves_input_order(
        self,
    ) -> None:
        prompt_strategy = _RecordingPromptStrategy()
        llm_client = _QueueLlmClient([["Docker"], ["React"]])
        batch_input = _make_batch_input(
            chunks=[
                (4, "Docker Compose でアプリと PostgreSQL を起動する。"),
                (1, "useEffect の依存配列を整理した。"),
            ],
            existing_tags=["React", "Docker", "PostgreSQL"],
            prompt_strategy=prompt_strategy,
            llm_client=llm_client,
        )

        actual = _normalize_results(tag(batch_input))

        assert actual == [
            {"chunk_index": 4, "tags": ["Docker"]},
            {"chunk_index": 1, "tags": ["React"]},
        ]
        assert prompt_strategy.calls == [
            {
                "chunk_text": "Docker Compose でアプリと PostgreSQL を起動する。",
                "existing_tags": ["React", "Docker", "PostgreSQL"],
            },
            {
                "chunk_text": "useEffect の依存配列を整理した。",
                "existing_tags": ["React", "Docker", "PostgreSQL"],
            },
        ]
        assert len(llm_client.calls) == 2

    def test_tagger_tc_11_uses_existing_tags_only_and_orders_by_existing_tags(
        self,
    ) -> None:
        prompt_strategy = _RecordingPromptStrategy()
        llm_client = _QueueLlmClient([["PostgreSQL", "Docker", "Docker", "MySQL"]])
        batch_input = _make_batch_input(
            chunks=[
                (0, "Docker Compose でアプリケーションと PostgreSQL をまとめて起動する。"),
            ],
            existing_tags=["Docker", "PostgreSQL", "Linux"],
            prompt_strategy=prompt_strategy,
            llm_client=llm_client,
        )

        actual = _normalize_results(tag(batch_input))

        assert actual == [{"chunk_index": 0, "tags": ["Docker", "PostgreSQL"]}]

    def test_tagger_tc_12_allows_new_tags_only_when_existing_tags_are_empty(
        self,
    ) -> None:
        prompt_strategy = _RecordingPromptStrategy()
        llm_client = _QueueLlmClient([["tRPC", "TypeScript", "tRPC"]])
        batch_input = _make_batch_input(
            chunks=[(3, "tRPC の router 定義と end-to-end 型安全の利点を整理した。")],
            existing_tags=[],
            prompt_strategy=prompt_strategy,
            llm_client=llm_client,
        )

        actual = _normalize_results(tag(batch_input))

        assert actual == [{"chunk_index": 3, "tags": ["tRPC", "TypeScript"]}]

    def test_tagger_tc_13_keeps_obsidian_links_unchanged_in_prompt_input(self) -> None:
        chunk_text = (
            "TypeScript のジェネリクスを整理した。"
            "[[TypeScript公式ドキュメント]] と [[型システム|型安全]] を参照。"
        )
        prompt_strategy = _RecordingPromptStrategy()
        llm_client = _QueueLlmClient([["TypeScript"]])
        batch_input = _make_batch_input(
            chunks=[(0, chunk_text)],
            existing_tags=["TypeScript", "React"],
            prompt_strategy=prompt_strategy,
            llm_client=llm_client,
        )

        actual = _normalize_results(tag(batch_input))

        assert actual == [{"chunk_index": 0, "tags": ["TypeScript"]}]
        assert prompt_strategy.calls == [
            {
                "chunk_text": chunk_text,
                "existing_tags": ["TypeScript", "React"],
            },
        ]

    def test_tagger_tc_14_normalizes_existing_tags_before_building_prompt(
        self,
    ) -> None:
        prompt_strategy = _RecordingPromptStrategy()
        llm_client = _QueueLlmClient([["React"]])
        batch_input = _make_batch_input(
            chunks=[(0, "React の useEffect を整理した。")],
            existing_tags=["  React  ", "", "React", " TypeScript "],
            prompt_strategy=prompt_strategy,
            llm_client=llm_client,
        )

        actual = _normalize_results(tag(batch_input))

        assert actual == [{"chunk_index": 0, "tags": ["React"]}]
        assert prompt_strategy.calls == [
            {
                "chunk_text": "React の useEffect を整理した。",
                "existing_tags": ["React", "TypeScript"],
            },
        ]

    def test_tagger_tc_15_switches_to_new_tag_mode_when_normalized_existing_tags_are_empty(
        self,
    ) -> None:
        prompt_strategy = _RecordingPromptStrategy()
        llm_client = _QueueLlmClient([["SQL"]])
        batch_input = _make_batch_input(
            chunks=[(2, "LEFT JOIN の使いどころを整理した。")],
            existing_tags=[" ", ""],
            prompt_strategy=prompt_strategy,
            llm_client=llm_client,
        )

        actual = _normalize_results(tag(batch_input))

        assert actual == [{"chunk_index": 2, "tags": ["SQL"]}]
        assert prompt_strategy.calls == [
            {
                "chunk_text": "LEFT JOIN の使いどころを整理した。",
                "existing_tags": [],
            },
        ]

    def test_tagger_tc_16_accepts_top_level_tag_for_subconcept_focused_chunk(
        self,
    ) -> None:
        prompt_strategy = _RecordingPromptStrategy()
        llm_client = _QueueLlmClient([["React"]])
        batch_input = _make_batch_input(
            chunks=[(7, "useEffect の依存配列とクリーンアップの挙動を整理した。")],
            existing_tags=["React", "TypeScript"],
            prompt_strategy=prompt_strategy,
            llm_client=llm_client,
        )

        actual = _normalize_results(tag(batch_input))

        assert actual == [{"chunk_index": 7, "tags": ["React"]}]


class TestTaggerPhase3:
    def test_tagger_tc_20_returns_empty_tags_for_candidate_outside_existing_tags(
        self,
    ) -> None:
        prompt_strategy = _RecordingPromptStrategy()
        llm_client = _QueueLlmClient([["TS", "JavaScript"]])
        batch_input = _make_batch_input(
            chunks=[(1, "TypeScript の型推論を整理した。")],
            existing_tags=["TypeScript", "React"],
            prompt_strategy=prompt_strategy,
            llm_client=llm_client,
        )

        actual = _normalize_results(tag(batch_input))

        assert actual == [{"chunk_index": 1, "tags": []}]

    def test_tagger_tc_21_returns_empty_tags_for_blank_chunk_text(self) -> None:
        prompt_strategy = _RecordingPromptStrategy()
        llm_client = _QueueLlmClient([["Docker"], ["Docker"]])
        batch_input = _make_batch_input(
            chunks=[(0, ""), (1, " \n\t ")],
            existing_tags=["Docker"],
            prompt_strategy=prompt_strategy,
            llm_client=llm_client,
        )

        actual = _normalize_results(tag(batch_input))

        assert actual == [
            {"chunk_index": 0, "tags": []},
            {"chunk_index": 1, "tags": []},
        ]

    def test_tagger_tc_22_returns_empty_tags_for_overly_granular_new_tags(
        self,
    ) -> None:
        prompt_strategy = _RecordingPromptStrategy()
        llm_client = _QueueLlmClient([["LEFT JOIN", "ON句"]])
        batch_input = _make_batch_input(
            chunks=[(2, "LEFT JOIN と ON 句の違いを整理した。")],
            existing_tags=[],
            prompt_strategy=prompt_strategy,
            llm_client=llm_client,
        )

        actual = _normalize_results(tag(batch_input))

        assert actual == [{"chunk_index": 2, "tags": []}]

    def test_tagger_tc_23_returns_multiple_related_existing_tags(self) -> None:
        prompt_strategy = _RecordingPromptStrategy()
        llm_client = _QueueLlmClient([["PostgreSQL", "Docker"]])
        batch_input = _make_batch_input(
            chunks=[
                (6, "Docker Compose で PostgreSQL を立ち上げ、コンテナ間通信も確認した。"),
            ],
            existing_tags=["Docker", "PostgreSQL", "Linux"],
            prompt_strategy=prompt_strategy,
            llm_client=llm_client,
        )

        actual = _normalize_results(tag(batch_input))

        assert actual == [{"chunk_index": 6, "tags": ["Docker", "PostgreSQL"]}]

    def test_tagger_tc_24_keeps_existing_tag_mode_when_normalization_still_leaves_candidates(
        self,
    ) -> None:
        prompt_strategy = _RecordingPromptStrategy()
        llm_client = _QueueLlmClient([["React", "Vue"]])
        batch_input = _make_batch_input(
            chunks=[(0, "React Hooks の整理。")],
            existing_tags=[" React ", "React", " "],
            prompt_strategy=prompt_strategy,
            llm_client=llm_client,
        )

        actual = _normalize_results(tag(batch_input))

        assert actual == [{"chunk_index": 0, "tags": ["React"]}]
        assert prompt_strategy.calls == [
            {
                "chunk_text": "React Hooks の整理。",
                "existing_tags": ["React"],
            },
        ]


class TestTaggerPhase4:
    @pytest.mark.parametrize("prompt_marker", ["strategy-a", "strategy-b"])
    def test_tagger_tc_30_accepts_swappable_prompt_strategies(
        self,
        prompt_marker: str,
    ) -> None:
        class _StrategyWithMarker:
            def __init__(self, marker: str) -> None:
                self.marker = marker
                self.calls: list[dict[str, object]] = []

            def build_prompt(
                self,
                chunk_text: str,
                existing_tags: list[str],
            ) -> object:
                self.calls.append(
                    {
                        "chunk_text": chunk_text,
                        "existing_tags": list(existing_tags),
                    },
                )
                return {"marker": self.marker, "chunk_text": chunk_text}

        prompt_strategy = _StrategyWithMarker(prompt_marker)
        llm_client = _QueueLlmClient([["Docker"]])
        batch_input = _make_batch_input(
            chunks=[(0, "Docker ネットワークを整理した。")],
            existing_tags=["Docker", "Linux"],
            prompt_strategy=prompt_strategy,
            llm_client=llm_client,
        )

        actual = _normalize_results(tag(batch_input))

        assert actual == [{"chunk_index": 0, "tags": ["Docker"]}]
        assert prompt_strategy.calls == [
            {
                "chunk_text": "Docker ネットワークを整理した。",
                "existing_tags": ["Docker", "Linux"],
            },
        ]
        assert llm_client.calls == [
            {"marker": prompt_marker, "chunk_text": "Docker ネットワークを整理した。"},
        ]

    def test_tagger_tc_31_raises_prompt_build_error_when_strategy_fails(self) -> None:
        prompt_strategy = _RecordingPromptStrategy(fail_on_call=1)
        llm_client = _QueueLlmClient([["React"]])
        batch_input = _make_batch_input(
            chunks=[(0, "React Hooks を整理した。")],
            existing_tags=["React"],
            prompt_strategy=prompt_strategy,
            llm_client=llm_client,
        )

        with pytest.raises(TaggingPromptBuildError):
            tag(batch_input)
        assert prompt_strategy.calls == [
            {
                "chunk_text": "React Hooks を整理した。",
                "existing_tags": ["React"],
            },
        ]
        assert llm_client.calls == []

    def test_tagger_tc_32_raises_llm_call_error_when_client_fails(self) -> None:
        prompt_strategy = _RecordingPromptStrategy()
        llm_client = _QueueLlmClient([["Docker"]], fail_on_call=1)
        batch_input = _make_batch_input(
            chunks=[(0, "Docker Compose を整理した。")],
            existing_tags=["Docker"],
            prompt_strategy=prompt_strategy,
            llm_client=llm_client,
            source_path="notes/docker.md",
        )

        with pytest.raises(TaggingLlmCallError):
            tag(batch_input)

        assert len(prompt_strategy.calls) == 1
        assert len(llm_client.calls) == 1

    def test_tagger_tc_33_raises_response_format_error_for_non_list_response(
        self,
    ) -> None:
        prompt_strategy = _RecordingPromptStrategy()
        llm_client = _QueueLlmClient([{"tags": ["Docker"]}])
        batch_input = _make_batch_input(
            chunks=[(0, "Docker Compose を整理した。")],
            existing_tags=["Docker"],
            prompt_strategy=prompt_strategy,
            llm_client=llm_client,
        )

        with pytest.raises(TaggingResponseFormatError):
            tag(batch_input)

    def test_tagger_tc_34_raises_response_format_error_for_non_string_items(
        self,
    ) -> None:
        prompt_strategy = _RecordingPromptStrategy()
        llm_client = _QueueLlmClient([["Docker", 1]])
        batch_input = _make_batch_input(
            chunks=[(0, "Docker Compose を整理した。")],
            existing_tags=["Docker"],
            prompt_strategy=prompt_strategy,
            llm_client=llm_client,
        )

        with pytest.raises(TaggingResponseFormatError):
            tag(batch_input)

    def test_tagger_tc_35_records_observability_fields(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        prompt_strategy = _RecordingPromptStrategy()
        llm_client = _QueueLlmClient([["React"], []])
        batch_input = _make_batch_input(
            chunks=[
                (0, "React Hooks を整理した。"),
                (1, "今日は次に読む記事を考えた。"),
            ],
            existing_tags=["React", "TypeScript"],
            prompt_strategy=prompt_strategy,
            llm_client=llm_client,
            source_path="notes/react.md",
        )

        with caplog.at_level(logging.INFO):
            actual = _normalize_results(tag(batch_input))

        assert actual == [
            {"chunk_index": 0, "tags": ["React"]},
            {"chunk_index": 1, "tags": []},
        ]

        observability_records = _find_log_records_with_observability_fields(caplog)
        assert observability_records

        assert any(
            getattr(record, "source_path", None) == "notes/react.md"
            for record in observability_records
        )
        assert {0, 1}.issubset(
            _collect_int_field_values(observability_records, "chunk_index"),
        )
        assert 2 in _collect_int_field_values(
            observability_records,
            "existing_tag_count",
        )
        assert 1 in _collect_int_field_values(
            observability_records,
            "generated_tag_count",
        )
        assert 1 in _collect_int_field_values(
            observability_records,
            "empty_result_count",
        )
        assert 0 in _collect_int_field_values(
            observability_records,
            "llm_failure_count",
        )
