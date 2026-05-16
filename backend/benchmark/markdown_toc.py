"""Markdown テキストから見出しを抽出し目次を生成するモジュール."""

from __future__ import annotations

import re
from dataclasses import dataclass

_HEADING_PATTERN = re.compile(r"^(#{1,6}) +(.*)$")
_FENCE_PATTERN = re.compile(r"^(`{3,}|~{3,})")
_ATX_CLOSING_PATTERN = re.compile(r" +#+ *$")

_LINK_PATTERN = re.compile(r"\[([^\]]*?)\]\([^)]*?\)")
_CODE_PATTERN = re.compile(r"`([^`]*?)`")
_BOLD_ASTERISK_PATTERN = re.compile(r"\*\*(.+?)\*\*")
_BOLD_UNDERSCORE_PATTERN = re.compile(r"(?<!\w)__(.+?)__(?!\w)")
_ITALIC_ASTERISK_PATTERN = re.compile(r"\*(.+?)\*")
_ITALIC_UNDERSCORE_PATTERN = re.compile(r"(?<!\w)_(.+?)_(?!\w)")

_LINK_LABEL_ESCAPE_PATTERN = re.compile(r"([\\[\]])")

_SLUG_KEEP_PATTERN = re.compile(
    r"[^a-z0-9\-_\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]",
)
_CONSECUTIVE_HYPHENS_PATTERN = re.compile(r"-+")
_SLUG_SEPARATOR = "-"

_DEFAULT_MIN_LEVEL = 1
_DEFAULT_MAX_LEVEL = 3
_INDENT_UNIT = "  "


@dataclass(frozen=True)
class TableOfContentsHeading:
    """目次の見出し1件を表す値オブジェクト."""

    text: str
    level: int
    anchor: str


@dataclass(frozen=True)
class TableOfContentsResult:
    """目次の生成結果を表す値オブジェクト."""

    headings: tuple[TableOfContentsHeading, ...]
    markdown: str


def _strip_decorations(text: str) -> str:
    """見出しテキストから Markdown 装飾を除去する."""
    text = _LINK_PATTERN.sub(r"\1", text)
    text = _CODE_PATTERN.sub(r"\1", text)
    text = _BOLD_ASTERISK_PATTERN.sub(r"\1", text)
    text = _BOLD_UNDERSCORE_PATTERN.sub(r"\1", text)
    text = _ITALIC_ASTERISK_PATTERN.sub(r"\1", text)
    text = _ITALIC_UNDERSCORE_PATTERN.sub(r"\1", text)
    return text


def _generate_slug(text: str) -> str:
    """GitHub 互換の簡易アンカースラッグを生成する."""
    slug = text.lower()
    slug = slug.replace(" ", _SLUG_SEPARATOR)
    slug = _SLUG_KEEP_PATTERN.sub("", slug)
    slug = _CONSECUTIVE_HYPHENS_PATTERN.sub(_SLUG_SEPARATOR, slug)
    slug = slug.strip(_SLUG_SEPARATOR)
    return slug


def _parse_fence(line: str) -> tuple[str, int] | None:
    """行がコードフェンスなら (フェンス文字, 個数) を返す."""
    match = _FENCE_PATTERN.match(line)
    if match is None:
        return None
    fence = match.group(1)
    return fence[0], len(fence)


def _parse_heading(line: str) -> tuple[str, int] | None:
    """行が見出しなら (テキスト, レベル) を返す."""
    match = _HEADING_PATTERN.match(line)
    if match is None:
        return None
    level = len(match.group(1))
    raw_text = _ATX_CLOSING_PATTERN.sub("", match.group(2))
    clean_text = _strip_decorations(raw_text)
    return clean_text, level


def _is_closing_fence(
    line: str,
    fence_character: str,
    fence_count: int,
) -> bool:
    """行が開きフェンスに対応する閉じフェンスかどうか判定する."""
    fence = _parse_fence(line)
    if fence is None:
        return False
    closing_character, closing_count = fence
    return closing_character == fence_character and closing_count >= fence_count


def _extract_raw_headings(lines: list[str]) -> list[tuple[str, int]]:
    """行リストから見出し (テキスト, レベル) を抽出する."""
    headings: list[tuple[str, int]] = []
    is_in_code_block = False
    fence_character = ""
    fence_count = 0

    for line in lines:
        if is_in_code_block:
            if _is_closing_fence(line, fence_character, fence_count):
                is_in_code_block = False
            continue

        fence = _parse_fence(line)
        if fence is not None:
            is_in_code_block = True
            fence_character, fence_count = fence
            continue

        heading = _parse_heading(line)
        if heading is not None:
            headings.append(heading)

    return headings


def _assign_anchors(
    headings: list[tuple[str, int]],
) -> list[tuple[str, int, str]]:
    """全見出しにアンカースラッグを付与する(重複付番込み)."""
    anchor_counts: dict[str, int] = {}
    result: list[tuple[str, int, str]] = []

    for text, level in headings:
        base_slug = _generate_slug(text)
        count = anchor_counts.get(base_slug, 0)
        anchor = base_slug if count == 0 else f"{base_slug}-{count}"
        anchor_counts[base_slug] = count + 1
        result.append((text, level, anchor))

    return result


def _escape_link_label(text: str) -> str:
    """リンクラベル内の Markdown 特殊文字をエスケープする."""
    return _LINK_LABEL_ESCAPE_PATTERN.sub(r"\\\1", text)


def _render_markdown(headings: list[TableOfContentsHeading]) -> str:
    """見出しリストから目次 Markdown を生成する."""
    if not headings:
        return ""

    min_level = min(heading.level for heading in headings)
    lines: list[str] = []
    for heading in headings:
        depth = heading.level - min_level
        indent = _INDENT_UNIT * depth
        label = _escape_link_label(heading.text)
        lines.append(f"{indent}- [{label}](#{heading.anchor})")

    return "\n".join(lines)


def generate_table_of_contents(
    text: str,
    *,
    min_level: int = _DEFAULT_MIN_LEVEL,
    max_level: int = _DEFAULT_MAX_LEVEL,
) -> TableOfContentsResult:
    """Markdown テキストから目次を生成する."""
    if min_level > max_level or not text:
        return TableOfContentsResult(headings=(), markdown="")

    lines = text.splitlines()
    raw_headings = _extract_raw_headings(lines)

    if not raw_headings:
        return TableOfContentsResult(headings=(), markdown="")

    all_with_anchors = _assign_anchors(raw_headings)

    filtered = [
        TableOfContentsHeading(text=heading_text, level=level, anchor=anchor)
        for heading_text, level, anchor in all_with_anchors
        if min_level <= level <= max_level
    ]

    if not filtered:
        return TableOfContentsResult(headings=(), markdown="")

    markdown = _render_markdown(filtered)
    return TableOfContentsResult(headings=tuple(filtered), markdown=markdown)
