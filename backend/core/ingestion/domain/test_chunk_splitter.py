import importlib
from collections.abc import Callable, Mapping
from typing import Any

import pytest

_Splitter = Callable[[object, Any], object]
_SplitterContract = tuple[_Splitter, type[Exception], type[Exception]]
_TARGET_SPLITTER_MODULE = "core.ingestion.chunk_splitter"


class _MappingTokenCounter:
    def __init__(self, counts: Mapping[str, int]) -> None:
        self._counts = dict(counts)
        self.calls: list[str] = []

    def count(self, text: str) -> int:
        self.calls.append(text)
        if text in self._counts:
            return self._counts[text]
        msg = f"unexpected token_counter.count() call for text: {text!r}"
        raise AssertionError(msg)


class _CallbackTokenCounter:
    def __init__(self, callback: Callable[[str], object]) -> None:
        self._callback = callback
        self.calls: list[str] = []

    def count(self, text: str) -> object:
        self.calls.append(text)
        return self._callback(text)


class _UnusedTokenCounter:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def count(self, text: str) -> int:
        self.calls.append(text)
        msg = "token_counter.count() should not be called"
        raise AssertionError(msg)


def _load_splitter_contract() -> _SplitterContract:
    module = importlib.import_module(_TARGET_SPLITTER_MODULE)
    input_error = _find_exception_type(module, "ChunkSplitInputError")
    token_count_error = _find_exception_type(module, "TokenCountError")
    splitter = getattr(module, "split", None)
    if not callable(splitter):
        msg = (
            "could not find callable 'split(markdown_text, token_counter)' "
            f"in {_TARGET_SPLITTER_MODULE}"
        )
        raise AssertionError(msg)
    return splitter, input_error, token_count_error


def _find_exception_type(
    module: object,
    exception_name: str,
) -> type[Exception]:
    value = getattr(module, exception_name, None)
    if isinstance(value, type) and issubclass(value, Exception):
        return value
    msg = (
        f"could not find exception type {exception_name!r} in {_TARGET_SPLITTER_MODULE}"
    )
    raise AssertionError(msg)


def _normalize_results(results: object) -> list[dict[str, object]]:
    assert isinstance(results, list)

    normalized: list[dict[str, object]] = []
    for result in results:
        content = _read_field(result, "content")
        heading_path = _read_field(result, "heading_path")
        token_count = _read_field(result, "token_count")

        assert isinstance(content, str)
        assert isinstance(heading_path, list)
        assert all(isinstance(item, str) for item in heading_path)
        assert type(token_count) is int

        normalized.append(
            {
                "content": content,
                "heading_path": heading_path,
                "token_count": token_count,
            },
        )
    return normalized


def _read_field(result: object, field_name: str) -> object:
    if isinstance(result, Mapping):
        assert field_name in result
        return result[field_name]

    assert hasattr(result, field_name)
    return getattr(result, field_name)


@pytest.fixture(name="splitter_contract")
def fixture_splitter_contract() -> _SplitterContract:
    return _load_splitter_contract()


class TestChunkSplitterPhase1:
    def test_splitter_tc_01_returns_single_h1_chunk(
        self,
        splitter_contract: _SplitterContract,
    ) -> None:
        splitter, _, _ = splitter_contract
        markdown_text = "# Docker\n\n概要"
        token_counter = _MappingTokenCounter({markdown_text: 12})

        actual = _normalize_results(splitter(markdown_text, token_counter))

        assert actual == [
            {
                "content": "# Docker\n\n概要",
                "heading_path": ["Docker"],
                "token_count": 12,
            },
        ]
        assert token_counter.calls == [markdown_text]

    def test_splitter_tc_02_returns_whole_body_when_h1_h2_are_absent(
        self,
        splitter_contract: _SplitterContract,
    ) -> None:
        splitter, _, _ = splitter_contract
        markdown_text = "本文のみ\n\n[[リンク先]]"
        token_counter = _MappingTokenCounter({markdown_text: 18})

        actual = _normalize_results(splitter(markdown_text, token_counter))

        assert actual == [
            {
                "content": "本文のみ\n\n[[リンク先]]",
                "heading_path": [],
                "token_count": 18,
            },
        ]
        assert token_counter.calls == [markdown_text]

    def test_splitter_tc_03_returns_empty_list_for_empty_file(
        self,
        splitter_contract: _SplitterContract,
    ) -> None:
        splitter, _, _ = splitter_contract
        token_counter = _UnusedTokenCounter()

        actual = _normalize_results(splitter("", token_counter))

        assert actual == []
        assert token_counter.calls == []


class TestChunkSplitterPhase2:
    def test_splitter_tc_10_excludes_frontmatter_and_splits_by_h1_h2(
        self,
        splitter_contract: _SplitterContract,
    ) -> None:
        splitter, _, _ = splitter_contract
        markdown_text = (
            "---\n"
            "title: TS Notes\n"
            "tags:\n"
            "  - study\n"
            "---\n\n"
            "# TypeScript\n"
            "Intro\n\n"
            "### Generics\n"
            "T extends U\n\n"
            "## Utility Types\n"
            "Pick と Omit"
        )
        first_chunk = "# TypeScript\nIntro\n\n### Generics\nT extends U"
        second_chunk = "## Utility Types\nPick と Omit"
        token_counter = _MappingTokenCounter(
            {
                first_chunk: 120,
                second_chunk: 65,
            },
        )

        actual = _normalize_results(splitter(markdown_text, token_counter))

        assert actual == [
            {
                "content": first_chunk,
                "heading_path": ["TypeScript"],
                "token_count": 120,
            },
            {
                "content": second_chunk,
                "heading_path": ["TypeScript", "Utility Types"],
                "token_count": 65,
            },
        ]
        assert token_counter.calls == [first_chunk, second_chunk]

    def test_splitter_tc_11_secondary_split_preserves_order_and_heading(
        self,
        splitter_contract: _SplitterContract,
    ) -> None:
        splitter, _, _ = splitter_contract
        markdown_text = "# Docker\n\n段落A\n\n段落B\n\n段落C"
        first_chunk = "# Docker\n\n段落A\n\n段落B"
        second_chunk = "# Docker\n\n段落C"
        token_counter = _MappingTokenCounter(
            {
                "# Docker\n\n段落A": 220,
                first_chunk: 430,
                markdown_text: 620,
                second_chunk: 210,
            },
        )

        actual = _normalize_results(splitter(markdown_text, token_counter))

        assert actual == [
            {
                "content": first_chunk,
                "heading_path": ["Docker"],
                "token_count": 430,
            },
            {
                "content": second_chunk,
                "heading_path": ["Docker"],
                "token_count": 210,
            },
        ]
        assert token_counter.calls[0] == markdown_text
        assert first_chunk in token_counter.calls[1:]
        assert second_chunk in token_counter.calls[1:]

    def test_splitter_tc_12_keeps_code_block_and_body_horizontal_rule(
        self,
        splitter_contract: _SplitterContract,
    ) -> None:
        splitter, _, _ = splitter_contract
        markdown_text = (
            "# Python\n\n"
            "```python\n"
            "# this is not a heading\n"
            'print("a")\n'
            'print("b")\n'
            "```\n\n"
            "---\n\n"
            "本文"
        )
        first_chunk = (
            "# Python\n\n"
            "```python\n"
            "# this is not a heading\n"
            'print("a")\n'
            'print("b")\n'
            "```"
        )
        second_chunk = "# Python\n\n---\n\n本文"
        token_counter = _MappingTokenCounter(
            {
                markdown_text: 580,
                first_chunk: 540,
                second_chunk: 40,
            },
        )

        actual = _normalize_results(splitter(markdown_text, token_counter))

        assert actual == [
            {
                "content": first_chunk,
                "heading_path": ["Python"],
                "token_count": 540,
            },
            {
                "content": second_chunk,
                "heading_path": ["Python"],
                "token_count": 40,
            },
        ]
        assert token_counter.calls[0] == markdown_text
        assert first_chunk in token_counter.calls[1:]
        assert second_chunk in token_counter.calls[1:]

    def test_splitter_tc_13_uses_h2_alone_as_heading_path(
        self,
        splitter_contract: _SplitterContract,
    ) -> None:
        splitter, _, _ = splitter_contract
        markdown_text = "## Utility Types\nPick と Omit"
        token_counter = _MappingTokenCounter({markdown_text: 65})

        actual = _normalize_results(splitter(markdown_text, token_counter))

        assert actual == [
            {
                "content": "## Utility Types\nPick と Omit",
                "heading_path": ["Utility Types"],
                "token_count": 65,
            },
        ]
        assert token_counter.calls == [markdown_text]

    def test_splitter_tc_14_keeps_heading_with_following_code_block_during_resplit(
        self,
        splitter_contract: _SplitterContract,
    ) -> None:
        splitter, _, _ = splitter_contract
        markdown_text = '# Python\n\n```python\nprint("a")\n```\n\n説明段落'
        first_chunk = '# Python\n\n```python\nprint("a")\n```'
        second_chunk = "# Python\n\n説明段落"
        token_counter = _MappingTokenCounter(
            {
                markdown_text: 620,
                first_chunk: 350,
                second_chunk: 120,
            },
        )

        actual = _normalize_results(splitter(markdown_text, token_counter))

        assert actual == [
            {
                "content": first_chunk,
                "heading_path": ["Python"],
                "token_count": 350,
            },
            {
                "content": second_chunk,
                "heading_path": ["Python"],
                "token_count": 120,
            },
        ]
        assert token_counter.calls[0] == markdown_text
        assert first_chunk in token_counter.calls[1:]
        assert second_chunk in token_counter.calls[1:]

    def test_splitter_tc_15_keeps_obsidian_links_unchanged(
        self,
        splitter_contract: _SplitterContract,
    ) -> None:
        splitter, _, _ = splitter_contract
        markdown_text = "# References\n\n[[リンク先]] と [[別ノート|表示名]] を見る"
        token_counter = _MappingTokenCounter({markdown_text: 55})

        actual = _normalize_results(splitter(markdown_text, token_counter))

        assert actual == [
            {
                "content": "# References\n\n[[リンク先]] と [[別ノート|表示名]] を見る",
                "heading_path": ["References"],
                "token_count": 55,
            },
        ]
        assert token_counter.calls == [markdown_text]


class TestChunkSplitterPhase3:
    def test_splitter_tc_20_returns_empty_list_for_whitespace_only_file(
        self,
        splitter_contract: _SplitterContract,
    ) -> None:
        splitter, _, _ = splitter_contract
        token_counter = _UnusedTokenCounter()

        actual = _normalize_results(splitter(" \n\t\n", token_counter))

        assert actual == []
        assert token_counter.calls == []

    def test_splitter_tc_21_returns_empty_list_when_only_frontmatter_exists(
        self,
        splitter_contract: _SplitterContract,
    ) -> None:
        splitter, _, _ = splitter_contract
        token_counter = _UnusedTokenCounter()

        actual = _normalize_results(
            splitter(
                "---\ntitle: only-meta\n---\n",
                token_counter,
            ),
        )

        assert actual == []
        assert token_counter.calls == []

    def test_splitter_tc_22_returns_single_chunk_for_h3_and_deeper_only(
        self,
        splitter_contract: _SplitterContract,
    ) -> None:
        splitter, _, _ = splitter_contract
        markdown_text = "### Generics\nT extends U\n\n#### Constraint\nextends を使う"
        token_counter = _MappingTokenCounter({markdown_text: 90})

        actual = _normalize_results(splitter(markdown_text, token_counter))

        assert actual == [
            {
                "content": "### Generics\nT extends U\n\n#### Constraint\nextends を使う",
                "heading_path": [],
                "token_count": 90,
            },
        ]
        assert token_counter.calls == [markdown_text]

    def test_splitter_tc_23_keeps_unclosed_frontmatter_as_body(
        self,
        splitter_contract: _SplitterContract,
    ) -> None:
        splitter, _, _ = splitter_contract
        markdown_text = "---\ntitle: draft\n本文"
        token_counter = _MappingTokenCounter({markdown_text: 30})

        actual = _normalize_results(splitter(markdown_text, token_counter))

        assert actual == [
            {
                "content": "---\ntitle: draft\n本文",
                "heading_path": [],
                "token_count": 30,
            },
        ]
        assert token_counter.calls == [markdown_text]

    def test_splitter_tc_24_returns_unsplittable_large_single_paragraph_as_is(
        self,
        splitter_contract: _SplitterContract,
    ) -> None:
        splitter, _, _ = splitter_contract
        markdown_text = "# Docker\n\n段落A 段落B 段落C"
        token_counter = _MappingTokenCounter({markdown_text: 620})

        actual = _normalize_results(splitter(markdown_text, token_counter))

        assert actual == [
            {
                "content": "# Docker\n\n段落A 段落B 段落C",
                "heading_path": ["Docker"],
                "token_count": 620,
            },
        ]
        assert token_counter.calls == [markdown_text]

    def test_splitter_tc_25_treats_unclosed_fence_as_code_block_until_eof(
        self,
        splitter_contract: _SplitterContract,
    ) -> None:
        splitter, _, _ = splitter_contract
        markdown_text = '# Before\n\n```python\n## これは見出しではない\nprint("x")'
        token_counter = _MappingTokenCounter({markdown_text: 160})

        actual = _normalize_results(splitter(markdown_text, token_counter))

        assert actual == [
            {
                "content": '# Before\n\n```python\n## これは見出しではない\nprint("x")',
                "heading_path": ["Before"],
                "token_count": 160,
            },
        ]
        assert token_counter.calls == [markdown_text]


class TestChunkSplitterPhase4:
    def test_splitter_tc_30_raises_input_error_for_non_string_markdown(
        self,
        splitter_contract: _SplitterContract,
    ) -> None:
        splitter, input_error, _ = splitter_contract
        token_counter = _MappingTokenCounter({"# Docker\n\n概要": 12})

        with pytest.raises(input_error):
            splitter(123, token_counter)
        assert token_counter.calls == []

    @pytest.mark.parametrize(
        "token_counter",
        [
            object(),
            pytest.param(
                type("InvalidCounter", (), {"count": 123})(),
                id="count-not-callable",
            ),
        ],
    )
    def test_splitter_tc_31_raises_input_error_for_invalid_token_counter_contract(
        self,
        splitter_contract: _SplitterContract,
        token_counter: object,
    ) -> None:
        splitter, input_error, _ = splitter_contract

        with pytest.raises(input_error):
            splitter("# Docker\n\n概要", token_counter)

    def test_splitter_tc_32_raises_token_count_error_when_counter_raises(
        self,
        splitter_contract: _SplitterContract,
    ) -> None:
        splitter, _, token_count_error = splitter_contract

        def count(_: str) -> int:
            msg = "counter failed"
            raise RuntimeError(msg)

        token_counter = _CallbackTokenCounter(count)

        with pytest.raises(token_count_error):
            splitter("# Docker\n\n概要", token_counter)
        assert token_counter.calls == ["# Docker\n\n概要"]

    def test_splitter_tc_33_raises_token_count_error_for_negative_count(
        self,
        splitter_contract: _SplitterContract,
    ) -> None:
        splitter, _, token_count_error = splitter_contract
        token_counter = _MappingTokenCounter({"# Docker\n\n概要": -1})

        with pytest.raises(token_count_error):
            splitter("# Docker\n\n概要", token_counter)
        assert token_counter.calls == ["# Docker\n\n概要"]

    def test_splitter_tc_34_raises_token_count_error_for_non_integer_count(
        self,
        splitter_contract: _SplitterContract,
    ) -> None:
        splitter, _, token_count_error = splitter_contract
        token_counter = _CallbackTokenCounter(lambda _: "12")

        with pytest.raises(token_count_error):
            splitter("# Docker\n\n概要", token_counter)
        assert token_counter.calls == ["# Docker\n\n概要"]
