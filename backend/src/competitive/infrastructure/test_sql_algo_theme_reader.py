"""SqlAlgoThemeReader のテスト。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from competitive.domain.competitive_types import ThemeSelectionError
from competitive.infrastructure.sql_algo_theme_reader import SqlAlgoThemeReader
from infrastructure.rdb.base import Base
from infrastructure.rdb.models import (
    AlgoThemeModel,
    CompetitiveAnswer,
    CompetitiveSession,
)


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def _seed_themes(engine):
    """3テーマを投入。"""
    with Session(engine) as s:
        s.add_all([
            AlgoThemeModel(id="algo-001", category="探索", label="全探索", display_order=0),
            AlgoThemeModel(id="algo-002", category="探索", label="二分探索", display_order=1),
            AlgoThemeModel(id="algo-003", category="ソート", label="バブルソート", display_order=2),
        ])
        s.commit()


def _add_session(engine, theme_id: str, *, status: str = "completed", score: int | None = None):
    """テスト用セッション + 回答を追加。"""
    sid = str(uuid.uuid4())
    now = datetime.now(tz=UTC)
    with Session(engine) as s:
        s.add(CompetitiveSession(
            id=uuid.UUID(sid),
            theme_id=theme_id,
            theme_label="dummy",
            theme_category="dummy",
            programming_language="python",
            problem_statement="p",
            input_format="i",
            output_format="o",
            constraints="c",
            examples_json="[]",
            reference_solution="s",
            grading_rubric_json="[]",
            status=status,
            created_at=now,
            completed_at=now if status == "completed" else None,
        ))
        if score is not None:
            s.add(CompetitiveAnswer(
                id=uuid.uuid4(),
                session_id=uuid.UUID(sid),
                answer_text="code",
                score=score,
                feedback="ok",
                time_complexity="O(n)",
                space_complexity="O(1)",
                improvement_suggestions="none",
                rubric_scores_json="[]",
                created_at=now,
            ))
        s.commit()


@pytest.mark.usefixtures("_seed_themes")
class TestListThemes:
    def test_returns_all_themes_in_order(self, engine) -> None:
        reader = SqlAlgoThemeReader(engine)
        themes = reader.list_themes()

        assert len(themes) == 3
        assert themes[0]["id"] == "algo-001"
        assert themes[0]["display_order"] == 0
        assert themes[1]["display_order"] == 1
        assert themes[2]["display_order"] == 2

    def test_unattempted_theme_has_zero_count(self, engine) -> None:
        reader = SqlAlgoThemeReader(engine)
        themes = reader.list_themes()

        assert themes[0]["attempt_count"] == 0
        assert themes[0]["best_score"] is None
        assert themes[0]["last_attempted_at"] is None

    def test_attempted_theme_has_history(self, engine) -> None:
        _add_session(engine, "algo-001", score=85)
        reader = SqlAlgoThemeReader(engine)
        themes = reader.list_themes()

        t = next(t for t in themes if t["id"] == "algo-001")
        assert t["attempt_count"] == 1
        assert t["best_score"] == 85
        assert isinstance(t["last_attempted_at"], str)

    def test_in_progress_session_counts_as_attempted(self, engine) -> None:
        _add_session(engine, "algo-002", status="in_progress")
        reader = SqlAlgoThemeReader(engine)
        themes = reader.list_themes()

        t = next(t for t in themes if t["id"] == "algo-002")
        assert t["attempt_count"] == 1
        assert t["best_score"] is None


@pytest.mark.usefixtures("_seed_themes")
class TestGetById:
    def test_returns_theme(self, engine) -> None:
        reader = SqlAlgoThemeReader(engine)
        theme = reader.get_by_id("algo-002")

        assert theme["id"] == "algo-002"
        assert theme["label"] == "二分探索"

    def test_raises_on_missing(self, engine) -> None:
        reader = SqlAlgoThemeReader(engine)

        with pytest.raises(ThemeSelectionError) as exc_info:
            reader.get_by_id("algo-999")
        assert exc_info.value.error_code == "theme_not_found"


@pytest.mark.usefixtures("_seed_themes")
class TestPickNext:
    def test_picks_first_unattempted(self, engine) -> None:
        reader = SqlAlgoThemeReader(engine)
        theme = reader.pick_next()

        assert theme["id"] == "algo-001"

    def test_skips_attempted_themes(self, engine) -> None:
        _add_session(engine, "algo-001", score=90)
        reader = SqlAlgoThemeReader(engine)
        theme = reader.pick_next()

        assert theme["id"] == "algo-002"

    def test_skips_in_progress_themes(self, engine) -> None:
        _add_session(engine, "algo-001", status="in_progress")
        reader = SqlAlgoThemeReader(engine)
        theme = reader.pick_next()

        assert theme["id"] == "algo-002"

    def test_all_attempted_picks_lowest_score(self, engine) -> None:
        _add_session(engine, "algo-001", score=90)
        _add_session(engine, "algo-002", score=50)
        _add_session(engine, "algo-003", score=70)
        reader = SqlAlgoThemeReader(engine)
        theme = reader.pick_next()

        assert theme["id"] == "algo-002"

    def test_all_in_progress_picks_by_display_order(self, engine) -> None:
        _add_session(engine, "algo-001", status="in_progress")
        _add_session(engine, "algo-002", status="in_progress")
        _add_session(engine, "algo-003", status="in_progress")
        reader = SqlAlgoThemeReader(engine)
        theme = reader.pick_next()

        # All in_progress with no score → nulls_first → pick by display_order
        assert theme["id"] == "algo-001"

    def test_no_themes_raises(self, engine) -> None:
        # Delete all themes
        with Session(engine) as s:
            s.query(AlgoThemeModel).delete()
            s.commit()

        reader = SqlAlgoThemeReader(engine)

        with pytest.raises(ThemeSelectionError) as exc_info:
            reader.pick_next()
        assert exc_info.value.error_code == "no_themes"
