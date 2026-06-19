"""competitive_types の型整合性テスト。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import get_args, get_type_hints, is_typeddict

from competitive.domain.competitive_types import (
    AlgoTheme,
    CompetitiveError,
    CompetitiveSessionState,
    CompetitiveSessionStatus,
    ProblemExample,
    ProblemGenerationError,
    ProgrammingLanguage,
    RubricItem,
    SolutionEvaluationError,
    ThemeSelectionError,
)
from competitive.domain.languages import list_supported_languages

_COMPETITIVE_SESSION_STATE_KEYS = (
    "session_id",
    "status",
    "algo_theme_id",
    "algo_theme_label",
    "algo_theme_category",
    "programming_language",
    "problem_statement",
    "input_format",
    "output_format",
    "constraints",
    "examples",
    "reference_solution",
    "grading_rubric",
    "user_code",
    "score",
    "feedback",
    "time_complexity",
    "space_complexity",
    "improvement_suggestions",
    "rubric_scores_json",
)

_ALGO_THEME_KEYS = ("id", "category", "label")
_PROBLEM_EXAMPLE_KEYS = ("input", "output")
_RUBRIC_ITEM_KEYS = ("criterion", "points", "description")

_EXPECTED_FIELD_TYPES: dict[str, str] = {
    "session_id": "str",
    "status": "Literal",
    "algo_theme_id": "str",
    "algo_theme_label": "str",
    "algo_theme_category": "str",
    "programming_language": "str",
    "problem_statement": "str",
    "input_format": "str",
    "output_format": "str",
    "constraints": "str",
    "examples": "ProblemExample",
    "reference_solution": "str",
    "grading_rubric": "RubricItem",
    "user_code": "str",
    "score": "int",
    "feedback": "str",
    "time_complexity": "str",
    "space_complexity": "str",
    "improvement_suggestions": "str",
    "rubric_scores_json": "str",
}


def test_competitive_session_state_is_typeddict_with_expected_keys() -> None:
    """CompetitiveSessionState が total=False の TypedDict であること。"""
    assert is_typeddict(CompetitiveSessionState)
    hints = get_type_hints(CompetitiveSessionState)
    assert tuple(hints.keys()) == _COMPETITIVE_SESSION_STATE_KEYS


def test_competitive_session_state_field_types() -> None:
    """CompetitiveSessionState の各フィールドの型が正しいこと。"""
    hints = get_type_hints(CompetitiveSessionState)
    for key, expected_type_name in _EXPECTED_FIELD_TYPES.items():
        actual = hints[key]
        assert expected_type_name in str(actual), (
            f"{key}: expected type containing '{expected_type_name}', "
            f"got {actual}"
        )


def test_algo_theme_is_typeddict_with_expected_keys() -> None:
    """AlgoTheme が TypedDict であること。"""
    assert is_typeddict(AlgoTheme)
    hints = get_type_hints(AlgoTheme)
    assert tuple(hints.keys()) == _ALGO_THEME_KEYS
    for key in _ALGO_THEME_KEYS:
        assert hints[key] is str, f"AlgoTheme.{key} should be str"


def test_problem_example_is_typeddict_with_expected_keys() -> None:
    """ProblemExample が TypedDict であること。"""
    assert is_typeddict(ProblemExample)
    hints = get_type_hints(ProblemExample)
    assert tuple(hints.keys()) == _PROBLEM_EXAMPLE_KEYS
    for key in _PROBLEM_EXAMPLE_KEYS:
        assert hints[key] is str, f"ProblemExample.{key} should be str"


def test_rubric_item_is_typeddict_with_expected_keys_and_types() -> None:
    """RubricItem が TypedDict であり各フィールドの型が正しいこと。"""
    assert is_typeddict(RubricItem)
    hints = get_type_hints(RubricItem)
    assert tuple(hints.keys()) == _RUBRIC_ITEM_KEYS
    assert hints["criterion"] is str
    assert hints["points"] is int
    assert hints["description"] is str


def test_competitive_session_status_literal_values() -> None:
    """CompetitiveSessionStatus の Literal 値が正しいこと。"""
    assert get_args(CompetitiveSessionStatus) == ("in_progress", "completed")


def test_programming_language_literal_values() -> None:
    """ProgrammingLanguage は str エイリアスとして扱う。"""
    assert ProgrammingLanguage is str


def test_supported_languages_registry() -> None:
    """言語レジストリが公開順に返ること。"""
    languages = list_supported_languages()
    assert [item["id"] for item in languages] == ["python", "typescript"]


def test_exception_hierarchy() -> None:
    """例外が CompetitiveError を基底とし error_code を持つこと。"""
    assert ThemeSelectionError.__base__ is CompetitiveError
    assert ProblemGenerationError.__base__ is CompetitiveError
    assert SolutionEvaluationError.__base__ is CompetitiveError

    exc = CompetitiveError(error_code="test_code", message="test message")
    assert exc.error_code == "test_code"
    assert str(exc) == "test message"


def test_competitive_session_state_is_total_false() -> None:
    """CompetitiveSessionState が total=False であること。"""
    assert not CompetitiveSessionState.__total__


def test_algo_themes_json_schema_and_uniqueness() -> None:
    """algo_themes.json が 120件以上で重複がなく、スキーマが正しいこと。"""
    json_path = Path(__file__).resolve().parents[3] / "data" / "algo_themes.json"
    with json_path.open(encoding="utf-8") as f:
        themes: list[dict[str, str]] = json.load(f)

    assert len(themes) >= 120, f"Expected >= 120 themes, got {len(themes)}"

    ids = [t["id"] for t in themes]
    labels = [t["label"] for t in themes]
    assert len(ids) == len(set(ids)), "Duplicate IDs found"
    assert len(labels) == len(set(labels)), "Duplicate labels found"

    expected_keys = {"id", "category", "label", "display_order"}
    for i, theme in enumerate(themes):
        assert set(theme.keys()) == expected_keys, (
            f"Theme {i} has unexpected keys: {set(theme.keys())}"
        )
        for key in ("id", "category", "label"):
            assert isinstance(theme[key], str), (
                f"Theme {i}.{key} should be str, got {type(theme[key])}"
            )
        assert isinstance(theme["display_order"], int), (
            f"Theme {i}.display_order should be int, got {type(theme['display_order'])}"
        )
