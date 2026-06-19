"""SQL道場のテーマバンク。"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sql_dojo.domain.sql_dojo_types import (
    SqlDojoCatalog,
    SqlDojoDifficulty,
    SqlDojoGenerationError,
    SqlDojoProblem,
    SqlDojoThemeSummary,
)

if TYPE_CHECKING:
    from sql_dojo.domain.sql_dojo_types import SqlDojoGradingContract


@dataclass(frozen=True)
class _ThemeVariant:
    problem_statement: str
    schema_markdown: str
    sample_data: list[dict[str, object]]
    expected_focus: str
    reference_sql: str
    grading_contract: SqlDojoGradingContract


@dataclass(frozen=True)
class _ThemeTemplate:
    family: str
    difficulty: SqlDojoDifficulty
    business_domain: str
    target_skill: str
    title: str
    generation_prompt: str
    variants: tuple[_ThemeVariant, ...]


_THEMES: tuple[_ThemeTemplate, ...] = (
    _ThemeTemplate(
        family="join-basics",
        difficulty="beginner",
        business_domain="EC",
        target_skill="JOIN と集約の基礎",
        title="顧客別の注文件数を集計する",
        generation_prompt="customers と orders を JOIN して顧客別件数を出す",
        variants=(
            _ThemeVariant(
                problem_statement=(
                    "EC サービスの月次レポートです。"
                    "顧客ごとの shipped 注文件数を多い順に 5 件取得してください。"
                    "出力列は customer_id, customer_name, shipped_order_count とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "customers(id bigint primary key, name text, segment text)\n"
                    "orders(id bigint primary key, customer_id bigint, status text, created_at timestamptz)\n"
                    "```"
                ),
                sample_data=[
                    {"table": "customers", "rows": 12500},
                    {"table": "orders", "rows": 184220},
                ],
                expected_focus="INNER JOIN, COUNT, WHERE, GROUP BY, ORDER BY, LIMIT",
                reference_sql=(
                    "SELECT c.id AS customer_id, c.name AS customer_name, "
                    "COUNT(o.id) AS shipped_order_count "
                    "FROM customers AS c "
                    "INNER JOIN orders AS o ON o.customer_id = c.id "
                    "WHERE o.status = 'shipped' "
                    "GROUP BY c.id, c.name "
                    "ORDER BY shipped_order_count DESC "
                    "LIMIT 5"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["customers", "orders"],
                    "required_joins": [
                        {"left": "customers", "right": "orders", "join_type": "INNER"},
                    ],
                    "required_predicate_columns": ["status"],
                    "required_group_by_columns": ["id", "name"],
                    "required_aggregates": [{"function": "COUNT", "column": "id"}],
                    "required_order_by": [{"column": "shipped_order_count", "direction": "DESC"}],
                    "required_limit": 5,
                    "prohibited_patterns": ["implicit_join"],
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="aggregation-reporting",
        difficulty="intermediate",
        business_domain="SaaS",
        target_skill="集計レポート",
        title="プラン別の月次売上を集計する",
        generation_prompt="subscriptions と invoices から月次売上を集計する",
        variants=(
            _ThemeVariant(
                problem_statement=(
                    "SaaS 請求データから、2026-05 のプラン別売上を求めてください。"
                    "出力列は plan_code, invoice_month, total_revenue とし、"
                    "売上の高い順に並べてください。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "subscriptions(id bigint primary key, account_id bigint, plan_code text)\n"
                    "invoices(id bigint primary key, subscription_id bigint, billed_at date, amount numeric)\n"
                    "```"
                ),
                sample_data=[
                    {"table": "subscriptions", "rows": 8800},
                    {"table": "invoices", "rows": 211000},
                ],
                expected_focus="DATE_TRUNC, SUM, GROUP BY, ORDER BY",
                reference_sql=(
                    "SELECT s.plan_code, DATE_TRUNC('month', i.billed_at) AS invoice_month, "
                    "SUM(i.amount) AS total_revenue "
                    "FROM subscriptions AS s "
                    "INNER JOIN invoices AS i ON i.subscription_id = s.id "
                    "WHERE DATE_TRUNC('month', i.billed_at) = DATE '2026-05-01' "
                    "GROUP BY s.plan_code, DATE_TRUNC('month', i.billed_at) "
                    "ORDER BY total_revenue DESC"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["subscriptions", "invoices"],
                    "required_joins": [
                        {"left": "subscriptions", "right": "invoices", "join_type": "INNER"},
                    ],
                    "required_predicate_columns": ["billed_at"],
                    "required_group_by_columns": ["plan_code"],
                    "required_aggregates": [{"function": "SUM", "column": "amount"}],
                    "required_order_by": [{"column": "total_revenue", "direction": "DESC"}],
                    "prohibited_patterns": ["implicit_join"],
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="window-ranking",
        difficulty="intermediate",
        business_domain="HR",
        target_skill="window function",
        title="部門ごとの売上上位担当を求める",
        generation_prompt="window function で部門別ランキングを作る",
        variants=(
            _ThemeVariant(
                problem_statement=(
                    "営業担当の実績から、department ごとに revenue 上位 1 名を抽出してください。"
                    "同率があっても 1 名だけ返す前提で、担当者名と revenue を含めてください。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "sales_reps(id bigint primary key, name text, department text)\n"
                    "monthly_sales(rep_id bigint, revenue numeric, target_month date)\n"
                    "```"
                ),
                sample_data=[
                    {"table": "sales_reps", "rows": 210},
                    {"table": "monthly_sales", "rows": 7560},
                ],
                expected_focus="ROW_NUMBER, PARTITION BY, ORDER BY, CTE",
                reference_sql=(
                    "WITH ranked_sales AS ("
                    "SELECT r.name, r.department, s.revenue, "
                    "ROW_NUMBER() OVER (PARTITION BY r.department ORDER BY s.revenue DESC) AS rn "
                    "FROM sales_reps AS r "
                    "INNER JOIN monthly_sales AS s ON s.rep_id = r.id "
                    "WHERE s.target_month = DATE '2026-05-01'"
                    ") "
                    "SELECT name, department, revenue "
                    "FROM ranked_sales "
                    "WHERE rn = 1"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["sales_reps", "monthly_sales"],
                    "required_joins": [
                        {"left": "sales_reps", "right": "monthly_sales", "join_type": "INNER"},
                    ],
                    "required_predicate_columns": ["target_month"],
                    "required_window_functions": ["ROW_NUMBER"],
                    "required_cte_names": ["ranked_sales"],
                    "prohibited_patterns": ["implicit_join"],
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="plan-reading",
        difficulty="advanced",
        business_domain="Marketplace",
        target_skill="EXPLAIN の確認",
        title="実行計画を確認する SQL を書く",
        generation_prompt="遅いクエリの実行計画を見るための EXPLAIN を書く",
        variants=(
            _ThemeVariant(
                problem_statement=(
                    "以下の検索クエリが遅いと報告されています。"
                    "まず実行計画と実測時間を確認したいです。"
                    "PostgreSQL でそのための 1 文を書いてください。\n\n"
                    "対象クエリ:\n"
                    "SELECT * FROM events WHERE account_id = 42 AND created_at >= DATE '2026-06-01'"
                ),
                schema_markdown=(
                    "```sql\n"
                    "events(id bigint primary key, account_id bigint, event_type text, created_at timestamptz)\n"
                    "```"
                ),
                sample_data=[{"table": "events", "rows": 8200000}],
                expected_focus="EXPLAIN ANALYZE, BUFFERS",
                reference_sql=(
                    "EXPLAIN (ANALYZE, BUFFERS) "
                    "SELECT * FROM events "
                    "WHERE account_id = 42 AND created_at >= DATE '2026-06-01'"
                ),
                grading_contract={
                    "statement_kind": "explain",
                    "required_tables": ["events"],
                    "required_predicate_columns": ["account_id", "created_at"],
                    "require_explain": True,
                    "required_explain_options": ["ANALYZE", "BUFFERS"],
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="slow-query-diagnosis",
        difficulty="advanced",
        business_domain="Observability",
        target_skill="スロークエリ改善",
        title="最新エラー取得クエリを絞り込む",
        generation_prompt="ログ検索のスロークエリを改善する SQL を書く",
        variants=(
            _ThemeVariant(
                problem_statement=(
                    "ログ分析テーブルから、service_name='billing' の ERROR ログを"
                    "新しい順に 50 件取得してください。"
                    "行数が非常に多いため、必要な条件と並び順を明確にした 1 文にしてください。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "application_logs(id bigint primary key, service_name text, level text, message text, created_at timestamptz)\n"
                    "```"
                ),
                sample_data=[{"table": "application_logs", "rows": 42000000}],
                expected_focus="WHERE, ORDER BY, LIMIT",
                reference_sql=(
                    "SELECT id, service_name, level, message, created_at "
                    "FROM application_logs "
                    "WHERE service_name = 'billing' AND level = 'ERROR' "
                    "ORDER BY created_at DESC "
                    "LIMIT 50"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["application_logs"],
                    "required_predicate_columns": [
                        "service_name",
                        "level",
                    ],
                    "required_order_by": [{"column": "created_at", "direction": "DESC"}],
                    "required_limit": 50,
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="index-design",
        difficulty="advanced",
        business_domain="Marketplace",
        target_skill="CREATE INDEX",
        title="検索条件に合う複合インデックスを作る",
        generation_prompt="filters と sort に合う index を 1 文で作る",
        variants=(
            _ThemeVariant(
                problem_statement=(
                    "items テーブルで `seller_id = ? AND status = 'active'` の条件で絞り込み、"
                    "`updated_at DESC` で一覧表示するクエリが頻出です。"
                    "このアクセスパターンを意識した PostgreSQL のインデックスを 1 文で作成してください。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "items(id bigint primary key, seller_id bigint, status text, price numeric, updated_at timestamptz)\n"
                    "```"
                ),
                sample_data=[{"table": "items", "rows": 13500000}],
                expected_focus="CREATE INDEX, 複合インデックスの列順",
                reference_sql=(
                    "CREATE INDEX idx_items_seller_status_updated_at "
                    "ON items (seller_id, status, updated_at DESC)"
                ),
                grading_contract={
                    "statement_kind": "create_index",
                    "required_index": {
                        "table": "items",
                        "columns": ["seller_id", "status", "updated_at"],
                        "orders": {"updated_at": "DESC"},
                    },
                },
            ),
        ),
    ),
)


class SqlThemeBank:
    """テーマ一覧と問題派生生成を担当する。"""

    def list_catalog(self) -> SqlDojoCatalog:
        themes: list[SqlDojoThemeSummary] = [
            {
                "family": theme.family,
                "difficulty": theme.difficulty,
                "business_domain": theme.business_domain,
                "target_skill": theme.target_skill,
                "title": theme.title,
            }
            for theme in _THEMES
        ]
        return {
            "difficulties": ["beginner", "intermediate", "advanced"],
            "themes": themes,
        }

    def create_problem(
        self,
        *,
        difficulty: SqlDojoDifficulty,
        theme_family: str | None = None,
    ) -> SqlDojoProblem:
        candidates = [
            theme for theme in _THEMES
            if theme.difficulty == difficulty
            and (theme_family is None or theme.family == theme_family)
        ]
        if not candidates:
            msg = (
                f"No SQL dojo theme for difficulty={difficulty!r}, "
                f"theme_family={theme_family!r}"
            )
            raise SqlDojoGenerationError(
                error_code="theme_not_found",
                message=msg,
            )
        theme = random.choice(candidates)  # noqa: S311
        variant = random.choice(theme.variants)  # noqa: S311
        return {
            "family": theme.family,
            "difficulty": theme.difficulty,
            "dialect": "postgresql",
            "business_domain": theme.business_domain,
            "target_skill": theme.target_skill,
            "theme_title": theme.title,
            "problem_statement": variant.problem_statement,
            "schema_markdown": variant.schema_markdown,
            "sample_data_json": json.dumps(variant.sample_data, ensure_ascii=False),
            "expected_focus": variant.expected_focus,
            "reference_sql": variant.reference_sql,
            "grading_contract": variant.grading_contract,
        }


__all__ = ["SqlThemeBank"]
