"""roadmap 生成ジョブの受付・実行・検証を担う。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, NoReturn, cast

import structlog

from roadmap.domain.roadmap_generation_types import (
    RoadmapGenerationAccepted,
    RoadmapGenerationClock,
    RoadmapGenerationFailureCode,
    RoadmapGenerationInputError,
    RoadmapGenerationItemLevel,
    RoadmapGenerationJobIdGenerator,
    RoadmapGenerationJobScheduler,
    RoadmapGenerationJobStatus,
    RoadmapGenerationJobStatusStore,
    RoadmapGenerationJsonParseError,
    RoadmapGenerationLlmClient,
    RoadmapGenerationLlmError,
    RoadmapGenerationLlmResponseError,
    RoadmapGenerationPersistencePort,
    RoadmapGenerationScheduleError,
    RoadmapGenerationSchemaValidationError,
    ValidatedRoadmapGeneration,
    ValidatedRoadmapGenerationItem,
)
from roadmap.domain.roadmap_persistence_types import (
    RoadmapItemInput,
    RoadmapPersistenceInputError,
    RoadmapPersistenceWriteError,
    RoadmapSaveInput,
    RoadmapSaveResult,
)

if TYPE_CHECKING:
    from uuid import UUID

logger = structlog.get_logger(__name__)
EVENT_ACCEPTED = "roadmap_generation_accepted"
EVENT_INPUT_REJECTED = "roadmap_generation_input_rejected"
EVENT_SCHEDULE_FAILED = "roadmap_generation_schedule_failed"
EVENT_JOB_STARTED = "roadmap_generation_job_started"
EVENT_LLM_RETRY = "roadmap_generation_llm_retry"
EVENT_JOB_COMPLETED = "roadmap_generation_job_completed"
EVENT_JOB_FAILED = "roadmap_generation_job_failed"
_MAX_TOTAL_ATTEMPTS = 3
_ROOT_REQUIRED_FIELDS = frozenset({"topic", "items"})
_ITEM_REQUIRED_FIELDS = frozenset({"title", "description", "level", "children"})
_MAJOR_TITLE_FOUNDATION = "基礎"
_MAJOR_TITLE_ADVANCED = "応用"
_ALLOWED_LEVELS = frozenset({"major", "middle", "detail"})
_NEXT_LEVEL_BY_PARENT: dict[
    RoadmapGenerationItemLevel,
    RoadmapGenerationItemLevel | None,
] = {
    "major": "middle",
    "middle": "detail",
    "detail": None,
}


@dataclass(frozen=True)
class _ItemValidationContext:
    expected_level: RoadmapGenerationItemLevel
    expected_title: str | None = None
    path: str = "items"
    parent_level: RoadmapGenerationItemLevel | None = None


@dataclass(frozen=True)
class _FailureDetails:
    error_code: RoadmapGenerationFailureCode
    error_message: str
    error_type: str


def request_roadmap_generation(
    topic: str,
    *,
    job_id_generator: RoadmapGenerationJobIdGenerator,
    scheduler: RoadmapGenerationJobScheduler,
    job_store: RoadmapGenerationJobStatusStore,
) -> RoadmapGenerationAccepted:
    """roadmap 生成ジョブを受け付けて queue へ載せる。"""
    if topic.strip() == "":
        logger.warning(
            EVENT_INPUT_REJECTED,
            error_type=RoadmapGenerationInputError.__name__,
        )
        message = f"topic must be non-blank: got {topic!r}"
        raise RoadmapGenerationInputError(message)

    job_id = job_id_generator.generate()
    job_store.create_queued_job(job_id, topic)

    try:
        scheduler.enqueue_roadmap_generation(job_id, topic)
    except RoadmapGenerationScheduleError as exception:
        logger.exception(
            EVENT_SCHEDULE_FAILED,
            job_id=job_id,
            error_type=type(exception).__name__,
        )
        job_store.mark_failed(job_id, "schedule_failed", str(exception))
        raise

    logger.info(EVENT_ACCEPTED, job_id=job_id, topic=topic)
    return {"job_id": job_id, "status": "queued"}


def get_roadmap_generation_job(
    job_id: UUID,
    *,
    job_store: RoadmapGenerationJobStatusStore,
) -> RoadmapGenerationJobStatus:
    """job id に対応する roadmap 生成状態を返す。"""
    return job_store.get_job(job_id)


def _run_roadmap_generation_job(  # noqa: PLR0913
    job_id: UUID,
    topic: str,
    *,
    llm_client: RoadmapGenerationLlmClient,
    persistence: RoadmapGenerationPersistencePort,
    job_store: RoadmapGenerationJobStatusStore,
    clock: RoadmapGenerationClock,
) -> None:
    """バックグラウンドで roadmap 生成から保存までを実行する。"""
    job_store.mark_running(job_id)
    logger.info(EVENT_JOB_STARTED, job_id=job_id, topic=topic)

    try:
        generation = _generate_validated_roadmap(job_id, topic, llm_client=llm_client)
        save_result = _save_generated_roadmap(
            generation,
            clock=clock,
            persistence=persistence,
        )
    except RoadmapGenerationLlmResponseError as exception:
        _mark_failed_and_log(
            job_id,
            _llm_response_failure_details(exception),
            job_store=job_store,
        )
        return
    except RoadmapGenerationLlmError as exception:
        _mark_failed_and_log(
            job_id,
            _exception_failure_details("llm_request_failed", exception),
            job_store=job_store,
        )
        return
    except (RoadmapPersistenceWriteError, RoadmapPersistenceInputError) as exception:
        _mark_failed_and_log(
            job_id,
            _exception_failure_details("persistence_failed", exception),
            job_store=job_store,
        )
        return

    job_store.mark_completed(job_id, save_result.roadmap_id)
    logger.info(
        EVENT_JOB_COMPLETED,
        job_id=job_id,
        roadmap_id=save_result.roadmap_id,
    )


def _generate_validated_roadmap(
    job_id: UUID,
    topic: str,
    *,
    llm_client: RoadmapGenerationLlmClient,
) -> ValidatedRoadmapGeneration:
    """LLM 応答を再試行つきで取得し、保存可能な形まで検証する。"""
    for attempt in range(1, _MAX_TOTAL_ATTEMPTS + 1):
        try:
            raw_response = llm_client.generate_roadmap_json(topic)
            parsed = _parse_json(raw_response)
            return _validate_generation_payload(parsed, expected_topic=topic)
        except RoadmapGenerationLlmResponseError as exception:
            if attempt < _MAX_TOTAL_ATTEMPTS:
                # JSON 不正や schema 不一致は再試行で改善する余地があるため、
                # transport 失敗とは分けてここで吸収する。
                logger.warning(
                    EVENT_LLM_RETRY,
                    job_id=job_id,
                    attempt=attempt,
                    error_type=type(exception).__name__,
                )
                continue
            raise
    message = "LLM generation attempts exhausted unexpectedly"
    raise AssertionError(message)


def _parse_json(raw_response: str) -> Any:
    """LLM の生レスポンスを JSON として解釈する。"""
    try:
        return json.loads(raw_response)
    except json.JSONDecodeError as exception:
        message = f"LLM response is not valid JSON: {exception}"
        raise RoadmapGenerationJsonParseError(message) from exception


def _validate_generation_payload(
    payload: Any,
    *,
    expected_topic: str,
) -> ValidatedRoadmapGeneration:
    """LLM 応答の全体構造を検証し、保存用型へ変換する。"""
    if not isinstance(payload, dict):
        message = "LLM response root must be an object"
        raise RoadmapGenerationSchemaValidationError(message)
    _validate_object_fields(payload, required_fields=_ROOT_REQUIRED_FIELDS, path="root")

    topic = payload["topic"]
    items = payload["items"]

    validated_topic = _validate_root_topic(topic, expected_topic=expected_topic)
    items = _validate_root_items(items)

    validated_major_items = [
        _validate_item_payload(
            items[0],
            context=_ItemValidationContext(
                expected_level="major",
                expected_title=_MAJOR_TITLE_FOUNDATION,
                path="items[0]",
            ),
        ),
        _validate_item_payload(
            items[1],
            context=_ItemValidationContext(
                expected_level="major",
                expected_title=_MAJOR_TITLE_ADVANCED,
                path="items[1]",
            ),
        ),
    ]
    return ValidatedRoadmapGeneration(
        topic=validated_topic,
        items=validated_major_items,
    )


def _validate_item_payload(
    payload: Any,
    *,
    context: _ItemValidationContext,
) -> ValidatedRoadmapGenerationItem:
    """roadmap item を期待 level つきで再帰的に検証する。"""
    path = context.path
    if not isinstance(payload, dict):
        _raise_schema_validation(f"{path} must be an object")
    _validate_object_fields(payload, required_fields=_ITEM_REQUIRED_FIELDS, path=path)

    title = payload["title"]
    description = payload["description"]
    level = payload["level"]
    children = payload["children"]

    validated_title = _validate_item_title(
        title,
        expected_title=context.expected_title,
        path=path,
    )
    validated_description = _validate_item_description(description, path=path)
    validated_level = _validate_item_level(level, context=context)
    validated_children = _validate_item_children(
        children,
        level=validated_level,
        path=path,
    )

    if validated_level == "detail":
        return ValidatedRoadmapGenerationItem(
            title=validated_title,
            description=validated_description,
            level=validated_level,
            children=[],
        )

    return ValidatedRoadmapGenerationItem(
        title=validated_title,
        description=validated_description,
        level=validated_level,
        children=_validate_child_items(
            validated_children,
            parent_level=validated_level,
            path=path,
        ),
    )


def _validate_object_fields(
    payload: dict[str, Any],
    *,
    required_fields: frozenset[str],
    path: str,
) -> None:
    """必須項目と余分な項目をまとめて検証する。"""
    missing_fields = sorted(required_fields - set(payload))
    if missing_fields:
        missing = ", ".join(missing_fields)
        _raise_schema_validation(f"{path} missing required field(s): {missing}")

    extra_fields = sorted(set(payload) - required_fields)
    if extra_fields:
        extra = ", ".join(extra_fields)
        _raise_schema_validation(f"{path} contains field(s) not permitted: {extra}")


def _to_persistence_item(
    item: ValidatedRoadmapGenerationItem,
) -> RoadmapItemInput:
    """検証済み item を persistence 層の入力型へ写す。"""
    return RoadmapItemInput(
        title=item.title,
        description=item.description,
        level=item.level,
        children=[_to_persistence_item(child) for child in item.children],
    )


def _mark_failed_and_log(
    job_id: UUID,
    failure: _FailureDetails,
    *,
    job_store: RoadmapGenerationJobStatusStore,
) -> None:
    """job を失敗状態へ更新し、運用ログを残す。"""
    job_store.mark_failed(job_id, failure.error_code, failure.error_message)
    logger.exception(
        EVENT_JOB_FAILED,
        job_id=job_id,
        error_code=failure.error_code,
        error_type=failure.error_type,
    )


def _save_generated_roadmap(
    generation: ValidatedRoadmapGeneration,
    *,
    clock: RoadmapGenerationClock,
    persistence: RoadmapGenerationPersistencePort,
) -> RoadmapSaveResult:
    """検証済み roadmap を persistence 層へ保存する。"""
    roadmap_input = RoadmapSaveInput(
        topic=generation.topic,
        items=[_to_persistence_item(item) for item in generation.items],
        created_at=clock.now(),
    )
    return persistence.save_roadmap(roadmap_input)


def _validate_root_topic(topic: Any, *, expected_topic: str) -> str:
    """root topic が要求 topic と一致するか検証する。"""
    if not isinstance(topic, str):
        _raise_schema_validation(
            f"root.topic must be a string: got {type(topic).__name__}",
        )
    if topic != expected_topic:
        _raise_schema_validation(
            "root.topic must match input topic exactly: "
            f"expected {expected_topic!r}, got {topic!r}",
        )
    return topic


def _validate_root_items(items: Any) -> list[Any]:
    """root items が major 2件固定の構造を満たすか検証する。"""
    if not isinstance(items, list):
        _raise_schema_validation(
            f"root.items must be a list: got {type(items).__name__}",
        )
    if len(items) != 2:
        _raise_schema_validation(
            "root.items must contain at least 2 entries and exactly 2 are "
            f"required: got {len(items)}",
        )
    return items


def _validate_item_title(
    title: Any,
    *,
    expected_title: str | None,
    path: str,
) -> str:
    """item title の存在と、必要なら固定タイトル契約を検証する。"""
    if not isinstance(title, str):
        _raise_schema_validation(f"{path}.title must be a string: got {title!r}")
    if expected_title is not None and title != expected_title:
        _raise_schema_validation(
            f"{path}.title must be {expected_title!r}: got {title!r}",
        )
    return title


def _validate_item_description(description: Any, *, path: str) -> str:
    """item description の存在を検証する。"""
    if not isinstance(description, str):
        _raise_schema_validation(
            f"{path}.description must be a string: got {type(description).__name__}",
        )
    return description


def _validate_item_level(
    level: Any,
    *,
    context: _ItemValidationContext,
) -> RoadmapGenerationItemLevel:
    """parent との関係を含めて item level を検証する。"""
    if not isinstance(level, str) or level not in _ALLOWED_LEVELS:
        _raise_schema_validation(
            f"{context.path}.level must be one of {sorted(_ALLOWED_LEVELS)!r}: got {level!r}",
        )
    validated_level = cast("RoadmapGenerationItemLevel", level)
    if validated_level != context.expected_level:
        _raise_schema_validation(
            f"{context.path}.level is invalid for parent {context.parent_level!r}: "
            f"expected {context.expected_level!r}, got {validated_level!r}",
        )
    return validated_level


def _validate_item_children(
    children: Any,
    *,
    level: RoadmapGenerationItemLevel,
    path: str,
) -> list[Any]:
    """children の容器型と detail item の空配列契約を検証する。"""
    if not isinstance(children, list):
        _raise_schema_validation(f"{path}.children must be a list: got {children!r}")
    if level == "detail" and children != []:
        _raise_schema_validation(f"{path}.children must be empty for detail items")
    return children


def _validate_child_items(
    children: list[Any],
    *,
    parent_level: RoadmapGenerationItemLevel,
    path: str,
) -> list[ValidatedRoadmapGenerationItem]:
    """親 level から導かれる次 level で子 item 群を検証する。"""
    next_level = _next_level_for(parent_level)
    return [
        _validate_item_payload(
            child,
            context=_ItemValidationContext(
                expected_level=next_level,
                path=f"{path}.children[{index}]",
                parent_level=parent_level,
            ),
        )
        for index, child in enumerate(children)
    ]


def _next_level_for(level: RoadmapGenerationItemLevel) -> RoadmapGenerationItemLevel:
    """親 level から子 level を導く。"""
    next_level = _NEXT_LEVEL_BY_PARENT[level]
    if next_level is None:
        message = f"next level missing for non-detail level: {level!r}"
        raise AssertionError(message)
    return next_level


def _llm_response_failure_details(
    exception: RoadmapGenerationLlmResponseError,
) -> _FailureDetails:
    """LLM 応答不正を job failure 詳細へ正規化する。"""
    error_code: RoadmapGenerationFailureCode
    if isinstance(exception, RoadmapGenerationJsonParseError):
        error_code = "llm_json_parse_failed"
    else:
        error_code = "llm_schema_validation_failed"
    return _exception_failure_details(error_code, exception)


def _exception_failure_details(
    error_code: RoadmapGenerationFailureCode,
    exception: Exception,
) -> _FailureDetails:
    """例外を job store とログ用の failure 情報へ変換する。"""
    return _FailureDetails(
        error_code=error_code,
        error_message=str(exception),
        error_type=type(exception).__name__,
    )


def _raise_schema_validation(message: str) -> NoReturn:
    """schema 検証失敗を統一例外へ寄せる。"""
    raise RoadmapGenerationSchemaValidationError(message)


__all__ = [
    "EVENT_ACCEPTED",
    "EVENT_INPUT_REJECTED",
    "EVENT_JOB_COMPLETED",
    "EVENT_JOB_FAILED",
    "EVENT_JOB_STARTED",
    "EVENT_LLM_RETRY",
    "EVENT_SCHEDULE_FAILED",
    "get_roadmap_generation_job",
    "request_roadmap_generation",
]
