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


def test_grades_left_join_count_query() -> None:
    result = grade_sql_answer(
        (
            "SELECT p.plan_code, COUNT(s.id) AS subscriber_count "
            "FROM plans AS p "
            "LEFT JOIN subscriptions AS s ON s.plan_id = p.id "
            "GROUP BY p.plan_code "
            "ORDER BY p.plan_code ASC"
        ),
        {
            "statement_kind": "select",
            "required_tables": ["plans", "subscriptions"],
            "required_joins": [
                {"left": "plans", "right": "subscriptions", "join_type": "LEFT"},
            ],
            "required_group_by_columns": ["plan_code"],
            "required_aggregates": [{"function": "COUNT", "column": "id"}],
            "required_order_by": [{"column": "plan_code", "direction": "ASC"}],
            "prohibited_patterns": ["implicit_join"],
        },
    )

    assert result.score >= 90
    assert all(rule["passed"] for rule in _rules(result.rule_breakdown_json))


def test_grades_left_outer_join_count_query() -> None:
    result = grade_sql_answer(
        (
            "SELECT p.plan_code, COUNT(s.id) AS subscriber_count "
            "FROM plans AS p "
            "LEFT OUTER JOIN subscriptions AS s ON s.plan_id = p.id "
            "GROUP BY p.plan_code "
            "ORDER BY p.plan_code ASC"
        ),
        {
            "statement_kind": "select",
            "required_tables": ["plans", "subscriptions"],
            "required_joins": [
                {"left": "plans", "right": "subscriptions", "join_type": "LEFT"},
            ],
            "required_group_by_columns": ["plan_code"],
            "required_aggregates": [{"function": "COUNT", "column": "id"}],
            "required_order_by": [{"column": "plan_code", "direction": "ASC"}],
            "prohibited_patterns": ["implicit_join"],
        },
    )

    assert result.score >= 90
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


def test_grades_parenthesized_explain_analyze_buffers_query() -> None:
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


def test_grades_parenthesized_explain_options_with_true_values() -> None:
    result = grade_sql_answer(
        (
            "EXPLAIN (ANALYZE TRUE, BUFFERS ON) "
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


def test_grades_explain_with_comments_around_options() -> None:
    result = grade_sql_answer(
        (
            "EXPLAIN /* planner details */ "
            "(ANALYZE /* runtime */, BUFFERS) "
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


@pytest.mark.parametrize(
    "user_sql",
    [
        (
            "/* review */ EXPLAIN (ANALYZE, BUFFERS) "
            "SELECT * FROM events "
            "WHERE account_id = 42 AND created_at >= DATE '2026-06-01'"
        ),
        (
            "-- review\n"
            "EXPLAIN (ANALYZE, BUFFERS) "
            "SELECT * FROM events "
            "WHERE account_id = 42 AND created_at >= DATE '2026-06-01'"
        ),
    ],
)
def test_grades_explain_with_leading_comments(user_sql: str) -> None:
    result = grade_sql_answer(
        user_sql,
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


def test_grades_explain_with_nested_block_comment_before_options() -> None:
    result = grade_sql_answer(
        (
            "EXPLAIN /* outer /* inner */ outer */ "
            "(ANALYZE, BUFFERS) "
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


def test_grades_explain_with_nested_block_comment_in_inner_query() -> None:
    result = grade_sql_answer(
        (
            "EXPLAIN (ANALYZE, BUFFERS) "
            "SELECT * FROM events "
            "/* outer /* inner */ outer */ "
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


def test_grades_explain_with_line_comment_before_query() -> None:
    result = grade_sql_answer(
        (
            "EXPLAIN (ANALYZE, BUFFERS) -- inspect index usage\n"
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


def test_explain_comment_stripping_preserves_string_literals() -> None:
    result = grade_sql_answer(
        (
            "EXPLAIN (ANALYZE, BUFFERS) "
            "SELECT * FROM events "
            "WHERE account_id = 42 AND message = 'not /* a comment */ here'"
        ),
        {
            "statement_kind": "explain",
            "required_tables": ["events"],
            "required_predicate_columns": ["account_id", "message"],
            "require_explain": True,
            "required_explain_options": ["ANALYZE", "BUFFERS"],
        },
    )

    assert result.score >= 90
    assert all(rule["passed"] for rule in _rules(result.rule_breakdown_json))


def test_explain_comment_stripping_preserves_escape_string_literals() -> None:
    result = grade_sql_answer(
        (
            "EXPLAIN (ANALYZE, BUFFERS) "
            "SELECT * FROM events "
            "WHERE account_id = 42 AND message = E'not \\' -- a comment'"
        ),
        {
            "statement_kind": "explain",
            "required_tables": ["events"],
            "required_predicate_columns": ["account_id", "message"],
            "require_explain": True,
            "required_explain_options": ["ANALYZE", "BUFFERS"],
        },
    )

    assert result.score >= 90
    assert all(rule["passed"] for rule in _rules(result.rule_breakdown_json))


def test_explain_comment_stripping_preserves_dollar_quoted_strings() -> None:
    result = grade_sql_answer(
        (
            "EXPLAIN (ANALYZE, BUFFERS) "
            "SELECT * FROM events "
            "WHERE account_id = 42 AND message = $$not /* a comment */ here$$"
        ),
        {
            "statement_kind": "explain",
            "required_tables": ["events"],
            "required_predicate_columns": ["account_id", "message"],
            "require_explain": True,
            "required_explain_options": ["ANALYZE", "BUFFERS"],
        },
    )

    assert result.score >= 90
    assert all(rule["passed"] for rule in _rules(result.rule_breakdown_json))


def test_explain_comment_stripping_preserves_tagged_dollar_quoted_strings() -> None:
    result = grade_sql_answer(
        (
            "EXPLAIN (ANALYZE, BUFFERS) "
            "SELECT * FROM events "
            "WHERE account_id = 42 AND message = $tag$not -- a comment$tag$"
        ),
        {
            "statement_kind": "explain",
            "required_tables": ["events"],
            "required_predicate_columns": ["account_id", "message"],
            "require_explain": True,
            "required_explain_options": ["ANALYZE", "BUFFERS"],
        },
    )

    assert result.score >= 90
    assert all(rule["passed"] for rule in _rules(result.rule_breakdown_json))


def test_parenthesized_explain_option_false_value_is_not_enabled() -> None:
    result = grade_sql_answer(
        (
            "EXPLAIN (ANALYZE TRUE, BUFFERS OFF) "
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

    explain_options_rule = next(
        rule for rule in _rules(result.rule_breakdown_json)
        if rule["name"] == "explain_options"
    )
    assert result.score < 90
    assert explain_options_rule["passed"] is False


def test_parenthesized_explain_duplicate_options_use_last_value() -> None:
    result = grade_sql_answer(
        (
            "EXPLAIN (ANALYZE, ANALYZE FALSE, BUFFERS) "
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

    explain_options_rule = next(
        rule for rule in _rules(result.rule_breakdown_json)
        if rule["name"] == "explain_options"
    )
    assert result.score < 90
    assert explain_options_rule["passed"] is False


def test_parenthesized_explain_duplicate_disabled_option_can_be_re_enabled() -> None:
    result = grade_sql_answer(
        (
            "EXPLAIN (ANALYZE, BUFFERS FALSE, BUFFERS TRUE) "
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


def test_parenthesized_explain_duplicate_generic_plan_can_be_disabled() -> None:
    result = grade_sql_answer(
        (
            "EXPLAIN (GENERIC_PLAN TRUE, GENERIC_PLAN FALSE, ANALYZE) "
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


def test_parenthesized_explain_invalid_option_value_fails_syntax_rule() -> None:
    result = grade_sql_answer(
        (
            "EXPLAIN (ANALYZE TRUE, BUFFERS OFFF) "
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

    syntax_rule = next(
        rule for rule in _rules(result.rule_breakdown_json)
        if rule["name"] == "explain_syntax"
    )
    assert result.score < 90
    assert syntax_rule["passed"] is False


def test_parenthesized_explain_unknown_option_fails_syntax_rule() -> None:
    result = grade_sql_answer(
        (
            "EXPLAIN (ANALYZE TRUE, BUFFERS TRUE, FOO) "
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

    syntax_rule = next(
        rule for rule in _rules(result.rule_breakdown_json)
        if rule["name"] == "explain_syntax"
    )
    assert result.score < 90
    assert syntax_rule["passed"] is False


def test_parenthesized_explain_accepts_serialize_option_values() -> None:
    result = grade_sql_answer(
        (
            "EXPLAIN (ANALYZE, BUFFERS, SERIALIZE TEXT) "
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


def test_parenthesized_explain_accepts_serialize_without_value() -> None:
    result = grade_sql_answer(
        (
            "EXPLAIN (ANALYZE, BUFFERS, SERIALIZE) "
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


def test_parenthesized_explain_rejects_analyze_with_generic_plan() -> None:
    result = grade_sql_answer(
        (
            "EXPLAIN (ANALYZE, GENERIC_PLAN, BUFFERS) "
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

    syntax_rule = next(
        rule for rule in _rules(result.rule_breakdown_json)
        if rule["name"] == "explain_syntax"
    )
    assert result.score < 90
    assert syntax_rule["passed"] is False


@pytest.mark.parametrize(
    "user_sql",
    [
        (
            "EXPLAIN (BUFFERS, WAL) "
            "SELECT * FROM events "
            "WHERE account_id = 42 AND created_at >= DATE '2026-06-01'"
        ),
        (
            "EXPLAIN (BUFFERS, TIMING) "
            "SELECT * FROM events "
            "WHERE account_id = 42 AND created_at >= DATE '2026-06-01'"
        ),
        (
            "EXPLAIN (BUFFERS, SERIALIZE TEXT) "
            "SELECT * FROM events "
            "WHERE account_id = 42 AND created_at >= DATE '2026-06-01'"
        ),
    ],
)
def test_parenthesized_explain_rejects_analyze_only_options_without_analyze(
    user_sql: str,
) -> None:
    result = grade_sql_answer(
        user_sql,
        {
            "statement_kind": "explain",
            "required_tables": ["events"],
            "required_predicate_columns": ["account_id", "created_at"],
            "require_explain": True,
            "required_explain_options": ["BUFFERS"],
        },
    )

    syntax_rule = next(
        rule for rule in _rules(result.rule_breakdown_json)
        if rule["name"] == "explain_syntax"
    )
    assert result.score < 90
    assert syntax_rule["passed"] is False


def test_parenthesized_explain_rejects_format_without_value() -> None:
    result = grade_sql_answer(
        (
            "EXPLAIN (ANALYZE, FORMAT, BUFFERS) "
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

    syntax_rule = next(
        rule for rule in _rules(result.rule_breakdown_json)
        if rule["name"] == "explain_syntax"
    )
    assert result.score < 90
    assert syntax_rule["passed"] is False


def test_parenthesized_explain_rejects_empty_option_entry() -> None:
    result = grade_sql_answer(
        (
            "EXPLAIN (ANALYZE,,BUFFERS) "
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

    syntax_rule = next(
        rule for rule in _rules(result.rule_breakdown_json)
        if rule["name"] == "explain_syntax"
    )
    assert result.score < 90
    assert syntax_rule["passed"] is False


def test_rejects_bare_explain_buffers_option() -> None:
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

    rules = _rules(result.rule_breakdown_json)
    explain_options_rule = next(
        rule for rule in rules
        if rule["name"] == "explain_options"
    )
    assert result.score < 90
    assert explain_options_rule["passed"] is False


def test_bare_explain_buffers_fails_even_when_buffers_not_required() -> None:
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
            "required_explain_options": ["ANALYZE"],
        },
    )

    syntax_rule = next(
        rule for rule in _rules(result.rule_breakdown_json)
        if rule["name"] == "explain_syntax"
    )
    assert result.score < 90
    assert syntax_rule["passed"] is False


def test_bare_explain_options_must_follow_postgresql_order() -> None:
    result = grade_sql_answer(
        (
            "EXPLAIN VERBOSE ANALYZE "
            "SELECT * FROM events "
            "WHERE account_id = 42 AND created_at >= DATE '2026-06-01'"
        ),
        {
            "statement_kind": "explain",
            "required_tables": ["events"],
            "required_predicate_columns": ["account_id", "created_at"],
            "require_explain": True,
            "required_explain_options": ["ANALYZE", "VERBOSE"],
        },
    )

    syntax_rule = next(
        rule for rule in _rules(result.rule_breakdown_json)
        if rule["name"] == "explain_syntax"
    )
    assert result.score < 90
    assert syntax_rule["passed"] is False


def test_explain_requires_order_and_limit_when_contract_demands_them() -> None:
    result = grade_sql_answer(
        (
            "EXPLAIN (ANALYZE, BUFFERS) "
            "SELECT id, total_amount FROM orders "
            "WHERE account_id = 9001 AND status = 'pending'"
        ),
        {
            "statement_kind": "explain",
            "required_tables": ["orders"],
            "required_predicate_columns": ["account_id", "status"],
            "require_explain": True,
            "required_explain_options": ["ANALYZE", "BUFFERS"],
            "required_order_by": [{"column": "created_at", "direction": "DESC"}],
            "required_limit": 100,
        },
    )

    assert result.score < 100
    assert any(
        rule["name"] == "order_by" and not rule["passed"]
        for rule in _rules(result.rule_breakdown_json)
    )
    assert any(
        rule["name"] == "limit" and not rule["passed"]
        for rule in _rules(result.rule_breakdown_json)
    )


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


def test_grades_lag_query_with_cte() -> None:
    result = grade_sql_answer(
        (
            "WITH monthly_totals AS ("
            "SELECT plan_code, bill_month, total_revenue, "
            "LAG(total_revenue) OVER (PARTITION BY plan_code ORDER BY bill_month) AS previous_revenue "
            "FROM plan_revenue "
            "WHERE bill_month >= DATE '2026-04-01'"
            ") "
            "SELECT plan_code, bill_month, total_revenue, previous_revenue "
            "FROM monthly_totals"
        ),
        {
            "statement_kind": "select",
            "required_tables": ["plan_revenue"],
            "required_predicate_columns": ["bill_month"],
            "required_window_functions": ["LAG"],
            "required_cte_names": ["monthly_totals"],
        },
    )

    assert result.score >= 90
    assert all(rule["passed"] for rule in _rules(result.rule_breakdown_json))
