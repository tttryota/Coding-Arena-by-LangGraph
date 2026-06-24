from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from algorithm_foundations.infrastructure.sql_foundation_store import (
    SqlAlgorithmFoundationStore,
)
from infrastructure.rdb.base import Base


def _store() -> SqlAlgorithmFoundationStore:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return SqlAlgorithmFoundationStore(engine)


def test_store_persists_session_answer_and_history() -> None:
    store = _store()
    store.create_session(
        session_id="00000000-0000-0000-0000-000000000001",
        unit_id="algo-102-hashmap-count",
        group_id="group-0",
        group_title="データ構造",
        unit_title="出現回数カウント",
        target_skill="出現回数カウント",
        unit_kind="foundation",
        prerequisite_unit_ids=["algo-102-hashmap-exists"],
        prerequisite_titles=["存在判定をハッシュで高速化"],
        allowed_knowledge=["出現回数カウント"],
        forbidden_knowledge=["尺取り法"],
        programming_language="python",
        problem_id="p-1",
        problem_title="問題1",
        problem_statement="問題文1",
        input_format="入力",
        output_format="出力",
        constraints="制約",
        examples=[{"input": "1", "output": "1"}],
        reference_solution="def solve(): pass",
        grading_rubric=[{"criterion": "正しさ", "points": 100, "description": "ok"}],
    )
    store.create_session(
        session_id="00000000-0000-0000-0000-000000000002",
        unit_id="algo-102-hashmap-count",
        group_id="group-0",
        group_title="データ構造",
        unit_title="出現回数カウント",
        target_skill="出現回数カウント",
        unit_kind="foundation",
        prerequisite_unit_ids=["algo-102-hashmap-exists"],
        prerequisite_titles=["存在判定をハッシュで高速化"],
        allowed_knowledge=["出現回数カウント"],
        forbidden_knowledge=["尺取り法"],
        programming_language="python",
        problem_id="p-2",
        problem_title="問題2",
        problem_statement="問題文2",
        input_format="入力",
        output_format="出力",
        constraints="制約",
        examples=[{"input": "2", "output": "2"}],
        reference_solution="def solve(): pass",
        grading_rubric=[{"criterion": "正しさ", "points": 100, "description": "ok"}],
    )

    details = store.get_session_details("00000000-0000-0000-0000-000000000001")
    assert details["unit_id"] == "algo-102-hashmap-count"
    assert details["allowed_knowledge"] == ["出現回数カウント"]

    recent_problem_ids = store.list_recent_problem_ids_for_unit("algo-102-hashmap-count")
    assert recent_problem_ids == []

    store.save_answer_and_complete(
        session_id="00000000-0000-0000-0000-000000000001",
        answer_text="print(1)",
        score=88,
        feedback="ok",
        time_complexity="O(N)",
        space_complexity="O(N)",
        improvement_suggestions="none",
        rubric_scores_json="[]",
    )

    answer = store.find_answer_by_session("00000000-0000-0000-0000-000000000001")
    assert answer is not None
    assert answer.score == 88

    recent_problem_ids = store.list_recent_problem_ids_for_unit("algo-102-hashmap-count")
    assert recent_problem_ids == ["p-1"]

    history = store.list_unit_history()
    assert history[0].unit_id == "algo-102-hashmap-count"
    assert history[0].attempt_count == 1
    assert history[0].best_score == 88
