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
    assert "basic-filtering" in families
    assert "distinct-and-derived-columns" in families
    assert "join-variants" in families
    assert "set-operations" in families
    assert "subquery-patterns" in families
    assert "write-operations" in families
    assert "business-analytics" in families
    assert "advanced-index-design" in families
    assert "recursive-cte" in families
    assert "schema-constraints" in families
    assert "transactions-locking" in families
    assert total_problem_count == 90


def test_catalog_exposes_unique_topic_entries() -> None:
    catalog = SqlThemeBank().list_catalog()
    topics = [
        topic
        for theme in catalog["themes"]
        for topic in theme["topics"]
    ]

    topic_ids = [topic["topic_id"] for topic in topics]
    assert len(topics) == 90
    assert len(set(topic_ids)) == len(topic_ids)
    assert "join-basics-shipped-orders" in topic_ids
    assert "like-customer-search" in topic_ids
    assert "update-from-mark-overdue" in topic_ids
    assert "index-design-api-requests-workspace-endpoint-requested-at" in topic_ids
    assert "case-when-paid-amount" in topic_ids
    assert "materialized-view-monthly-revenue" in topic_ids
    assert "archive-and-log-transaction" in topic_ids


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


def test_claim_next_job_contract_requires_queue_filter_and_oldest_order() -> None:
    problem = SqlThemeBank().create_problem(
        difficulty="advanced",
        topic_id="claim-next-job-skip-locked",
    )

    result = grade_sql_answer(
        (
            "BEGIN; "
            "WITH claimed_job AS ("
            "SELECT id "
            "FROM queue_jobs "
            "LIMIT 1 "
            "FOR UPDATE SKIP LOCKED"
            ") "
            "UPDATE queue_jobs "
            "SET status = 'claimed' "
            "FROM claimed_job "
            "WHERE queue_jobs.id = claimed_job.id "
            "RETURNING queue_jobs.id; "
            "COMMIT;"
        ),
        problem["grading_contract"],
    )

    assert result.score < 90


def test_reserve_inventory_contract_rejects_global_update_even_with_matching_values() -> None:
    problem = SqlThemeBank().create_problem(
        difficulty="advanced",
        topic_id="reserve-inventory-transaction",
    )

    result = grade_sql_answer(
        (
            "BEGIN; "
            "UPDATE inventory "
            "SET available_quantity = available_quantity - 1 "
            "WHERE product_id = 42 OR 1 = 1; "
            "INSERT INTO inventory_reservations (product_id, reserved_quantity) "
            "VALUES (42, 1); "
            "COMMIT;"
        ),
        problem["grading_contract"],
    )

    assert result.score < 90


def test_reserve_inventory_contract_requires_top_level_update_predicate() -> None:
    problem = SqlThemeBank().create_problem(
        difficulty="advanced",
        topic_id="reserve-inventory-transaction",
    )

    result = grade_sql_answer(
        (
            "BEGIN; "
            "UPDATE inventory "
            "SET available_quantity = available_quantity - 1 "
            "FROM (SELECT product_id FROM inventory WHERE product_id = 42) matched; "
            "INSERT INTO inventory_reservations (product_id, reserved_quantity) "
            "VALUES (42, 1); "
            "COMMIT;"
        ),
        problem["grading_contract"],
    )

    assert result.score < 90


def test_archive_and_log_contract_requires_same_cutoff_on_delete() -> None:
    problem = SqlThemeBank().create_problem(
        difficulty="advanced",
        topic_id="archive-and-log-transaction",
    )

    result = grade_sql_answer(
        (
            "BEGIN; "
            "INSERT INTO archived_orders (id, completed_at, total_amount) "
            "SELECT id, completed_at, total_amount "
            "FROM completed_orders "
            "WHERE completed_at < DATE '2026-01-01'; "
            "DELETE FROM completed_orders "
            "WHERE completed_at < DATE '2026-01-01' OR TRUE; "
            "COMMIT;"
        ),
        problem["grading_contract"],
    )

    assert result.score < 90


def test_archive_and_log_contract_requires_top_level_delete_predicate() -> None:
    problem = SqlThemeBank().create_problem(
        difficulty="advanced",
        topic_id="archive-and-log-transaction",
    )

    result = grade_sql_answer(
        (
            "BEGIN; "
            "INSERT INTO archived_orders (id, completed_at, total_amount) "
            "SELECT id, completed_at, total_amount "
            "FROM completed_orders "
            "WHERE completed_at < DATE '2026-01-01'; "
            "DELETE FROM completed_orders "
            "USING ("
            "SELECT id FROM completed_orders "
            "WHERE completed_at < DATE '2026-01-01'"
            ") old_rows; "
            "COMMIT;"
        ),
        problem["grading_contract"],
    )

    assert result.score < 90


def test_claim_next_job_contract_rejects_self_join_shortcut() -> None:
    problem = SqlThemeBank().create_problem(
        difficulty="advanced",
        topic_id="claim-next-job-skip-locked",
    )

    result = grade_sql_answer(
        (
            "BEGIN; "
            "WITH locked_job AS ("
            "SELECT id "
            "FROM queue_jobs "
            "WHERE status = 'queued' "
            "ORDER BY created_at ASC "
            "LIMIT 1 "
            "FOR UPDATE SKIP LOCKED"
            ") "
            "UPDATE queue_jobs "
            "SET status = 'claimed' "
            "FROM queue_jobs "
            "WHERE queue_jobs.id = queue_jobs.id "
            "RETURNING queue_jobs.id; "
            "COMMIT;"
        ),
        problem["grading_contract"],
    )

    assert result.score < 90


def test_transaction_contracts_accept_reasonable_alias_usage() -> None:
    claim_problem = SqlThemeBank().create_problem(
        difficulty="advanced",
        topic_id="claim-next-job-skip-locked",
    )
    reserve_problem = SqlThemeBank().create_problem(
        difficulty="advanced",
        topic_id="reserve-inventory-transaction",
    )
    archive_problem = SqlThemeBank().create_problem(
        difficulty="advanced",
        topic_id="archive-and-log-transaction",
    )

    claim_result = grade_sql_answer(
        (
            "BEGIN; "
            "WITH claimed_job AS ("
            "SELECT id "
            "FROM queue_jobs "
            "WHERE status = 'queued' "
            "ORDER BY created_at ASC "
            "LIMIT 1 "
            "FOR UPDATE SKIP LOCKED"
            ") "
            "UPDATE queue_jobs AS q "
            "SET status = 'claimed' "
            "FROM claimed_job "
            "WHERE q.id = claimed_job.id "
            "RETURNING q.id; "
            "COMMIT;"
        ),
        claim_problem["grading_contract"],
    )
    reserve_result = grade_sql_answer(
        (
            "BEGIN; "
            "UPDATE inventory AS i "
            "SET available_quantity = available_quantity - 1 "
            "WHERE i.product_id = 42; "
            "INSERT INTO inventory_reservations (product_id, reserved_quantity) "
            "VALUES (42, 1); "
            "COMMIT;"
        ),
        reserve_problem["grading_contract"],
    )
    archive_result = grade_sql_answer(
        (
            "BEGIN; "
            "INSERT INTO archived_orders (id, completed_at, total_amount) "
            "SELECT c.id, c.completed_at, c.total_amount "
            "FROM completed_orders AS c "
            "WHERE c.completed_at < DATE '2026-01-01'; "
            "DELETE FROM completed_orders AS c "
            "WHERE c.completed_at < DATE '2026-01-01'; "
            "COMMIT;"
        ),
        archive_problem["grading_contract"],
    )

    assert claim_result.score >= 90
    assert reserve_result.score >= 90
    assert archive_result.score >= 90
