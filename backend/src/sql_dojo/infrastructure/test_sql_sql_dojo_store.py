"""SqlSqlDojoStore のテスト。"""

from __future__ import annotations

import pytest
from sqlalchemy import Engine, create_engine


def _setup_db() -> Engine:
    import infrastructure.rdb.models  # noqa: F401
    from infrastructure.rdb.base import Base

    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def engine() -> Engine:
    return _setup_db()


def _create_session(
    engine: Engine,
    *,
    theme_family: str = "join-basics",
    difficulty: str = "beginner",
) -> object:
    from sql_dojo.infrastructure.sql_sql_dojo_store import SqlSqlDojoStore

    store = SqlSqlDojoStore(engine)
    return store.create_session(
        theme_family=theme_family,
        difficulty=difficulty,
        dialect="postgresql",
        theme_title="顧客別注文件数",
        business_domain="EC",
        target_skill="JOIN",
        problem_statement="問題文",
        schema_markdown="schema",
        sample_data_json="[]",
        expected_focus="JOIN, COUNT",
        reference_sql="SELECT 1",
        grading_contract_json='{"statement_kind":"select"}',
    )


class TestSqlSqlDojoStoreThemeHistory:
    def test_returns_empty_when_no_history(self, engine: Engine) -> None:
        from sql_dojo.infrastructure.sql_sql_dojo_store import SqlSqlDojoStore

        store = SqlSqlDojoStore(engine)

        assert store.list_theme_history() == []

    def test_aggregates_attempts_best_score_and_last_attempted_at(
        self,
        engine: Engine,
    ) -> None:
        from sql_dojo.infrastructure.sql_sql_dojo_store import SqlSqlDojoStore

        store = SqlSqlDojoStore(engine)
        first = _create_session(engine, theme_family="join-basics")
        second = _create_session(engine, theme_family="join-basics")
        _create_session(engine, theme_family="window-ranking", difficulty="intermediate")

        store.save_answer_and_complete(
            session_id=first.id,
            answer_text="SELECT 1",
            score=72,
            feedback="ok",
            rule_breakdown_json="[]",
            improvement_suggestions="none",
        )
        store.save_answer_and_complete(
            session_id=second.id,
            answer_text="SELECT 2",
            score=91,
            feedback="great",
            rule_breakdown_json="[]",
            improvement_suggestions="none",
        )

        history = {
            row.theme_family: row
            for row in store.list_theme_history()
        }

        assert history["join-basics"].attempt_count == 2
        assert history["join-basics"].best_score == 91
        assert history["join-basics"].last_attempted_at is not None
        assert history["window-ranking"].attempt_count == 1
        assert history["window-ranking"].best_score is None

