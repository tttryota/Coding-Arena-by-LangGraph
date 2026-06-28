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
    _ThemeTemplate(
        family="conditional-aggregation",
        difficulty="intermediate",
        business_domain="Analytics",
        target_skill="CASE WHEN と条件付き集計",
        title="条件付き集計で実務レポートを作る",
        generation_prompt="CASE WHEN, FILTER, ratio を使った集計を作る",
        variants=(
            _ThemeVariant(
                topic_id="case-when-paid-amount",
                topic_title="paid売上の条件付き集計",
                problem_statement=(
                    "請求テーブルから account ごとの paid 売上だけを集計してください。"
                    "status='paid' の amount だけを足し、出力列は account_id, paid_amount とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "invoices(id bigint primary key, account_id bigint, status text, amount numeric, issued_at date)\n"
                    "```"
                ),
                sample_data=_sample_rows(("invoices", 430000)),
                expected_focus="SUM, CASE WHEN, GROUP BY",
                reference_sql=(
                    "SELECT account_id, "
                    "SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) AS paid_amount "
                    "FROM invoices "
                    "GROUP BY account_id"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["invoices"],
                    "required_group_by_columns": ["account_id"],
                    "required_aggregates": [{"function": "SUM", "column": "*"}],
                    "required_case": True,
                },
            ),
            _ThemeVariant(
                topic_id="case-when-user-buckets",
                topic_title="利用頻度bucket分類",
                problem_statement=(
                    "user_activity の event_count を利用頻度帯に分類してください。"
                    "100以上を 'power', 10以上を 'active', それ以外を 'light' とし、"
                    "出力列は user_id, usage_bucket とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "user_activity(user_id bigint primary key, event_count int, last_seen_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("user_activity", 920000)),
                expected_focus="CASE WHEN, bucket 分類",
                reference_sql=(
                    "SELECT user_id, "
                    "CASE "
                    "WHEN event_count >= 100 THEN 'power' "
                    "WHEN event_count >= 10 THEN 'active' "
                    "ELSE 'light' END AS usage_bucket "
                    "FROM user_activity"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["user_activity"],
                    "required_case": True,
                },
            ),
            _ThemeVariant(
                topic_id="filter-error-rate",
                topic_title="FILTERでerror rate算出",
                problem_statement=(
                    "api_requests から endpoint ごとの総リクエスト数と 5xx 件数を出してください。"
                    "5xx 件数は FILTER (WHERE ...) を使い、error_rate も計算します。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "api_requests(id bigint primary key, endpoint text, status_code int, requested_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("api_requests", 68000000)),
                expected_focus="COUNT FILTER, NULLIF, ratio",
                reference_sql=(
                    "SELECT endpoint, "
                    "COUNT(*) AS request_count, "
                    "COUNT(*) FILTER (WHERE status_code >= 500) AS error_count, "
                    "COUNT(*) FILTER (WHERE status_code >= 500)::numeric / NULLIF(COUNT(*), 0) AS error_rate "
                    "FROM api_requests "
                    "GROUP BY endpoint"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["api_requests"],
                    "required_group_by_columns": ["endpoint"],
                    "required_filter_aggregates": [{"function": "COUNT", "column": "*"}],
                    "required_functions": ["NULLIF"],
                    "required_predicate_columns": ["status_code"],
                },
            ),
            _ThemeVariant(
                topic_id="pivot-order-status-counts",
                topic_title="status別注文件数の横持ち集計",
                problem_statement=(
                    "orders を account_id ごとに status 別件数で横持ち集計してください。"
                    "出力列は account_id, pending_count, paid_count, cancelled_count とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "orders(id bigint primary key, account_id bigint, status text, created_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("orders", 14600000)),
                expected_focus="SUM, CASE WHEN, pivot 風集計",
                reference_sql=(
                    "SELECT account_id, "
                    "SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending_count, "
                    "SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) AS paid_count, "
                    "SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_count "
                    "FROM orders "
                    "GROUP BY account_id"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["orders"],
                    "required_group_by_columns": ["account_id"],
                    "required_aggregates": [{"function": "SUM", "column": "*"}],
                    "required_case": True,
                },
            ),
            _ThemeVariant(
                topic_id="ratio-cancellation-rate",
                topic_title="cancellation rate算出",
                problem_statement=(
                    "orders から account_id ごとの cancellation_rate を算出してください。"
                    "cancelled 件数を総件数で割り、0除算を避けてください。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "orders(id bigint primary key, account_id bigint, status text, created_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("orders", 14600000)),
                expected_focus="CASE WHEN, NULLIF, ratio",
                reference_sql=(
                    "SELECT account_id, "
                    "SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END)::numeric "
                    "/ NULLIF(COUNT(*), 0) AS cancellation_rate "
                    "FROM orders "
                    "GROUP BY account_id"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["orders"],
                    "required_group_by_columns": ["account_id"],
                    "required_aggregates": [
                        {"function": "SUM", "column": "*"},
                        {"function": "COUNT", "column": "*"},
                    ],
                    "required_case": True,
                    "required_functions": ["NULLIF"],
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="null-handling",
        difficulty="beginner",
        business_domain="Product",
        target_skill="NULL 処理",
        title="NULL を安全に扱う",
        generation_prompt="COALESCE, NULLIF, IS DISTINCT FROM を使う",
        variants=(
            _ThemeVariant(
                topic_id="coalesce-profile-display-name",
                topic_title="表示名fallback",
                problem_statement=(
                    "profiles の display_name が NULL の場合は email を表示名にしてください。"
                    "出力列は user_id, visible_name とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "profiles(user_id bigint primary key, display_name text, email text)\n"
                    "```"
                ),
                sample_data=_sample_rows(("profiles", 850000)),
                expected_focus="COALESCE",
                reference_sql=(
                    "SELECT user_id, COALESCE(display_name, email) AS visible_name "
                    "FROM profiles"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["profiles"],
                    "required_functions": ["COALESCE"],
                },
            ),
            _ThemeVariant(
                topic_id="nullif-division-safe-rate",
                topic_title="0除算回避のrate計算",
                problem_statement=(
                    "campaign_metrics から campaign_id ごとの conversion_rate を計算してください。"
                    "clicks が 0 の場合に 0除算しないようにします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "campaign_metrics(campaign_id bigint primary key, clicks int, conversions int)\n"
                    "```"
                ),
                sample_data=_sample_rows(("campaign_metrics", 120000)),
                expected_focus="NULLIF, rate 計算",
                reference_sql=(
                    "SELECT campaign_id, conversions::numeric / NULLIF(clicks, 0) AS conversion_rate "
                    "FROM campaign_metrics"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["campaign_metrics"],
                    "required_functions": ["NULLIF"],
                },
            ),
            _ThemeVariant(
                topic_id="is-distinct-from-sync-diff",
                topic_title="NULL安全な差分検出",
                problem_statement=(
                    "crm_contacts と warehouse_contacts の email を比較し、"
                    "NULL を安全に扱って差分がある contact_id を抽出してください。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "crm_contacts(contact_id bigint primary key, email text)\n"
                    "warehouse_contacts(contact_id bigint primary key, email text)\n"
                    "```"
                ),
                sample_data=_sample_rows(("crm_contacts", 420000), ("warehouse_contacts", 420000)),
                expected_focus="IS DISTINCT FROM, JOIN",
                reference_sql=(
                    "SELECT c.contact_id "
                    "FROM crm_contacts AS c "
                    "INNER JOIN warehouse_contacts AS w ON w.contact_id = c.contact_id "
                    "WHERE c.email IS DISTINCT FROM w.email"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["crm_contacts", "warehouse_contacts"],
                    "required_joins": [{"left": "crm_contacts", "right": "warehouse_contacts", "join_type": "INNER"}],
                    "required_functions": ["IS DISTINCT FROM"],
                    "required_predicate_columns": ["email"],
                    "prohibited_patterns": ["implicit_join"],
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="date-time-reporting",
        difficulty="intermediate",
        business_domain="Analytics",
        target_skill="日付処理と期間集計",
        title="日付を丸めて期間レポートを作る",
        generation_prompt="date_trunc, 期間条件, rolling window を使う",
        variants=(
            _ThemeVariant(
                topic_id="date-trunc-monthly-revenue",
                topic_title="月次売上集計",
                problem_statement=(
                    "payments から月次売上を集計してください。"
                    "2026年以降を対象に、出力列は revenue_month, total_revenue とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "payments(id bigint primary key, paid_at timestamptz, amount numeric, status text)\n"
                    "```"
                ),
                sample_data=_sample_rows(("payments", 23100000)),
                expected_focus="DATE_TRUNC, SUM, GROUP BY",
                reference_sql=(
                    "SELECT DATE_TRUNC('month', paid_at) AS revenue_month, "
                    "SUM(amount) AS total_revenue "
                    "FROM payments "
                    "WHERE paid_at >= TIMESTAMPTZ '2026-01-01 00:00:00+00:00' "
                    "GROUP BY DATE_TRUNC('month', paid_at) "
                    "ORDER BY revenue_month ASC"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["payments"],
                    "required_functions": ["DATE_TRUNC"],
                    "required_predicate_columns": ["paid_at"],
                    "required_aggregates": [{"function": "SUM", "column": "amount"}],
                    "required_order_by": [{"column": "revenue_month", "direction": "ASC"}],
                },
            ),
            _ThemeVariant(
                topic_id="date-range-weekly-active-users",
                topic_title="期間指定WAU",
                problem_statement=(
                    "user_events から 2026-06-01 以降の weekly active users を週ごとに集計してください。"
                    "出力列は week_start, active_users とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "user_events(id bigint primary key, user_id bigint, event_name text, occurred_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("user_events", 125000000)),
                expected_focus="DATE_TRUNC, COUNT DISTINCT, 期間条件",
                reference_sql=(
                    "SELECT DATE_TRUNC('week', occurred_at) AS week_start, "
                    "COUNT(DISTINCT user_id) AS active_users "
                    "FROM user_events "
                    "WHERE occurred_at >= TIMESTAMPTZ '2026-06-01 00:00:00+00:00' "
                    "GROUP BY DATE_TRUNC('week', occurred_at) "
                    "ORDER BY week_start ASC"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["user_events"],
                    "required_functions": ["DATE_TRUNC", "COUNT"],
                    "required_predicate_columns": ["occurred_at"],
                    "required_order_by": [{"column": "week_start", "direction": "ASC"}],
                },
            ),
            _ThemeVariant(
                topic_id="rolling-7day-orders",
                topic_title="7日移動注文数",
                problem_statement=(
                    "daily_orders から日別注文数と7日移動合計を出してください。"
                    "出力列は order_date, order_count, rolling_7day_orders とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "daily_orders(order_date date primary key, order_count int)\n"
                    "```"
                ),
                sample_data=_sample_rows(("daily_orders", 1460)),
                expected_focus="SUM OVER, ROWS BETWEEN",
                reference_sql=(
                    "SELECT order_date, order_count, "
                    "SUM(order_count) OVER (ORDER BY order_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS rolling_7day_orders "
                    "FROM daily_orders "
                    "ORDER BY order_date ASC"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["daily_orders"],
                    "required_window_functions": ["SUM"],
                    "required_order_by": [{"column": "order_date", "direction": "ASC"}],
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="dedup-latest-row",
        difficulty="intermediate",
        business_domain="Product",
        target_skill="重複排除と最新行取得",
        title="重複を排除して代表行を取る",
        generation_prompt="DISTINCT, DISTINCT ON, 最新1件取得を使う",
        variants=(
            _ThemeVariant(
                topic_id="distinct-email-domains",
                topic_title="重複排除したdomain抽出",
                problem_statement=(
                    "users の email から domain を抽出し、重複なしで一覧化してください。"
                    "出力列は email_domain とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "users(id bigint primary key, email text, created_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("users", 2200000)),
                expected_focus="DISTINCT, SPLIT_PART",
                reference_sql=(
                    "SELECT DISTINCT SPLIT_PART(email, '@', 2) AS email_domain "
                    "FROM users "
                    "WHERE email IS NOT NULL"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["users"],
                    "required_functions": ["SPLIT_PART"],
                    "required_predicate_columns": ["email"],
                },
            ),
            _ThemeVariant(
                topic_id="distinct-on-latest-login",
                topic_title="user別最新login",
                problem_statement=(
                    "login_events から user_id ごとの最新ログイン1件を取得してください。"
                    "PostgreSQL の DISTINCT ON を使い、出力列は user_id, logged_in_at, ip_address とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "login_events(id bigint primary key, user_id bigint, logged_in_at timestamptz, ip_address inet)\n"
                    "```"
                ),
                sample_data=_sample_rows(("login_events", 9800000)),
                expected_focus="DISTINCT ON, ORDER BY",
                reference_sql=(
                    "SELECT DISTINCT ON (user_id) user_id, logged_in_at, ip_address "
                    "FROM login_events "
                    "ORDER BY user_id, logged_in_at DESC"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["login_events"],
                    "required_distinct_on": ["user_id"],
                    "required_order_by": [
                        {"column": "user_id", "direction": "ASC"},
                        {"column": "logged_in_at", "direction": "DESC"},
                    ],
                },
            ),
            _ThemeVariant(
                topic_id="latest-order-per-account",
                topic_title="account別最新注文",
                problem_statement=(
                    "orders から account_id ごとの最新注文1件を取得してください。"
                    "DISTINCT ON を使い、出力列は account_id, order_id, created_at とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "orders(id bigint primary key, account_id bigint, created_at timestamptz, total_amount numeric)\n"
                    "```"
                ),
                sample_data=_sample_rows(("orders", 14600000)),
                expected_focus="DISTINCT ON, ORDER BY DESC",
                reference_sql=(
                    "SELECT DISTINCT ON (account_id) account_id, id AS order_id, created_at "
                    "FROM orders "
                    "ORDER BY account_id, created_at DESC"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["orders"],
                    "required_distinct_on": ["account_id"],
                    "required_order_by": [
                        {"column": "account_id", "direction": "ASC"},
                        {"column": "created_at", "direction": "DESC"},
                    ],
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="exists-subquery",
        difficulty="intermediate",
        business_domain="Cross-domain",
        target_skill="EXISTS / NOT EXISTS",
        title="関連レコードの存在有無で抽出する",
        generation_prompt="EXISTS, NOT EXISTS, semi join, anti join を使う",
        variants=(
            _ThemeVariant(
                topic_id="exists-active-subscription",
                topic_title="active subscriptionありuser",
                problem_statement=(
                    "users から active な subscription を持つ user だけを抽出してください。"
                    "EXISTS を使い、出力列は id, email とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "users(id bigint primary key, email text)\n"
                    "subscriptions(id bigint primary key, user_id bigint, status text)\n"
                    "```"
                ),
                sample_data=_sample_rows(("users", 2200000), ("subscriptions", 860000)),
                expected_focus="EXISTS, correlated subquery",
                reference_sql=(
                    "SELECT u.id, u.email "
                    "FROM users AS u "
                    "WHERE EXISTS ("
                    "SELECT 1 FROM subscriptions AS s "
                    "WHERE s.user_id = u.id AND s.status = 'active'"
                    ")"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["users", "subscriptions"],
                    "required_exists": True,
                    "required_predicate_columns": ["status", "user_id"],
                },
            ),
            _ThemeVariant(
                topic_id="not-exists-unpaid-invoices",
                topic_title="未払いinvoiceなしaccount",
                problem_statement=(
                    "accounts から unpaid invoice が存在しない account を抽出してください。"
                    "NOT EXISTS を使い、出力列は id, name とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "accounts(id bigint primary key, name text)\n"
                    "invoices(id bigint primary key, account_id bigint, status text)\n"
                    "```"
                ),
                sample_data=_sample_rows(("accounts", 180000), ("invoices", 430000)),
                expected_focus="NOT EXISTS, anti semi join",
                reference_sql=(
                    "SELECT a.id, a.name "
                    "FROM accounts AS a "
                    "WHERE NOT EXISTS ("
                    "SELECT 1 FROM invoices AS i "
                    "WHERE i.account_id = a.id AND i.status = 'unpaid'"
                    ")"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["accounts", "invoices"],
                    "required_not_exists": True,
                    "required_predicate_columns": ["account_id", "status"],
                },
            ),
            _ThemeVariant(
                topic_id="anti-join-no-purchase-users",
                topic_title="未購入user抽出",
                problem_statement=(
                    "users から一度も purchase がない user を抽出してください。"
                    "NOT EXISTS を使い、出力列は id, email とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "users(id bigint primary key, email text)\n"
                    "purchases(id bigint primary key, user_id bigint, purchased_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("users", 2200000), ("purchases", 9300000)),
                expected_focus="NOT EXISTS, anti join",
                reference_sql=(
                    "SELECT u.id, u.email "
                    "FROM users AS u "
                    "WHERE NOT EXISTS ("
                    "SELECT 1 FROM purchases AS p WHERE p.user_id = u.id"
                    ")"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["users", "purchases"],
                    "required_not_exists": True,
                    "required_predicate_columns": ["user_id"],
                },
            ),
            _ThemeVariant(
                topic_id="semi-join-has-successful-payment",
                topic_title="成功決済ありorder抽出",
                problem_statement=(
                    "orders から successful payment がある注文だけを抽出してください。"
                    "EXISTS を使い、出力列は id, account_id とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "orders(id bigint primary key, account_id bigint)\n"
                    "payments(id bigint primary key, order_id bigint, status text)\n"
                    "```"
                ),
                sample_data=_sample_rows(("orders", 14600000), ("payments", 23100000)),
                expected_focus="EXISTS, semi join",
                reference_sql=(
                    "SELECT o.id, o.account_id "
                    "FROM orders AS o "
                    "WHERE EXISTS ("
                    "SELECT 1 FROM payments AS p "
                    "WHERE p.order_id = o.id AND p.status = 'successful'"
                    ")"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["orders", "payments"],
                    "required_exists": True,
                    "required_predicate_columns": ["order_id", "status"],
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="post-aggregation-filter",
        difficulty="beginner",
        business_domain="Analytics",
        target_skill="HAVING",
        title="集計後に HAVING で絞り込む",
        generation_prompt="GROUP BY 後の条件を HAVING で書く",
        variants=(
            _ThemeVariant(
                topic_id="having-repeat-buyers",
                topic_title="複数購入者抽出",
                problem_statement=(
                    "purchases から2回以上購入した user_id を抽出してください。"
                    "出力列は user_id, purchase_count とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "purchases(id bigint primary key, user_id bigint, purchased_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("purchases", 9300000)),
                expected_focus="GROUP BY, HAVING, COUNT",
                reference_sql=(
                    "SELECT user_id, COUNT(*) AS purchase_count "
                    "FROM purchases "
                    "GROUP BY user_id "
                    "HAVING COUNT(*) >= 2"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["purchases"],
                    "required_group_by_columns": ["user_id"],
                    "required_aggregates": [{"function": "COUNT", "column": "*"}],
                    "required_having_columns": ["*"],
                },
            ),
            _ThemeVariant(
                topic_id="having-high-value-accounts",
                topic_title="集計後の高額account抽出",
                problem_statement=(
                    "invoices から2026年以降の合計請求額が 100000 以上の account を抽出してください。"
                    "出力列は account_id, total_amount とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "invoices(id bigint primary key, account_id bigint, amount numeric, issued_at date)\n"
                    "```"
                ),
                sample_data=_sample_rows(("invoices", 430000)),
                expected_focus="SUM, GROUP BY, HAVING",
                reference_sql=(
                    "SELECT account_id, SUM(amount) AS total_amount "
                    "FROM invoices "
                    "WHERE issued_at >= DATE '2026-01-01' "
                    "GROUP BY account_id "
                    "HAVING SUM(amount) >= 100000"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["invoices"],
                    "required_predicate_columns": ["issued_at"],
                    "required_group_by_columns": ["account_id"],
                    "required_aggregates": [{"function": "SUM", "column": "amount"}],
                    "required_having_columns": ["amount"],
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="basic-filtering",
        difficulty="beginner",
        business_domain="Cross-domain",
        target_skill="WHERE の代表パターン",
        title="WHERE の代表パターンで絞り込む",
        generation_prompt="IN, BETWEEN, LIKE/ILIKE の基本を使う",
        variants=(
            _ThemeVariant(
                topic_id="where-status-in-orders",
                topic_title="status IN で注文抽出",
                problem_statement=(
                    "orders から status が shipped または delivered の注文を抽出してください。"
                    "出力列は id, status, created_at とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "orders(id bigint primary key, status text, created_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("orders", 14600000)),
                expected_focus="WHERE, IN, ORDER BY",
                reference_sql=(
                    "SELECT id, status, created_at "
                    "FROM orders "
                    "WHERE status IN ('shipped', 'delivered') "
                    "ORDER BY created_at DESC"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["orders"],
                    "required_predicate_columns": ["status"],
                    "required_predicate_patterns": ["IN"],
                    "required_order_by": [{"column": "created_at", "direction": "DESC"}],
                },
            ),
            _ThemeVariant(
                topic_id="between-issued-at-invoices",
                topic_title="BETWEEN で期間絞り込み",
                problem_statement=(
                    "invoices から 2026-04-01 から 2026-04-30 までに発行された請求だけを抽出してください。"
                    "出力列は id, account_id, issued_at, amount とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "invoices(id bigint primary key, account_id bigint, issued_at date, amount numeric)\n"
                    "```"
                ),
                sample_data=_sample_rows(("invoices", 430000)),
                expected_focus="WHERE, BETWEEN, ORDER BY",
                reference_sql=(
                    "SELECT id, account_id, issued_at, amount "
                    "FROM invoices "
                    "WHERE issued_at BETWEEN DATE '2026-04-01' AND DATE '2026-04-30' "
                    "ORDER BY issued_at ASC"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["invoices"],
                    "required_predicate_columns": ["issued_at"],
                    "required_predicate_patterns": ["BETWEEN"],
                    "required_order_by": [{"column": "issued_at", "direction": "ASC"}],
                },
            ),
            _ThemeVariant(
                topic_id="like-customer-search",
                topic_title="ILIKE で顧客検索",
                problem_statement=(
                    "customers から name に 'shop' を含む顧客を抽出してください。"
                    "大文字小文字は区別しません。出力列は id, name とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "customers(id bigint primary key, name text, segment text)\n"
                    "```"
                ),
                sample_data=_sample_rows(("customers", 12500)),
                expected_focus="WHERE, ILIKE",
                reference_sql=(
                    "SELECT id, name "
                    "FROM customers "
                    "WHERE name ILIKE '%shop%'"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["customers"],
                    "required_predicate_columns": ["name"],
                    "required_predicate_patterns": ["ILIKE"],
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="distinct-and-derived-columns",
        difficulty="beginner",
        business_domain="Cross-domain",
        target_skill="DISTINCT と派生列",
        title="DISTINCT と派生列を作る",
        generation_prompt="DISTINCT と簡単な計算式・文字列式を SELECT に載せる",
        variants=(
            _ThemeVariant(
                topic_id="distinct-customer-emails",
                topic_title="重複なし email 一覧",
                problem_statement=(
                    "crm_contacts から重複しない email 一覧を抽出してください。"
                    "出力列は email とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "crm_contacts(id bigint primary key, email text, company_name text)\n"
                    "```"
                ),
                sample_data=_sample_rows(("crm_contacts", 580000)),
                expected_focus="SELECT DISTINCT, ORDER BY",
                reference_sql=(
                    "SELECT DISTINCT email "
                    "FROM crm_contacts "
                    "ORDER BY email ASC"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["crm_contacts"],
                    "required_sql_fragments": ["SELECT DISTINCT email"],
                    "required_order_by": [{"column": "email", "direction": "ASC"}],
                },
            ),
            _ThemeVariant(
                topic_id="price-with-tax",
                topic_title="税込価格の派生列",
                problem_statement=(
                    "products から price に 10% の税を乗せた taxed_price を出してください。"
                    "出力列は id, name, taxed_price とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "products(id bigint primary key, name text, price numeric, category_id bigint)\n"
                    "```"
                ),
                sample_data=_sample_rows(("products", 860000)),
                expected_focus="算術式, alias",
                reference_sql=(
                    "SELECT id, name, price * 1.1 AS taxed_price "
                    "FROM products"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["products"],
                    "required_sql_fragments": ["price * 1.1 AS taxed_price"],
                },
            ),
            _ThemeVariant(
                topic_id="display-name-expression",
                topic_title="文字列結合の表示名",
                problem_statement=(
                    "profiles から first_name と last_name を結合した display_name を作ってください。"
                    "出力列は user_id, display_name とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "profiles(user_id bigint primary key, first_name text, last_name text, email text)\n"
                    "```"
                ),
                sample_data=_sample_rows(("profiles", 850000)),
                expected_focus="文字列結合, alias",
                reference_sql=(
                    "SELECT user_id, first_name || ' ' || last_name AS display_name "
                    "FROM profiles"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["profiles"],
                    "required_sql_fragments": ["first_name || ' ' || last_name AS display_name"],
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="join-variants",
        difficulty="intermediate",
        business_domain="Operations",
        target_skill="RIGHT/FULL JOIN",
        title="外部結合のバリエーションを使い分ける",
        generation_prompt="RIGHT JOIN と FULL OUTER JOIN を使う",
        variants=(
            _ThemeVariant(
                topic_id="right-join-unassigned-records",
                topic_title="RIGHT JOIN で未アサインも含める",
                problem_statement=(
                    "agents と tickets を結合し、すべての ticket を残したまま担当 agent 名を表示してください。"
                    "RIGHT JOIN を使い、出力列は ticket_id, agent_name とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "agents(id bigint primary key, name text)\n"
                    "tickets(id bigint primary key, agent_id bigint, status text)\n"
                    "```"
                ),
                sample_data=_sample_rows(("agents", 2400), ("tickets", 185000)),
                expected_focus="RIGHT JOIN",
                reference_sql=(
                    "SELECT t.id AS ticket_id, a.name AS agent_name "
                    "FROM agents AS a "
                    "RIGHT JOIN tickets AS t ON t.agent_id = a.id"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["agents", "tickets"],
                    "required_joins": [{"left": "agents", "right": "tickets", "join_type": "RIGHT"}],
                },
            ),
            _ThemeVariant(
                topic_id="full-join-ledger-reconciliation",
                topic_title="FULL JOIN で突合差分を見る",
                problem_statement=(
                    "billing_ledger と payout_ledger を transaction_id で突合し、"
                    "片側だけにある transaction も含めて一覧化してください。"
                    "出力列は transaction_id, billing_amount, payout_amount とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "billing_ledger(transaction_id text primary key, amount numeric)\n"
                    "payout_ledger(transaction_id text primary key, amount numeric)\n"
                    "```"
                ),
                sample_data=_sample_rows(("billing_ledger", 1800000), ("payout_ledger", 1795000)),
                expected_focus="FULL OUTER JOIN",
                reference_sql=(
                    "SELECT COALESCE(b.transaction_id, p.transaction_id) AS transaction_id, "
                    "b.amount AS billing_amount, p.amount AS payout_amount "
                    "FROM billing_ledger AS b "
                    "FULL OUTER JOIN payout_ledger AS p ON p.transaction_id = b.transaction_id"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["billing_ledger", "payout_ledger"],
                    "required_joins": [{"left": "billing_ledger", "right": "payout_ledger", "join_type": "FULL"}],
                    "required_functions": ["COALESCE"],
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="set-operations",
        difficulty="intermediate",
        business_domain="Analytics",
        target_skill="集合演算",
        title="集合演算で結果集合を組み立てる",
        generation_prompt="UNION, UNION ALL, INTERSECT, EXCEPT を使う",
        variants=(
            _ThemeVariant(
                topic_id="union-all-event-streams",
                topic_title="UNION ALL でイベント連結",
                problem_statement=(
                    "web_events と mobile_events の event_id, occurred_at をまとめて時系列で出してください。"
                    "UNION ALL を使います。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "web_events(event_id bigint primary key, occurred_at timestamptz)\n"
                    "mobile_events(event_id bigint primary key, occurred_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("web_events", 6200000), ("mobile_events", 8400000)),
                expected_focus="UNION ALL, ORDER BY",
                reference_sql=(
                    "SELECT event_id, occurred_at FROM web_events "
                    "UNION ALL "
                    "SELECT event_id, occurred_at FROM mobile_events "
                    "ORDER BY occurred_at ASC"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["web_events", "mobile_events"],
                    "required_set_operations": ["UNION ALL"],
                    "required_order_by": [{"column": "occurred_at", "direction": "ASC"}],
                },
            ),
            _ThemeVariant(
                topic_id="union-unique-target-users",
                topic_title="UNION で重複排除",
                problem_statement=(
                    "email_targets と push_targets の user_id を重複なくまとめてください。"
                    "UNION を使い、出力列は user_id とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "email_targets(user_id bigint primary key)\n"
                    "push_targets(user_id bigint primary key)\n"
                    "```"
                ),
                sample_data=_sample_rows(("email_targets", 180000), ("push_targets", 145000)),
                expected_focus="UNION",
                reference_sql=(
                    "SELECT user_id FROM email_targets "
                    "UNION "
                    "SELECT user_id FROM push_targets"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["email_targets", "push_targets"],
                    "required_set_operations": ["UNION"],
                },
            ),
            _ThemeVariant(
                topic_id="intersect-power-users",
                topic_title="INTERSECT で共通ユーザー抽出",
                problem_statement=(
                    "paid_users と webinar_attendees の両方に存在する user_id を抽出してください。"
                    "INTERSECT を使います。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "paid_users(user_id bigint primary key)\n"
                    "webinar_attendees(user_id bigint primary key)\n"
                    "```"
                ),
                sample_data=_sample_rows(("paid_users", 91000), ("webinar_attendees", 42000)),
                expected_focus="INTERSECT",
                reference_sql=(
                    "SELECT user_id FROM paid_users "
                    "INTERSECT "
                    "SELECT user_id FROM webinar_attendees"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["paid_users", "webinar_attendees"],
                    "required_set_operations": ["INTERSECT"],
                },
            ),
            _ThemeVariant(
                topic_id="except-churn-candidates",
                topic_title="EXCEPT で除外集合を作る",
                problem_statement=(
                    "all_subscribers から active_subscribers を除いた user_id を抽出してください。"
                    "EXCEPT を使います。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "all_subscribers(user_id bigint primary key)\n"
                    "active_subscribers(user_id bigint primary key)\n"
                    "```"
                ),
                sample_data=_sample_rows(("all_subscribers", 280000), ("active_subscribers", 251000)),
                expected_focus="EXCEPT",
                reference_sql=(
                    "SELECT user_id FROM all_subscribers "
                    "EXCEPT "
                    "SELECT user_id FROM active_subscribers"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["all_subscribers", "active_subscribers"],
                    "required_set_operations": ["EXCEPT"],
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="subquery-patterns",
        difficulty="intermediate",
        business_domain="Analytics",
        target_skill="Subquery の使い分け",
        title="Subquery の使い分けを覚える",
        generation_prompt="IN(subquery), scalar subquery, derived table を使う",
        variants=(
            _ThemeVariant(
                topic_id="in-subquery-paid-accounts",
                topic_title="IN(subquery) で支払済み account 抽出",
                problem_statement=(
                    "accounts から paid invoice がある account だけを抽出してください。"
                    "IN (subquery) を使い、出力列は id, name とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "accounts(id bigint primary key, name text)\n"
                    "invoices(id bigint primary key, account_id bigint, status text)\n"
                    "```"
                ),
                sample_data=_sample_rows(("accounts", 120000), ("invoices", 430000)),
                expected_focus="IN(subquery)",
                reference_sql=(
                    "SELECT id, name "
                    "FROM accounts "
                    "WHERE id IN ("
                    "SELECT account_id FROM invoices WHERE status = 'paid'"
                    ")"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["accounts", "invoices"],
                    "required_predicate_columns": ["id", "account_id", "status"],
                    "required_subquery_patterns": ["IN_SUBQUERY"],
                },
            ),
            _ThemeVariant(
                topic_id="scalar-subquery-latest-order-at",
                topic_title="scalar subquery で最終注文日時",
                problem_statement=(
                    "accounts ごとに最新注文日時を 1 列で返してください。"
                    "scalar subquery を使い、出力列は id, latest_order_at とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "accounts(id bigint primary key, name text)\n"
                    "orders(id bigint primary key, account_id bigint, created_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("accounts", 120000), ("orders", 14600000)),
                expected_focus="scalar subquery",
                reference_sql=(
                    "SELECT a.id, ("
                    "SELECT MAX(o.created_at) FROM orders AS o WHERE o.account_id = a.id"
                    ") AS latest_order_at "
                    "FROM accounts AS a"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["accounts", "orders"],
                    "required_aggregates": [{"function": "MAX", "column": "created_at"}],
                    "required_subquery_patterns": ["SCALAR_SUBQUERY"],
                    "required_predicate_columns": ["account_id", "id"],
                },
            ),
            _ThemeVariant(
                topic_id="derived-table-top-plan-month",
                topic_title="derived table で月次トッププラン",
                problem_statement=(
                    "plan_revenue の月次集計結果を derived table にまとめてから、"
                    "売上 100000 以上の行だけを抽出してください。"
                    "出力列は plan_code, bill_month, total_revenue とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "plan_revenue(id bigint primary key, plan_code text, bill_month date, amount numeric)\n"
                    "```"
                ),
                sample_data=_sample_rows(("plan_revenue", 540000)),
                expected_focus="FROM(subquery), GROUP BY",
                reference_sql=(
                    "SELECT monthly.plan_code, monthly.bill_month, monthly.total_revenue "
                    "FROM ("
                    "SELECT plan_code, bill_month, SUM(amount) AS total_revenue "
                    "FROM plan_revenue "
                    "GROUP BY plan_code, bill_month"
                    ") AS monthly "
                    "WHERE monthly.total_revenue >= 100000"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["plan_revenue"],
                    "required_aggregates": [{"function": "SUM", "column": "amount"}],
                    "required_group_by_columns": ["plan_code", "bill_month"],
                    "required_subquery_patterns": ["DERIVED_TABLE"],
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="write-operations",
        difficulty="intermediate",
        business_domain="Operations",
        target_skill="DML 基本形",
        title="DML の基本形を書く",
        generation_prompt="UPDATE FROM, DELETE USING, INSERT SELECT を使う",
        variants=(
            _ThemeVariant(
                topic_id="update-from-mark-overdue",
                topic_title="UPDATE FROM で延滞更新",
                problem_statement=(
                    "accounts の billing_status が delinquent の account に属する orders を archived に更新してください。"
                    "UPDATE ... FROM を使い、更新された order の id を返します。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "accounts(id bigint primary key, billing_status text)\n"
                    "orders(id bigint primary key, account_id bigint, status text)\n"
                    "```"
                ),
                sample_data=_sample_rows(("accounts", 120000), ("orders", 14600000)),
                expected_focus="UPDATE ... FROM, RETURNING",
                reference_sql=(
                    "UPDATE orders AS o "
                    "SET status = 'archived' "
                    "FROM accounts AS a "
                    "WHERE o.account_id = a.id "
                    "AND a.billing_status = 'delinquent' "
                    "RETURNING o.id"
                ),
                grading_contract={
                    "statement_kind": "update",
                    "required_tables": ["orders", "accounts"],
                    "required_predicate_columns": ["account_id", "id", "billing_status"],
                    "required_returning": True,
                    "required_sql_fragments": ["FROM accounts AS a"],
                },
            ),
            _ThemeVariant(
                topic_id="delete-using-remove-orphans",
                topic_title="DELETE USING で孤児行削除",
                problem_statement=(
                    "cancelled_accounts に紐づく sessions を削除してください。"
                    "DELETE ... USING を使い、削除された session の id を返します。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "sessions(id bigint primary key, account_id bigint, created_at timestamptz)\n"
                    "cancelled_accounts(account_id bigint primary key, cancelled_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("sessions", 8900000), ("cancelled_accounts", 18000)),
                expected_focus="DELETE ... USING, RETURNING",
                reference_sql=(
                    "DELETE FROM sessions AS s "
                    "USING cancelled_accounts AS c "
                    "WHERE s.account_id = c.account_id "
                    "RETURNING s.id"
                ),
                grading_contract={
                    "statement_kind": "delete",
                    "required_tables": ["sessions", "cancelled_accounts"],
                    "required_predicate_columns": ["account_id"],
                    "required_returning": True,
                    "required_sql_fragments": ["USING cancelled_accounts AS c"],
                },
            ),
            _ThemeVariant(
                topic_id="insert-select-backfill-settings",
                topic_title="INSERT SELECT で設定を補完",
                problem_statement=(
                    "marketing_opt_in=true の users について、user_settings に未作成なら"
                    " key='newsletter', value='enabled' を backfill してください。"
                    "INSERT ... SELECT を使います。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "users(id bigint primary key, marketing_opt_in boolean)\n"
                    "user_settings(id bigint primary key, user_id bigint, key text, value text)\n"
                    "```"
                ),
                sample_data=_sample_rows(("users", 480000), ("user_settings", 730000)),
                expected_focus="INSERT ... SELECT, NOT EXISTS",
                reference_sql=(
                    "INSERT INTO user_settings (user_id, key, value) "
                    "SELECT u.id, 'newsletter', 'enabled' "
                    "FROM users AS u "
                    "WHERE u.marketing_opt_in = TRUE "
                    "AND NOT EXISTS ("
                    "SELECT 1 FROM user_settings AS s "
                    "WHERE s.user_id = u.id AND s.key = 'newsletter'"
                    ")"
                ),
                grading_contract={
                    "statement_kind": "insert",
                    "required_tables": ["users", "user_settings"],
                    "required_predicate_columns": ["marketing_opt_in", "user_id", "id", "key"],
                    "required_sql_fragments": ["SELECT u.id, 'newsletter', 'enabled'"],
                    "required_not_exists": True,
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="business-analytics",
        difficulty="advanced",
        business_domain="Analytics",
        target_skill="実務分析SQL",
        title="cohort・retention・funnel などの分析SQLを書く",
        generation_prompt="実務分析で頻出する集計・window・percentile を使う",
        variants=(
            _ThemeVariant(
                topic_id="cohort-first-purchase-month",
                topic_title="初回購入月cohort",
                problem_statement=(
                    "purchases から user_id ごとの初回購入月 cohort を作ってください。"
                    "出力列は user_id, cohort_month とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "purchases(id bigint primary key, user_id bigint, purchased_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("purchases", 9300000)),
                expected_focus="DATE_TRUNC, MIN, GROUP BY",
                reference_sql=(
                    "SELECT user_id, DATE_TRUNC('month', MIN(purchased_at)) AS cohort_month "
                    "FROM purchases "
                    "GROUP BY user_id"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["purchases"],
                    "required_functions": ["DATE_TRUNC"],
                    "required_group_by_columns": ["user_id"],
                    "required_aggregates": [{"function": "MIN", "column": "purchased_at"}],
                },
            ),
            _ThemeVariant(
                topic_id="retention-next-month-active",
                topic_title="翌月継続率",
                problem_statement=(
                    "monthly_active_users から cohort_month ごとの翌月継続率を計算してください。"
                    "出力列は cohort_month, retention_rate とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "monthly_active_users(user_id bigint, activity_month date)\n"
                    "```"
                ),
                sample_data=_sample_rows(("monthly_active_users", 5200000)),
                expected_focus="CTE, self join, COUNT DISTINCT, NULLIF",
                reference_sql=(
                    "WITH first_month AS ("
                    "SELECT user_id, MIN(activity_month) AS cohort_month "
                    "FROM monthly_active_users "
                    "GROUP BY user_id"
                    ") "
                    "SELECT f.cohort_month, "
                    "COUNT(DISTINCT m.user_id)::numeric / NULLIF(COUNT(DISTINCT f.user_id), 0) AS retention_rate "
                    "FROM first_month AS f "
                    "LEFT JOIN monthly_active_users AS m "
                    "ON m.user_id = f.user_id AND m.activity_month = f.cohort_month + INTERVAL '1 month' "
                    "GROUP BY f.cohort_month"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["monthly_active_users"],
                    "required_joins": [{"left": "first_month", "right": "monthly_active_users", "join_type": "LEFT"}],
                    "required_cte_names": ["first_month"],
                    "required_functions": ["NULLIF"],
                    "required_aggregates": [{"function": "COUNT", "column": "user_id"}],
                },
            ),
            _ThemeVariant(
                topic_id="funnel-signup-to-purchase",
                topic_title="signupからpurchase funnel",
                problem_statement=(
                    "user_events から signup, trial_started, purchase の funnel 件数を1行で出してください。"
                    "FILTER (WHERE ...) を使い、出力列は signups, trials, purchases とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "user_events(id bigint primary key, user_id bigint, event_name text, occurred_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("user_events", 125000000)),
                expected_focus="COUNT DISTINCT FILTER",
                reference_sql=(
                    "SELECT "
                    "COUNT(DISTINCT user_id) FILTER (WHERE event_name = 'signup') AS signups, "
                    "COUNT(DISTINCT user_id) FILTER (WHERE event_name = 'trial_started') AS trials, "
                    "COUNT(DISTINCT user_id) FILTER (WHERE event_name = 'purchase') AS purchases "
                    "FROM user_events"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["user_events"],
                    "required_filter_aggregates": [{"function": "COUNT", "column": "user_id"}],
                    "required_predicate_columns": ["event_name"],
                },
            ),
            _ThemeVariant(
                topic_id="moving-average-daily-sales",
                topic_title="日次売上移動平均",
                problem_statement=(
                    "daily_sales から7日移動平均を計算してください。"
                    "出力列は sales_date, revenue, moving_avg_7day とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "daily_sales(sales_date date primary key, revenue numeric)\n"
                    "```"
                ),
                sample_data=_sample_rows(("daily_sales", 1460)),
                expected_focus="AVG OVER, ROWS BETWEEN",
                reference_sql=(
                    "SELECT sales_date, revenue, "
                    "AVG(revenue) OVER (ORDER BY sales_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS moving_avg_7day "
                    "FROM daily_sales "
                    "ORDER BY sales_date ASC"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["daily_sales"],
                    "required_window_functions": ["AVG"],
                    "required_order_by": [{"column": "sales_date", "direction": "ASC"}],
                },
            ),
            _ThemeVariant(
                topic_id="cumulative-revenue-by-day",
                topic_title="累積売上",
                problem_statement=(
                    "daily_sales から日別売上と累積売上を出してください。"
                    "出力列は sales_date, revenue, cumulative_revenue とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "daily_sales(sales_date date primary key, revenue numeric)\n"
                    "```"
                ),
                sample_data=_sample_rows(("daily_sales", 1460)),
                expected_focus="SUM OVER, cumulative sum",
                reference_sql=(
                    "SELECT sales_date, revenue, "
                    "SUM(revenue) OVER (ORDER BY sales_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_revenue "
                    "FROM daily_sales "
                    "ORDER BY sales_date ASC"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["daily_sales"],
                    "required_window_functions": ["SUM"],
                    "required_order_by": [{"column": "sales_date", "direction": "ASC"}],
                },
            ),
            _ThemeVariant(
                topic_id="percentile-response-time",
                topic_title="response time p95",
                problem_statement=(
                    "api_requests から endpoint ごとの p95 latency を計算してください。"
                    "percentile_cont を使い、出力列は endpoint, p95_latency_ms とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "api_requests(id bigint primary key, endpoint text, latency_ms int, requested_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("api_requests", 68000000)),
                expected_focus="percentile_cont, WITHIN GROUP, GROUP BY",
                reference_sql=(
                    "SELECT endpoint, "
                    "PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) AS p95_latency_ms "
                    "FROM api_requests "
                    "GROUP BY endpoint"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["api_requests"],
                    "required_functions": ["PERCENTILE_CONT"],
                    "required_group_by_columns": ["endpoint"],
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="postgres-json-array",
        difficulty="advanced",
        business_domain="Product",
        target_skill="JSONB と array",
        title="PostgreSQL の JSONB / array を扱う",
        generation_prompt="JSONB operator, jsonb_array_elements, ANY, unnest を使う",
        variants=(
            _ThemeVariant(
                topic_id="jsonb-event-property-filter",
                topic_title="JSONB property抽出検索",
                problem_statement=(
                    "events の payload JSONB から plan='pro' のイベントを抽出してください。"
                    "出力列は id, account_id, plan とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "events(id bigint primary key, account_id bigint, payload jsonb, created_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("events", 8200000)),
                expected_focus="JSONB ->>, WHERE",
                reference_sql=(
                    "SELECT id, account_id, payload ->> 'plan' AS plan "
                    "FROM events "
                    "WHERE payload ->> 'plan' = 'pro'"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["events"],
                    "required_json_operators": ["->>"],
                    "required_predicate_columns": ["payload"],
                },
            ),
            _ThemeVariant(
                topic_id="jsonb-array-items-expand",
                topic_title="JSONB配列展開",
                problem_statement=(
                    "orders の items JSONB 配列を展開し、注文IDと sku を返してください。"
                    "出力列は order_id, sku とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "orders(id bigint primary key, items jsonb, created_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("orders", 14600000)),
                expected_focus="jsonb_array_elements, LATERAL, ->>",
                reference_sql=(
                    "SELECT o.id AS order_id, item ->> 'sku' AS sku "
                    "FROM orders AS o "
                    "CROSS JOIN LATERAL jsonb_array_elements(o.items) AS item"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["orders"],
                    "required_functions": ["jsonb_array_elements"],
                    "required_json_operators": ["->>"],
                },
            ),
            _ThemeVariant(
                topic_id="array-any-tag-filter",
                topic_title="ANYによるtag検索",
                problem_statement=(
                    "articles の tags 配列に 'postgres' が含まれる記事を抽出してください。"
                    "ANY を使い、出力列は id, title とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "articles(id bigint primary key, title text, tags text[], published_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("articles", 280000)),
                expected_focus="ANY(array)",
                reference_sql=(
                    "SELECT id, title "
                    "FROM articles "
                    "WHERE 'postgres' = ANY(tags)"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["articles"],
                    "required_array_functions": ["ANY"],
                    "required_predicate_columns": ["tags"],
                },
            ),
            _ThemeVariant(
                topic_id="unnest-campaign-tags",
                topic_title="unnestでtag別集計",
                problem_statement=(
                    "campaigns の tags 配列を展開し、tag ごとの campaign 件数を集計してください。"
                    "出力列は tag, campaign_count とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "campaigns(id bigint primary key, name text, tags text[])\n"
                    "```"
                ),
                sample_data=_sample_rows(("campaigns", 4200)),
                expected_focus="unnest, GROUP BY, COUNT",
                reference_sql=(
                    "SELECT tag, COUNT(*) AS campaign_count "
                    "FROM campaigns AS c "
                    "CROSS JOIN LATERAL unnest(c.tags) AS tag "
                    "GROUP BY tag"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["campaigns"],
                    "required_array_functions": ["unnest"],
                    "required_aggregates": [{"function": "COUNT", "column": "*"}],
                    "required_group_by_columns": ["tag"],
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="postgres-write-patterns",
        difficulty="advanced",
        business_domain="Product",
        target_skill="UPSERT",
        title="ON CONFLICT で冪等に書き込む",
        generation_prompt="INSERT ... ON CONFLICT を使う",
        variants=(
            _ThemeVariant(
                topic_id="upsert-user-preferences",
                topic_title="ON CONFLICT upsert",
                problem_statement=(
                    "user_preferences に user_id=42, key='theme', value='dark' を保存してください。"
                    "(user_id, key) が既にある場合は value と updated_at を更新します。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "user_preferences(user_id bigint, key text, value text, updated_at timestamptz, primary key(user_id, key))\n"
                    "```"
                ),
                sample_data=_sample_rows(("user_preferences", 1200000)),
                expected_focus="INSERT, ON CONFLICT, DO UPDATE",
                reference_sql=(
                    "INSERT INTO user_preferences (user_id, key, value, updated_at) "
                    "VALUES (42, 'theme', 'dark', NOW()) "
                    "ON CONFLICT (user_id, key) DO UPDATE "
                    "SET value = EXCLUDED.value, updated_at = EXCLUDED.updated_at"
                ),
                grading_contract={
                    "statement_kind": "insert",
                    "required_tables": ["user_preferences"],
                    "required_on_conflict": True,
                    "required_functions": ["NOW"],
                    "required_sql_fragments": [
                        "DO UPDATE",
                        "value = EXCLUDED.value",
                        "updated_at = EXCLUDED.updated_at",
                    ],
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="advanced-index-design",
        difficulty="advanced",
        business_domain="Performance",
        target_skill="高度なインデックス設計",
        title="partial / expression / include / trigram index を設計する",
        generation_prompt="PostgreSQL の高度な CREATE INDEX を書く",
        variants=(
            _ThemeVariant(
                topic_id="partial-index-active-orders",
                topic_title="active条件のpartial index",
                problem_statement=(
                    "orders で status='active' の行だけを account_id と created_at でよく検索します。"
                    "active 行に絞った partial index を作成してください。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "orders(id bigint primary key, account_id bigint, status text, created_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("orders", 14600000)),
                expected_focus="CREATE INDEX, WHERE, partial index",
                reference_sql=(
                    "CREATE INDEX idx_orders_active_account_created_at "
                    "ON orders (account_id, created_at DESC) "
                    "WHERE status = 'active'"
                ),
                grading_contract={
                    "statement_kind": "create_index",
                    "required_index": {
                        "table": "orders",
                        "columns": ["account_id", "created_at"],
                        "orders": {"created_at": "DESC"},
                    },
                    "required_partial_index_predicate_columns": ["status"],
                    "required_sql_fragments": ["WHERE status = 'active'"],
                },
            ),
            _ThemeVariant(
                topic_id="expression-index-lower-email",
                topic_title="lower(email) expression index",
                problem_statement=(
                    "users で lower(email) = lower(?) の検索が多いです。"
                    "大文字小文字を無視した検索に使う expression index を作成してください。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "users(id bigint primary key, email text, created_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("users", 2200000)),
                expected_focus="CREATE INDEX, lower(email), expression index",
                reference_sql=(
                    "CREATE INDEX idx_users_lower_email "
                    "ON users (LOWER(email))"
                ),
                grading_contract={
                    "statement_kind": "create_index",
                    "required_index": {"table": "users"},
                    "required_expression_index_terms": ["LOWER(email)"],
                    "required_functions": ["LOWER"],
                },
            ),
            _ThemeVariant(
                topic_id="include-index-covering-orders",
                topic_title="INCLUDE付きindex",
                problem_statement=(
                    "orders で account_id と created_at で絞って並べ、total_amount も頻繁に表示します。"
                    "検索キーに account_id, created_at を使い、total_amount を INCLUDE する index を作成してください。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "orders(id bigint primary key, account_id bigint, created_at timestamptz, total_amount numeric)\n"
                    "```"
                ),
                sample_data=_sample_rows(("orders", 14600000)),
                expected_focus="CREATE INDEX, INCLUDE",
                reference_sql=(
                    "CREATE INDEX idx_orders_account_created_at_include_amount "
                    "ON orders (account_id, created_at DESC) INCLUDE (total_amount)"
                ),
                grading_contract={
                    "statement_kind": "create_index",
                    "required_index": {
                        "table": "orders",
                        "columns": ["account_id", "created_at"],
                        "orders": {"created_at": "DESC"},
                    },
                    "required_include_columns": ["total_amount"],
                },
            ),
            _ThemeVariant(
                topic_id="trigram-search-products",
                topic_title="%keyword%検索のtrigram index方針",
                problem_statement=(
                    "products.name に対して ILIKE '%keyword%' の検索が多いです。"
                    "pg_trgm を前提に、name の trigram index を作成してください。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "products(id bigint primary key, name text, status text)\n"
                    "```"
                ),
                sample_data=_sample_rows(("products", 124000)),
                expected_focus="CREATE INDEX, gin, gin_trgm_ops",
                reference_sql=(
                    "CREATE INDEX idx_products_name_trgm "
                    "ON products USING gin (name gin_trgm_ops)"
                ),
                grading_contract={
                    "statement_kind": "create_index",
                    "required_index": {"table": "products"},
                    "required_index_method": "gin",
                    "required_expression_index_terms": ["name gin_trgm_ops"],
                    "prohibited_patterns": ["leading_wildcard_without_trigram"],
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="performance-reading",
        difficulty="advanced",
        business_domain="Performance",
        target_skill="性能を意識したSQL",
        title="実行計画・N+1・ページネーションを意識する",
        generation_prompt="EXPLAIN, 集約SQL, keyset pagination を書く",
        variants=(
            _ThemeVariant(
                topic_id="plan-read-seq-scan-warning",
                topic_title="Seq Scan読解",
                problem_statement=(
                    "events の account_id 検索で Seq Scan が疑われます。"
                    "実測時間とバッファを確認する EXPLAIN を書いてください。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "events(id bigint primary key, account_id bigint, created_at timestamptz, event_type text)\n"
                    "```"
                ),
                sample_data=_sample_rows(("events", 8200000)),
                expected_focus="EXPLAIN ANALYZE, BUFFERS, Seq Scan確認",
                reference_sql=(
                    "EXPLAIN (ANALYZE, BUFFERS) "
                    "SELECT id, account_id, created_at "
                    "FROM events "
                    "WHERE account_id = 42"
                ),
                grading_contract=_explain_contract(
                    table="events",
                    predicate_columns=["account_id"],
                ),
            ),
            _ThemeVariant(
                topic_id="plan-read-bitmap-heap-scan",
                topic_title="Bitmap Heap Scan読解",
                problem_statement=(
                    "orders の status と created_at 条件で Bitmap Heap Scan が出るか確認します。"
                    "実測時間とバッファを確認する EXPLAIN を書いてください。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "orders(id bigint primary key, status text, created_at timestamptz, total_amount numeric)\n"
                    "```"
                ),
                sample_data=_sample_rows(("orders", 14600000)),
                expected_focus="EXPLAIN ANALYZE, BUFFERS, Bitmap Heap Scan確認",
                reference_sql=(
                    "EXPLAIN (ANALYZE, BUFFERS) "
                    "SELECT id, total_amount "
                    "FROM orders "
                    "WHERE status = 'paid' AND created_at >= TIMESTAMPTZ '2026-06-01 00:00:00+00:00'"
                ),
                grading_contract=_explain_contract(
                    table="orders",
                    predicate_columns=["status", "created_at"],
                ),
            ),
            _ThemeVariant(
                topic_id="n-plus-one-orders-summary",
                topic_title="N+1回避の集約SQL",
                problem_statement=(
                    "accounts 一覧に各 account の注文数を表示します。"
                    "N+1 を避けるため、JOIN と GROUP BY で account ごとの order_count を1文で出してください。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "accounts(id bigint primary key, name text)\n"
                    "orders(id bigint primary key, account_id bigint, created_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("accounts", 180000), ("orders", 14600000)),
                expected_focus="LEFT JOIN, COUNT, GROUP BY",
                reference_sql=(
                    "SELECT a.id, a.name, COUNT(o.id) AS order_count "
                    "FROM accounts AS a "
                    "LEFT JOIN orders AS o ON o.account_id = a.id "
                    "GROUP BY a.id, a.name"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["accounts", "orders"],
                    "required_joins": [{"left": "accounts", "right": "orders", "join_type": "LEFT"}],
                    "required_group_by_columns": ["id", "name"],
                    "required_aggregates": [{"function": "COUNT", "column": "id"}],
                    "prohibited_patterns": ["implicit_join"],
                },
            ),
            _ThemeVariant(
                topic_id="keyset-pagination-events",
                topic_title="keyset pagination",
                problem_statement=(
                    "events を created_at DESC, id DESC で keyset pagination してください。"
                    "前ページ末尾が created_at='2026-06-20 10:00:00+00:00', id=5000 の想定で、次の50件を取得します。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "events(id bigint primary key, account_id bigint, created_at timestamptz, event_type text)\n"
                    "```"
                ),
                sample_data=_sample_rows(("events", 8200000)),
                expected_focus="WHERE cursor predicate, ORDER BY, LIMIT, no OFFSET",
                reference_sql=(
                    "SELECT id, account_id, created_at, event_type "
                    "FROM events "
                    "WHERE (created_at, id) < (TIMESTAMPTZ '2026-06-20 10:00:00+00:00', 5000) "
                    "ORDER BY created_at DESC, id DESC "
                    "LIMIT 50"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["events"],
                    "required_predicate_columns": ["created_at", "id"],
                    "required_order_by": [
                        {"column": "created_at", "direction": "DESC"},
                        {"column": "id", "direction": "DESC"},
                    ],
                    "required_limit": 50,
                    "required_pagination_style": "keyset",
                    "prohibited_patterns": ["offset_pagination"],
                },
            ),
            _ThemeVariant(
                topic_id="offset-pagination-risk",
                topic_title="offset paginationの問題指摘",
                problem_statement=(
                    "api_requests を requested_at DESC で深いページまで表示します。"
                    "OFFSET を使わず、前ページ末尾 requested_at/id を使う keyset pagination のSQLを書いてください。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "api_requests(id bigint primary key, requested_at timestamptz, endpoint text, status_code int)\n"
                    "```"
                ),
                sample_data=_sample_rows(("api_requests", 68000000)),
                expected_focus="keyset pagination, OFFSET禁止",
                reference_sql=(
                    "SELECT id, requested_at, endpoint, status_code "
                    "FROM api_requests "
                    "WHERE (requested_at, id) < (TIMESTAMPTZ '2026-06-20 10:00:00+00:00', 900000) "
                    "ORDER BY requested_at DESC, id DESC "
                    "LIMIT 100"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["api_requests"],
                    "required_predicate_columns": ["requested_at", "id"],
                    "required_order_by": [
                        {"column": "requested_at", "direction": "DESC"},
                        {"column": "id", "direction": "DESC"},
                    ],
                    "required_limit": 100,
                    "required_pagination_style": "keyset",
                    "prohibited_patterns": ["offset_pagination"],
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="materialized-view-design",
        difficulty="advanced",
        business_domain="Analytics",
        target_skill="Materialized View",
        title="重い集計を materialized view に逃がす",
        generation_prompt="CREATE MATERIALIZED VIEW で集計結果を保存する",
        variants=(
            _ThemeVariant(
                topic_id="materialized-view-monthly-revenue",
                topic_title="月次売上materialized view設計",
                problem_statement=(
                    "payments の月次売上集計が重いため、月次売上の materialized view を作成してください。"
                    "列は revenue_month, total_revenue とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "payments(id bigint primary key, paid_at timestamptz, amount numeric, status text)\n"
                    "```"
                ),
                sample_data=_sample_rows(("payments", 23100000)),
                expected_focus="CREATE MATERIALIZED VIEW, DATE_TRUNC, SUM, GROUP BY",
                reference_sql=(
                    "CREATE MATERIALIZED VIEW monthly_revenue AS "
                    "SELECT DATE_TRUNC('month', paid_at) AS revenue_month, "
                    "SUM(amount) AS total_revenue "
                    "FROM payments "
                    "WHERE status = 'paid' "
                    "GROUP BY DATE_TRUNC('month', paid_at)"
                ),
                grading_contract={
                    "statement_kind": "create_materialized_view",
                    "required_tables": ["payments"],
                    "required_functions": ["DATE_TRUNC"],
                    "required_predicate_columns": ["status"],
                    "required_aggregates": [{"function": "SUM", "column": "amount"}],
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="recursive-cte",
        difficulty="advanced",
        business_domain="Cross-domain",
        target_skill="WITH RECURSIVE",
        title="再帰CTEで階層や依存関係をたどる",
        generation_prompt="WITH RECURSIVE と UNION ALL を使って階層を展開する",
        variants=(
            _ThemeVariant(
                topic_id="category-descendants-tree",
                topic_title="カテゴリ配下を再帰展開",
                problem_statement=(
                    "categories から id=10 を起点に、配下カテゴリをすべて再帰的に取得してください。"
                    "出力列は id, parent_id, depth とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "categories(id bigint primary key, parent_id bigint, name text)\n"
                    "```"
                ),
                sample_data=_sample_rows(("categories", 9200)),
                expected_focus="WITH RECURSIVE, UNION ALL",
                reference_sql=(
                    "WITH RECURSIVE category_tree AS ("
                    "SELECT id, parent_id, 0 AS depth "
                    "FROM categories "
                    "WHERE id = 10 "
                    "UNION ALL "
                    "SELECT c.id, c.parent_id, ct.depth + 1 AS depth "
                    "FROM categories AS c "
                    "INNER JOIN category_tree AS ct ON c.parent_id = ct.id"
                    ") "
                    "SELECT id, parent_id, depth "
                    "FROM category_tree "
                    "ORDER BY depth ASC, id ASC"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["categories"],
                    "required_cte_names": ["category_tree"],
                    "required_recursive_cte": True,
                    "required_set_operations": ["UNION ALL"],
                    "required_predicate_columns": ["id"],
                    "required_joins": [{"left": "categories", "right": "category_tree", "join_type": "INNER"}],
                    "required_order_by": [{"column": "depth", "direction": "ASC"}],
                },
            ),
            _ThemeVariant(
                topic_id="manager-chain-depth",
                topic_title="上司チェーンをたどる",
                problem_statement=(
                    "employees から id=42 の上司チェーンを再帰的にたどってください。"
                    "出力列は employee_id, manager_id, level とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "employees(id bigint primary key, manager_id bigint, name text)\n"
                    "```"
                ),
                sample_data=_sample_rows(("employees", 38000)),
                expected_focus="WITH RECURSIVE, self join",
                reference_sql=(
                    "WITH RECURSIVE manager_chain AS ("
                    "SELECT id AS employee_id, manager_id, 0 AS level "
                    "FROM employees "
                    "WHERE id = 42 "
                    "UNION ALL "
                    "SELECT e.id AS employee_id, e.manager_id, mc.level + 1 AS level "
                    "FROM employees AS e "
                    "INNER JOIN manager_chain AS mc ON e.id = mc.manager_id"
                    ") "
                    "SELECT employee_id, manager_id, level "
                    "FROM manager_chain "
                    "ORDER BY level ASC"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["employees"],
                    "required_cte_names": ["manager_chain"],
                    "required_recursive_cte": True,
                    "required_set_operations": ["UNION ALL"],
                    "required_predicate_columns": ["id"],
                    "required_joins": [{"left": "employees", "right": "manager_chain", "join_type": "INNER"}],
                    "required_order_by": [{"column": "level", "direction": "ASC"}],
                },
            ),
            _ThemeVariant(
                topic_id="dependency-expansion",
                topic_title="依存関係を再帰展開",
                problem_statement=(
                    "package_dependencies から package_id=7 の依存先をすべて再帰的に取得してください。"
                    "出力列は package_id, depends_on_id, depth とします。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "package_dependencies(package_id bigint, depends_on_id bigint)\n"
                    "```"
                ),
                sample_data=_sample_rows(("package_dependencies", 145000)),
                expected_focus="WITH RECURSIVE, UNION ALL",
                reference_sql=(
                    "WITH RECURSIVE dependency_tree AS ("
                    "SELECT package_id, depends_on_id, 0 AS depth "
                    "FROM package_dependencies "
                    "WHERE package_id = 7 "
                    "UNION ALL "
                    "SELECT pd.package_id, pd.depends_on_id, dt.depth + 1 AS depth "
                    "FROM package_dependencies AS pd "
                    "INNER JOIN dependency_tree AS dt ON pd.package_id = dt.depends_on_id"
                    ") "
                    "SELECT package_id, depends_on_id, depth "
                    "FROM dependency_tree "
                    "ORDER BY depth ASC, depends_on_id ASC"
                ),
                grading_contract={
                    "statement_kind": "select",
                    "required_tables": ["package_dependencies"],
                    "required_cte_names": ["dependency_tree"],
                    "required_recursive_cte": True,
                    "required_set_operations": ["UNION ALL"],
                    "required_predicate_columns": ["package_id"],
                    "required_joins": [{"left": "package_dependencies", "right": "dependency_tree", "join_type": "INNER"}],
                    "required_order_by": [{"column": "depth", "direction": "ASC"}],
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="schema-constraints",
        difficulty="advanced",
        business_domain="Platform",
        target_skill="DDL と制約",
        title="DDL と制約を設計する",
        generation_prompt="CREATE TABLE と ALTER TABLE で制約を付ける",
        variants=(
            _ThemeVariant(
                topic_id="create-table-subscriptions-with-constraints",
                topic_title="制約付き subscriptions テーブル作成",
                problem_statement=(
                    "subscriptions テーブルを作成してください。"
                    "id を PRIMARY KEY、user_id を users(id) 参照の FOREIGN KEY、"
                    "external_key を UNIQUE、seat_count に 1 以上の CHECK 制約を付けます。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "users(id bigint primary key)\n"
                    "```"
                ),
                sample_data=_sample_rows(("users", 120000)),
                expected_focus="CREATE TABLE, PRIMARY KEY, FOREIGN KEY, UNIQUE, CHECK",
                reference_sql=(
                    "CREATE TABLE subscriptions ("
                    "id bigint PRIMARY KEY, "
                    "user_id bigint REFERENCES users(id), "
                    "external_key text UNIQUE, "
                    "seat_count int CHECK (seat_count >= 1)"
                    ")"
                ),
                grading_contract={
                    "statement_kind": "create_table",
                    "required_tables": ["subscriptions", "users"],
                    "required_constraint_types": ["PRIMARY_KEY", "FOREIGN_KEY", "UNIQUE", "CHECK"],
                },
            ),
            _ThemeVariant(
                topic_id="alter-table-add-foreign-key",
                topic_title="ALTER TABLE で外部キー追加",
                problem_statement=(
                    "subscriptions.user_id が users(id) を参照するように、"
                    "ALTER TABLE で外部キー制約を追加してください。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "subscriptions(id bigint primary key, user_id bigint)\n"
                    "users(id bigint primary key)\n"
                    "```"
                ),
                sample_data=_sample_rows(("subscriptions", 380000), ("users", 120000)),
                expected_focus="ALTER TABLE, ADD CONSTRAINT, FOREIGN KEY",
                reference_sql=(
                    "ALTER TABLE subscriptions "
                    "ADD CONSTRAINT subscriptions_user_id_fkey "
                    "FOREIGN KEY (user_id) REFERENCES users(id)"
                ),
                grading_contract={
                    "statement_kind": "alter_table",
                    "required_tables": ["subscriptions", "users"],
                    "required_constraint_types": ["FOREIGN_KEY"],
                    "required_sql_fragments": ["ADD CONSTRAINT subscriptions_user_id_fkey"],
                },
            ),
            _ThemeVariant(
                topic_id="alter-table-add-unique-check",
                topic_title="ALTER TABLE で UNIQUE 制約追加",
                problem_statement=(
                    "subscriptions.external_key に UNIQUE 制約を追加してください。"
                    "ALTER TABLE ... ADD CONSTRAINT を使います。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "subscriptions(id bigint primary key, external_key text)\n"
                    "```"
                ),
                sample_data=_sample_rows(("subscriptions", 380000)),
                expected_focus="ALTER TABLE, ADD CONSTRAINT, UNIQUE",
                reference_sql=(
                    "ALTER TABLE subscriptions "
                    "ADD CONSTRAINT subscriptions_external_key_unique "
                    "UNIQUE (external_key)"
                ),
                grading_contract={
                    "statement_kind": "alter_table",
                    "required_tables": ["subscriptions"],
                    "required_constraint_types": ["UNIQUE"],
                    "required_sql_fragments": ["ADD CONSTRAINT subscriptions_external_key_unique"],
                },
            ),
        ),
    ),
    _ThemeTemplate(
        family="transactions-locking",
        difficulty="advanced",
        business_domain="Operations",
        target_skill="Transaction と Locking",
        title="Transaction と Locking を扱う",
        generation_prompt="BEGIN/COMMIT, FOR UPDATE, SKIP LOCKED を含む複数文を書く",
        variants=(
            _ThemeVariant(
                topic_id="claim-next-job-skip-locked",
                topic_title="SKIP LOCKED で次ジョブ取得",
                problem_statement=(
                    "必要なら複数文で、queue_jobs から status='queued' の最古ジョブを"
                    "競合なく 1 件 claimed に更新し、その id を返してください。"
                    "BEGIN と COMMIT、FOR UPDATE SKIP LOCKED、UPDATE、RETURNING を使います。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "queue_jobs(id bigint primary key, status text, created_at timestamptz)\n"
                    "```"
                ),
                sample_data=_sample_rows(("queue_jobs", 1850000)),
                expected_focus="BEGIN, FOR UPDATE SKIP LOCKED, UPDATE, COMMIT",
                reference_sql=(
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
                    "FROM locked_job "
                    "WHERE queue_jobs.id = locked_job.id "
                    "RETURNING queue_jobs.id; "
                    "COMMIT;"
                ),
                grading_contract={
                    "allow_multiple_statements": True,
                    "required_statement_sequence": [
                        "transaction_begin",
                        "update",
                        "commit",
                    ],
                    "required_tables": ["queue_jobs"],
                    "required_lock_clauses": ["FOR_UPDATE", "SKIP_LOCKED"],
                    "required_returning": True,
                    "required_sql_fragments": [
                        "WHERE status = 'queued'",
                        "ORDER BY created_at ASC",
                        "SET status = 'claimed'",
                        "LIMIT 1",
                    ],
                    "required_sql_regexes": [
                        (
                            r"(?:updatequeue_jobssetstatus='claimed'from"
                            r"(?P<source>(?!queue_jobs)\w+)"
                            r"wherequeue_jobs\.id=(?P=source)\.idreturningqueue_jobs\.id;|"
                            r"updatequeue_jobs(?:as)?(?P<target>\w+)setstatus='claimed'from"
                            r"(?P<source_alias>(?!queue_jobs)\w+)"
                            r"where(?P=target)\.id=(?P=source_alias)\.id"
                            r"returning(?P=target)\.id;)"
                        ),
                    ],
                },
            ),
            _ThemeVariant(
                topic_id="reserve-inventory-transaction",
                topic_title="在庫引当 transaction",
                problem_statement=(
                    "必要なら複数文で、product_id = 42 の inventory.available_quantity を 1 減らし、"
                    "inventory_reservations に (product_id, reserved_quantity) = (42, 1)"
                    " の予約行を追加してください。"
                    "BEGIN と COMMIT を含めます。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "inventory(product_id bigint primary key, available_quantity int)\n"
                    "inventory_reservations(id bigint primary key, product_id bigint, reserved_quantity int)\n"
                    "```"
                ),
                sample_data=_sample_rows(("inventory", 860000), ("inventory_reservations", 3200000)),
                expected_focus="BEGIN, UPDATE, INSERT, COMMIT",
                reference_sql=(
                    "BEGIN; "
                    "UPDATE inventory "
                    "SET available_quantity = available_quantity - 1 "
                    "WHERE product_id = 42; "
                    "INSERT INTO inventory_reservations (product_id, reserved_quantity) "
                    "VALUES (42, 1); "
                    "COMMIT;"
                ),
                grading_contract={
                    "allow_multiple_statements": True,
                    "required_statement_sequence": [
                        "transaction_begin",
                        "update",
                        "insert",
                        "commit",
                    ],
                    "required_tables": ["inventory", "inventory_reservations"],
                    "required_statement_predicates": [
                        {
                            "statement_kind": "update",
                            "predicate": "product_id = 42",
                        },
                    ],
                    "required_sql_fragments": [
                        "SET available_quantity = available_quantity - 1",
                        "INSERT INTO inventory_reservations",
                        "VALUES (42, 1)",
                    ],
                },
            ),
            _ThemeVariant(
                topic_id="archive-and-log-transaction",
                topic_title="archive と削除を同一 transaction で行う",
                problem_statement=(
                    "必要なら複数文で、completed_orders のうち completed_at が 2025 年以前の行を"
                    "archived_orders に退避してから completed_orders から削除してください。"
                    "BEGIN と COMMIT を含めます。"
                ),
                schema_markdown=(
                    "```sql\n"
                    "completed_orders(id bigint primary key, completed_at date, total_amount numeric)\n"
                    "archived_orders(id bigint primary key, completed_at date, total_amount numeric)\n"
                    "```"
                ),
                sample_data=_sample_rows(("completed_orders", 9200000), ("archived_orders", 18500000)),
                expected_focus="BEGIN, INSERT SELECT, DELETE, COMMIT",
                reference_sql=(
                    "BEGIN; "
                    "INSERT INTO archived_orders (id, completed_at, total_amount) "
                    "SELECT id, completed_at, total_amount "
                    "FROM completed_orders "
                    "WHERE completed_at < DATE '2026-01-01'; "
                    "DELETE FROM completed_orders "
                    "WHERE completed_at < DATE '2026-01-01'; "
                    "COMMIT;"
                ),
                grading_contract={
                    "allow_multiple_statements": True,
                    "required_statement_sequence": [
                        "transaction_begin",
                        "insert",
                        "delete",
                        "commit",
                    ],
                    "required_tables": ["completed_orders", "archived_orders"],
                    "required_predicate_columns": ["completed_at"],
                    "required_statement_predicates": [
                        {
                            "statement_kind": "insert",
                            "predicate": "completed_at < CAST('2026-01-01' AS DATE)",
                        },
                        {
                            "statement_kind": "delete",
                            "predicate": "completed_at < CAST('2026-01-01' AS DATE)",
                        },
                    ],
                    "required_sql_fragments": [
                        "INSERT INTO archived_orders",
                        "DELETE FROM completed_orders",
                    ],
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
