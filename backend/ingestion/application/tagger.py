from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import structlog

logger = structlog.get_logger(__name__)

_KNOWN_GRANULAR_TAGS = {
    "left join",
    "on句",
}
_GRANULAR_SUFFIXES = ("句",)


class TaggingPromptBuildError(Exception):
    pass


class TaggingLlmCallError(Exception):
    pass


class TaggingResponseFormatError(Exception):
    pass


class TaggingPromptStrategy(Protocol):
    def build_prompt(self, chunk_text: str, existing_tags: list[str]) -> object: ...


class LlmTagClassifier(Protocol):
    def classify(self, prompt: object) -> list[str]: ...


@dataclass(frozen=True)
class ChunkTaggingInput:
    chunk_index: int
    text: str


@dataclass(frozen=True)
class ChunkTaggingResult:
    chunk_index: int
    tags: list[str]


@dataclass(frozen=True)
class _ObservabilityContext:
    source_path: str | None
    chunk_index: int
    existing_tag_count: int


@dataclass(frozen=True)
class TaggingBatchInput:
    chunks: list[ChunkTaggingInput]
    existing_tags: list[str]
    prompt_strategy: TaggingPromptStrategy
    llm_client: LlmTagClassifier
    source_path: str | None = None


def tag(batch_input: TaggingBatchInput) -> list[ChunkTaggingResult]:
    normalized_existing_tags = _normalize_existing_tags(batch_input.existing_tags)
    results: list[ChunkTaggingResult] = []

    for chunk in batch_input.chunks:
        observability_context = _ObservabilityContext(
            source_path=batch_input.source_path,
            chunk_index=chunk.chunk_index,
            existing_tag_count=len(normalized_existing_tags),
        )
        if chunk.text.strip() == "":
            results.append(ChunkTaggingResult(chunk_index=chunk.chunk_index, tags=[]))
            _log_chunk_processed(
                observability_context,
                generated_tag_count=0,
                empty_result_count=1,
                llm_failure_count=0,
            )
            continue

        prompt = _build_prompt(
            batch_input.prompt_strategy,
            chunk.text,
            normalized_existing_tags,
        )
        raw_tags = _classify_tags(
            batch_input.llm_client,
            prompt,
            observability_context,
        )
        normalized_response_tags = _normalize_response_tags(raw_tags)
        final_tags = _finalize_tags(normalized_existing_tags, normalized_response_tags)

        results.append(
            ChunkTaggingResult(
                chunk_index=chunk.chunk_index,
                tags=final_tags,
            ),
        )
        _log_chunk_processed(
            observability_context,
            generated_tag_count=len(final_tags),
            empty_result_count=int(len(final_tags) == 0),
            llm_failure_count=0,
        )

    return results


def _build_prompt(
    prompt_strategy: TaggingPromptStrategy,
    chunk_text: str,
    existing_tags: list[str],
) -> object:
    try:
        return prompt_strategy.build_prompt(chunk_text, existing_tags)
    except Exception as exc:
        message = "prompt strategy failed to build prompt"
        raise TaggingPromptBuildError(message) from exc


def _classify_tags(
    llm_client: LlmTagClassifier,
    prompt: object,
    observability_context: _ObservabilityContext,
) -> list[str]:
    try:
        response = llm_client.classify(prompt)
    except Exception as exc:
        _log_llm_call_failed(observability_context)
        message = "llm client classify failed"
        raise TaggingLlmCallError(message) from exc

    if not isinstance(response, list):
        message = "llm client must return list[str]"
        raise TaggingResponseFormatError(message)
    if any(not isinstance(item, str) for item in response):
        message = "llm client must return list[str]"
        raise TaggingResponseFormatError(message)
    return response


def _normalize_existing_tags(existing_tags: list[str]) -> list[str]:
    normalized_tags: list[str] = []
    seen_tags: set[str] = set()

    for tag in existing_tags:
        normalized_tag = tag.strip()
        if normalized_tag == "" or normalized_tag in seen_tags:
            continue
        seen_tags.add(normalized_tag)
        normalized_tags.append(normalized_tag)

    return normalized_tags


def _normalize_response_tags(response_tags: list[str]) -> list[str]:
    normalized_tags: list[str] = []
    seen_tags: set[str] = set()

    for tag in response_tags:
        normalized_tag = tag.strip()
        if normalized_tag == "" or normalized_tag in seen_tags:
            continue
        seen_tags.add(normalized_tag)
        normalized_tags.append(normalized_tag)

    return normalized_tags


def _finalize_tags(existing_tags: list[str], response_tags: list[str]) -> list[str]:
    if existing_tags:
        response_tag_set = set(response_tags)
        return [tag for tag in existing_tags if tag in response_tag_set]
    return [tag for tag in response_tags if _is_top_level_tag(tag)]


def _is_top_level_tag(tag: str) -> bool:
    normalized_tag = tag.strip()
    if normalized_tag == "":
        return False
    if normalized_tag.casefold() in _KNOWN_GRANULAR_TAGS:
        return False
    if " " in normalized_tag:
        return False
    return not normalized_tag.endswith(_GRANULAR_SUFFIXES)


def _log_chunk_processed(
    observability_context: _ObservabilityContext,
    *,
    generated_tag_count: int,
    empty_result_count: int,
    llm_failure_count: int,
) -> None:
    logger.info(
        "tagger_chunk_processed",
        source_path=observability_context.source_path,
        chunk_index=observability_context.chunk_index,
        existing_tag_count=observability_context.existing_tag_count,
        generated_tag_count=generated_tag_count,
        empty_result_count=empty_result_count,
        llm_failure_count=llm_failure_count,
    )


def _log_llm_call_failed(observability_context: _ObservabilityContext) -> None:
    logger.exception(
        "tagger_llm_call_failed",
        source_path=observability_context.source_path,
        chunk_index=observability_context.chunk_index,
        existing_tag_count=observability_context.existing_tag_count,
        generated_tag_count=0,
        empty_result_count=0,
        llm_failure_count=1,
    )
