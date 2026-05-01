"""Markdown テキストから目次を生成する."""

from __future__ import annotations

import re
from dataclasses import dataclass

HEADING_PATTERN = re.compile(r"^(#{1,6}) +(.*)$")
ATX_CLOSING_PATTERN = re.compile(r" +#+\s*$")

BACKTICK_FENCE_OPEN_PATTERN = re.compile(r"^(`{3,})")
TILDE_FENCE_OPEN_PATTERN = re.compile(r"^(~{3,})")
BACKTICK_FENCE_CLOSE_PATTERN = re.compile(r"^(`{3,})\s*$")
TILDE_FENCE_CLOSE_PATTERN = re.compile(r"^(~{3,})\s*$")

LINK_PATTERN = re.compile(r"\[([^\]]*)\]\([^)]*\)")
INLINE_CODE_PATTERN = re.compile(r"`([^`]+)`")
BOLD_ASTERISK_PATTERN = re.compile(r"\*\*(.+?)\*\*")
BOLD_UNDERSCORE_PATTERN = re.compile(r"(?<!\w)__(.+?)__(?!\w)")
ITALIC_ASTERISK_PATTERN = re.compile(r"\*(.+?)\*")
ITALIC_UNDERSCORE_PATTERN = re.compile(r"(?<!\w)_(.+?)_(?!\w)")

SLUG_DISALLOWED_PATTERN = re.compile(
    r"[^a-z0-9\-_\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]",
)
CONSECUTIVE_HYPHENS_PATTERN = re.compile(r"-{2,}")

INDENT_UNIT = 2


@dataclass(frozen=True)
class TocHeading:
    """目次の1エントリ."""

    text: str
    level: int
    anchor: str


@dataclass(frozen=True)
class TocResult:
    """目次の生成結果."""

    headings: list[TocHeading]
    markdown: str


def _remove_decorations(text: str) -> str:
    """Markdown 装飾を除去する."""
    text = LINK_PATTERN.sub(r"\1", text)
    text = INLINE_CODE_PATTERN.sub(r"\1", text)
    text = BOLD_ASTERISK_PATTERN.sub(r"\1", text)
    text = BOLD_UNDERSCORE_PATTERN.sub(r"\1", text)
    text = ITALIC_ASTERISK_PATTERN.sub(r"\1", text)
    return ITALIC_UNDERSCORE_PATTERN.sub(r"\1", text)


def _generate_slug(text: str) -> str:
    """GitHub 互換のアンカースラッグを生成する."""
    slug = text.lower().replace(" ", "-")
    slug = SLUG_DISALLOWED_PATTERN.sub("", slug)
    slug = CONSECUTIVE_HYPHENS_PATTERN.sub("-", slug)
    return slug.strip("-")


def _update_fence_state(
    line: str,
    fence_char: str | None,
    fence_length: int,
) -> tuple[bool, str | None, int]:
    """コードブロックのフェンス状態を更新する.

    Returns:
        (この行はコードブロック内か, 現在のフェンス文字, フェンス長)
    """
    if fence_char is not None:
        return _check_fence_close(line, fence_char, fence_length)

    return _check_fence_open(line)


def _check_fence_close(
    line: str,
    fence_char: str,
    fence_length: int,
) -> tuple[bool, str | None, int]:
    """コードブロックの閉じフェンスを判定する."""
    pattern = (
        BACKTICK_FENCE_CLOSE_PATTERN if fence_char == "`" else TILDE_FENCE_CLOSE_PATTERN
    )
    close_match = pattern.match(line)
    if close_match and len(close_match.group(1)) >= fence_length:
        return True, None, 0
    return True, fence_char, fence_length


def _check_fence_open(line: str) -> tuple[bool, str | None, int]:
    """コードブロックの開きフェンスを判定する."""
    backtick_match = BACKTICK_FENCE_OPEN_PATTERN.match(line)
    if backtick_match:
        return True, "`", len(backtick_match.group(1))

    tilde_match = TILDE_FENCE_OPEN_PATTERN.match(line)
    if tilde_match:
        return True, "~", len(tilde_match.group(1))

    return False, None, 0


def _extract_raw_headings(lines: list[str]) -> list[tuple[str, int]]:
    """行リストから見出しテキストとレベルを抽出する."""
    raw_headings: list[tuple[str, int]] = []
    fence_char: str | None = None
    fence_length = 0

    for line in lines:
        is_code, fence_char, fence_length = _update_fence_state(
            line,
            fence_char,
            fence_length,
        )
        if is_code:
            continue

        heading_match = HEADING_PATTERN.match(line)
        if heading_match:
            level = len(heading_match.group(1))
            raw_text = ATX_CLOSING_PATTERN.sub("", heading_match.group(2))
            raw_text = _remove_decorations(raw_text)
            raw_headings.append((raw_text, level))

    return raw_headings


def _assign_anchors(
    raw_headings: list[tuple[str, int]],
) -> list[TocHeading]:
    """スラッグ生成と重複アンカー付番を行う."""
    anchor_counts: dict[str, int] = {}
    result: list[TocHeading] = []

    for text, level in raw_headings:
        base_slug = _generate_slug(text)
        count = anchor_counts.get(base_slug, 0)
        anchor = base_slug if count == 0 else f"{base_slug}-{count}"
        anchor_counts[base_slug] = count + 1
        result.append(TocHeading(text=text, level=level, anchor=anchor))

    return result


def _render_markdown(headings: list[TocHeading]) -> str:
    """目次の Markdown テキストを生成する."""
    if not headings:
        return ""

    min_level = min(h.level for h in headings)
    lines: list[str] = []
    for heading in headings:
        depth = heading.level - min_level
        indent = " " * (INDENT_UNIT * depth)
        lines.append(f"{indent}- [{heading.text}](#{heading.anchor})")

    return "\n".join(lines)


def generate_toc(
    text: str,
    min_level: int = 1,
    max_level: int = 3,
) -> TocResult:
    """Markdown テキストから目次を生成する."""
    if not text or min_level > max_level:
        return TocResult(headings=[], markdown="")

    raw_headings = _extract_raw_headings(text.splitlines())
    all_headings = _assign_anchors(raw_headings)
    filtered = [h for h in all_headings if min_level <= h.level <= max_level]

    return TocResult(headings=filtered, markdown=_render_markdown(filtered))
