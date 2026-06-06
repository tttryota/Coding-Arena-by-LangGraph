"""SqlCompetitiveStore のテスト。

in-memory SQLite で CRUD 動作を検証する。
"""

from __future__ import annotations

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.exc import IntegrityError


def _setup_db() -> Engine:
    import infrastructure.rdb.models  # noqa: F401
    from infrastructure.rdb.base import Base

    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def engine() -> Engine:
    return _setup_db()


_SAMPLE_EXAMPLES = [
    {"input": "5\n1 3 5 7 9\n5", "output": "2"},
    {"input": "3\n1 2 3\n4", "output": "-1"},
]

_SAMPLE_RUBRIC = [
    {"criterion": "正しさ", "points": 50, "description": "正しい結果を返す"},
    {"criterion": "効率性", "points": 30, "description": "O(log N)"},
    {"criterion": "可読性", "points": 20, "description": "変数名など"},
]


def _create_session(engine: Engine) -> object:
    from competitive.infrastructure.sql_competitive_store import (
        SqlCompetitiveStore,
    )

    store = SqlCompetitiveStore(engine)
    return store.create_session(
        theme_id="algo-001",
        theme_label="二分探索",
        theme_category="探索",
        programming_language="python",
        problem_statement="二分探索で値を見つけよ",
        input_format="入力形式",
        output_format="出力形式",
        constraints="1 <= N <= 100000",
        examples=_SAMPLE_EXAMPLES,
        reference_solution="def solve(): pass",
        grading_rubric=_SAMPLE_RUBRIC,
    )


class TestSqlCompetitiveStoreSession:
    def test_create_session_returns_record(self, engine: Engine) -> None:
        from competitive.infrastructure.sql_competitive_store import (
            SqlCompetitiveStore,
        )

        store = SqlCompetitiveStore(engine)
        record = store.create_session(
            theme_id="algo-001",
            theme_label="二分探索",
            theme_category="探索",
            programming_language="python",
            problem_statement="問題文",
            input_format="入力",
            output_format="出力",
            constraints="制約",
            examples=_SAMPLE_EXAMPLES,
            reference_solution="code",
            grading_rubric=_SAMPLE_RUBRIC,
        )

        assert record.theme_id == "algo-001"
        assert record.theme_label == "二分探索"
        assert record.programming_language == "python"
        assert record.status == "in_progress"
        assert record.id  # UUID string

    def test_find_session_returns_created(self, engine: Engine) -> None:
        from competitive.infrastructure.sql_competitive_store import (
            SqlCompetitiveStore,
        )

        store = SqlCompetitiveStore(engine)
        created = _create_session(engine)
        found = store.find_session(created.id)

        assert found.id == created.id
        assert found.theme_id == "algo-001"

    def test_find_session_raises_on_missing(self, engine: Engine) -> None:
        from competitive.infrastructure.sql_competitive_store import (
            SqlCompetitiveStore,
        )

        store = SqlCompetitiveStore(engine)

        with pytest.raises(ValueError, match="CompetitiveSession not found"):
            store.find_session("00000000-0000-0000-0000-000000000000")

    def test_get_session_details_returns_full_data(
        self, engine: Engine,
    ) -> None:
        from competitive.infrastructure.sql_competitive_store import (
            SqlCompetitiveStore,
        )

        store = SqlCompetitiveStore(engine)
        created = _create_session(engine)
        details = store.get_session_details(created.id)

        assert details["problem_statement"] == "二分探索で値を見つけよ"
        assert len(details["examples"]) == 2
        assert len(details["grading_rubric"]) == 3
        assert details["reference_solution"] == "def solve(): pass"

    def test_list_recent_sessions(self, engine: Engine) -> None:
        from competitive.infrastructure.sql_competitive_store import (
            SqlCompetitiveStore,
        )

        store = SqlCompetitiveStore(engine)
        _create_session(engine)
        _create_session(engine)

        sessions = store.list_recent_sessions(limit=10)
        assert len(sessions) == 2


class TestSqlCompetitiveStoreAnswer:
    def test_save_and_find_answer(self, engine: Engine) -> None:
        from competitive.infrastructure.sql_competitive_store import (
            SqlCompetitiveStore,
        )

        store = SqlCompetitiveStore(engine)
        session = _create_session(engine)

        answer = store.save_answer_and_complete(
            session_id=session.id,
            answer_text="def solve(): return 42",
            score=85,
            feedback="良い解答です",
            time_complexity="O(log N)",
            space_complexity="O(1)",
            improvement_suggestions="特になし",
            rubric_scores_json='[{"criterion":"正しさ","points_awarded":45,"points_max":50}]',
        )

        assert answer.score == 85
        assert answer.session_id == session.id

        found = store.find_answer_by_session(session.id)
        assert found is not None
        assert found.score == 85
        assert found.feedback == "良い解答です"

        completed = store.find_session(session.id)
        assert completed.status == "completed"

    def test_find_answer_returns_none_when_no_answer(
        self, engine: Engine,
    ) -> None:
        from competitive.infrastructure.sql_competitive_store import (
            SqlCompetitiveStore,
        )

        store = SqlCompetitiveStore(engine)
        session = _create_session(engine)

        found = store.find_answer_by_session(session.id)
        assert found is None

    def test_save_answer_and_complete_raises_on_missing_session(
        self, engine: Engine,
    ) -> None:
        from competitive.infrastructure.sql_competitive_store import (
            SqlCompetitiveStore,
        )

        store = SqlCompetitiveStore(engine)

        with pytest.raises(ValueError, match="CompetitiveSession not found"):
            store.save_answer_and_complete(
                session_id="00000000-0000-0000-0000-000000000000",
                answer_text="code",
                score=50,
                feedback="ok",
                time_complexity="O(1)",
                space_complexity="O(1)",
                improvement_suggestions="none",
                rubric_scores_json="[]",
            )

    def test_duplicate_answer_raises_integrity_error(
        self, engine: Engine,
    ) -> None:
        from competitive.infrastructure.sql_competitive_store import (
            SqlCompetitiveStore,
        )

        store = SqlCompetitiveStore(engine)
        session = _create_session(engine)

        store.save_answer_and_complete(
            session_id=session.id,
            answer_text="first",
            score=50,
            feedback="ok",
            time_complexity="O(1)",
            space_complexity="O(1)",
            improvement_suggestions="none",
            rubric_scores_json="[]",
        )

        with pytest.raises(IntegrityError):
            store.save_answer_and_complete(
                session_id=session.id,
                answer_text="second",
                score=60,
                feedback="ok again",
                time_complexity="O(1)",
                space_complexity="O(1)",
                improvement_suggestions="none",
                rubric_scores_json="[]",
            )
