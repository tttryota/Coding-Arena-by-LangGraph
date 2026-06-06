from __future__ import annotations

from typing import TYPE_CHECKING

from quiz.application.question_set_design import design_question_set
from quiz.application.question_set_design_types import QuestionSetDesignResult

if TYPE_CHECKING:
    from quiz.domain.session_state import (
        ConfirmationPoint,
        RoadmapItemLevel,
        SessionState,
    )

_STUB_TOPIC_OVERVIEW = "テスト概要テキスト"


class _StubQuestionSetDesignLlm:
    def __init__(self, confirmation_points: list[ConfirmationPoint]) -> None:
        self._confirmation_points = confirmation_points

    def generate_confirmation_points(
        self,
        title: str,
        description: str,
        level: RoadmapItemLevel,
    ) -> QuestionSetDesignResult:
        return QuestionSetDesignResult(
            confirmation_points=list(self._confirmation_points),
            topic_overview=_STUB_TOPIC_OVERVIEW,
        )


def test_tc_02_question_set_design_public_contract_uses_confirmation_point_dto() -> (
    None
):
    # Arrange
    """テスト対象: design_question_set 関数。
    テストケース: 個別条件での処理を検証する。
    期待結果: 想定どおりの処理結果が得られる。"""
    confirmation_points: list[ConfirmationPoint] = [
        {
            "id": "cp_001",
            "content": "型推論が効く条件を説明できる",
            "format": "knowledge",
        },
        {
            "id": "cp_002",
            "content": "ジェネリクスを使った関数の利用例を示せる",
            "format": "knowledge_and_practice",
        },
    ]
    state: SessionState = {
        "roadmap_item_title": "TypeScript ジェネリクス",
        "roadmap_item_description": "型パラメータと型推論の理解を確認する",
        "roadmap_item_level": "detail",
    }

    # Act
    result = design_question_set(
        state,
        llm_client=_StubQuestionSetDesignLlm(confirmation_points),
    )

    # Assert
    returned_points = result["confirmation_points"]
    assert returned_points == confirmation_points
    assert result["current_point_index"] == 0
    assert isinstance(returned_points, list)
    ids = [point["id"] for point in returned_points]
    assert all(point_id != "" for point_id in ids)
    assert len(ids) == len(set(ids))
    for point in returned_points:
        assert point.keys() == {"id", "content", "format"}
        assert isinstance(point["id"], str)
        assert isinstance(point["content"], str)
        assert point["format"] in {"knowledge", "knowledge_and_practice"}
