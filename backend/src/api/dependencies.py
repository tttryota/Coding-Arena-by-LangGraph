"""アプリ全体で共有する依存オブジェクトを組み立てる。"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

from infrastructure.llm.codex_transport import CodexLlmTransport
from infrastructure.uuid_generator import UuidGenerator

if TYPE_CHECKING:
    from collections.abc import Callable
    from uuid import UUID

    from sqlalchemy import Engine


class Container:
    """アプリ全体の依存を束ねるコンテナ。

    router からはこのインスタンスだけを参照し、具体実装の選択はここに閉じ込める。
    そうすることで API 層は「どの機能が使えるか」だけを判定すればよく、
    具体クラスの import や初期化順序を意識しなくて済む。
    """

    graph_runner: Any
    coding_graph_runner: Any
    competitive_graph_runner: Any
    quiz_checkpointer: Any
    competitive_checkpointer: Any
    coding_checkpointer: Any
    competitive_question_llm: Any
    algorithm_foundation_solution_evaluator: Any
    algorithm_foundation_language_adapter: Any
    sql_dojo_feedback_llm: Any
    sql_dojo_question_llm: Any

    def __init__(
        self,
        engine: Engine,
        preset_topics_path: str = "data/preset_topics.json",
    ) -> None:
        self._engine = engine
        self._preset_topics_path = preset_topics_path
        self.transport = CodexLlmTransport()
        self.uuid_generator = UuidGenerator()
        self.executor = ThreadPoolExecutor(max_workers=2)
        try:
            # 初期化順序は、下流の依存解決が読みやすいまとまりを優先する。
            # 先に store を作っておくと、後段の graph / adapter 初期化が
            # 「何を受け取るか」を追いやすい。
            self._init_quiz_stores()
            self._init_roadmap_stores()
            self._init_llm_clients()
            self._init_graph_runner()
            self._init_competitive()
            self._init_algorithm_foundations()
            self._init_sql_dojo()
            self._init_coding_graph()
            self._init_scheduler()
        except Exception:
            # 一部初期化後に失敗しても executor を残さない。
            self.executor.shutdown(wait=False)
            raise

    def _init_quiz_stores(self) -> None:
        """quiz セッションの永続化に必要な store 群を初期化する。"""
        from quiz.infrastructure.sql_progress_update_store import (
            SqlProgressUpdateStore,
        )
        from quiz.infrastructure.sql_quiz_answer_store import SqlQuizAnswerStore
        from quiz.infrastructure.sql_quiz_session_store import SqlQuizSessionStore
        from quiz.infrastructure.sql_roadmap_item_read_store import (
            SqlRoadmapItemReadStore,
        )
        from quiz.infrastructure.sql_summary_test_result_store import (
            SqlSummaryTestResultStore,
        )

        self.quiz_session_store = SqlQuizSessionStore(self._engine)
        self.quiz_answer_store = SqlQuizAnswerStore(self._engine)
        self.roadmap_item_read_store = SqlRoadmapItemReadStore(self._engine)
        self.progress_update_store = SqlProgressUpdateStore(self._engine)
        self.summary_test_result_store = SqlSummaryTestResultStore(self._engine)

    def _init_roadmap_stores(self) -> None:
        """roadmap の一覧・生成ジョブ・手動 topic 管理を束ねる store を作る。"""
        from roadmap.infrastructure.in_memory_job_status_store import (
            InMemoryJobStatusStore,
        )
        from roadmap.infrastructure.preset_topic_file_reader import (
            PresetTopicFileReader,
        )
        from roadmap.infrastructure.sql_roadmap_item_crud_store import (
            SqlRoadmapItemCrudStore,
        )
        from roadmap.infrastructure.sql_roadmap_persistence_writer import (
            SqlRoadmapPersistenceWriter,
        )
        from roadmap.infrastructure.sql_roadmap_retrieval_reader import (
            SqlRoadmapRetrievalReader,
        )
        from roadmap.infrastructure.sql_topic_store import SqlTopicStore

        self.roadmap_persistence_writer = SqlRoadmapPersistenceWriter(self._engine)
        self.roadmap_retrieval_reader = SqlRoadmapRetrievalReader(self._engine)
        self.roadmap_item_crud_store = SqlRoadmapItemCrudStore(self._engine)
        self.job_status_store = InMemoryJobStatusStore()
        self.topic_store = SqlTopicStore(self._engine)
        self.preset_reader = PresetTopicFileReader(self._preset_topics_path)

    def _init_llm_clients(self) -> None:
        """各ユースケース向けの LLM adapter を生成する。"""
        from quiz.infrastructure.codex_llm_adapters import (
            CodexAnswerEvaluationLlm,
            CodexChatResponseLlm,
            CodexExplanationLlm,
            CodexInputClassificationLlm,
            CodexProgressUpdateLlm,
            CodexQuestionDeliveryLlm,
            CodexQuestionSetDesignLlm,
            CodexSummaryTestLlm,
        )
        from roadmap.infrastructure.codex_roadmap_generation_llm import (
            CodexRoadmapGenerationLlm,
        )

        t = self.transport
        self.question_set_design_llm = CodexQuestionSetDesignLlm(t)
        self.question_delivery_llm = CodexQuestionDeliveryLlm(t)
        self.input_classification_llm = CodexInputClassificationLlm(t)
        self.chat_response_llm = CodexChatResponseLlm(t)
        self.answer_evaluation_llm = CodexAnswerEvaluationLlm(t)
        self.explanation_llm = CodexExplanationLlm(t)
        self.progress_update_llm = CodexProgressUpdateLlm(t)
        self.summary_test_llm = CodexSummaryTestLlm(t)
        self.roadmap_generation_llm = CodexRoadmapGenerationLlm(t)

    def _init_graph_runner(self) -> None:
        """通常 quiz 用の LangGraph 実行器を初期化する。"""
        # MemorySaver はプロセス内保存なので、再起動をまたぐ復旧契約は持たせない。
        from langgraph.checkpoint.memory import MemorySaver

        from quiz.application.graph import QuizGraphRunner, build_graph
        from quiz.application.graph_types import GraphDependencies

        deps = GraphDependencies(
            question_set_design_llm=self.question_set_design_llm,
            question_delivery_llm=self.question_delivery_llm,
            input_classification_llm=cast("Any", self.input_classification_llm),
            chat_response_llm=self.chat_response_llm,
            answer_evaluation_llm=cast("Any", self.answer_evaluation_llm),
            explanation_llm=self.explanation_llm,
            progress_update_llm=self.progress_update_llm,
            progress_update_store=self.progress_update_store,
            summary_test_llm=self.summary_test_llm,
            summary_test_store=self.summary_test_result_store,
        )
        self.quiz_checkpointer = MemorySaver()
        compiled = build_graph(deps, checkpointer=self.quiz_checkpointer)
        self.graph_runner = QuizGraphRunner(compiled)

    def _init_competitive(self) -> None:
        """競プロセッション用の graph と永続化 store を初期化する。"""
        from langgraph.checkpoint.memory import MemorySaver

        from competitive.application.competitive_graph import (
            CompetitiveGraphDependencies,
            CompetitiveGraphRunner,
            build_competitive_graph,
        )
        from competitive.infrastructure.codex_competitive_llm import (
            CodexCompetitiveProblemGenerationLlm,
            CodexCompetitiveQuestionResponseLlm,
            CodexCompetitiveSolutionEvaluationLlm,
        )
        from competitive.infrastructure.sql_algo_theme_reader import (
            SqlAlgoThemeReader,
        )
        from competitive.infrastructure.sql_competitive_store import (
            SqlCompetitiveStore,
        )

        self.algo_theme_reader = SqlAlgoThemeReader(self._engine)
        self.competitive_store = SqlCompetitiveStore(self._engine)
        problem_llm = CodexCompetitiveProblemGenerationLlm(self.transport)
        eval_llm = CodexCompetitiveSolutionEvaluationLlm(self.transport)
        self.competitive_question_llm = CodexCompetitiveQuestionResponseLlm(
            self.transport,
        )
        deps = CompetitiveGraphDependencies(
            theme_reader=self.algo_theme_reader,
            problem_generation_llm=problem_llm,
            solution_evaluation_llm=cast("Any", eval_llm),
        )
        self.competitive_checkpointer = MemorySaver()
        compiled = build_competitive_graph(
            deps,
            checkpointer=self.competitive_checkpointer,
        )
        self.competitive_graph_runner = CompetitiveGraphRunner(compiled)

    def _init_sql_dojo(self) -> None:
        """SQL道場のテーマバンク・store・LLM を初期化する。"""
        from sql_dojo.infrastructure.codex_sql_dojo_llm import (
            CodexSqlDojoFeedbackLlm,
            CodexSqlDojoQuestionLlm,
        )
        from sql_dojo.infrastructure.sql_sql_dojo_store import SqlSqlDojoStore
        from sql_dojo.infrastructure.sql_theme_bank import SqlThemeBank

        self.sql_theme_bank = SqlThemeBank()
        self.sql_dojo_store = SqlSqlDojoStore(self._engine)
        self.sql_dojo_feedback_llm = CodexSqlDojoFeedbackLlm(self.transport)
        self.sql_dojo_question_llm = CodexSqlDojoQuestionLlm(self.transport)

    def _init_algorithm_foundations(self) -> None:
        """競プロうさぎの静的カタログと store を初期化する。"""
        from algorithm_foundations.infrastructure.codex_foundation_language_adapter import (
            CodexAlgorithmFoundationLanguageAdapter,
        )
        from algorithm_foundations.infrastructure.foundation_catalog import (
            AlgorithmFoundationCatalog,
        )
        from algorithm_foundations.infrastructure.sql_foundation_store import (
            SqlAlgorithmFoundationStore,
        )
        from competitive.infrastructure.codex_competitive_llm import (
            CodexCompetitiveSolutionEvaluationLlm,
        )

        self.algorithm_foundation_catalog = AlgorithmFoundationCatalog()
        self.algorithm_foundation_store = SqlAlgorithmFoundationStore(self._engine)
        self.algorithm_foundation_language_adapter = (
            CodexAlgorithmFoundationLanguageAdapter(self.transport)
        )
        self.algorithm_foundation_solution_evaluator = (
            CodexCompetitiveSolutionEvaluationLlm(self.transport)
        )

    def _init_coding_graph(self) -> None:
        """座学 + 練習のコーディングセッション用 graph を初期化する。"""
        from langgraph.checkpoint.memory import MemorySaver

        from quiz.application.coding_graph import (
            CodingGraphDependencies,
            CodingGraphRunner,
            build_coding_graph,
        )
        from quiz.infrastructure.codex_coding_llm_adapters import (
            CodexCodeEvaluationLlm,
            CodexCodingProblemDeliveryLlm,
            CodexCodingProblemSetDesignLlm,
            CodexLectureChatResponseLlm,
            CodexLectureGenerationLlm,
        )

        t = self.transport
        deps = CodingGraphDependencies(
            lecture_generation_llm=CodexLectureGenerationLlm(t),
            lecture_chat_response_llm=CodexLectureChatResponseLlm(t),
            coding_problem_set_design_llm=cast(
                "Any",
                CodexCodingProblemSetDesignLlm(t),
            ),
            coding_problem_delivery_llm=CodexCodingProblemDeliveryLlm(t),
            coding_chat_response_llm=CodexLectureChatResponseLlm(t),
            code_evaluation_llm=CodexCodeEvaluationLlm(t),
        )
        self.coding_checkpointer = MemorySaver()
        compiled = build_coding_graph(deps, checkpointer=self.coding_checkpointer)
        self.coding_graph_runner = CodingGraphRunner(compiled)

    def _init_scheduler(self) -> None:
        """roadmap 生成ジョブを別スレッドで流す実行器を用意する。"""
        from roadmap.infrastructure.thread_pool_scheduler import (
            ThreadPoolJobScheduler,
        )

        self.job_scheduler = ThreadPoolJobScheduler(
            executor=self.executor,
            job_runner=self._make_job_runner(),
        )

    def _make_job_runner(self) -> Callable[[UUID, str], None]:
        """scheduler に渡す roadmap 生成ジョブ本体を閉包で束ねる。"""
        from roadmap.application.roadmap_generation import (
            _run_roadmap_generation_job,
        )

        llm = self.roadmap_generation_llm
        persistence = self.roadmap_persistence_writer
        job_store = self.job_status_store
        clock = _UtcClock()

        def runner(job_id: UUID, topic: str) -> None:
            _run_roadmap_generation_job(
                job_id,
                topic,
                llm_client=llm,
                persistence=persistence,
                job_store=job_store,
                clock=clock,
            )

        return runner

    def shutdown(self) -> None:
        """アプリ終了時にバックグラウンド executor と子プロセスを停止する。"""
        close_transport = getattr(self.transport, "close", None)
        if callable(close_transport):
            close_transport()
        self.executor.shutdown(wait=True)

    def delete_quiz_checkpoint(self, session_id: str) -> None:
        """完了済み通常 quiz の LangGraph checkpoint を破棄する。"""
        if hasattr(self, "quiz_checkpointer"):
            self.quiz_checkpointer.delete_thread(session_id)

    def delete_competitive_checkpoint(self, session_id: str) -> None:
        """完了済み競プロ session の LangGraph checkpoint を破棄する。"""
        if hasattr(self, "competitive_checkpointer"):
            self.competitive_checkpointer.delete_thread(session_id)

    def delete_coding_checkpoint(self, session_id: str) -> None:
        """完了済み coding session の LangGraph checkpoint を破棄する。"""
        if hasattr(self, "coding_checkpointer"):
            self.coding_checkpointer.delete_thread(session_id)


class _UtcClock:
    def now(self) -> str:
        """UTC の現在時刻を ISO 8601 文字列で返す。"""
        return datetime.now(tz=UTC).isoformat()


__all__ = ["Container"]
