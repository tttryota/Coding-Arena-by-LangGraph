"""DB ベースのアルゴリズムテーマ読み込み。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from competitive.domain.competitive_types import (
    AlgoTheme,
    AlgoThemeWithHistory,
    ThemeSelectionError,
)
from infrastructure.rdb.models import (
    AlgoThemeModel,
    CompetitiveAnswer,
    CompetitiveSession,
)

if TYPE_CHECKING:
    from sqlalchemy import Engine


class SqlAlgoThemeReader:
    """DB からテーマを読み込み、セッション履歴を元に次のテーマを選択する。"""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_themes(self) -> list[AlgoThemeWithHistory]:
        """全テーマを display_order 順で、挑戦履歴付きで返す。"""
        with Session(self._engine) as session:
            # サブクエリ: テーマごとの挑戦回数・最高スコア・最終挑戦日
            history_sq = (
                select(
                    CompetitiveSession.theme_id,
                    func.count(CompetitiveSession.id).label("attempt_count"),
                    func.max(CompetitiveAnswer.score).label("best_score"),
                    func.max(CompetitiveSession.created_at).label(
                        "last_attempted_at",
                    ),
                )
                .outerjoin(
                    CompetitiveAnswer,
                    CompetitiveAnswer.session_id == CompetitiveSession.id,
                )
                # completed + in_progress 両方を挑戦済みとして集計
                .group_by(CompetitiveSession.theme_id)
                .subquery()
            )

            stmt = (
                select(
                    AlgoThemeModel.id,
                    AlgoThemeModel.category,
                    AlgoThemeModel.label,
                    AlgoThemeModel.display_order,
                    func.coalesce(history_sq.c.attempt_count, 0).label(
                        "attempt_count",
                    ),
                    history_sq.c.best_score,
                    history_sq.c.last_attempted_at,
                )
                .outerjoin(
                    history_sq,
                    AlgoThemeModel.id == history_sq.c.theme_id,
                )
                .order_by(AlgoThemeModel.display_order)
            )

            rows = session.execute(stmt).all()

        return [
            AlgoThemeWithHistory(
                id=row.id,
                category=row.category,
                label=row.label,
                display_order=row.display_order,
                attempt_count=row.attempt_count,
                best_score=row.best_score,
                last_attempted_at=(
                    row.last_attempted_at.isoformat()
                    if row.last_attempted_at
                    else None
                ),
            )
            for row in rows
        ]

    def get_by_id(self, theme_id: str) -> AlgoTheme:
        """ID 指定でテーマを取得する。"""
        with Session(self._engine) as session:
            theme = session.get(AlgoThemeModel, theme_id)
        if theme is None:
            msg = f"Theme not found: {theme_id}"
            raise ThemeSelectionError(error_code="theme_not_found", message=msg)
        return AlgoTheme(id=theme.id, category=theme.category, label=theme.label)

    def pick_next(self) -> AlgoTheme:
        """学習順で次に挑戦すべきテーマを選択する。

        1. 未挑戦テーマがあれば display_order 最小のものを返す
        2. 全テーマ挑戦済みなら best_score が最低のテーマを返す
        """
        with Session(self._engine) as session:
            # 挑戦済み (completed/in_progress) の theme_id 一覧
            attempted_ids = (
                select(CompetitiveSession.theme_id)
                .distinct()
                .subquery()
            )

            # 未挑戦テーマ (display_order 最小)
            unattempted = session.execute(
                select(AlgoThemeModel)
                .where(AlgoThemeModel.id.notin_(select(attempted_ids.c.theme_id)))
                .order_by(AlgoThemeModel.display_order)
                .limit(1),
            ).scalar_one_or_none()

            if unattempted is not None:
                return AlgoTheme(
                    id=unattempted.id,
                    category=unattempted.category,
                    label=unattempted.label,
                )

            # 全テーマ挑戦済み: best_score が最低 (NULL=未提出を優先) のテーマ
            worst_sq = (
                select(
                    CompetitiveSession.theme_id,
                    func.max(CompetitiveAnswer.score).label("best_score"),
                )
                .outerjoin(
                    CompetitiveAnswer,
                    CompetitiveAnswer.session_id == CompetitiveSession.id,
                )
                .group_by(CompetitiveSession.theme_id)
                .subquery()
            )

            worst_row = session.execute(
                select(AlgoThemeModel)
                .join(worst_sq, AlgoThemeModel.id == worst_sq.c.theme_id)
                .order_by(
                    worst_sq.c.best_score.asc().nulls_first(),
                    AlgoThemeModel.display_order,
                )
                .limit(1),
            ).scalar_one_or_none()

            if worst_row is not None:
                return AlgoTheme(
                    id=worst_row.id,
                    category=worst_row.category,
                    label=worst_row.label,
                )

        msg = "No themes available"
        raise ThemeSelectionError(error_code="no_themes", message=msg)


__all__ = ["SqlAlgoThemeReader"]
