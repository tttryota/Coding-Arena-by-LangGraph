"""SQL道場テーマバンクのテスト。"""

from __future__ import annotations

import pytest

from sql_dojo.application.sql_grading import grade_sql_answer
from sql_dojo.domain.sql_dojo_types import SqlDojoGenerationError
from sql_dojo.infrastructure.sql_theme_bank import _THEMES, SqlThemeBank


def test_catalog_exposes_broad_theme_coverage_and_variant_counts() -> None:
    catalog = SqlThemeBank().list_catalog()

    families = {theme["family"] for theme in catalog["themes"]}
    total_problem_count = sum(theme["variant_count"] for theme in catalog["themes"])

    assert "join-basics" in families
    assert "left-join-counts" in families
    assert "aggregation-reporting" in families
    assert "window-ranking" in families
    assert "window-trends" in families
    assert "plan-reading" in families
    assert "slow-query-diagnosis" in families
    assert "index-design" in families
    assert "conditional-aggregation" in families
    assert "business-analytics" in families
    assert "advanced-index-design" in families
    assert total_problem_count == 63


def test_catalog_exposes_unique_topic_entries() -> None:
    catalog = SqlThemeBank().list_catalog()
    topics = [
        topic
        for theme in catalog["themes"]
        for topic in theme["topics"]
    ]

    topic_ids = [topic["topic_id"] for topic in topics]
    assert len(topics) == 63
    assert len(set(topic_ids)) == len(topic_ids)
    assert "join-basics-shipped-orders" in topic_ids
    assert "index-design-api-requests-workspace-endpoint-requested-at" in topic_ids
    assert "case-when-paid-amount" in topic_ids
    assert "materialized-view-monthly-revenue" in topic_ids


def test_create_problem_can_pick_topic_deterministically() -> None:
    problem = SqlThemeBank().create_problem(
        difficulty="advanced",
        topic_id="plan-reading-orders-account-status-created-at",
    )

    assert problem["family"] == "plan-reading"
    assert problem["topic_id"] == "plan-reading-orders-account-status-created-at"
    assert problem["topic_title"] == "orders一覧の実行計画"
    assert problem["difficulty"] == "advanced"
    assert "orders 一覧クエリ" in problem["problem_statement"]


def test_create_problem_rejects_unknown_topic() -> None:
    with pytest.raises(SqlDojoGenerationError) as excinfo:
        SqlThemeBank().create_problem(
            difficulty="beginner",
            topic_id="missing-topic",
        )

    assert excinfo.value.error_code == "topic_not_found"


def test_create_problem_can_generate_lag_variant(monkeypatch) -> None:
    monkeypatch.setattr("sql_dojo.infrastructure.sql_theme_bank.random.choice", lambda items: items[0])

    problem = SqlThemeBank().create_problem(
        difficulty="intermediate",
        theme_family="window-trends",
    )

    assert problem["family"] == "window-trends"
    assert "LAG(" in problem["reference_sql"]
    assert problem["grading_contract"]["required_window_functions"] == ["LAG"]


def test_all_reference_sql_variants_satisfy_their_grading_contracts() -> None:
    for theme in _THEMES:
        for variant in theme.variants:
            result = grade_sql_answer(
                variant.reference_sql,
                variant.grading_contract,
            )

            assert result.score >= 90, (
                f"{theme.family} reference SQL should satisfy its contract: "
                f"{variant.reference_sql}"
            )
