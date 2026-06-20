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
    SqlDojoTopicSummary,
)

if TYPE_CHECKING:
    from sql_dojo.domain.sql_dojo_types import SqlDojoGradingContract


@dataclass(frozen=True)
class _ThemeVariant:
    topic_id: str
    topic_title: str
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


def _sample_rows(*items: tuple[str, int]) -> list[dict[str, object]]:
    return [{"table": table, "rows": rows} for table, rows in items]


def _count_join_contract(  # noqa: PLR0913
    *,
    left: str,
    right: str,
    predicate_columns: list[str],
    group_by_columns: list[str],
    order_by_column: str,
    limit: int | None = None,
    join_type: str = "INNER",
    aggregate_column: str = "*",
    order_direction: str = "DESC",
) -> SqlDojoGradingContract:
    contract: SqlDojoGradingContract = {
        "statement_kind": "select",
        "required_tables": [left, right],
        "required_joins": [{"left": left, "right": right, "join_type": join_type}],
        "required_predicate_columns": predicate_columns,
        "required_group_by_columns": group_by_columns,
        "required_aggregates": [{"function": "COUNT", "column": aggregate_column}],
        "required_order_by": [{"column": order_by_column, "direction": order_direction}],
        "prohibited_patterns": ["implicit_join"],
    }
    if isinstance(limit, int):
        contract["required_limit"] = limit
    return contract


def _sum_join_contract(  # noqa: PLR0913
    *,
    left: str,
    right: str,
    predicate_columns: list[str],
    group_by_columns: list[str],
    aggregate_column: str,
    order_by_column: str,
) -> SqlDojoGradingContract:
    return {
        "statement_kind": "select",
        "required_tables": [left, right],
        "required_joins": [{"left": left, "right": right, "join_type": "INNER"}],
        "required_predicate_columns": predicate_columns,
        "required_group_by_columns": group_by_columns,
        "required_aggregates": [{"function": "SUM", "column": aggregate_column}],
        "required_order_by": [{"column": order_by_column, "direction": "DESC"}],
        "prohibited_patterns": ["implicit_join"],
    }


def _window_contract(
    *,
    left: str,
    right: str,
    predicate_columns: list[str],
    cte_name: str,
) -> SqlDojoGradingContract:
    return {
        "statement_kind": "select",
        "required_tables": [left, right],
        "required_joins": [{"left": left, "right": right, "join_type": "INNER"}],
        "required_predicate_columns": predicate_columns,
        "required_window_functions": ["ROW_NUMBER"],
        "required_cte_names": [cte_name],
        "prohibited_patterns": ["implicit_join"],
    }


def _lag_contract(
    *,
    table: str,
    predicate_columns: list[str],
    cte_name: str,
) -> SqlDojoGradingContract:
    return {
        "statement_kind": "select",
        "required_tables": [table],
        "required_predicate_columns": predicate_columns,
        "required_window_functions": ["LAG"],
        "required_cte_names": [cte_name],
    }


def _explain_contract(  # noqa: PLR0913
    *,
    table: str,
    predicate_columns: list[str],
    order_by_column: str | None = None,
    order_direction: str = "DESC",
    limit: int | None = None,
) -> SqlDojoGradingContract:
    contract: SqlDojoGradingContract = {
        "statement_kind": "explain",
        "required_tables": [table],
        "required_predicate_columns": predicate_columns,
        "require_explain": True,
        "required_explain_options": ["ANALYZE", "BUFFERS"],
    }
    if order_by_column is not None:
        contract["required_order_by"] = [{
            "column": order_by_column,
            "direction": order_direction,
        }]
    if isinstance(limit, int):
        contract["required_limit"] = limit
    return contract


def _index_contract(
    *,
    table: str,
    columns: list[str],
    desc_column: str,
) -> SqlDojoGradingContract:
    return {
        "statement_kind": "create_index",
        "required_index": {
            "table": table,
            "columns": columns,
            "orders": {desc_column: "DESC"},
        },
    }


_THEMES: tuple[_ThemeTemplate, ...] = (
    _ThemeTemplate(
        family="join-basics",
        difficulty="beginner",
        business_domain="Cross-domain",
        target_skill="JOIN と件数集計",
        title="JOIN で件数集計を作る",
        generation_prompt="2テーブルを JOIN して COUNT 集計を作る",
        variants=(
            _ThemeVariant(
                topic_id="join-basics-shipped-orders",
                topic_title="shipped注文件数",
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
                sample_data=_sample_rows(("customers", 12500), ("orders", 184220)),
                expected_focus="INNER JOIN, COUNT, WHERE, GROUP BY, ORDER BY, LIMIT",
                reference_sql=(
                    "SELECT c.id AS customer_id, c.name AS customer_name, "
                    "COUNT(*) AS shipped_order_count "
                    "FROM customers AS c "
                    "INNER JOIN orders AS o ON o.customer_id = c.id "
                    "WHERE o.status = 'shipped' "
                    "GROUP BY c.id, c.name "
                    "ORDER BY shipped_order_count DESC "
                    "LIMIT 5"
                ),
                grading_contract=_count_join_contract(
                    left="customers",
                    right="orders",
                    predicate_columns=["status"],
                    group_by_columns=["id", "name"],
                    order_by_column="shipped_order_count",
                    limit=5,
                ),
            ),
            _ThemeVariant(
                topic_id="join-basics-open-tickets",
                topic_title="未解決チケット数",
                problem_statement=(
                    "サポートチームが workspace ごとの未解決チケット数を確認したいです。"
                    "status='open' のチケット件数を多い順に 10 件取得してください。"
                    "出力列は workspace_id, workspace_name, open_ticket_count とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "workspaces(id bigint primary key, name text, plan_code text)\n"
                    "support_tickets(id bigint primary key, workspace_id bigint, status text, priority text, created_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("workspaces", 6400), ("support_tickets", 985000)),
                expected_focus="INNER JOIN, COUNT, WHERE, GROUP BY, ORDER BY, LIMIT",
                reference_sql=(
                    "SELECT w.id AS workspace_id, w.name AS workspace_name, "
                    "COUNT(*) AS open_ticket_count "
                    "FROM workspaces AS w "
                    "INNER JOIN support_tickets AS t ON t.workspace_id = w.id "
                    "WHERE t.status = 'open' "
                    "GROUP BY w.id, w.name "
                    "ORDER BY open_ticket_count DESC "
                    "LIMIT 10"
                ),
                grading_contract=_count_join_contract(
                    left="workspaces",
                    right="support_tickets",
                    predicate_columns=["status"],
                    group_by_columns=["id", "name"],
                    order_by_column="open_ticket_count",
                    limit=10,
                ),
            ),
            _ThemeVariant(
                topic_id="join-basics-course-completions",
                topic_title="講座完了件数",
                problem_statement=(
                    "学習サービスで、講座ごとの completed 受講件数を確認します。"
                    "完了件数の多い順に 8 件取得してください。"
                    "出力列は course_id, course_title, completion_count とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "courses(id bigint primary key, title text, category text)\n"
                    "course_completions(id bigint primary key, course_id bigint, user_id bigint, status text, completed_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("courses", 980), ("course_completions", 436000)),
                expected_focus="INNER JOIN, COUNT, WHERE, GROUP BY, ORDER BY, LIMIT",
                reference_sql=(
                    "SELECT c.id AS course_id, c.title AS course_title, "
                    "COUNT(*) AS completion_count "
                    "FROM courses AS c "
                    "INNER JOIN course_completions AS cc ON cc.course_id = c.id "
                    "WHERE cc.status = 'completed' "
                    "GROUP BY c.id, c.title "
                    "ORDER BY completion_count DESC "
                    "LIMIT 8"
                ),
                grading_contract=_count_join_contract(
                    left="courses",
                    right="course_completions",
                    predicate_columns=["status"],
                    group_by_columns=["id", "title"],
                    order_by_column="completion_count",
                    limit=8,
                ),
            ),
        ),
    ),
    _ThemeTemplate(
        family="left-join-counts",
        difficulty="beginner",
        business_domain="Cross-domain",
        target_skill="LEFT JOIN とゼロ件込み集計",
        title="LEFT JOIN でゼロ件込みの件数を出す",
        generation_prompt="LEFT JOIN を使って関連件数をゼロ件込みで集計する",
        variants=(
            _ThemeVariant(
                topic_id="left-join-plan-subscriptions",
                topic_title="プラン別subscription件数",
                problem_statement=(
                    "全プランについて、紐づく subscription 件数を 0 件も含めて表示してください。"
                    "出力列は plan_code, subscriber_count とし、plan_code 昇順に並べます。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "plans(id bigint primary key, plan_code text, is_active boolean)\n"
                    "subscriptions(id bigint primary key, plan_id bigint, account_id bigint, status text)\n"
                    "```"
                ),
                sample_data=_sample_rows(("plans", 12), ("subscriptions", 28600)),
                expected_focus="LEFT JOIN, COUNT(column), GROUP BY, ORDER BY",
                reference_sql=(
                    "SELECT p.plan_code, COUNT(s.id) AS subscriber_count "
                    "FROM plans AS p "
                    "LEFT JOIN subscriptions AS s ON s.plan_id = p.id "
                    "GROUP BY p.plan_code "
                    "ORDER BY p.plan_code ASC"
                ),
                grading_contract=_count_join_contract(
                    left="plans",
                    right="subscriptions",
                    predicate_columns=[],
                    group_by_columns=["plan_code"],
                    order_by_column="plan_code",
                    join_type="LEFT",
                    aggregate_column="id",
                    order_direction="ASC",
                ),
            ),
            _ThemeVariant(
                topic_id="left-join-category-products",
                topic_title="カテゴリ別product件数",
                problem_statement=(
                    "すべての category について、紐づく product 数をゼロ件も含めて出してください。"
                    "出力列は category_name, product_count とし、category_name 昇順に並べます。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "categories(id bigint primary key, name text)\n"
                    "products(id bigint primary key, category_id bigint, status text, published_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("categories", 180), ("products", 124000)),
                expected_focus="LEFT JOIN, COUNT(column), GROUP BY, ORDER BY",
                reference_sql=(
                    "SELECT c.name AS category_name, COUNT(p.id) AS product_count "
                    "FROM categories AS c "
                    "LEFT JOIN products AS p ON p.category_id = c.id "
                    "GROUP BY c.name "
                    "ORDER BY category_name ASC"
                ),
                grading_contract=_count_join_contract(
                    left="categories",
                    right="products",
                    predicate_columns=[],
                    group_by_columns=["name"],
                    order_by_column="category_name",
                    join_type="LEFT",
                    aggregate_column="id",
                    order_direction="ASC",
                ),
            ),
        ),
    ),
    _ThemeTemplate(
        family="aggregation-reporting",
        difficulty="intermediate",
        business_domain="Cross-domain",
        target_skill="SUM と集計レポート",
        title="集計レポートを組み立てる",
        generation_prompt="JOIN したデータから SUM 集計レポートを作る",
        variants=(
            _ThemeVariant(
                topic_id="aggregation-plan-revenue",
                topic_title="プラン別月次売上",
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
                sample_data=_sample_rows(("subscriptions", 8800), ("invoices", 211000)),
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
                grading_contract=_sum_join_contract(
                    left="subscriptions",
                    right="invoices",
                    predicate_columns=["billed_at"],
                    group_by_columns=["plan_code"],
                    aggregate_column="amount",
                    order_by_column="total_revenue",
                ),
            ),
            _ThemeVariant(
                topic_id="aggregation-region-ad-spend",
                topic_title="region別広告費",
                problem_statement=(
                    "広告運用チームが 2026-06 の region 別広告費を確認したいです。"
                    "出力列は region, spend_month, total_spend とし、"
                    "広告費の高い順に並べてください。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "campaigns(id bigint primary key, channel text, region text)\n"
                    "ad_spend(id bigint primary key, campaign_id bigint, spend_date date, amount numeric)\n"
                    "```"
                ),
                sample_data=_sample_rows(("campaigns", 4200), ("ad_spend", 1280000)),
                expected_focus="DATE_TRUNC, SUM, GROUP BY, ORDER BY",
                reference_sql=(
                    "SELECT c.region, DATE_TRUNC('month', s.spend_date) AS spend_month, "
                    "SUM(s.amount) AS total_spend "
                    "FROM campaigns AS c "
                    "INNER JOIN ad_spend AS s ON s.campaign_id = c.id "
                    "WHERE DATE_TRUNC('month', s.spend_date) = DATE '2026-06-01' "
                    "GROUP BY c.region, DATE_TRUNC('month', s.spend_date) "
                    "ORDER BY total_spend DESC"
                ),
                grading_contract=_sum_join_contract(
                    left="campaigns",
                    right="ad_spend",
                    predicate_columns=["spend_date"],
                    group_by_columns=["region"],
                    aggregate_column="amount",
                    order_by_column="total_spend",
                ),
            ),
            _ThemeVariant(
                topic_id="aggregation-country-payouts",
                topic_title="country別支払総額",
                problem_statement=(
                    "クリエイター向けサービスで、2026-01-01 以降の country 別支払総額を集計します。"
                    "出力列は country, total_payout とし、"
                    "支払総額の高い順に並べてください。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "creators(id bigint primary key, display_name text, country text)\n"
                    "payouts(id bigint primary key, creator_id bigint, paid_at date, amount numeric)\n"
                    "```"
                ),
                sample_data=_sample_rows(("creators", 38000), ("payouts", 592000)),
                expected_focus="SUM, WHERE, GROUP BY, ORDER BY",
                reference_sql=(
                    "SELECT c.country, SUM(p.amount) AS total_payout "
                    "FROM creators AS c "
                    "INNER JOIN payouts AS p ON p.creator_id = c.id "
                    "WHERE p.paid_at >= DATE '2026-01-01' "
                    "GROUP BY c.country "
                    "ORDER BY total_payout DESC"
                ),
                grading_contract=_sum_join_contract(
                    left="creators",
                    right="payouts",
                    predicate_columns=["paid_at"],
                    group_by_columns=["country"],
                    aggregate_column="amount",
                    order_by_column="total_payout",
                ),
            ),
        ),
    ),
    _ThemeTemplate(
        family="window-trends",
        difficulty="intermediate",
        business_domain="Cross-domain",
        target_skill="LAG と前回比較",
        title="LAG で前回値との差分を出す",
        generation_prompt="LAG を使って前回値との差分を出す",
        variants=(
            _ThemeVariant(
                topic_id="window-trends-plan-revenue-lag",
                topic_title="plan_code別前月売上",
                problem_statement=(
                    "plan_code ごとの月次売上テーブルがあります。"
                    "2026-04-01 以降について、前月売上を比較できるように previous_revenue を出してください。"
                    "出力列は plan_code, bill_month, total_revenue, previous_revenue とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "plan_revenue(plan_code text, bill_month date, total_revenue numeric)\n"
                    "```"
                ),
                sample_data=_sample_rows(("plan_revenue", 240)),
                expected_focus="CTE, LAG, PARTITION BY, ORDER BY",
                reference_sql=(
                    "WITH monthly_totals AS ("
                    "SELECT plan_code, bill_month, total_revenue, "
                    "LAG(total_revenue) OVER (PARTITION BY plan_code ORDER BY bill_month) AS previous_revenue "
                    "FROM plan_revenue "
                    "WHERE bill_month >= DATE '2026-04-01'"
                    ") "
                    "SELECT plan_code, bill_month, total_revenue, previous_revenue "
                    "FROM monthly_totals"
                ),
                grading_contract=_lag_contract(
                    table="plan_revenue",
                    predicate_columns=["bill_month"],
                    cte_name="monthly_totals",
                ),
            ),
            _ThemeVariant(
                topic_id="window-trends-warehouse-shipments-lag",
                topic_title="warehouse別前日出荷件数",
                problem_statement=(
                    "warehouse ごとの日次出荷件数があります。"
                    "2026-06-01 以降について、前日件数を比較できるように"
                    "warehouse_id, report_date, shipped_count, previous_shipped_count を返してください。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "warehouse_shipments(warehouse_id bigint, report_date date, shipped_count int)\n"
                    "```"
                ),
                sample_data=_sample_rows(("warehouse_shipments", 7200)),
                expected_focus="CTE, LAG, PARTITION BY, ORDER BY",
                reference_sql=(
                    "WITH shipment_trends AS ("
                    "SELECT warehouse_id, report_date, shipped_count, "
                    "LAG(shipped_count) OVER (PARTITION BY warehouse_id ORDER BY report_date) AS previous_shipped_count "
                    "FROM warehouse_shipments "
                    "WHERE report_date >= DATE '2026-06-01'"
                    ") "
                    "SELECT warehouse_id, report_date, shipped_count, previous_shipped_count "
                    "FROM shipment_trends"
                ),
                grading_contract=_lag_contract(
                    table="warehouse_shipments",
                    predicate_columns=["report_date"],
                    cte_name="shipment_trends",
                ),
            ),
        ),
    ),
    _ThemeTemplate(
        family="window-ranking",
        difficulty="intermediate",
        business_domain="Cross-domain",
        target_skill="ROW_NUMBER と CTE",
        title="ウィンドウ関数でランキングを作る",
        generation_prompt="ROW_NUMBER と CTE で 1 位だけを抽出する",
        variants=(
            _ThemeVariant(
                topic_id="window-ranking-department-sales",
                topic_title="department別売上1位",
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
                sample_data=_sample_rows(("sales_reps", 210), ("monthly_sales", 7560)),
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
                grading_contract=_window_contract(
                    left="sales_reps",
                    right="monthly_sales",
                    predicate_columns=["target_month"],
                    cte_name="ranked_sales",
                ),
            ),
            _ThemeVariant(
                topic_id="window-ranking-service-deployments",
                topic_title="service別最新成功deploy",
                problem_statement=(
                    "各 service について、status='success' の最新デプロイ 1 件だけを返してください。"
                    "出力には service_name, team, deployed_at, duration_seconds を含めます。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "services(id bigint primary key, name text, team text)\n"
                    "deployments(id bigint primary key, service_id bigint, status text, deployed_at timestamptz, duration_seconds int)\n"
                    "```"
                ),
                sample_data=_sample_rows(("services", 180), ("deployments", 92400)),
                expected_focus="ROW_NUMBER, PARTITION BY, ORDER BY, CTE",
                reference_sql=(
                    "WITH ranked_deployments AS ("
                    "SELECT s.name AS service_name, s.team, d.deployed_at, d.duration_seconds, "
                    "ROW_NUMBER() OVER (PARTITION BY s.id ORDER BY d.deployed_at DESC) AS rn "
                    "FROM services AS s "
                    "INNER JOIN deployments AS d ON d.service_id = s.id "
                    "WHERE d.status = 'success'"
                    ") "
                    "SELECT service_name, team, deployed_at, duration_seconds "
                    "FROM ranked_deployments "
                    "WHERE rn = 1"
                ),
                grading_contract=_window_contract(
                    left="services",
                    right="deployments",
                    predicate_columns=["status"],
                    cte_name="ranked_deployments",
                ),
            ),
            _ThemeVariant(
                topic_id="window-ranking-queue-agent-metrics",
                topic_title="queue別最速agent",
                problem_statement=(
                    "queue ごとに、report_date='2026-06-01' 時点で"
                    "avg_first_response_seconds が最も小さい agent を 1 名ずつ返してください。"
                    "出力には queue_name, region, agent_name, avg_first_response_seconds を含めます。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "queues(id bigint primary key, name text, region text)\n"
                    "ticket_metrics(id bigint primary key, queue_id bigint, agent_name text, avg_first_response_seconds numeric, report_date date)\n"
                    "```"
                ),
                sample_data=_sample_rows(("queues", 65), ("ticket_metrics", 14400)),
                expected_focus="ROW_NUMBER, PARTITION BY, ORDER BY, CTE",
                reference_sql=(
                    "WITH ranked_metrics AS ("
                    "SELECT q.name AS queue_name, q.region, m.agent_name, m.avg_first_response_seconds, "
                    "ROW_NUMBER() OVER (PARTITION BY q.id ORDER BY m.avg_first_response_seconds ASC) AS rn "
                    "FROM queues AS q "
                    "INNER JOIN ticket_metrics AS m ON m.queue_id = q.id "
                    "WHERE m.report_date = DATE '2026-06-01'"
                    ") "
                    "SELECT queue_name, region, agent_name, avg_first_response_seconds "
                    "FROM ranked_metrics "
                    "WHERE rn = 1"
                ),
                grading_contract=_window_contract(
                    left="queues",
                    right="ticket_metrics",
                    predicate_columns=["report_date"],
                    cte_name="ranked_metrics",
                ),
            ),
        ),
    ),
    _ThemeTemplate(
        family="plan-reading",
        difficulty="advanced",
        business_domain="Cross-domain",
        target_skill="EXPLAIN ANALYZE",
        title="実行計画を確認する SQL を書く",
        generation_prompt="実行計画と実測時間を見る EXPLAIN を 1 文で書く",
        variants=(
            _ThemeVariant(
                topic_id="plan-reading-events-account-created-at",
                topic_title="events検索の実行計画",
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
                sample_data=_sample_rows(("events", 8200000)),
                expected_focus="EXPLAIN ANALYZE, BUFFERS",
                reference_sql=(
                    "EXPLAIN (ANALYZE, BUFFERS) "
                    "SELECT * FROM events "
                    "WHERE account_id = 42 AND created_at >= DATE '2026-06-01'"
                ),
                grading_contract=_explain_contract(
                    table="events",
                    predicate_columns=["account_id", "created_at"],
                ),
            ),
            _ThemeVariant(
                topic_id="plan-reading-orders-account-status-created-at",
                topic_title="orders一覧の実行計画",
                problem_statement=(
                    "orders 一覧クエリが遅く、account_id と status で絞って"
                    "created_at の新しい順に 100 件返す処理を調べたいです。"
                    "まず実行計画と実測時間、バッファ使用状況を確認する 1 文を書いてください。\n\n"
                    "対象クエリ:\n"
                    "SELECT id, total_amount FROM orders "
                    "WHERE account_id = 9001 AND status = 'pending' "
                    "ORDER BY created_at DESC LIMIT 100"
                ),
                schema_markdown=(
                    "```sql\n"
                    "orders(id bigint primary key, account_id bigint, status text, total_amount numeric, created_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("orders", 14600000)),
                expected_focus="EXPLAIN ANALYZE, BUFFERS",
                reference_sql=(
                    "EXPLAIN (ANALYZE, BUFFERS) "
                    "SELECT id, total_amount FROM orders "
                    "WHERE account_id = 9001 AND status = 'pending' "
                    "ORDER BY created_at DESC LIMIT 100"
                ),
                grading_contract=_explain_contract(
                    table="orders",
                    predicate_columns=["account_id", "status"],
                    order_by_column="created_at",
                    limit=100,
                ),
            ),
            _ThemeVariant(
                topic_id="plan-reading-payments-merchant-paid-at",
                topic_title="payments検索の実行計画",
                problem_statement=(
                    "payments 検索クエリの実行計画を確認したいです。"
                    "merchant_id と paid_at 条件のクエリについて、"
                    "実行計画・実測時間・バッファ使用状況を確認する 1 文を書いてください。\n\n"
                    "対象クエリ:\n"
                    "SELECT * FROM payments "
                    "WHERE merchant_id = 77 "
                    "AND paid_at >= TIMESTAMPTZ '2026-05-01 00:00:00+00:00'"
                ),
                schema_markdown=(
                    "```sql\n"
                    "payments(id bigint primary key, merchant_id bigint, status text, paid_at timestamptz, amount numeric)\n"
                    "```"
                ),
                sample_data=_sample_rows(("payments", 23100000)),
                expected_focus="EXPLAIN ANALYZE, BUFFERS",
                reference_sql=(
                    "EXPLAIN (ANALYZE, BUFFERS) "
                    "SELECT * FROM payments "
                    "WHERE merchant_id = 77 "
                    "AND paid_at >= TIMESTAMPTZ '2026-05-01 00:00:00+00:00'"
                ),
                grading_contract=_explain_contract(
                    table="payments",
                    predicate_columns=["merchant_id", "paid_at"],
                ),
            ),
        ),
    ),
    _ThemeTemplate(
        family="slow-query-diagnosis",
        difficulty="advanced",
        business_domain="Cross-domain",
        target_skill="条件整理と並び順最適化",
        title="スロークエリの取得条件を整理する",
        generation_prompt="WHERE, ORDER BY, LIMIT を揃えて取得クエリを作る",
        variants=(
            _ThemeVariant(
                topic_id="slow-query-application-logs",
                topic_title="ERRORログ取得",
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
                sample_data=_sample_rows(("application_logs", 42000000)),
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
                    "required_predicate_columns": ["service_name", "level"],
                    "required_order_by": [{"column": "created_at", "direction": "DESC"}],
                    "required_limit": 50,
                },
            ),
            _ThemeVariant(
                topic_id="slow-query-api-requests",
                topic_title="5xx APIリクエスト取得",
                problem_statement=(
                    "API 監視テーブルから、endpoint='/v1/orders' かつ status_code が 500 以上のリクエストを"
                    "新しい順に 100 件確認したいです。"
                    "条件と並び順を明示した 1 文を書いてください。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "api_requests(id bigint primary key, endpoint text, status_code int, latency_ms int, requested_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("api_requests", 68000000)),
                expected_focus="WHERE, ORDER BY, LIMIT",
                reference_sql=(
                    "SELECT id, endpoint, status_code, latency_ms, requested_at "
                    "FROM api_requests "
                    "WHERE endpoint = '/v1/orders' AND status_code >= 500 "
                    "ORDER BY requested_at DESC "
                    "LIMIT 100"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["api_requests"],
                    "required_predicate_columns": ["endpoint", "status_code"],
                    "required_order_by": [{"column": "requested_at", "direction": "DESC"}],
                    "required_limit": 100,
                },
            ),
            _ThemeVariant(
                topic_id="slow-query-webhook-deliveries",
                topic_title="webhook retry取得",
                problem_statement=(
                    "webhook 配信のリトライ対象を確認します。"
                    "integration_id=55 かつ status='retrying' の配信を"
                    "次の再試行時刻が早い順に 20 件取得してください。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "webhook_deliveries(id bigint primary key, integration_id bigint, status text, next_retry_at timestamptz, created_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("webhook_deliveries", 14800000)),
                expected_focus="WHERE, ORDER BY, LIMIT",
                reference_sql=(
                    "SELECT id, integration_id, status, next_retry_at, created_at "
                    "FROM webhook_deliveries "
                    "WHERE integration_id = 55 AND status = 'retrying' "
                    "ORDER BY next_retry_at ASC "
                    "LIMIT 20"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["webhook_deliveries"],
                    "required_predicate_columns": ["integration_id", "status"],
                    "required_order_by": [{"column": "next_retry_at", "direction": "ASC"}],
                    "required_limit": 20,
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="index-design",
        difficulty="advanced",
        business_domain="Cross-domain",
        target_skill="複合インデックス設計",
        title="アクセスパターンに合う複合インデックスを設計する",
        generation_prompt="絞り込み条件と並び順に合う CREATE INDEX を書く",
        variants=(
            _ThemeVariant(
                topic_id="index-design-items-seller-status-updated-at",
                topic_title="items複合インデックス",
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
                sample_data=_sample_rows(("items", 13500000)),
                expected_focus="CREATE INDEX, 複合インデックスの列順",
                reference_sql=(
                    "CREATE INDEX idx_items_seller_status_updated_at "
                    "ON items (seller_id, status, updated_at DESC)"
                ),
                grading_contract=_index_contract(
                    table="items",
                    columns=["seller_id", "status", "updated_at"],
                    desc_column="updated_at",
                ),
            ),
            _ThemeVariant(
                topic_id="index-design-orders-account-status-created-at",
                topic_title="orders複合インデックス",
                problem_statement=(
                    "orders テーブルで `account_id = ? AND status = 'pending'` で絞り込み、"
                    "`created_at DESC` で最近の注文を取得するクエリが多いです。"
                    "この用途を意識した PostgreSQL のインデックスを 1 文で作成してください。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "orders(id bigint primary key, account_id bigint, status text, total_amount numeric, created_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("orders", 14600000)),
                expected_focus="CREATE INDEX, 複合インデックスの列順",
                reference_sql=(
                    "CREATE INDEX idx_orders_account_status_created_at "
                    "ON orders (account_id, status, created_at DESC)"
                ),
                grading_contract=_index_contract(
                    table="orders",
                    columns=["account_id", "status", "created_at"],
                    desc_column="created_at",
                ),
            ),
            _ThemeVariant(
                topic_id="index-design-api-requests-workspace-endpoint-requested-at",
                topic_title="api_requests複合インデックス",
                problem_statement=(
                    "api_requests テーブルで `workspace_id = ? AND endpoint = ?` で絞り込み、"
                    "`requested_at DESC` で最近のアクセスを確認する処理があります。"
                    "このアクセスパターンに合う PostgreSQL のインデックスを 1 文で作成してください。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "api_requests(id bigint primary key, workspace_id bigint, endpoint text, requested_at timestamptz, status_code int)\n"
                    "```"
                ),
                sample_data=_sample_rows(("api_requests", 68000000)),
                expected_focus="CREATE INDEX, 複合インデックスの列順",
                reference_sql=(
                    "CREATE INDEX idx_api_requests_workspace_endpoint_requested_at "
                    "ON api_requests (workspace_id, endpoint, requested_at DESC)"
                ),
                grading_contract=_index_contract(
                    table="api_requests",
                    columns=["workspace_id", "endpoint", "requested_at"],
                    desc_column="requested_at",
                ),
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
                "variant_count": len(theme.variants),
                "attempt_count": 0,
                "best_score": None,
                "last_attempted_at": None,
                "topics": [
                    self._topic_summary(theme, variant)
                    for variant in theme.variants
                ],
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
        topic_id: str | None = None,
    ) -> SqlDojoProblem:
        if topic_id is not None:
            theme, variant = self._find_topic(topic_id)
            return self._problem_from_variant(theme, variant)

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
        return self._problem_from_variant(theme, variant)

    @staticmethod
    def _topic_summary(
        theme: _ThemeTemplate,
        variant: _ThemeVariant,
    ) -> SqlDojoTopicSummary:
        return {
            "topic_id": variant.topic_id,
            "topic_title": variant.topic_title,
            "family": theme.family,
            "difficulty": theme.difficulty,
            "business_domain": theme.business_domain,
            "target_skill": theme.target_skill,
            "attempt_count": 0,
            "best_score": None,
            "last_attempted_at": None,
        }

    @staticmethod
    def _find_topic(topic_id: str) -> tuple[_ThemeTemplate, _ThemeVariant]:
        for theme in _THEMES:
            for variant in theme.variants:
                if variant.topic_id == topic_id:
                    return theme, variant
        msg = f"No SQL dojo topic for topic_id={topic_id!r}"
        raise SqlDojoGenerationError(
            error_code="topic_not_found",
            message=msg,
        )

    @staticmethod
    def _problem_from_variant(
        theme: _ThemeTemplate,
        variant: _ThemeVariant,
    ) -> SqlDojoProblem:
        return {
            "family": theme.family,
            "topic_id": variant.topic_id,
            "topic_title": variant.topic_title,
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
