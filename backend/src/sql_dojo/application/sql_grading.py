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


_BOOLEAN_EXPLAIN_OPTIONS = {
    "ANALYZE",
    "VERBOSE",
    "COSTS",
    "SETTINGS",
    "GENERIC_PLAN",
    "BUFFERS",
    "WAL",
    "TIMING",
    "SUMMARY",
    "MEMORY",
}
_BOOLEAN_EXPLAIN_VALUES = {"TRUE", "ON", "1", "FALSE", "OFF", "0"}
_DISABLED_EXPLAIN_VALUES = {"FALSE", "OFF", "0"}
_ENABLED_EXPLAIN_VALUES = {"TRUE", "ON", "1"}
_EXPLAIN_FORMAT_VALUES = {"TEXT", "XML", "JSON", "YAML"}
_EXPLAIN_SERIALIZE_VALUES = {"NONE", "TEXT", "BINARY"}
_VALID_BARE_EXPLAIN_SEQUENCES = {
    (),
    ("ANALYZE",),
    ("VERBOSE",),
    ("ANALYZE", "VERBOSE"),
}
_EXPLAIN_PATTERN = re.compile(
    r"^\s*EXPLAIN\s*(?:\((?P<options>[^)]*)\))?\s*(?P<query>.+)$",
    re.IGNORECASE | re.DOTALL,
)
_DOLLAR_QUOTE_TAG_PATTERN = re.compile(r"\$[A-Za-z_][A-Za-z_0-9]*\$|\$\$")


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
    selects = list(parsed.find_all(exp.Select))
    if isinstance(parsed, exp.Select) and not selects:
        selects = [parsed]
    for select in selects:
        base = select.args.get("from_")
        left_tables = [
            _normalize_identifier(table.name)
            for table in base.find_all(exp.Table)
        ] if isinstance(base, exp.From) else []
        left_default = left_tables[0] if left_tables else ""
        for join in select.args.get("joins") or []:
            if not isinstance(join, exp.Join):
                continue
            right_table_exp = join.this
            if not isinstance(right_table_exp, exp.Table):
                continue
            right = _normalize_identifier(right_table_exp.name)
            left = left_default
            join_side = join.args.get("side")
            join_kind = join.args.get("kind")
            join_type = _normalize_identifier(join_side or join_kind or "INNER").upper()
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
        for column in agg.find_all(exp.Column):
            if column.table:
                column_names.add(
                    f"{_normalize_identifier(column.table)}."
                    f"{_normalize_identifier(column.name)}",
                )
            column_names.add(_normalize_identifier(column.name))
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
    with_clause = parsed.args.get("with") or parsed.args.get("with_")
    if not isinstance(with_clause, exp.With):
        return result
    for cte in with_clause.expressions:
        alias = cte.alias_or_name
        if alias:
            result.add(_normalize_identifier(alias))
    return result


def _predicate_columns(parsed: exp.Expression) -> set[str]:
    return _column_names(
        column
        for where_exp in parsed.find_all(exp.Where)
        for column in where_exp.find_all(exp.Column)
    )


def _statement_kind(parsed: exp.Expression, raw_sql: str) -> str:
    sql_without_comments = _strip_sql_comments_preserving_offsets(raw_sql)
    normalized_prefix = sql_without_comments.strip().upper()
    if normalized_prefix.startswith("EXPLAIN"):
        return "explain"
    if normalized_prefix.startswith("CREATE MATERIALIZED VIEW"):
        return "create_materialized_view"
    if isinstance(parsed, exp.Create) and parsed.args.get("kind") == "INDEX":
        return "create_index"
    if isinstance(parsed, exp.Insert):
        return "insert"
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


def _consume_quoted_sql(
    raw_sql: str,
    index: int,
    quote: str,
    *,
    escape_backslash: bool = False,
) -> tuple[str, int]:
    result: list[str] = []
    result.append(raw_sql[index])
    index += 1
    while index < len(raw_sql):
        current = raw_sql[index]
        next_char = raw_sql[index + 1] if index + 1 < len(raw_sql) else ""
        result.append(current)
        if escape_backslash and current == "\\" and next_char:
            result.append(next_char)
            index += 2
            continue
        if current == quote and next_char == quote:
            result.append(next_char)
            index += 2
            continue
        if current == quote:
            index += 1
            break
        index += 1
    return "".join(result), index


def _consume_line_comment(raw_sql: str, index: int) -> tuple[str, int]:
    result = ["  "]
    index += 2
    while index < len(raw_sql) and raw_sql[index] not in "\r\n":
        result.append(" ")
        index += 1
    return "".join(result), index


def _consume_block_comment(raw_sql: str, index: int) -> tuple[str, int]:
    result = ["  "]
    index += 2
    depth = 1
    while index < len(raw_sql) and depth > 0:
        current = raw_sql[index]
        next_char = raw_sql[index + 1] if index + 1 < len(raw_sql) else ""
        if current == "/" and next_char == "*":
            result.append("  ")
            index += 2
            depth += 1
            continue
        if current == "*" and next_char == "/":
            result.append("  ")
            index += 2
            depth -= 1
            continue
        result.append("\n" if current in "\r\n" else " ")
        index += 1
    return "".join(result), index


def _consume_dollar_quoted_sql(raw_sql: str, index: int) -> tuple[str, int] | None:
    matched = _DOLLAR_QUOTE_TAG_PATTERN.match(raw_sql, index)
    if matched is None:
        return None
    tag = matched.group(0)
    close_index = raw_sql.find(tag, matched.end())
    if close_index == -1:
        return raw_sql[index:], len(raw_sql)
    end_index = close_index + len(tag)
    return raw_sql[index:end_index], end_index


def _consume_sql_literal_or_comment(
    raw_sql: str,
    index: int,
) -> tuple[str, int] | None:
    current = raw_sql[index]
    next_char = raw_sql[index + 1] if index + 1 < len(raw_sql) else ""
    if current == "$":
        consumed = _consume_dollar_quoted_sql(raw_sql, index)
        if consumed is not None:
            return consumed
    if current in {"'", '"'}:
        return _consume_quoted_sql(
            raw_sql,
            index,
            current,
            escape_backslash=_is_postgres_escape_string_quote(raw_sql, index),
        )
    if current == "-" and next_char == "-":
        return _consume_line_comment(raw_sql, index)
    if current == "/" and next_char == "*":
        return _consume_block_comment(raw_sql, index)
    return None


def _strip_sql_comments_preserving_offsets(raw_sql: str) -> str:
    result: list[str] = []
    index = 0
    while index < len(raw_sql):
        consumed = _consume_sql_literal_or_comment(raw_sql, index)
        if consumed is not None:
            text, index = consumed
            result.append(text)
            continue
        result.append(raw_sql[index])
        index += 1
    return "".join(result)


def _mask_sql_literals_preserving_offsets(raw_sql: str) -> str:
    sql_without_comments = _strip_sql_comments_preserving_offsets(raw_sql)
    result: list[str] = []
    index = 0
    while index < len(sql_without_comments):
        current = sql_without_comments[index]
        if current == "$":
            consumed = _consume_dollar_quoted_sql(sql_without_comments, index)
            if consumed is not None:
                text, index = consumed
                result.append(" " * len(text))
                continue
        if current == "'":
            text, index = _consume_quoted_sql(
                sql_without_comments,
                index,
                current,
                escape_backslash=_is_postgres_escape_string_quote(
                    sql_without_comments,
                    index,
                ),
            )
            result.append(" " * len(text))
            continue
        result.append(current)
        index += 1
    return "".join(result)


def _sql_literal_ranges(raw_sql: str) -> list[tuple[int, int]]:
    sql_without_comments = _strip_sql_comments_preserving_offsets(raw_sql)
    ranges: list[tuple[int, int]] = []
    index = 0
    while index < len(sql_without_comments):
        current = sql_without_comments[index]
        if current == "$":
            consumed = _consume_dollar_quoted_sql(sql_without_comments, index)
            if consumed is not None:
                _, end_index = consumed
                ranges.append((index, end_index))
                index = end_index
                continue
        if current == "'":
            _, end_index = _consume_quoted_sql(
                sql_without_comments,
                index,
                current,
                escape_backslash=_is_postgres_escape_string_quote(
                    sql_without_comments,
                    index,
                ),
            )
            ranges.append((index, end_index))
            index = end_index
            continue
        index += 1
    return ranges


def _is_postgres_escape_string_quote(raw_sql: str, quote_index: int) -> bool:
    if quote_index == 0 or raw_sql[quote_index - 1].lower() != "e":
        return False
    return quote_index == 1 or not (
        raw_sql[quote_index - 2].isalnum() or raw_sql[quote_index - 2] == "_"
    )


def _extract_grouped_explain_options(grouped_options: str) -> tuple[set[str], bool]:
    option_states: dict[str, bool] = {}
    invalid_options = False
    for part in grouped_options.split(","):
        option, enabled, invalid = _parse_parenthesized_explain_option(part)
        invalid_options = invalid_options or invalid
        if option is not None:
            option_states[option] = enabled
    options = {
        option
        for option, enabled in option_states.items()
        if enabled
    }
    invalid_options = invalid_options or _has_invalid_explain_option_combination(
        options,
    )
    return options, invalid_options


def _extract_bare_explain_parts(query: str) -> tuple[str, set[str], bool]:
    statement_keyword = re.search(
        r"\b(WITH|SELECT|INSERT|UPDATE|DELETE|CREATE)\b",
        query,
        re.IGNORECASE,
    )
    if statement_keyword is None:
        return query, set(), False
    option_tokens = [
        _normalize_identifier(part).upper()
        for part in query[:statement_keyword.start()].split()
        if part.strip()
    ]
    invalid_options = tuple(option_tokens) not in _VALID_BARE_EXPLAIN_SEQUENCES
    options = set(option_tokens) & {"ANALYZE", "VERBOSE"}
    return query[statement_keyword.start():].strip(), options, invalid_options


def _extract_explain_parts(raw_sql: str) -> tuple[str, set[str], bool]:
    extraction_sql = _strip_sql_comments_preserving_offsets(raw_sql)
    matched = _EXPLAIN_PATTERN.match(extraction_sql)
    if matched is None:
        return raw_sql, set(), False
    grouped_options = matched.group("options")
    if grouped_options is not None:
        options, invalid_options = _extract_grouped_explain_options(grouped_options)
        return matched.group("query").strip(), options, invalid_options
    query = matched.group("query").strip()
    return _extract_bare_explain_parts(query)


def _parse_parenthesized_explain_option(
    raw_option: str,
) -> tuple[str | None, bool, bool]:
    parts = raw_option.strip().split()
    if not parts:
        return None, False, True
    option = _normalize_identifier(parts[0]).upper()
    if option in _BOOLEAN_EXPLAIN_OPTIONS:
        return _parse_boolean_explain_option(option, parts)
    if option == "FORMAT":
        return _parse_keyword_explain_option(
            option,
            parts,
            valid_values=_EXPLAIN_FORMAT_VALUES,
        )
    if option == "SERIALIZE":
        if len(parts) == 1:
            return option, True, False
        return _parse_keyword_explain_option(
            option,
            parts,
            valid_values=_EXPLAIN_SERIALIZE_VALUES,
            disabled_values={"NONE"},
        )
    return None, False, True


def _parse_boolean_explain_option(
    option: str,
    parts: list[str],
) -> tuple[str | None, bool, bool]:
    if len(parts) == 1:
        return option, True, False
    if len(parts) > 2:
        return None, False, True
    value = _normalize_identifier(parts[1]).upper()
    if value not in _BOOLEAN_EXPLAIN_VALUES:
        return None, False, True
    if value in _DISABLED_EXPLAIN_VALUES:
        return option, False, False
    if value in _ENABLED_EXPLAIN_VALUES:
        return option, True, False
    return None, False, True


def _parse_keyword_explain_option(
    option: str,
    parts: list[str],
    *,
    valid_values: set[str],
    disabled_values: set[str] | None = None,
) -> tuple[str | None, bool, bool]:
    if len(parts) != 2:
        return None, False, True
    value = _normalize_identifier(parts[1]).upper()
    if value not in valid_values:
        return None, False, True
    if disabled_values is not None and value in disabled_values:
        return option, False, False
    return option, True, False


def _has_invalid_explain_option_combination(options: set[str]) -> bool:
    if "ANALYZE" in options and "GENERIC_PLAN" in options:
        return True
    analyze_only_options = {"SERIALIZE", "TIMING", "WAL"}
    return bool(analyze_only_options & options) and "ANALYZE" not in options


def _normalized_sql(raw_sql: str) -> str:
    without_comments = _strip_sql_comments_preserving_offsets(raw_sql)
    return re.sub(r"\s+", " ", without_comments).strip().lower()


def _normalized_structural_sql(raw_sql: str) -> str:
    without_literals = _mask_sql_literals_preserving_offsets(raw_sql)
    return re.sub(r"\s+", " ", without_literals).strip().lower()


def _compact_sql(raw_sql: str) -> str:
    return re.sub(r"\s+", "", _normalized_sql(raw_sql))


def _compact_structural_sql(raw_sql: str) -> str:
    return re.sub(r"\s+", "", _normalized_structural_sql(raw_sql))


def _compact_sql_with_offsets(raw_sql: str) -> tuple[str, list[int]]:
    sql_without_comments = _strip_sql_comments_preserving_offsets(raw_sql)
    compact_chars: list[str] = []
    offsets: list[int] = []
    for index, char in enumerate(sql_without_comments):
        if char.isspace():
            continue
        compact_chars.append(char.lower())
        offsets.append(index)
    return "".join(compact_chars), offsets


def _sql_fragment_present(user_sql: str, fragment: str) -> bool:
    compact_sql, offsets = _compact_sql_with_offsets(user_sql)
    compact_fragment = _compact_sql(fragment)
    literal_ranges = _sql_literal_ranges(user_sql)
    start = compact_sql.find(compact_fragment)
    while start != -1:
        end = start + len(compact_fragment) - 1
        original_start = offsets[start]
        original_end = offsets[end] + 1
        if not any(
            literal_start <= original_start and original_end <= literal_end
            for literal_start, literal_end in literal_ranges
        ):
            return True
        start = compact_sql.find(compact_fragment, start + 1)
    return False


def _required_function_present(sql_lower: str, function_name: str) -> bool:
    normalized = _normalize_identifier(function_name)
    if normalized == "is distinct from":
        return " is distinct from " in f" {sql_lower} "
    return re.search(rf"\b{re.escape(normalized)}\s*\(", sql_lower) is not None


def _actual_filter_aggregates(sql_lower: str) -> set[tuple[str, str]]:
    result: set[tuple[str, str]] = set()
    pattern = re.compile(
        r"\b(?P<func>[a-z_][a-z0-9_]*)\s*\((?P<body>[^)]*)\)\s*filter\s*\(\s*where\b",
    )
    for matched in pattern.finditer(sql_lower):
        func_name = matched.group("func").upper()
        body = matched.group("body")
        result.add((func_name, "*"))
        for column in re.findall(r"\b[a-z_][a-z0-9_]*\b", body):
            result.add((func_name, _normalize_identifier(column)))
    return result


def _distinct_on_columns(sql_lower: str) -> set[str]:
    matched = re.search(r"\bdistinct\s+on\s*\((?P<body>[^)]*)\)", sql_lower)
    if matched is None:
        return set()
    return {
        _normalize_identifier(part.split(".")[-1])
        for part in matched.group("body").split(",")
        if part.strip()
    }


def _having_columns(parsed: exp.Expression) -> set[str]:
    having_expressions = list(parsed.find_all(exp.Having))
    result = _column_names(
        column
        for having_exp in having_expressions
        for column in having_exp.find_all(exp.Column)
    )
    if having_expressions:
        result.add("*")
    return result


def _json_operator_present(sql_lower: str, operator: str) -> bool:
    if operator == "->":
        return "->" in sql_lower
    return operator in sql_lower


def _array_function_present(sql_lower: str, function_name: str) -> bool:
    normalized = _normalize_identifier(function_name)
    if normalized == "any":
        return re.search(r"\bany\s*\(", sql_lower) is not None
    return _required_function_present(sql_lower, normalized)


def _index_include_columns(sql_lower: str) -> set[str]:
    matched = re.search(r"\binclude\s*\((?P<body>[^)]*)\)", sql_lower)
    if matched is None:
        return set()
    return {
        _normalize_identifier(part.split(".")[-1])
        for part in matched.group("body").split(",")
        if part.strip()
    }


def _index_method(sql_lower: str) -> str | None:
    matched = re.search(r"\busing\s+(?P<method>[a-z_][a-z0-9_]*)\b", sql_lower)
    if matched is None:
        return None
    return _normalize_identifier(matched.group("method"))


def _pagination_style_present(sql_lower: str, style: str) -> bool:
    normalized = _normalize_identifier(style)
    if normalized == "keyset":
        has_cursor_predicate = re.search(r"\bwhere\b.+(?:>|<)", sql_lower) is not None
        return has_cursor_predicate and " order by " in sql_lower and " limit " in sql_lower
    if normalized == "offset":
        return re.search(r"\boffset\s+\d+", sql_lower) is not None
    return normalized in sql_lower


def _order_requirements_satisfied(
    actual_orders: list[tuple[str, str]],
    expected_orders: list[tuple[str, str]],
) -> bool:
    if not expected_orders:
        return True
    return actual_orders[:len(expected_orders)] == expected_orders


def _prohibited_pattern_hits(user_sql: str, patterns: list[str]) -> list[str]:
    sql_lower = _normalized_sql(user_sql)
    implicit_join = "," in sql_lower and " join " not in sql_lower
    prohibited_hits: list[str] = []
    for item in patterns:
        if _is_prohibited_pattern_hit(item, sql_lower, implicit_join):
            prohibited_hits.append(item)
    return prohibited_hits


def _is_prohibited_pattern_hit(
    item: str,
    sql_lower: str,
    implicit_join: bool,
) -> bool:
    special_patterns = {
        "implicit_join",
        "offset_pagination",
        "select_star_for_report",
        "leading_wildcard_without_trigram",
    }
    if item == "implicit_join":
        return implicit_join
    if item == "offset_pagination":
        return re.search(r"\boffset\s+\d+", sql_lower) is not None
    if item == "select_star_for_report":
        return re.search(r"\bselect\s+\*", sql_lower) is not None
    if item == "leading_wildcard_without_trigram":
        return (
            re.search(r"\blike\s+'%", sql_lower) is not None
            and "gin_trgm_ops" not in sql_lower
        )
    return item not in special_patterns and item.lower() in sql_lower


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
    invalid_explain_options = False
    if actual_kind == "explain":
        inner_sql, explain_options, invalid_explain_options = _extract_explain_parts(
            user_sql,
        )
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
        actual_predicates = _predicate_columns(target_parsed)
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
        actual_orders: list[tuple[str, str]] = []
        if order_exp is not None:
            for ordered in order_exp.expressions:
                if isinstance(ordered, exp.Ordered) and isinstance(ordered.this, exp.Column):
                    name = _normalize_identifier(ordered.this.name)
                    direction = "DESC" if ordered.args.get("desc") else "ASC"
                    actual_orders.append((name, direction))
                elif isinstance(ordered, exp.Column):
                    actual_orders.append((_normalize_identifier(ordered.name), "ASC"))
        expected_orders = [
            (
                _normalize_identifier(str(item["column"])),
                _normalize_identifier(str(item.get("direction", "ASC"))).upper(),
            )
            for item in required_order_by
        ]
        _add_rule(
            rules,
            name="order_by",
            weight=10,
            passed=_order_requirements_satisfied(actual_orders, expected_orders),
            message=f"Expected order by {expected_orders}, got {actual_orders}",
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

    sql_lower = _normalized_structural_sql(user_sql)
    sql_compact = _compact_structural_sql(user_sql)

    required_functions = grading_contract.get("required_functions", [])
    if required_functions:
        expected = {_normalize_identifier(name) for name in required_functions}
        actual = {
            name for name in expected
            if _required_function_present(sql_lower, name)
        }
        _add_rule(
            rules,
            name="required_functions",
            weight=10,
            passed=expected.issubset(actual),
            message=f"Expected functions {sorted(expected)}, got {sorted(actual)}",
        )

    if grading_contract.get("required_case") is True:
        has_case = target_parsed.find(exp.Case) is not None or (
            " case " in f" {sql_lower} " and " when " in f" {sql_lower} "
        )
        _add_rule(
            rules,
            name="case_expression",
            weight=10,
            passed=has_case,
            message="Expected CASE WHEN expression",
        )

    required_filter_aggregates = grading_contract.get("required_filter_aggregates", [])
    if required_filter_aggregates:
        actual_filter_aggs = _actual_filter_aggregates(sql_lower)
        expected_filter_aggs = {
            (
                _normalize_identifier(str(item["function"])).upper(),
                _normalize_identifier(str(item["column"])),
            )
            for item in required_filter_aggregates
        }
        _add_rule(
            rules,
            name="filter_aggregates",
            weight=10,
            passed=expected_filter_aggs.issubset(actual_filter_aggs),
            message=(
                f"Expected filter aggregates {sorted(expected_filter_aggs)}, "
                f"got {sorted(actual_filter_aggs)}"
            ),
        )

    required_distinct_on = grading_contract.get("required_distinct_on", [])
    if required_distinct_on:
        actual_distinct_on = _distinct_on_columns(sql_lower)
        expected = {_normalize_identifier(column) for column in required_distinct_on}
        _add_rule(
            rules,
            name="distinct_on",
            weight=10,
            passed=expected.issubset(actual_distinct_on),
            message=(
                f"Expected DISTINCT ON {sorted(expected)}, "
                f"got {sorted(actual_distinct_on)}"
            ),
        )

    required_having_columns = grading_contract.get("required_having_columns", [])
    if required_having_columns:
        actual_having = _having_columns(target_parsed)
        expected = {_normalize_identifier(column) for column in required_having_columns}
        _add_rule(
            rules,
            name="having_columns",
            weight=10,
            passed=expected.issubset(actual_having),
            message=f"Expected HAVING {sorted(expected)}, got {sorted(actual_having)}",
        )

    if grading_contract.get("required_exists") is True:
        exists_present = re.search(r"(?<!not\s)\bexists\s*\(", sql_lower) is not None
        _add_rule(
            rules,
            name="exists_subquery",
            weight=10,
            passed=exists_present,
            message="Expected EXISTS subquery",
        )

    if grading_contract.get("required_not_exists") is True:
        not_exists_present = re.search(r"\bnot\s+exists\s*\(", sql_lower) is not None
        _add_rule(
            rules,
            name="not_exists_subquery",
            weight=10,
            passed=not_exists_present,
            message="Expected NOT EXISTS subquery",
        )

    required_json_operators = grading_contract.get("required_json_operators", [])
    if required_json_operators:
        expected = set(required_json_operators)
        actual = {
            operator for operator in expected
            if _json_operator_present(sql_lower, operator)
        }
        _add_rule(
            rules,
            name="json_operators",
            weight=10,
            passed=expected.issubset(actual),
            message=f"Expected JSON operators {sorted(expected)}, got {sorted(actual)}",
        )

    required_array_functions = grading_contract.get("required_array_functions", [])
    if required_array_functions:
        expected = {_normalize_identifier(name) for name in required_array_functions}
        actual = {
            name for name in expected
            if _array_function_present(sql_lower, name)
        }
        _add_rule(
            rules,
            name="array_functions",
            weight=10,
            passed=expected.issubset(actual),
            message=f"Expected array functions {sorted(expected)}, got {sorted(actual)}",
        )

    if grading_contract.get("required_on_conflict") is True:
        _add_rule(
            rules,
            name="on_conflict",
            weight=10,
            passed=" on conflict " in f" {sql_lower} ",
            message="Expected ON CONFLICT clause",
        )

    partial_index_columns = grading_contract.get(
        "required_partial_index_predicate_columns",
        [],
    )
    if partial_index_columns:
        where_sql = sql_lower.split(" where ", 1)[1] if " where " in sql_lower else ""
        expected = {_normalize_identifier(column) for column in partial_index_columns}
        actual = {
            column for column in expected
            if re.search(rf"\b{re.escape(column)}\b", where_sql)
        }
        _add_rule(
            rules,
            name="partial_index_predicate",
            weight=10,
            passed=expected.issubset(actual),
            message=(
                f"Expected partial index predicate columns {sorted(expected)}, "
                f"got {sorted(actual)}"
            ),
        )

    expression_terms = grading_contract.get("required_expression_index_terms", [])
    if expression_terms:
        expected = {_compact_sql(term) for term in expression_terms}
        actual = {
            term for term in expected
            if term in sql_compact
        }
        _add_rule(
            rules,
            name="expression_index_terms",
            weight=10,
            passed=expected.issubset(actual),
            message=(
                f"Expected expression index terms {sorted(expected)}, "
                f"got {sorted(actual)}"
            ),
        )

    include_columns = grading_contract.get("required_include_columns", [])
    if include_columns:
        actual_include = _index_include_columns(sql_lower)
        expected = {_normalize_identifier(column) for column in include_columns}
        _add_rule(
            rules,
            name="include_columns",
            weight=10,
            passed=expected.issubset(actual_include),
            message=f"Expected INCLUDE {sorted(expected)}, got {sorted(actual_include)}",
        )

    required_index_method = grading_contract.get("required_index_method")
    if isinstance(required_index_method, str):
        actual_method = _index_method(sql_lower)
        expected_method = _normalize_identifier(required_index_method)
        _add_rule(
            rules,
            name="index_method",
            weight=10,
            passed=actual_method == expected_method,
            message=f"Expected index method {expected_method}, got {actual_method}",
        )

    required_pagination_style = grading_contract.get("required_pagination_style")
    if isinstance(required_pagination_style, str):
        _add_rule(
            rules,
            name="pagination_style",
            weight=10,
            passed=_pagination_style_present(sql_lower, required_pagination_style),
            message=f"Expected pagination style {required_pagination_style}",
        )

    required_sql_fragments = grading_contract.get("required_sql_fragments", [])
    if required_sql_fragments:
        expected = {_compact_sql(fragment) for fragment in required_sql_fragments}
        actual = {
            fragment for fragment in expected
            if _sql_fragment_present(user_sql, fragment)
        }
        _add_rule(
            rules,
            name="sql_fragments",
            weight=10,
            passed=expected.issubset(actual),
            message=f"Expected SQL fragments {sorted(expected)}, got {sorted(actual)}",
        )

    if grading_contract.get("require_explain") is True:
        _add_rule(
            rules,
            name="require_explain",
            weight=10,
            passed=actual_kind == "explain",
            message=f"Expected EXPLAIN, got {actual_kind}",
        )
        _add_rule(
            rules,
            name="explain_syntax",
            weight=10,
            passed=not invalid_explain_options,
            message="Expected valid EXPLAIN options",
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
        prohibited_hits = _prohibited_pattern_hits(user_sql, prohibited)
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
