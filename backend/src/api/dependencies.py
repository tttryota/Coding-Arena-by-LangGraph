"""DI container: Settings -> concrete instances."""

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

    from ingestion.domain.embedder_types import EmbeddingModel


class Container:
    """Application-level DI container."""

    graph_runner: Any
    coding_graph_runner: Any
    competitive_graph_runner: Any
    batch_embedder: Any

    def __init__(  # noqa: PLR0915
        self,
        engine: Engine,
        chroma_collection: object,
        embedder: object | None = None,
        preset_topics_path: str = "data/preset_topics.json",
    ) -> None:
        self._engine = engine
        self._chroma = chroma_collection
        self._embedder = embedder
        self._preset_topics_path = preset_topics_path
        self.transport = CodexLlmTransport()
        self.uuid_generator = UuidGenerator()
        self.executor = ThreadPoolExecutor(max_workers=2)
        try:
            self._init_quiz_stores()
            self._init_roadmap_stores()
            self._init_ingestion_stores()
            self._init_llm_clients()
            self._init_chroma_clients()
            self._init_graph_runner()
            self._init_competitive()
            self._init_coding_graph()
            self._init_scheduler()
            self._init_batch_adapters()
        except Exception:
            self.executor.shutdown(wait=False)
            raise

    def _init_quiz_stores(self) -> None:
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

    def _init_ingestion_stores(self) -> None:
        from ingestion.infrastructure.sql_file_diff_snapshot_store import (
            SqlFileDiffSnapshotStore,
        )
        from ingestion.infrastructure.sql_ingestion_feedback_store import (
            SqlIngestionFeedbackStore,
        )

        self.ingestion_feedback_store = SqlIngestionFeedbackStore(self._engine)
        self.diff_snapshot_store = SqlFileDiffSnapshotStore(self._engine)

    def _init_llm_clients(self) -> None:
        from ingestion.infrastructure.codex_ingestion_feedback_llm import (
            CodexIngestionFeedbackLlm,
        )
        from ingestion.infrastructure.codex_llm_tag_classifier import (
            CodexLlmTagClassifier,
        )
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
        self.ingestion_feedback_llm = CodexIngestionFeedbackLlm(t)
        self.tag_classifier = CodexLlmTagClassifier(t)

    def _init_chroma_clients(self) -> None:
        from ingestion.infrastructure.chroma_chunk_store import (
            ChromaChunkStore,
            ChunkCollection,
        )
        from quiz.infrastructure.chroma_explanation_rag import (
            ChromaExplanationRagClient,
            ChromaQueryCollection,
        )
        from roadmap.infrastructure.chroma_note_topic_reader import (
            ChromaMetadataCollection,
            ChromaNoteTopicReader,
        )

        self.chunk_store = ChromaChunkStore(cast("ChunkCollection", self._chroma))
        self.explanation_rag_client: Any | None = None
        if self._embedder is not None:
            self.explanation_rag_client = ChromaExplanationRagClient(
                cast("ChromaQueryCollection", self._chroma),
                cast("EmbeddingModel", self._embedder),
            )
        self.note_topic_reader = ChromaNoteTopicReader(
            cast("ChromaMetadataCollection", self._chroma),
        )

    def _init_graph_runner(self) -> None:
        # MemorySaver: in-memory checkpointer。プロセス再起動で interrupt 中のセッションは失われる。
        from langgraph.checkpoint.memory import MemorySaver

        from quiz.application.graph import QuizGraphRunner, build_graph
        from quiz.application.graph_types import GraphDependencies

        if self.explanation_rag_client is None:
            self.graph_runner = None
            return
        deps = GraphDependencies(
            question_set_design_llm=self.question_set_design_llm,
            question_delivery_llm=self.question_delivery_llm,
            input_classification_llm=cast("Any", self.input_classification_llm),
            chat_response_llm=self.chat_response_llm,
            answer_evaluation_llm=cast("Any", self.answer_evaluation_llm),
            explanation_rag=self.explanation_rag_client,
            explanation_llm=self.explanation_llm,
            progress_update_llm=self.progress_update_llm,
            progress_update_store=self.progress_update_store,
            summary_test_llm=self.summary_test_llm,
            summary_test_store=self.summary_test_result_store,
        )
        compiled = build_graph(deps, checkpointer=MemorySaver())
        self.graph_runner = QuizGraphRunner(compiled)

    def _init_competitive(self) -> None:
        from langgraph.checkpoint.memory import MemorySaver

        from competitive.application.competitive_graph import (
            CompetitiveGraphDependencies,
            CompetitiveGraphRunner,
            build_competitive_graph,
        )
        from competitive.infrastructure.codex_competitive_llm import (
            CodexCompetitiveProblemGenerationLlm,
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
        deps = CompetitiveGraphDependencies(
            theme_reader=self.algo_theme_reader,
            problem_generation_llm=problem_llm,
            solution_evaluation_llm=cast("Any", eval_llm),
        )
        compiled = build_competitive_graph(deps, checkpointer=MemorySaver())
        self.competitive_graph_runner = CompetitiveGraphRunner(compiled)

    def _init_coding_graph(self) -> None:
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
                "Any", CodexCodingProblemSetDesignLlm(t),
            ),
            coding_problem_delivery_llm=CodexCodingProblemDeliveryLlm(t),
            coding_chat_response_llm=CodexLectureChatResponseLlm(t),
            code_evaluation_llm=CodexCodeEvaluationLlm(t),
        )
        compiled = build_coding_graph(deps, checkpointer=MemorySaver())
        self.coding_graph_runner = CodingGraphRunner(compiled)

    def _init_scheduler(self) -> None:
        from roadmap.infrastructure.thread_pool_scheduler import (
            ThreadPoolJobScheduler,
        )

        self.job_scheduler = ThreadPoolJobScheduler(
            executor=self.executor,
            job_runner=self._make_job_runner(),
        )

    def _make_job_runner(self) -> Callable[[UUID, str], None]:
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

    def _init_batch_adapters(self) -> None:
        from ingestion.infrastructure.batch_adapters import (
            ChunkSplitterAdapter,
            ChunkTaggerAdapter,
            DefaultTaggingPromptStrategy,
            EmbedderAdapter,
            FileDiffDetectorAdapter,
            SimpleTokenCounter,
        )
        from ingestion.infrastructure.ingestion_feedback_hook import (
            IngestionFeedbackHook,
            RoadmapItemReaderAdapter,
        )

        self.batch_diff_detector = FileDiffDetectorAdapter(self.diff_snapshot_store)
        self.batch_chunk_splitter = ChunkSplitterAdapter(SimpleTokenCounter())
        self.batch_chunk_tagger = ChunkTaggerAdapter(
            DefaultTaggingPromptStrategy(),
            self.tag_classifier,
        )
        if self._embedder is not None:
            self.batch_embedder = EmbedderAdapter(cast("Any", self._embedder))
        else:
            self.batch_embedder = None
        self.post_ingestion_hook = IngestionFeedbackHook(
            llm_client=self.ingestion_feedback_llm,
            roadmap_reader=RoadmapItemReaderAdapter(self.roadmap_retrieval_reader),
            writer=self.ingestion_feedback_store,
        )

    def shutdown(self) -> None:
        self.executor.shutdown(wait=True)


class _UtcClock:
    def now(self) -> str:
        return datetime.now(tz=UTC).isoformat()


__all__ = ["Container"]
