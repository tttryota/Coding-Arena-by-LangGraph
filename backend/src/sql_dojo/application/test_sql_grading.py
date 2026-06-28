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


def test_grades_case_filter_and_having_rules() -> None:
    result = grade_sql_answer(
        (
            "SELECT account_id, "
            "SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) AS paid_amount, "
            "COUNT(*) FILTER (WHERE status = 'failed') AS failed_count "
            "FROM invoices "
            "GROUP BY account_id "
            "HAVING SUM(amount) >= 1000"
        ),
        {
            "statement_kind": "select",
            "required_tables": ["invoices"],
            "required_case": True,
            "required_filter_aggregates": [{"function": "COUNT", "column": "*"}],
            "required_having_columns": ["amount"],
            "required_aggregates": [{"function": "SUM", "column": "amount"}],
        },
    )

    assert result.score >= 90
    assert all(rule["passed"] for rule in _rules(result.rule_breakdown_json))


def test_grades_distinct_on_exists_and_not_exists_rules() -> None:
    distinct_result = grade_sql_answer(
        (
            "SELECT DISTINCT ON (user_id) user_id, logged_in_at "
            "FROM login_events "
            "ORDER BY user_id, logged_in_at DESC"
        ),
        {
            "statement_kind": "select",
            "required_tables": ["login_events"],
            "required_distinct_on": ["user_id"],
        },
    )
    exists_result = grade_sql_answer(
        (
            "SELECT u.id FROM users AS u "
            "WHERE EXISTS (SELECT 1 FROM subscriptions AS s WHERE s.user_id = u.id)"
        ),
        {
            "statement_kind": "select",
            "required_tables": ["users", "subscriptions"],
            "required_exists": True,
        },
    )
    not_exists_result = grade_sql_answer(
        (
            "SELECT u.id FROM users AS u "
            "WHERE NOT EXISTS (SELECT 1 FROM purchases AS p WHERE p.user_id = u.id)"
        ),
        {
            "statement_kind": "select",
            "required_tables": ["users", "purchases"],
            "required_not_exists": True,
        },
    )

    assert distinct_result.score >= 90
    assert exists_result.score >= 90
    assert not_exists_result.score >= 90


def test_distinct_on_latest_row_requires_timestamp_desc_order() -> None:
    result = grade_sql_answer(
        (
            "SELECT DISTINCT ON (user_id) user_id, logged_in_at "
            "FROM login_events "
            "ORDER BY user_id"
        ),
        {
            "statement_kind": "select",
            "required_tables": ["login_events"],
            "required_distinct_on": ["user_id"],
            "required_order_by": [
                {"column": "user_id", "direction": "ASC"},
                {"column": "logged_in_at", "direction": "DESC"},
            ],
        },
    )

    order_rule = next(
        rule for rule in _rules(result.rule_breakdown_json)
        if rule["name"] == "order_by"
    )
    assert result.score < 90
    assert order_rule["passed"] is False


def test_distinct_on_latest_row_rejects_wrong_order_sequence() -> None:
    result = grade_sql_answer(
        (
            "SELECT DISTINCT ON (user_id) user_id, logged_in_at "
            "FROM login_events "
            "ORDER BY logged_in_at DESC, user_id"
        ),
        {
            "statement_kind": "select",
            "required_tables": ["login_events"],
            "required_distinct_on": ["user_id"],
            "required_order_by": [
                {"column": "user_id", "direction": "ASC"},
                {"column": "logged_in_at", "direction": "DESC"},
            ],
        },
    )

    order_rule = next(
        rule for rule in _rules(result.rule_breakdown_json)
        if rule["name"] == "order_by"
    )
    assert result.score < 90
    assert order_rule["passed"] is False


def test_distinct_on_latest_row_rejects_extra_leading_order_key() -> None:
    result = grade_sql_answer(
        (
            "SELECT DISTINCT ON (user_id) user_id, logged_in_at "
            "FROM login_events "
            "ORDER BY id, user_id, logged_in_at DESC"
        ),
        {
            "statement_kind": "select",
            "required_tables": ["login_events"],
            "required_distinct_on": ["user_id"],
            "required_order_by": [
                {"column": "user_id", "direction": "ASC"},
                {"column": "logged_in_at", "direction": "DESC"},
            ],
        },
    )

    order_rule = next(
        rule for rule in _rules(result.rule_breakdown_json)
        if rule["name"] == "order_by"
    )
    assert result.score < 90
    assert order_rule["passed"] is False


def test_grades_postgresql_json_array_and_upsert_rules() -> None:
    json_result = grade_sql_answer(
        "SELECT payload ->> 'plan' AS plan FROM events WHERE payload ->> 'plan' = 'pro'",
        {
            "statement_kind": "select",
            "required_tables": ["events"],
            "required_json_operators": ["->>"],
        },
    )
    array_result = grade_sql_answer(
        "SELECT id FROM articles WHERE 'postgres' = ANY(tags)",
        {
            "statement_kind": "select",
            "required_tables": ["articles"],
            "required_array_functions": ["ANY"],
        },
    )
    upsert_result = grade_sql_answer(
        (
            "INSERT INTO user_preferences (user_id, key, value) "
            "VALUES (42, 'theme', 'dark') "
            "ON CONFLICT (user_id, key) DO UPDATE SET value = EXCLUDED.value"
        ),
        {
            "statement_kind": "insert",
            "required_tables": ["user_preferences"],
            "required_on_conflict": True,
        },
    )

    assert json_result.score >= 90
    assert array_result.score >= 90
    assert upsert_result.score >= 90


def test_grades_advanced_index_rules() -> None:
    result = grade_sql_answer(
        (
            "CREATE INDEX idx_orders_active_account_created_at "
            "ON orders USING btree (account_id, created_at DESC) "
            "INCLUDE (total_amount) "
            "WHERE status = 'active'"
        ),
        {
            "statement_kind": "create_index",
            "required_index": {
                "table": "orders",
                "columns": ["account_id", "created_at"],
                "orders": {"created_at": "DESC"},
            },
            "required_partial_index_predicate_columns": ["status"],
            "required_include_columns": ["total_amount"],
            "required_index_method": "btree",
        },
    )

    assert result.score >= 90
    assert all(rule["passed"] for rule in _rules(result.rule_breakdown_json))


def test_grades_expression_index_and_materialized_view_rules() -> None:
    index_result = grade_sql_answer(
        "CREATE INDEX idx_users_lower_email ON users (LOWER(email))",
        {
            "statement_kind": "create_index",
            "required_index": {"table": "users"},
            "required_expression_index_terms": ["LOWER(email)"],
            "required_functions": ["LOWER"],
        },
    )
    materialized_result = grade_sql_answer(
        (
            "CREATE MATERIALIZED VIEW monthly_revenue AS "
            "SELECT DATE_TRUNC('month', paid_at) AS revenue_month, SUM(amount) AS total_revenue "
            "FROM payments GROUP BY DATE_TRUNC('month', paid_at)"
        ),
        {
            "statement_kind": "create_materialized_view",
            "required_tables": ["payments"],
            "required_functions": ["DATE_TRUNC"],
            "required_aggregates": [{"function": "SUM", "column": "amount"}],
        },
    )

    assert index_result.score >= 90
    assert materialized_result.score >= 90


def test_structural_string_checks_ignore_sql_literals() -> None:
    result = grade_sql_answer(
        "SELECT 'COALESCE(display_name, email)' AS hint FROM profiles",
        {
            "statement_kind": "select",
            "required_tables": ["profiles"],
            "required_functions": ["COALESCE"],
        },
    )

    function_rule = next(
        rule for rule in _rules(result.rule_breakdown_json)
        if rule["name"] == "required_functions"
    )
    assert result.score < 90
    assert function_rule["passed"] is False


def test_required_sql_fragments_enforce_upsert_update_shape() -> None:
    result = grade_sql_answer(
        (
            "INSERT INTO user_preferences (user_id, key, value) "
            "VALUES (42, 'theme', 'dark') "
            "ON CONFLICT (user_id, key) DO NOTHING"
        ),
        {
            "statement_kind": "insert",
            "required_tables": ["user_preferences"],
            "required_on_conflict": True,
            "required_sql_fragments": [
                "DO UPDATE",
                "value = EXCLUDED.value",
            ],
        },
    )

    fragment_rule = next(
        rule for rule in _rules(result.rule_breakdown_json)
        if rule["name"] == "sql_fragments"
    )
    assert result.score < 90
    assert fragment_rule["passed"] is False


def test_required_sql_fragments_ignore_fragments_inside_literals() -> None:
    result = grade_sql_answer(
        (
            "INSERT INTO user_preferences (user_id, key, value) "
            "VALUES (42, 'theme', 'DO UPDATE value = EXCLUDED.value updated_at = EXCLUDED.updated_at') "
            "ON CONFLICT (user_id, key) DO NOTHING"
        ),
        {
            "statement_kind": "insert",
            "required_tables": ["user_preferences"],
            "required_on_conflict": True,
            "required_sql_fragments": [
                "DO UPDATE",
                "value = EXCLUDED.value",
                "updated_at = EXCLUDED.updated_at",
            ],
        },
    )

    fragment_rule = next(
        rule for rule in _rules(result.rule_breakdown_json)
        if rule["name"] == "sql_fragments"
    )
    assert result.score < 90
    assert fragment_rule["passed"] is False


def test_required_sql_fragments_accept_compact_operator_spacing() -> None:
    result = grade_sql_answer(
        (
            "INSERT INTO user_preferences (user_id, key, value, updated_at) "
            "VALUES (42, 'theme', 'dark', NOW()) "
            "ON CONFLICT (user_id, key) DO UPDATE "
            "SET value=EXCLUDED.value, updated_at=EXCLUDED.updated_at"
        ),
        {
            "statement_kind": "insert",
            "required_tables": ["user_preferences"],
            "required_on_conflict": True,
            "required_sql_fragments": [
                "DO UPDATE",
                "value = EXCLUDED.value",
                "updated_at = EXCLUDED.updated_at",
            ],
        },
    )

    assert result.score >= 90
    assert all(rule["passed"] for rule in _rules(result.rule_breakdown_json))


def test_required_sql_fragments_enforce_partial_index_predicate_value() -> None:
    result = grade_sql_answer(
        (
            "CREATE INDEX idx_orders_cancelled_account_created_at "
            "ON orders (account_id, created_at DESC) "
            "WHERE status = 'cancelled'"
        ),
        {
            "statement_kind": "create_index",
            "required_index": {
                "table": "orders",
                "columns": ["account_id", "created_at"],
                "orders": {"created_at": "DESC"},
            },
            "required_partial_index_predicate_columns": ["status"],
            "required_sql_fragments": ["WHERE status = 'active'"],
        },
    )

    fragment_rule = next(
        rule for rule in _rules(result.rule_breakdown_json)
        if rule["name"] == "sql_fragments"
    )
    assert result.score < 90
    assert fragment_rule["passed"] is False


def test_expression_index_terms_can_require_trigram_target_column() -> None:
    result = grade_sql_answer(
        "CREATE INDEX idx_products_status_trgm ON products USING gin (status gin_trgm_ops)",
        {
            "statement_kind": "create_index",
            "required_index": {"table": "products"},
            "required_index_method": "gin",
            "required_expression_index_terms": ["name gin_trgm_ops"],
        },
    )

    expression_rule = next(
        rule for rule in _rules(result.rule_breakdown_json)
        if rule["name"] == "expression_index_terms"
    )
    assert result.score < 90
    assert expression_rule["passed"] is False


def test_grades_pagination_and_new_prohibited_patterns() -> None:
    keyset_result = grade_sql_answer(
        (
            "SELECT id, created_at FROM events "
            "WHERE (created_at, id) < (TIMESTAMPTZ '2026-06-20 10:00:00+00:00', 5000) "
            "ORDER BY created_at DESC, id DESC LIMIT 50"
        ),
        {
            "statement_kind": "select",
            "required_tables": ["events"],
            "required_pagination_style": "keyset",
            "prohibited_patterns": ["offset_pagination"],
        },
    )
    offset_result = grade_sql_answer(
        "SELECT id FROM events ORDER BY created_at DESC LIMIT 50 OFFSET 5000",
        {
            "statement_kind": "select",
            "required_tables": ["events"],
            "prohibited_patterns": ["offset_pagination"],
        },
    )

    prohibited_rule = next(
        rule for rule in _rules(offset_result.rule_breakdown_json)
        if rule["name"] == "prohibited_patterns"
    )
    assert keyset_result.score >= 90
    assert offset_result.score < 90
    assert prohibited_rule["passed"] is False


def test_keyset_pagination_requires_tiebreaker_order_key() -> None:
    result = grade_sql_answer(
        (
            "SELECT id, created_at FROM events "
            "WHERE (created_at, id) < (TIMESTAMPTZ '2026-06-20 10:00:00+00:00', 5000) "
            "ORDER BY created_at DESC LIMIT 50"
        ),
        {
            "statement_kind": "select",
            "required_tables": ["events"],
            "required_pagination_style": "keyset",
            "required_order_by": [
                {"column": "created_at", "direction": "DESC"},
                {"column": "id", "direction": "DESC"},
            ],
            "required_limit": 50,
            "prohibited_patterns": ["offset_pagination"],
        },
    )

    order_rule = next(
        rule for rule in _rules(result.rule_breakdown_json)
        if rule["name"] == "order_by"
    )
    assert result.score < 90
    assert order_rule["passed"] is False


def test_grades_predicate_patterns_and_distinguishes_ilike() -> None:
    result = grade_sql_answer(
        "SELECT id, name FROM customers WHERE name ILIKE '%shop%'",
        {
            "statement_kind": "select",
            "required_tables": ["customers"],
            "required_predicate_columns": ["name"],
            "required_predicate_patterns": ["ILIKE"],
        },
    )

    assert result.score >= 90
    assert all(rule["passed"] for rule in _rules(result.rule_breakdown_json))


def test_grades_set_operation_and_subquery_patterns() -> None:
    union_result = grade_sql_answer(
        "SELECT user_id FROM email_targets UNION SELECT user_id FROM push_targets",
        {
            "statement_kind": "select",
            "required_tables": ["email_targets", "push_targets"],
            "required_set_operations": ["UNION"],
        },
    )
    subquery_result = grade_sql_answer(
        (
            "SELECT a.id, ("
            "SELECT MAX(o.created_at) FROM orders AS o WHERE o.account_id = a.id"
            ") AS latest_order_at "
            "FROM accounts AS a"
        ),
        {
            "statement_kind": "select",
            "required_tables": ["accounts", "orders"],
            "required_subquery_patterns": ["SCALAR_SUBQUERY"],
            "required_aggregates": [{"function": "MAX", "column": "created_at"}],
        },
    )

    assert union_result.score >= 90
    assert subquery_result.score >= 90


def test_grades_recursive_cte() -> None:
    result = grade_sql_answer(
        (
            "WITH RECURSIVE category_tree AS ("
            "SELECT id, parent_id, 0 AS depth FROM categories WHERE id = 10 "
            "UNION ALL "
            "SELECT c.id, c.parent_id, ct.depth + 1 AS depth "
            "FROM categories AS c "
            "INNER JOIN category_tree AS ct ON c.parent_id = ct.id"
            ") "
            "SELECT id, parent_id, depth FROM category_tree"
        ),
        {
            "statement_kind": "select",
            "required_tables": ["categories"],
            "required_cte_names": ["category_tree"],
            "required_recursive_cte": True,
            "required_set_operations": ["UNION ALL"],
        },
    )

    assert result.score >= 90
    assert all(rule["passed"] for rule in _rules(result.rule_breakdown_json))


def test_grades_update_delete_and_returning() -> None:
    update_result = grade_sql_answer(
        (
            "UPDATE orders AS o "
            "SET status = 'archived' "
            "FROM accounts AS a "
            "WHERE o.account_id = a.id AND a.billing_status = 'delinquent' "
            "RETURNING o.id"
        ),
        {
            "statement_kind": "update",
            "required_tables": ["orders", "accounts"],
            "required_predicate_columns": ["account_id", "id", "billing_status"],
            "required_returning": True,
            "required_sql_fragments": ["FROM accounts AS a"],
        },
    )
    delete_result = grade_sql_answer(
        (
            "DELETE FROM sessions AS s "
            "USING cancelled_accounts AS c "
            "WHERE s.account_id = c.account_id "
            "RETURNING s.id"
        ),
        {
            "statement_kind": "delete",
            "required_tables": ["sessions", "cancelled_accounts"],
            "required_predicate_columns": ["account_id"],
            "required_returning": True,
            "required_sql_fragments": ["USING cancelled_accounts AS c"],
        },
    )

    assert update_result.score >= 90
    assert delete_result.score >= 90


def test_grades_create_table_and_alter_table_constraints() -> None:
    create_result = grade_sql_answer(
        (
            "CREATE TABLE subscriptions ("
            "id bigint PRIMARY KEY, "
            "user_id bigint REFERENCES users(id), "
            "external_key text UNIQUE, "
            "seat_count int CHECK (seat_count >= 1)"
            ")"
        ),
        {
            "statement_kind": "create_table",
            "required_tables": ["subscriptions", "users"],
            "required_constraint_types": [
                "PRIMARY_KEY",
                "FOREIGN_KEY",
                "UNIQUE",
                "CHECK",
            ],
        },
    )
    alter_result = grade_sql_answer(
        (
            "ALTER TABLE subscriptions "
            "ADD CONSTRAINT subscriptions_user_id_fkey "
            "FOREIGN KEY (user_id) REFERENCES users(id)"
        ),
        {
            "statement_kind": "alter_table",
            "required_tables": ["subscriptions", "users"],
            "required_constraint_types": ["FOREIGN_KEY"],
            "required_sql_fragments": ["ADD CONSTRAINT subscriptions_user_id_fkey"],
        },
    )

    assert create_result.score >= 90
    assert alter_result.score >= 90


def test_grades_multiple_statement_transaction_when_allowed() -> None:
    result = grade_sql_answer(
        (
            "BEGIN; "
            "WITH locked_job AS ("
            "SELECT id FROM queue_jobs "
            "WHERE status = 'queued' "
            "ORDER BY created_at ASC "
            "LIMIT 1 "
            "FOR UPDATE SKIP LOCKED"
            ") "
            "UPDATE queue_jobs "
            "SET status = 'claimed' "
            "FROM locked_job "
            "WHERE queue_jobs.id = locked_job.id "
            "RETURNING queue_jobs.id; "
            "COMMIT;"
        ),
        {
            "allow_multiple_statements": True,
            "required_statement_sequence": [
                "transaction_begin",
                "update",
                "commit",
            ],
            "required_tables": ["queue_jobs"],
            "required_lock_clauses": ["FOR_UPDATE", "SKIP_LOCKED"],
            "required_cte_names": ["locked_job"],
            "required_returning": True,
            "required_sql_fragments": [
                "SET status = 'claimed'",
                "FROM locked_job",
                "WHERE queue_jobs.id = locked_job.id",
            ],
        },
    )

    assert result.score >= 90
    assert all(rule["passed"] for rule in _rules(result.rule_breakdown_json))


def test_multiple_statement_transaction_fails_sequence_rule_when_out_of_order() -> None:
    result = grade_sql_answer(
        (
            "BEGIN; "
            "COMMIT; "
            "UPDATE queue_jobs SET status = 'claimed' WHERE id = 42;"
        ),
        {
            "allow_multiple_statements": True,
            "required_statement_sequence": [
                "transaction_begin",
                "update",
                "commit",
            ],
        },
    )

    sequence_rule = next(
        rule for rule in _rules(result.rule_breakdown_json)
        if rule["name"] == "statement_sequence"
    )
    assert result.score < 90
    assert sequence_rule["passed"] is False


def test_transaction_update_requires_using_locked_row_in_update() -> None:
    result = grade_sql_answer(
        (
            "BEGIN; "
            "SELECT id FROM queue_jobs "
            "WHERE status = 'queued' "
            "ORDER BY created_at ASC "
            "LIMIT 1 "
            "FOR UPDATE SKIP LOCKED; "
            "UPDATE queue_jobs SET status = 'claimed' WHERE id = 42; "
            "COMMIT;"
        ),
        {
            "allow_multiple_statements": True,
            "required_statement_sequence": [
                "transaction_begin",
                "select",
                "update",
                "commit",
            ],
            "required_tables": ["queue_jobs"],
            "required_lock_clauses": ["FOR_UPDATE", "SKIP_LOCKED"],
            "required_sql_fragments": [
                "FROM locked_job",
                "WHERE queue_jobs.id = locked_job.id",
            ],
        },
    )

    fragment_rule = next(
        rule for rule in _rules(result.rule_breakdown_json)
        if rule["name"] == "sql_fragments"
    )
    assert result.score < 90
    assert fragment_rule["passed"] is False


def test_multiple_statement_sequence_recognizes_create_materialized_view() -> None:
    result = grade_sql_answer(
        (
            "CREATE MATERIALIZED VIEW monthly_revenue AS SELECT 1 AS revenue; "
            "CREATE TABLE audit_logs (id bigint PRIMARY KEY);"
        ),
        {
            "allow_multiple_statements": True,
            "required_statement_sequence": [
                "create_materialized_view",
                "create_table",
            ],
        },
    )

    assert result.score >= 90
