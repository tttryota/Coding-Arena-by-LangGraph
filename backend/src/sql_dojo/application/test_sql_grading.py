"""SQL道場の静的採点テスト。"""

from __future__ import annotations

import json

import pytest

from sql_dojo.application.sql_grading import grade_sql_answer
from sql_dojo.domain.sql_dojo_types import SqlDojoEvaluationError


def _rules(rule_breakdown_json: str) -> list[dict[str, object]]:
    return json.loads(rule_breakdown_json)


def test_grades_select_query_with_join_aggregate_and_limit() -> None:
    result = grade_sql_answer(
        (
            "SELECT c.id, c.name, COUNT(*) AS shipped_order_count "
            "FROM customers AS c "
            "INNER JOIN orders AS o ON o.customer_id = c.id "
            "WHERE o.status = 'shipped' "
            "GROUP BY c.id, c.name "
            "ORDER BY shipped_order_count DESC "
            "LIMIT 5"
        ),
        {
            "statement_kind": "select",
            "required_tables": ["customers", "orders"],
            "required_joins": [
                {"left": "customers", "right": "orders", "join_type": "INNER"},
            ],
            "required_predicate_columns": ["status"],
            "required_group_by_columns": ["id", "name"],
            "required_aggregates": [{"function": "COUNT", "column": "*"}],
            "required_order_by": [{"column": "shipped_order_count", "direction": "DESC"}],
            "required_limit": 5,
            "prohibited_patterns": ["implicit_join"],
        },
    )

    assert result.score >= 90
    assert result.parsed_statement_kind == "select"
    assert all(rule["passed"] for rule in _rules(result.rule_breakdown_json))


def test_rejects_multiple_statements() -> None:
    with pytest.raises(SqlDojoEvaluationError) as excinfo:
        grade_sql_answer(
            "SELECT 1; SELECT 2;",
            {"statement_kind": "select"},
        )

    assert excinfo.value.error_code == "multiple_statements_not_allowed"


def test_grades_explain_query() -> None:
    result = grade_sql_answer(
        (
            "EXPLAIN (ANALYZE, BUFFERS) "
            "SELECT * FROM events "
            "WHERE account_id = 42 AND created_at >= DATE '2026-06-01'"
        ),
        {
            "statement_kind": "explain",
            "required_tables": ["events"],
            "required_predicate_columns": ["account_id", "created_at"],
            "require_explain": True,
            "required_explain_options": ["ANALYZE", "BUFFERS"],
        },
    )

    assert result.score >= 90
    assert all(rule["passed"] for rule in _rules(result.rule_breakdown_json))


def test_grades_bare_explain_analyze_query() -> None:
    result = grade_sql_answer(
        (
            "EXPLAIN ANALYZE "
            "SELECT * FROM events "
            "WHERE account_id = 42 AND created_at >= DATE '2026-06-01'"
        ),
        {
            "statement_kind": "explain",
            "required_tables": ["events"],
            "required_predicate_columns": ["account_id", "created_at"],
            "require_explain": True,
            "required_explain_options": ["ANALYZE"],
        },
    )

    assert result.score >= 90
    assert all(rule["passed"] for rule in _rules(result.rule_breakdown_json))


def test_grades_bare_explain_analyze_buffers_query() -> None:
    result = grade_sql_answer(
        (
            "EXPLAIN ANALYZE BUFFERS "
            "SELECT * FROM events "
            "WHERE account_id = 42 AND created_at >= DATE '2026-06-01'"
        ),
        {
            "statement_kind": "explain",
            "required_tables": ["events"],
            "required_predicate_columns": ["account_id", "created_at"],
            "require_explain": True,
            "required_explain_options": ["ANALYZE", "BUFFERS"],
        },
    )

    assert result.score >= 90
    assert all(rule["passed"] for rule in _rules(result.rule_breakdown_json))


def test_grades_create_index_query() -> None:
    result = grade_sql_answer(
        (
            "CREATE INDEX idx_items_seller_status_updated_at "
            "ON items (seller_id, status, updated_at DESC)"
        ),
        {
            "statement_kind": "create_index",
            "required_index": {
                "table": "items",
                "columns": ["seller_id", "status", "updated_at"],
                "orders": {"updated_at": "DESC"},
            },
        },
    )

    assert result.score >= 90
    assert all(rule["passed"] for rule in _rules(result.rule_breakdown_json))
