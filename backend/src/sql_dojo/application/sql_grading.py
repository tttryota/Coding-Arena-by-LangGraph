"""SQL道場の静的採点。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

import sqlglot
from sqlglot import exp

from sql_dojo.domain.sql_dojo_types import (
    SqlDojoEvaluationError,
    SqlDojoGradingContract,
    SqlDojoGradingRule,
    SqlDojoIndexRequirement,
)

if TYPE_CHECKING:
    from collections.abc import Iterable


@dataclass(frozen=True)
class SqlGradingResult:
    score: int
    rule_breakdown_json: str
    parsed_statement_kind: str


def _normalize_identifier(value: str) -> str:
    return value.strip().strip('"').lower()


def _column_names(columns: Iterable[exp.Expression]) -> set[str]:
    result: set[str] = set()
    for column in columns:
        if isinstance(column, exp.Column):
            table = column.table
            name = column.name
            if table:
                result.add(f"{_normalize_identifier(table)}.{_normalize_identifier(name)}")
            result.add(_normalize_identifier(name))
    return result


def _table_names(parsed: exp.Expression) -> set[str]:
    return {
        _normalize_identifier(table.name)
        for table in parsed.find_all(exp.Table)
        if table.name
    }


def _join_signatures(parsed: exp.Expression) -> set[tuple[str, str, str]]:
    signatures: set[tuple[str, str, str]] = set()
    base = parsed.args.get("from_")
    left_tables = [
        _normalize_identifier(table.name)
        for table in base.find_all(exp.Table)
    ] if isinstance(base, exp.From) else []
    left_default = left_tables[0] if left_tables else ""
    for join in parsed.find_all(exp.Join):
        right_table_exp = join.this
        if not isinstance(right_table_exp, exp.Table):
            continue
        right = _normalize_identifier(right_table_exp.name)
        left = left_default
        join_type = _normalize_identifier(join.args.get("kind", "INNER") or "INNER").upper()
        signatures.add((left, right, join_type))
    return signatures


def _aggregate_signatures(parsed: exp.Expression) -> set[tuple[str, str]]:
    result: set[tuple[str, str]] = set()
    for agg in parsed.find_all(exp.AggFunc):
        func_name = agg.sql_name().upper()
        column_names = {"*"}
        first_arg = agg.this if hasattr(agg, "this") else None
        if isinstance(first_arg, exp.Column):
            if first_arg.table:
                column_names.add(
                    f"{_normalize_identifier(first_arg.table)}."
                    f"{_normalize_identifier(first_arg.name)}",
                )
            column_names.add(_normalize_identifier(first_arg.name))
        for column_name in column_names:
            result.add((func_name, column_name))
    return result


def _window_functions(parsed: exp.Expression) -> set[str]:
    return {
        window.this.sql_name().upper()
        for window in parsed.find_all(exp.Window)
        if isinstance(window.this, exp.Func)
    }


def _cte_names(parsed: exp.Expression) -> set[str]:
    result: set[str] = set()
    with_clause = parsed.args.get("with")
    if not isinstance(with_clause, exp.With):
        return result
    for cte in with_clause.expressions:
        alias = cte.alias_or_name
        if alias:
            result.add(_normalize_identifier(alias))
    return result


def _statement_kind(parsed: exp.Expression, raw_sql: str) -> str:
    if raw_sql.strip().upper().startswith("EXPLAIN"):
        return "explain"
    if isinstance(parsed, exp.Create) and parsed.args.get("kind") == "INDEX":
        return "create_index"
    if isinstance(parsed, exp.Select) or parsed.find(exp.Select) is not None:
        return "select"
    return parsed.key


def _require_expression(
    parsed: exp.Expr | None,
    *,
    message: str,
) -> exp.Expression:
    if not isinstance(parsed, exp.Expression):
        raise SqlDojoEvaluationError(
            error_code="sql_parse_failed",
            message=message,
        )
    return parsed


def _index_details(parsed: exp.Expression) -> SqlDojoIndexRequirement:
    if not isinstance(parsed, exp.Create):
        return {}
    index_exp = parsed.this
    if not isinstance(index_exp, exp.Index):
        return {}
    table_exp = index_exp.args.get("table")
    params = index_exp.args.get("params")
    if not isinstance(table_exp, exp.Table):
        return {}
    columns: list[str] = []
    orders: dict[str, str] = {}
    if isinstance(params, exp.IndexParameters):
        for ordered in list(params.args.get("columns") or []):
            if isinstance(ordered, exp.Ordered) and isinstance(ordered.this, exp.Column):
                column_name = _normalize_identifier(ordered.this.name)
                columns.append(column_name)
                desc = ordered.args.get("desc")
                if desc:
                    orders[column_name] = "DESC"
            elif isinstance(ordered, exp.Column):
                columns.append(_normalize_identifier(ordered.name))
    return {
        "table": _normalize_identifier(table_exp.name),
        "columns": columns,
        "orders": orders,
    }


def _extract_explain_parts(raw_sql: str) -> tuple[str, set[str]]:
    pattern = re.compile(r"^\s*EXPLAIN\s*(?:\((?P<options>[^)]*)\))?\s*(?P<query>.+)$", re.IGNORECASE | re.DOTALL)
    matched = pattern.match(raw_sql)
    if matched is None:
        return raw_sql, set()
    options = {
        _normalize_identifier(part).upper()
        for part in (matched.group("options") or "").split(",")
        if part.strip()
    }
    return matched.group("query").strip(), options


def _add_rule(  # noqa: PLR0913
    rules: list[SqlDojoGradingRule],
    *,
    name: str,
    weight: int,
    passed: bool,
    message: str,
) -> None:
    rules.append(
        {
            "name": name,
            "weight": weight,
            "passed": passed,
            "message": message,
        },
    )


def grade_sql_answer(  # noqa: C901, PLR0915
    user_sql: str,
    grading_contract: SqlDojoGradingContract,
) -> SqlGradingResult:
    """PostgreSQL 方言の 1 文を静的採点する。"""
    try:
        parsed_statements = sqlglot.parse(user_sql, read="postgres")
    except sqlglot.errors.ParseError as exc:
        raise SqlDojoEvaluationError(
            error_code="sql_parse_failed",
            message=f"SQL parse failed: {exc}",
        ) from exc
    if len(parsed_statements) != 1:
        raise SqlDojoEvaluationError(
            error_code="multiple_statements_not_allowed",
            message="Only a single SQL statement is allowed per session",
        )
    parsed = _require_expression(
        parsed_statements[0],
        message="SQL parse produced an empty statement",
    )
    actual_kind = _statement_kind(parsed, user_sql)
    target_parsed = parsed
    explain_options: set[str] = set()
    if actual_kind == "explain":
        inner_sql, explain_options = _extract_explain_parts(user_sql)
        try:
            target_parsed = _require_expression(
                sqlglot.parse_one(inner_sql, read="postgres"),
                message="EXPLAIN inner SQL parse produced an empty statement",
            )
        except sqlglot.errors.ParseError as exc:
            raise SqlDojoEvaluationError(
                error_code="sql_parse_failed",
                message=f"EXPLAIN inner SQL parse failed: {exc}",
            ) from exc
    rules: list[SqlDojoGradingRule] = []

    expected_kind = grading_contract.get("statement_kind")
    if isinstance(expected_kind, str):
        _add_rule(
            rules,
            name="statement_kind",
            weight=15,
            passed=actual_kind == expected_kind,
            message=f"Expected {expected_kind}, got {actual_kind}",
        )

    required_tables = grading_contract.get("required_tables", [])
    if required_tables:
        actual_tables = _table_names(target_parsed)
        expected = {_normalize_identifier(table) for table in required_tables}
        _add_rule(
            rules,
            name="required_tables",
            weight=15,
            passed=expected.issubset(actual_tables),
            message=f"Expected tables {sorted(expected)}, got {sorted(actual_tables)}",
        )

    required_joins = grading_contract.get("required_joins", [])
    if required_joins:
        actual_joins = _join_signatures(target_parsed)
        expected_joins = {
            (
                _normalize_identifier(str(item["left"])),
                _normalize_identifier(str(item["right"])),
                _normalize_identifier(str(item["join_type"])).upper(),
            )
            for item in required_joins
        }
        _add_rule(
            rules,
            name="required_joins",
            weight=15,
            passed=expected_joins.issubset(actual_joins),
            message=f"Expected joins {sorted(expected_joins)}, got {sorted(actual_joins)}",
        )

    predicate_columns = grading_contract.get("required_predicate_columns", [])
    if predicate_columns:
        where_exp = target_parsed.find(exp.Where)
        actual_predicates = _column_names(where_exp.find_all(exp.Column)) if where_exp else set()
        expected = {_normalize_identifier(column) for column in predicate_columns}
        _add_rule(
            rules,
            name="predicate_columns",
            weight=10,
            passed=expected.issubset(actual_predicates),
            message=f"Expected predicates {sorted(expected)}, got {sorted(actual_predicates)}",
        )

    group_by_columns = grading_contract.get("required_group_by_columns", [])
    if group_by_columns:
        group_exp = target_parsed.find(exp.Group)
        actual_group = _column_names(group_exp.find_all(exp.Column)) if group_exp else set()
        expected = {_normalize_identifier(column) for column in group_by_columns}
        _add_rule(
            rules,
            name="group_by_columns",
            weight=10,
            passed=expected.issubset(actual_group),
            message=f"Expected group by {sorted(expected)}, got {sorted(actual_group)}",
        )

    required_aggregates = grading_contract.get("required_aggregates", [])
    if required_aggregates:
        actual_aggs = _aggregate_signatures(target_parsed)
        expected_aggs = {
            (
                _normalize_identifier(str(item["function"])).upper(),
                _normalize_identifier(str(item["column"])),
            )
            for item in required_aggregates
        }
        _add_rule(
            rules,
            name="aggregates",
            weight=10,
            passed=expected_aggs.issubset(actual_aggs),
            message=f"Expected aggregates {sorted(expected_aggs)}, got {sorted(actual_aggs)}",
        )

    required_order_by = grading_contract.get("required_order_by", [])
    if required_order_by:
        order_exp = target_parsed.find(exp.Order)
        actual_orders: set[tuple[str, str]] = set()
        if order_exp is not None:
            for ordered in order_exp.expressions:
                if isinstance(ordered, exp.Ordered) and isinstance(ordered.this, exp.Column):
                    name = _normalize_identifier(ordered.this.name)
                    direction = "DESC" if ordered.args.get("desc") else "ASC"
                    actual_orders.add((name, direction))
                elif isinstance(ordered, exp.Column):
                    actual_orders.add((_normalize_identifier(ordered.name), "ASC"))
        expected_orders = {
            (
                _normalize_identifier(str(item["column"])),
                _normalize_identifier(str(item.get("direction", "ASC"))).upper(),
            )
            for item in required_order_by
        }
        _add_rule(
            rules,
            name="order_by",
            weight=10,
            passed=expected_orders.issubset(actual_orders),
            message=f"Expected order by {sorted(expected_orders)}, got {sorted(actual_orders)}",
        )

    required_limit = grading_contract.get("required_limit")
    if isinstance(required_limit, int):
        limit_exp = target_parsed.find(exp.Limit)
        actual_limit = None
        if isinstance(limit_exp, exp.Limit):
            expression = limit_exp.expression
            if isinstance(expression, exp.Literal) and expression.is_int:
                actual_limit = int(expression.this)
        _add_rule(
            rules,
            name="limit",
            weight=5,
            passed=actual_limit == required_limit,
            message=f"Expected LIMIT {required_limit}, got {actual_limit}",
        )

    window_functions = grading_contract.get("required_window_functions", [])
    if window_functions:
        actual_windows = _window_functions(target_parsed)
        expected = {_normalize_identifier(name).upper() for name in window_functions}
        _add_rule(
            rules,
            name="window_functions",
            weight=10,
            passed=expected.issubset(actual_windows),
            message=f"Expected windows {sorted(expected)}, got {sorted(actual_windows)}",
        )

    cte_names = grading_contract.get("required_cte_names", [])
    if cte_names:
        actual_ctes = _cte_names(target_parsed)
        expected = {_normalize_identifier(name) for name in cte_names}
        _add_rule(
            rules,
            name="cte_names",
            weight=10,
            passed=expected.issubset(actual_ctes),
            message=f"Expected CTEs {sorted(expected)}, got {sorted(actual_ctes)}",
        )

    if grading_contract.get("require_explain") is True:
        _add_rule(
            rules,
            name="require_explain",
            weight=10,
            passed=actual_kind == "explain",
            message=f"Expected EXPLAIN, got {actual_kind}",
        )
        required_options = grading_contract.get("required_explain_options", [])
        if required_options:
            expected_options = {
                _normalize_identifier(option).upper() for option in required_options
            }
            _add_rule(
                rules,
                name="explain_options",
                weight=10,
                passed=expected_options.issubset(explain_options),
                message=(
                    f"Expected EXPLAIN options {sorted(expected_options)}, "
                    f"got {sorted(explain_options)}"
                ),
            )

    required_index = grading_contract.get("required_index")
    if required_index is not None:
        actual_index = _index_details(parsed)
        expected_table = _normalize_identifier(str(required_index.get("table", "")))
        expected_columns = [
            _normalize_identifier(str(column))
            for column in required_index.get("columns", [])
        ]
        actual_columns = actual_index.get("columns", [])
        _add_rule(
            rules,
            name="index_table",
            weight=15,
            passed=actual_index.get("table") == expected_table,
            message=(
                f"Expected index table {expected_table}, "
                f"got {actual_index.get('table')}"
            ),
        )
        _add_rule(
            rules,
            name="index_columns",
            weight=20,
            passed=actual_columns == expected_columns,
            message=(
                f"Expected index columns {expected_columns}, "
                f"got {actual_columns}"
            ),
        )
        expected_index_orders = {
            _normalize_identifier(str(key)): _normalize_identifier(str(value)).upper()
            for key, value in required_index.get("orders", {}).items()
        }
        actual_index_orders = {
            _normalize_identifier(str(key)): _normalize_identifier(str(value)).upper()
            for key, value in actual_index.get("orders", {}).items()
        }
        _add_rule(
            rules,
            name="index_orders",
            weight=10,
            passed=all(
                actual_index_orders.get(key) == value
                for key, value in expected_index_orders.items()
            ),
            message=(
                f"Expected index orders {expected_index_orders}, "
                f"got {actual_index_orders}"
            ),
        )

    prohibited = grading_contract.get("prohibited_patterns", [])
    if prohibited:
        sql_lower = user_sql.lower()
        implicit_join = "," in sql_lower and " join " not in sql_lower
        prohibited_hits: list[str] = []
        for item in prohibited:
            if (
                (item == "implicit_join" and implicit_join) or
                (item != "implicit_join" and item.lower() in sql_lower)
            ):
                prohibited_hits.append(item)
        _add_rule(
            rules,
            name="prohibited_patterns",
            weight=10,
            passed=not prohibited_hits,
            message=f"Prohibited patterns found: {prohibited_hits}",
        )

    total_weight = sum(int(rule["weight"]) for rule in rules) or 100
    score = round(
        sum(int(rule["weight"]) for rule in rules if rule["passed"]) / total_weight * 100,
    )
    return SqlGradingResult(
        score=score,
        rule_breakdown_json=json.dumps(rules, ensure_ascii=False),
        parsed_statement_kind=actual_kind,
    )


__all__ = ["SqlGradingResult", "grade_sql_answer"]
