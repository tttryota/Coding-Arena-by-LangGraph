from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Protocol

logger = logging.getLogger(__name__)

_TOKEN_LIMIT = 512
_HEADING_PATTERN = re.compile(r"^(#{1,2}) (.+)$")


class ChunkSplitInputError(Exception):
    pass


class TokenCountError(Exception):
    pass


class TokenCounter(Protocol):
    def count(self, text: str) -> int: ...


@dataclass(frozen=True)
class ChunkSplitResult:
    content: str
    heading_path: list[str]
    token_count: int


@dataclass(frozen=True)
class _PrimaryChunk:
    content: str
    heading_path: list[str]


def split(markdown_text: str, token_counter: TokenCounter) -> list[ChunkSplitResult]:
    _validate_input(markdown_text, token_counter)

    body = _strip_frontmatter(markdown_text)
    if body.strip() == "":
        return []

    primary_chunks = _split_primary_chunks(body)

    results: list[ChunkSplitResult] = []
    for primary_chunk in primary_chunks:
        token_count = _count_tokens(primary_chunk.content, token_counter)
        if token_count <= _TOKEN_LIMIT:
            results.append(
                ChunkSplitResult(
                    content=primary_chunk.content,
                    heading_path=primary_chunk.heading_path,
                    token_count=token_count,
                ),
            )
            continue

        results.extend(_split_secondary(primary_chunk, token_count, token_counter))

    over_limit_chunks = sum(1 for chunk in results if chunk.token_count > _TOKEN_LIMIT)
    logger.info(
        "chunk_splitter completed total_chunks=%s over_limit_chunks=%s",
        len(results),
        over_limit_chunks,
    )
    return results


def _validate_input(markdown_text: object, token_counter: object) -> None:
    if not isinstance(markdown_text, str):
        raise ChunkSplitInputError("markdown_text must be a string")

    count = getattr(token_counter, "count", None)
    if not callable(count):
        raise ChunkSplitInputError(
            "token_counter must provide callable count(text: str) -> int",
        )


def _strip_frontmatter(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    if not lines or lines[0] != "---":
        return markdown_text

    closing_index: int | None = None
    for index in range(1, len(lines)):
        if lines[index] == "---":
            closing_index = index
            break

    if closing_index is None:
        return markdown_text

    remaining_lines = lines[closing_index + 1 :]
    while remaining_lines and remaining_lines[0] == "":
        remaining_lines = remaining_lines[1:]
    return "\n".join(remaining_lines)


def _split_primary_chunks(body: str) -> list[_PrimaryChunk]:
    lines = body.splitlines()
    if not lines:
        return []

    chunks: list[_PrimaryChunk] = []
    current_lines: list[str] = []
    current_heading_path: list[str] = []
    current_h1: str | None = None
    in_code_block = False
    found_boundary = False

    for line in lines:
        heading = None if in_code_block else _parse_heading(line)
        if heading is not None:
            if current_lines and (found_boundary or "\n".join(current_lines).strip() != ""):
                chunks.append(
                    _PrimaryChunk(
                        content="\n".join(_trim_trailing_blank_lines(current_lines)),
                        heading_path=current_heading_path,
                    ),
                )

            found_boundary = True
            level, text = heading
            if level == 1:
                current_h1 = text
                current_heading_path = [text]
            else:
                current_heading_path = [current_h1, text] if current_h1 else [text]
            current_lines = [line]
        else:
            current_lines.append(line)

        if _is_fence_line(line):
            in_code_block = not in_code_block

    if not found_boundary:
        return [_PrimaryChunk(content=body, heading_path=[])]

    if current_lines:
        chunks.append(
            _PrimaryChunk(
                content="\n".join(_trim_trailing_blank_lines(current_lines)),
                heading_path=current_heading_path,
            ),
        )
    return chunks


def _parse_heading(line: str) -> tuple[int, str] | None:
    matched = _HEADING_PATTERN.match(line)
    if matched is None:
        return None
    hashes, text = matched.groups()
    return len(hashes), text


def _is_fence_line(line: str) -> bool:
    return line.startswith("```")


def _count_tokens(text: str, token_counter: TokenCounter) -> int:
    try:
        token_count = token_counter.count(text)
    except Exception as exc:
        raise TokenCountError("token counting failed") from exc

    if type(token_count) is not int or token_count < 0:
        raise TokenCountError("token_counter must return a non-negative integer")
    return token_count


def _split_secondary(
    primary_chunk: _PrimaryChunk,
    primary_token_count: int,
    token_counter: TokenCounter,
) -> list[ChunkSplitResult]:
    heading_line, body = _extract_heading_context(primary_chunk.content)
    segments = _split_body_segments(body if heading_line is not None else primary_chunk.content)
    if len(segments) <= 1:
        return [
            ChunkSplitResult(
                content=primary_chunk.content,
                heading_path=primary_chunk.heading_path,
                token_count=primary_token_count,
            ),
        ]

    results: list[ChunkSplitResult] = []
    current_segments = [segments[0]]
    current_token_count: int | None = None

    for segment in segments[1:]:
        candidate_content = _compose_chunk_content(heading_line, current_segments + [segment])
        candidate_token_count = _count_tokens(candidate_content, token_counter)
        if candidate_token_count <= _TOKEN_LIMIT:
            current_segments.append(segment)
            current_token_count = candidate_token_count
            continue

        finalized_content = _compose_chunk_content(heading_line, current_segments)
        finalized_token_count = current_token_count
        if finalized_token_count is None:
            finalized_token_count = _count_tokens(finalized_content, token_counter)

        results.append(
            ChunkSplitResult(
                content=finalized_content,
                heading_path=primary_chunk.heading_path,
                token_count=finalized_token_count,
            ),
        )

        current_segments = [segment]
        current_token_count = None

    finalized_content = _compose_chunk_content(heading_line, current_segments)
    finalized_token_count = current_token_count
    if finalized_token_count is None:
        finalized_token_count = _count_tokens(finalized_content, token_counter)

    results.append(
        ChunkSplitResult(
            content=finalized_content,
            heading_path=primary_chunk.heading_path,
            token_count=finalized_token_count,
        ),
    )
    return results


def _extract_heading_context(content: str) -> tuple[str | None, str]:
    lines = content.splitlines()
    if not lines:
        return None, ""

    heading = _parse_heading(lines[0])
    if heading is None:
        return None, content

    body_lines = lines[1:]
    while body_lines and body_lines[0] == "":
        body_lines = body_lines[1:]
    return lines[0], "\n".join(body_lines)


def _split_body_segments(text: str) -> list[str]:
    lines = text.splitlines()
    segments: list[str] = []
    current_lines: list[str] = []
    in_code_block = False

    for line in lines:
        if not in_code_block and line == "":
            if current_lines:
                segments.append("\n".join(current_lines))
                current_lines = []
            continue

        current_lines.append(line)
        if _is_fence_line(line):
            in_code_block = not in_code_block

    if current_lines:
        segments.append("\n".join(current_lines))

    return _merge_horizontal_rule_segments(segments)


def _merge_horizontal_rule_segments(segments: list[str]) -> list[str]:
    if not segments:
        return []

    merged: list[str] = []
    index = 0
    while index < len(segments):
        segment = segments[index]
        if segment == "---" and index + 1 < len(segments):
            merged.append(f"{segment}\n\n{segments[index + 1]}")
            index += 2
            continue
        merged.append(segment)
        index += 1
    return merged


def _trim_trailing_blank_lines(lines: list[str]) -> list[str]:
    trimmed = list(lines)
    while trimmed and trimmed[-1] == "":
        trimmed.pop()
    return trimmed


def _compose_chunk_content(heading_line: str | None, segments: list[str]) -> str:
    body = "\n\n".join(segments)
    if heading_line is None:
        return body
    if body == "":
        return heading_line
    return f"{heading_line}\n\n{body}"
