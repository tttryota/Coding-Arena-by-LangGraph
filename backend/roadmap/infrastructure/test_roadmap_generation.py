from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import is_dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    cast,
    get_args,
    is_typeddict,
)
from uuid import UUID

if TYPE_CHECKING:
    from collections.abc import MutableMapping

import pytest
from structlog.testing import capture_logs

from roadmap.domain.roadmap_generation_types import (
    RoadmapGenerationAccepted,
    RoadmapGenerationCompletedStatus,
    RoadmapGenerationError,
    RoadmapGenerationFailedStatus,
    RoadmapGenerationFailureCode,
    RoadmapGenerationInputError,
    RoadmapGenerationJobNotFoundError,
    RoadmapGenerationJobStatus,
    RoadmapGenerationJobStoreError,
    RoadmapGenerationJsonParseError,
    RoadmapGenerationLlmError,
    RoadmapGenerationLlmResponseError,
    RoadmapGenerationQueuedStatus,
    RoadmapGenerationRunningStatus,
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
from roadmap.infrastructure.roadmap_generation import (
    EVENT_ACCEPTED,
    EVENT_INPUT_REJECTED,
    EVENT_JOB_COMPLETED,
    EVENT_JOB_FAILED,
    EVENT_JOB_STARTED,
    EVENT_LLM_RETRY,
    EVENT_SCHEDULE_FAILED,
    _run_roadmap_generation_job,
    get_roadmap_generation_job,
    request_roadmap_generation,
)
from shared.log_assertions import assert_no_log_event as _assert_no_log_event
from shared.log_assertions import assert_single_log_event as _assert_single_log_event
from shared.log_assertions import find_log_events

_JOB_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_SECOND_JOB_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_ROADMAP_ID = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_TOPIC = "  TypeScript  "
_SECOND_TOPIC = "Data Engineering"
_CREATED_AT = "2026-05-21T12:00:00+09:00"
_FAILURE_CODES = (
    "schedule_failed",
    "llm_request_failed",
    "llm_json_parse_failed",
    "llm_schema_validation_failed",
    "persistence_failed",
)
_JOB_ID_FIELDS = frozenset({"job_id"})
_JOB_AND_ROADMAP_ID_FIELDS = frozenset({"job_id", "roadmap_id"})


class _RecordingJobIdGenerator:
    def __init__(
        self,
        generated_ids: list[UUID],
        *,
        operation_log: list[str] | None = None,
    ) -> None:
        self._generated_ids = list(generated_ids)
        self._operation_log = operation_log
        self.calls = 0

    def generate(self) -> UUID:
        self.calls += 1
        if self._operation_log is not None:
            self._operation_log.append("generate")
        assert self._generated_ids
        return self._generated_ids.pop(0)

    def __getattr__(self, name: str) -> object:
        message = f"unexpected job id generator attribute access: {name}"
        raise AssertionError(message)


class _RecordingScheduler:
    def __init__(
        self,
        *,
        error: Exception | None = None,
        operation_log: list[str] | None = None,
    ) -> None:
        self._error = error
        self._operation_log = operation_log
        self.calls: list[dict[str, object]] = []

    def enqueue_roadmap_generation(self, job_id: UUID, topic: str) -> None:
        self.calls.append({"job_id": job_id, "topic": topic})
        if self._operation_log is not None:
            self._operation_log.append("enqueue_roadmap_generation")
        if self._error is not None:
            raise self._error

    def __getattr__(self, name: str) -> object:
        message = f"unexpected scheduler attribute access: {name}"
        raise AssertionError(message)


class _RecordingJobStore:
    def __init__(
        self,
        *,
        get_job_result: RoadmapGenerationJobStatus | None = None,
        create_queued_job_error: Exception | None = None,
        mark_running_error: Exception | None = None,
        mark_completed_error: Exception | None = None,
        mark_failed_error: Exception | None = None,
        get_job_error: Exception | None = None,
        operation_log: list[str] | None = None,
    ) -> None:
        self._get_job_result = get_job_result
        self._create_queued_job_error = create_queued_job_error
        self._mark_running_error = mark_running_error
        self._mark_completed_error = mark_completed_error
        self._mark_failed_error = mark_failed_error
        self._get_job_error = get_job_error
        self._operation_log = operation_log
        self.create_queued_job_calls: list[dict[str, object]] = []
        self.mark_running_calls: list[UUID] = []
        self.mark_completed_calls: list[dict[str, object]] = []
        self.mark_failed_calls: list[dict[str, object]] = []
        self.get_job_calls: list[UUID] = []

    def create_queued_job(self, job_id: UUID, topic: str) -> None:
        self.create_queued_job_calls.append({"job_id": job_id, "topic": topic})
        if self._operation_log is not None:
            self._operation_log.append("create_queued_job")
        if self._create_queued_job_error is not None:
            raise self._create_queued_job_error

    def mark_running(self, job_id: UUID) -> None:
        self.mark_running_calls.append(job_id)
        if self._operation_log is not None:
            self._operation_log.append("mark_running")
        if self._mark_running_error is not None:
            raise self._mark_running_error

    def mark_completed(self, job_id: UUID, roadmap_id: UUID) -> None:
        self.mark_completed_calls.append(
            {"job_id": job_id, "roadmap_id": roadmap_id},
        )
        if self._operation_log is not None:
            self._operation_log.append("mark_completed")
        if self._mark_completed_error is not None:
            raise self._mark_completed_error

    def mark_failed(
        self,
        job_id: UUID,
        error_code: RoadmapGenerationFailureCode,
        error_message: str,
    ) -> None:
        self.mark_failed_calls.append(
            {
                "job_id": job_id,
                "error_code": error_code,
                "error_message": error_message,
            },
        )
        if self._operation_log is not None:
            self._operation_log.append("mark_failed")
        if self._mark_failed_error is not None:
            raise self._mark_failed_error

    def get_job(self, job_id: UUID) -> RoadmapGenerationJobStatus:
        self.get_job_calls.append(job_id)
        if self._get_job_error is not None:
            raise self._get_job_error
        assert self._get_job_result is not None
        return self._get_job_result

    def __getattr__(self, name: str) -> object:
        message = f"unexpected job store attribute access: {name}"
        raise AssertionError(message)


class _RecordingLlmClient:
    def __init__(
        self,
        scripted_results: list[str | RoadmapGenerationLlmError],
        *,
        operation_log: list[str] | None = None,
    ) -> None:
        self._scripted_results = list(scripted_results)
        self._operation_log = operation_log
        self.calls: list[str] = []

    def generate_roadmap_json(self, topic: str) -> str:
        self.calls.append(topic)
        if self._operation_log is not None:
            self._operation_log.append("generate_roadmap_json")
        assert self._scripted_results
        result = self._scripted_results.pop(0)
        if isinstance(result, RoadmapGenerationLlmError):
            raise result
        return result

    def __getattr__(self, name: str) -> object:
        message = f"unexpected llm client attribute access: {name}"
        raise AssertionError(message)


class _RecordingPersistence:
    def __init__(
        self,
        *,
        result: RoadmapSaveResult | None = None,
        error: Exception | None = None,
        operation_log: list[str] | None = None,
    ) -> None:
        self._result = result or RoadmapSaveResult(
            roadmap_id=_ROADMAP_ID,
            saved_count=4,
        )
        self._error = error
        self._operation_log = operation_log
        self.inputs: list[RoadmapSaveInput] = []

    def save_roadmap(self, roadmap_input: RoadmapSaveInput) -> RoadmapSaveResult:
        self.inputs.append(roadmap_input)
        if self._operation_log is not None:
            self._operation_log.append("save_roadmap")
        if self._error is not None:
            raise self._error
        return self._result

    def __getattr__(self, name: str) -> object:
        message = f"unexpected persistence attribute access: {name}"
        raise AssertionError(message)


class _RecordingClock:
    def __init__(
        self,
        now_value: str = _CREATED_AT,
        *,
        operation_log: list[str] | None = None,
    ) -> None:
        self._now_value = now_value
        self._operation_log = operation_log
        self.calls = 0

    def now(self) -> str:
        self.calls += 1
        if self._operation_log is not None:
            self._operation_log.append("now")
        return self._now_value

    def __getattr__(self, name: str) -> object:
        message = f"unexpected clock attribute access: {name}"
        raise AssertionError(message)


def _assert_retry_events(
    log_output: list[MutableMapping[str, Any]],
    *,
    expected_error_types: list[str],
) -> None:
    retry_events = find_log_events(log_output, EVENT_LLM_RETRY, log_level="warning")
    assert len(retry_events) == len(expected_error_types)
    assert [event["error_type"] for event in retry_events] == expected_error_types
    assert [event["attempt"] for event in retry_events] == list(
        range(1, len(expected_error_types) + 1),
    )
    assert [str(event["job_id"]) for event in retry_events] == [str(_JOB_ID)] * len(
        expected_error_types,
    )


def _to_required_item_tree(items: list[RoadmapItemInput]) -> list[dict[str, object]]:
    return [
        {
            "title": item.title,
            "description": item.description,
            "level": item.level,
            "children": _to_required_item_tree(item.children),
        }
        for item in items
    ]


def _payload_items_to_required_tree(
    items: list[dict[str, object]],
) -> list[dict[str, object]]:
    return [
        {
            "title": item["title"],
            "description": item["description"],
            "level": item["level"],
            "children": _payload_items_to_required_tree(item["children"]),  # type: ignore[arg-type]
        }
        for item in items
    ]


def _assert_saved_input_matches_required_tree(
    saved_input: RoadmapSaveInput,
    *,
    expected_topic: str,
    expected_created_at: str,
    expected_items: list[dict[str, object]],
) -> None:
    assert saved_input.topic == expected_topic
    assert saved_input.created_at == expected_created_at
    assert _to_required_item_tree(saved_input.items) == _payload_items_to_required_tree(
        expected_items,
    )


def _detail_payload(
    *,
    title: str,
    description: str,
    children: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "title": title,
        "description": description,
        "level": "detail",
        "children": list(children or []),
    }


def _middle_payload(
    *,
    title: str,
    description: str,
    children: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "title": title,
        "description": description,
        "level": "middle",
        "children": list(children or []),
    }


def _major_payload(
    *,
    title: str,
    description: str,
    children: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "title": title,
        "description": description,
        "level": "major",
        "children": list(children or []),
    }


def _make_valid_payload(topic: str = _TOPIC) -> dict[str, object]:
    return {
        "topic": topic,
        "items": [
            _major_payload(
                title="基礎",
                description="初学者が押さえるべき基本事項",
                children=[
                    _middle_payload(
                        title="変数と型",
                        description="基本的な型注釈",
                        children=[
                            _detail_payload(
                                title="プリミティブ型",
                                description="string と number の基礎",
                            ),
                            _detail_payload(
                                title="配列とタプル",
                                description="配列型とタプル型の使い分け",
                            ),
                        ],
                    ),
                ],
            ),
            _major_payload(
                title="応用",
                description="中上級者へのステップアップ",
                children=[],
            ),
        ],
    }


def _make_tc_04_success_payload(topic: str = _TOPIC) -> dict[str, object]:
    return {
        "topic": topic,
        "items": [
            _major_payload(
                title="基礎",
                description="初学者が押さえるべきTypeScriptの基本事項",
                children=[
                    _middle_payload(
                        title="関数",
                        description="関数宣言と型注釈を学ぶ",
                        children=[
                            _detail_payload(
                                title="関数の型注釈",
                                description="引数と返り値の型を書く",
                            ),
                            _detail_payload(
                                title="オーバーロード",
                                description="複数シグネチャを定義する",
                            ),
                        ],
                    ),
                    _middle_payload(
                        title="型システム",
                        description="値に対する型の表現を学ぶ",
                        children=[
                            _detail_payload(
                                title="ユニオン型",
                                description="複数候補の型を扱う",
                            ),
                            _detail_payload(
                                title="型推論",
                                description="注釈なしで推論される型を理解する",
                            ),
                        ],
                    ),
                ],
            ),
            _major_payload(
                title="応用",
                description="中上級者へのステップアップに必要な知識",
                children=[
                    _middle_payload(
                        title="型レベルプログラミング",
                        description="高度な型操作を学ぶ",
                        children=[
                            _detail_payload(
                                title="条件型",
                                description="条件に応じて型を分岐させる",
                            ),
                            _detail_payload(
                                title="mapped types",
                                description="既存型から新しい型を導く",
                            ),
                        ],
                    ),
                ],
            ),
        ],
    }


def _make_branch_preserving_payload(topic: str = _TOPIC) -> dict[str, object]:
    return {
        "topic": topic,
        "items": [
            _major_payload(
                title="基礎",
                description="TypeScript学習の土台を固める",
                children=[
                    _middle_payload(
                        title="関数",
                        description="関数定義と型付けの基礎を学ぶ",
                        children=[
                            _detail_payload(
                                title="関数宣言",
                                description="function 構文で関数を定義する",
                            ),
                            _detail_payload(
                                title="引数の型注釈",
                                description="引数へ明示的に型を書く",
                            ),
                            _detail_payload(
                                title="戻り値の型注釈",
                                description="戻り値へ明示的に型を書く",
                            ),
                        ],
                    ),
                    _middle_payload(
                        title="実行環境",
                        description="TypeScriptコードを動かす準備を整える",
                        children=[],
                    ),
                ],
            ),
            _major_payload(
                title="応用",
                description="発展的な内容へ進む前提を整える",
                children=[],
            ),
        ],
    }


def _to_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _assert_is_frozen_dataclass(candidate: object) -> None:
    assert is_dataclass(candidate)
    dataclass_params = getattr(candidate, "__dataclass_params__", None)
    assert dataclass_params is not None
    assert dataclass_params.frozen is True


def _schema_invalid_root_topic_mismatch(topic: str) -> dict[str, object]:
    payload = _make_valid_payload(topic)
    payload["topic"] = "Different Topic"
    return payload


def _schema_invalid_root_missing_topic(topic: str) -> dict[str, object]:
    payload = _make_valid_payload(topic)
    del payload["topic"]
    return payload


def _schema_invalid_root_missing_items(topic: str) -> dict[str, object]:
    payload = _make_valid_payload(topic)
    del payload["items"]
    return payload


def _schema_invalid_root_extra_field(topic: str) -> dict[str, object]:
    payload = _make_valid_payload(topic)
    payload["extra"] = "unexpected"
    return payload


def _schema_invalid_items_wrong_length(topic: str) -> dict[str, object]:
    payload = _make_valid_payload(topic)
    payload["items"] = [payload["items"][0]]  # type: ignore[index]
    return payload


def _schema_invalid_major_missing_description(topic: str) -> dict[str, object]:
    payload = _make_valid_payload(topic)
    del payload["items"][0]["description"]  # type: ignore[index]
    return payload


def _schema_invalid_major_extra_field(topic: str) -> dict[str, object]:
    payload = _make_valid_payload(topic)
    payload["items"][0]["extra"] = "unexpected"  # type: ignore[index]
    return payload


def _schema_invalid_item_title_type(topic: str) -> dict[str, object]:
    payload = _make_valid_payload(topic)
    payload["items"][0]["title"] = 123  # type: ignore[index]
    return payload


def _schema_invalid_item_description_type(topic: str) -> dict[str, object]:
    payload = _make_valid_payload(topic)
    payload["items"][0]["description"] = ["unexpected"]  # type: ignore[index]
    return payload


def _schema_invalid_item_children_type(topic: str) -> dict[str, object]:
    payload = _make_valid_payload(topic)
    payload["items"][0]["children"] = "unexpected"  # type: ignore[index]
    return payload


def _schema_invalid_unknown_level(topic: str) -> dict[str, object]:
    payload = _make_valid_payload(topic)
    payload["items"][0]["children"][0]["level"] = "minor"  # type: ignore[index]
    return payload


def _schema_invalid_major_has_detail_child(topic: str) -> dict[str, object]:
    payload = _make_valid_payload(topic)
    payload["items"][0]["children"] = [  # type: ignore[index]
        _detail_payload(
            title="直接ぶら下がる detail",
            description="major 配下に detail を置いている",
        ),
    ]
    return payload


def _schema_invalid_detail_has_non_empty_children(topic: str) -> dict[str, object]:
    payload = _make_valid_payload(topic)
    payload["items"][0]["children"][0]["children"][0]["children"] = [  # type: ignore[index]
        _detail_payload(
            title="入れ子 detail",
            description="detail.children は空配列だけ許可される",
        ),
    ]
    return payload


_SCHEMA_INVALID_CASES = [
    ("root_missing_topic", _schema_invalid_root_missing_topic, ("topic", "required")),
    ("root_missing_items", _schema_invalid_root_missing_items, ("items", "required")),
    (
        "root_extra_field",
        _schema_invalid_root_extra_field,
        ("extra", "not permitted"),
    ),
    (
        "items_wrong_length",
        _schema_invalid_items_wrong_length,
        ("items", "at least", "2"),
    ),
    (
        "major_missing_description",
        _schema_invalid_major_missing_description,
        ("items", "0", "description", "required"),
    ),
    (
        "major_extra_field",
        _schema_invalid_major_extra_field,
        ("items", "0", "extra", "not permitted"),
    ),
    (
        "unknown_level",
        _schema_invalid_unknown_level,
        ("items", "0", "children", "0", "level", "minor"),
    ),
    (
        "major_has_detail_child",
        _schema_invalid_major_has_detail_child,
        ("major", "middle", "detail"),
    ),
    (
        "detail_children_non_empty",
        _schema_invalid_detail_has_non_empty_children,
        ("detail", "children", "empty"),
    ),
    (
        "item_title_type_invalid",
        _schema_invalid_item_title_type,
        ("items", "0", "title", "123", "string"),
    ),
    (
        "item_description_type_invalid",
        _schema_invalid_item_description_type,
        ("items", "0", "description", "list", "string"),
    ),
    (
        "item_children_type_invalid",
        _schema_invalid_item_children_type,
        ("items", "0", "children", "unexpected", "list"),
    ),
    (
        "root_topic_mismatch",
        _schema_invalid_root_topic_mismatch,
        ("topic", "TypeScript", "Different Topic"),
    ),
]


def test_tc_01_static_contracts_for_public_dto_failure_codes_and_internal_dto() -> None:
    # TypedDict 公開 DTO
    for td in (RoadmapGenerationAccepted, RoadmapGenerationQueuedStatus, RoadmapGenerationRunningStatus, RoadmapGenerationCompletedStatus, RoadmapGenerationFailedStatus):
        assert is_typeddict(td)

    # FailureCode
    assert get_args(RoadmapGenerationFailureCode) == _FAILURE_CODES

    # JobStatus union
    assert get_args(RoadmapGenerationJobStatus) == (RoadmapGenerationQueuedStatus, RoadmapGenerationRunningStatus, RoadmapGenerationCompletedStatus, RoadmapGenerationFailedStatus)

    # 例外階層
    assert RoadmapGenerationInputError.__base__ is RoadmapGenerationError
    assert RoadmapGenerationScheduleError.__base__ is RoadmapGenerationError
    assert RoadmapGenerationLlmError.__base__ is RoadmapGenerationError
    assert RoadmapGenerationJobStoreError.__base__ is RoadmapGenerationError
    assert RoadmapGenerationJobNotFoundError.__base__ is RoadmapGenerationError
    assert RoadmapGenerationLlmResponseError.__base__ is RoadmapGenerationError
    assert RoadmapGenerationJsonParseError.__base__ is RoadmapGenerationLlmResponseError
    assert RoadmapGenerationSchemaValidationError.__base__ is RoadmapGenerationLlmResponseError

    # 内部 DTO は frozen dataclass
    _assert_is_frozen_dataclass(ValidatedRoadmapGeneration)
    _assert_is_frozen_dataclass(ValidatedRoadmapGenerationItem)


def test_tc_02_request_accepts_topic_preserves_shape_order_and_logs() -> None:
    operation_log: list[str] = []
    job_id_generator = _RecordingJobIdGenerator([_JOB_ID], operation_log=operation_log)
    scheduler = _RecordingScheduler(operation_log=operation_log)
    job_store = _RecordingJobStore(operation_log=operation_log)

    with capture_logs() as log_output:
        result = request_roadmap_generation(
            _TOPIC,
            job_id_generator=job_id_generator,
            scheduler=scheduler,
            job_store=job_store,
        )

    assert result == {"job_id": _JOB_ID, "status": "queued"}
    assert set(result) == {"job_id", "status"}
    job_id = result["job_id"]
    status = result["status"]
    assert isinstance(job_id, UUID)
    assert job_id == _JOB_ID
    assert isinstance(status, str)
    assert status == "queued"
    assert job_id_generator.calls == 1
    assert job_store.create_queued_job_calls == [{"job_id": _JOB_ID, "topic": _TOPIC}]
    assert scheduler.calls == [{"job_id": _JOB_ID, "topic": _TOPIC}]
    assert job_store.mark_failed_calls == []
    assert operation_log == [
        "generate",
        "create_queued_job",
        "enqueue_roadmap_generation",
    ]
    _assert_single_log_event(
        log_output,
        EVENT_ACCEPTED,
        {"job_id": str(_JOB_ID), "topic": _TOPIC},
        log_level="info",
        str_coerce_fields=_JOB_ID_FIELDS,
    )
    _assert_no_log_event(log_output, EVENT_INPUT_REJECTED)
    _assert_no_log_event(log_output, EVENT_SCHEDULE_FAILED)


@pytest.mark.parametrize(
    (
        "stored_status",
        "expected_keys",
        "expected_status",
        "expected_roadmap_id",
        "expected_error_code",
        "expected_error_message",
    ),
    [
        ({"status": "queued"}, {"status"}, "queued", None, None, None),
        ({"status": "running"}, {"status"}, "running", None, None, None),
        (
            {"status": "completed", "roadmap_id": _ROADMAP_ID},
            {"status", "roadmap_id"},
            "completed",
            _ROADMAP_ID,
            None,
            None,
        ),
        (
            {
                "status": "failed",
                "error_code": "schedule_failed",
                "error_message": "queue down",
            },
            {"status", "error_code", "error_message"},
            "failed",
            None,
            "schedule_failed",
            "queue down",
        ),
    ],
    ids=["queued", "running", "completed", "failed"],
)
def test_tc_03_get_job_returns_each_status_shape_as_is(
    stored_status: RoadmapGenerationJobStatus,
    expected_keys: set[str],
    expected_status: str,
    expected_roadmap_id: UUID | None,
    expected_error_code: RoadmapGenerationFailureCode | None,
    expected_error_message: str | None,
) -> None:
    job_store = _RecordingJobStore(get_job_result=stored_status)

    result = get_roadmap_generation_job(_JOB_ID, job_store=job_store)

    assert result == stored_status
    assert set(result) == expected_keys
    status = result["status"]
    assert isinstance(status, str)
    assert status == expected_status
    if expected_roadmap_id is not None:
        completed_result = cast("RoadmapGenerationCompletedStatus", result)
        roadmap_id = completed_result["roadmap_id"]
        assert isinstance(roadmap_id, UUID)
        assert roadmap_id == expected_roadmap_id
    if expected_error_code is not None and expected_error_message is not None:
        failed_result = cast("RoadmapGenerationFailedStatus", result)
        error_code = failed_result["error_code"]
        error_message = failed_result["error_message"]
        assert error_code == expected_error_code
        assert isinstance(error_message, str)
        assert error_message == expected_error_message
    assert job_store.get_job_calls == [_JOB_ID]


def test_tc_04_worker_success_marks_running_persists_and_completes() -> None:
    operation_log: list[str] = []
    payload = _make_tc_04_success_payload(_TOPIC)
    llm_client = _RecordingLlmClient(
        [_to_json(payload)],
        operation_log=operation_log,
    )
    persistence = _RecordingPersistence(
        result=RoadmapSaveResult(roadmap_id=_ROADMAP_ID, saved_count=4),
        operation_log=operation_log,
    )
    job_store = _RecordingJobStore(operation_log=operation_log)
    clock = _RecordingClock(operation_log=operation_log)

    with capture_logs() as log_output:
        _run_roadmap_generation_job(
            _JOB_ID,
            _TOPIC,
            llm_client=llm_client,
            persistence=persistence,
            job_store=job_store,
            clock=clock,
        )

    assert job_store.mark_running_calls == [_JOB_ID]
    assert llm_client.calls == [_TOPIC]
    assert clock.calls == 1
    assert len(persistence.inputs) == 1
    _assert_saved_input_matches_required_tree(
        persistence.inputs[0],
        expected_topic=_TOPIC,
        expected_created_at=_CREATED_AT,
        expected_items=payload["items"],  # type: ignore[arg-type]
    )
    assert job_store.mark_completed_calls == [
        {"job_id": _JOB_ID, "roadmap_id": _ROADMAP_ID},
    ]
    assert job_store.mark_failed_calls == []
    assert operation_log == [
        "mark_running",
        "generate_roadmap_json",
        "now",
        "save_roadmap",
        "mark_completed",
    ]
    _assert_single_log_event(
        log_output,
        EVENT_JOB_STARTED,
        {"job_id": str(_JOB_ID), "topic": _TOPIC},
        log_level="info",
        str_coerce_fields=_JOB_ID_FIELDS,
    )
    _assert_single_log_event(
        log_output,
        EVENT_JOB_COMPLETED,
        {"job_id": str(_JOB_ID), "roadmap_id": str(_ROADMAP_ID)},
        log_level="info",
        str_coerce_fields=_JOB_AND_ROADMAP_ID_FIELDS,
    )
    _assert_no_log_event(log_output, EVENT_LLM_RETRY)
    _assert_no_log_event(log_output, EVENT_JOB_FAILED)


@pytest.mark.parametrize("topic", ["", " \n\t "], ids=["empty", "whitespace_only"])
def test_tc_10_request_rejects_blank_topic_before_enqueue_and_logs(topic: str) -> None:
    job_id_generator = _RecordingJobIdGenerator([_JOB_ID])
    scheduler = _RecordingScheduler()
    job_store = _RecordingJobStore()

    with (
        capture_logs() as log_output,
        pytest.raises(RoadmapGenerationInputError),
    ):
        request_roadmap_generation(
            topic,
            job_id_generator=job_id_generator,
            scheduler=scheduler,
            job_store=job_store,
        )

    assert job_id_generator.calls == 0
    assert job_store.create_queued_job_calls == []
    assert scheduler.calls == []
    assert job_store.mark_failed_calls == []
    _assert_single_log_event(
        log_output,
        EVENT_INPUT_REJECTED,
        {"error_type": "RoadmapGenerationInputError"},
        log_level="warning",
    )
    _assert_no_log_event(log_output, EVENT_ACCEPTED)
    _assert_no_log_event(log_output, EVENT_SCHEDULE_FAILED)


def test_tc_11_worker_retries_parse_and_schema_failures_with_shared_budget() -> None:
    operation_log: list[str] = []
    llm_client = _RecordingLlmClient(
        [
            "{invalid json",
            _to_json(_schema_invalid_root_topic_mismatch(_TOPIC)),
            _to_json(_make_valid_payload(_TOPIC)),
        ],
        operation_log=operation_log,
    )
    persistence = _RecordingPersistence(operation_log=operation_log)
    job_store = _RecordingJobStore(operation_log=operation_log)
    clock = _RecordingClock(operation_log=operation_log)

    with capture_logs() as log_output:
        _run_roadmap_generation_job(
            _JOB_ID,
            _TOPIC,
            llm_client=llm_client,
            persistence=persistence,
            job_store=job_store,
            clock=clock,
        )

    assert llm_client.calls == [_TOPIC, _TOPIC, _TOPIC]
    assert clock.calls == 1
    assert len(persistence.inputs) == 1
    assert job_store.mark_completed_calls == [
        {"job_id": _JOB_ID, "roadmap_id": _ROADMAP_ID},
    ]
    assert job_store.mark_failed_calls == []
    assert operation_log == [
        "mark_running",
        "generate_roadmap_json",
        "generate_roadmap_json",
        "generate_roadmap_json",
        "now",
        "save_roadmap",
        "mark_completed",
    ]
    _assert_retry_events(
        log_output,
        expected_error_types=[
            "RoadmapGenerationJsonParseError",
            "RoadmapGenerationSchemaValidationError",
        ],
    )
    _assert_single_log_event(
        log_output,
        EVENT_JOB_COMPLETED,
        {"job_id": str(_JOB_ID), "roadmap_id": str(_ROADMAP_ID)},
        log_level="info",
        str_coerce_fields=_JOB_AND_ROADMAP_ID_FIELDS,
    )
    _assert_no_log_event(log_output, EVENT_JOB_FAILED)


def test_tc_12_worker_uses_last_parse_failure_code_after_retry_budget_exhausted() -> (
    None
):
    final_parse_failure = '{not-valid-json: "third-attempt"}'
    llm_client = _RecordingLlmClient(
        [
            _to_json(_schema_invalid_root_topic_mismatch(_TOPIC)),
            _to_json(_schema_invalid_unknown_level(_TOPIC)),
            final_parse_failure,
        ],
    )
    persistence = _RecordingPersistence()
    job_store = _RecordingJobStore()
    clock = _RecordingClock()

    with capture_logs() as log_output:
        _run_roadmap_generation_job(
            _JOB_ID,
            _TOPIC,
            llm_client=llm_client,
            persistence=persistence,
            job_store=job_store,
            clock=clock,
        )

    assert llm_client.calls == [_TOPIC, _TOPIC, _TOPIC]
    assert persistence.inputs == []
    assert clock.calls == 0
    assert job_store.mark_completed_calls == []
    assert len(job_store.mark_failed_calls) == 1
    assert job_store.mark_failed_calls[0]["job_id"] == _JOB_ID
    assert job_store.mark_failed_calls[0]["error_code"] == "llm_json_parse_failed"
    assert "Expecting property name enclosed in double quotes" in str(
        job_store.mark_failed_calls[0]["error_message"],
    )
    _assert_retry_events(
        log_output,
        expected_error_types=[
            "RoadmapGenerationSchemaValidationError",
            "RoadmapGenerationSchemaValidationError",
        ],
    )
    _assert_single_log_event(
        log_output,
        EVENT_JOB_FAILED,
        {
            "job_id": str(_JOB_ID),
            "error_code": "llm_json_parse_failed",
            "error_type": "RoadmapGenerationJsonParseError",
        },
        log_level="error",
        str_coerce_fields=_JOB_ID_FIELDS,
    )
    _assert_no_log_event(log_output, EVENT_JOB_COMPLETED)


@pytest.mark.parametrize(
    ("case_name", "invalid_payload_builder", "expected_reason_fragments"),
    _SCHEMA_INVALID_CASES,
    ids=[case_name for case_name, _, _ in _SCHEMA_INVALID_CASES],
)
def test_tc_13_all_schema_violation_patterns_retry_and_fail_with_schema_code(
    case_name: str,
    invalid_payload_builder: Any,
    expected_reason_fragments: tuple[str, ...],
) -> None:
    del case_name
    invalid_payload = invalid_payload_builder(_TOPIC)
    llm_client = _RecordingLlmClient(
        [
            _to_json(deepcopy(invalid_payload)),
            _to_json(deepcopy(invalid_payload)),
            _to_json(deepcopy(invalid_payload)),
        ],
    )
    persistence = _RecordingPersistence()
    job_store = _RecordingJobStore()
    clock = _RecordingClock()

    with capture_logs() as log_output:
        _run_roadmap_generation_job(
            _JOB_ID,
            _TOPIC,
            llm_client=llm_client,
            persistence=persistence,
            job_store=job_store,
            clock=clock,
        )

    assert llm_client.calls == [_TOPIC, _TOPIC, _TOPIC]
    assert persistence.inputs == []
    assert clock.calls == 0
    assert job_store.mark_completed_calls == []
    assert len(job_store.mark_failed_calls) == 1
    assert job_store.mark_failed_calls[0]["job_id"] == _JOB_ID
    assert job_store.mark_failed_calls[0]["error_code"] == (
        "llm_schema_validation_failed"
    )
    error_message = str(job_store.mark_failed_calls[0]["error_message"])
    for expected_reason_fragment in expected_reason_fragments:
        assert expected_reason_fragment in error_message
    _assert_retry_events(
        log_output,
        expected_error_types=[
            "RoadmapGenerationSchemaValidationError",
            "RoadmapGenerationSchemaValidationError",
        ],
    )
    _assert_single_log_event(
        log_output,
        EVENT_JOB_FAILED,
        {
            "job_id": str(_JOB_ID),
            "error_code": "llm_schema_validation_failed",
            "error_type": "RoadmapGenerationSchemaValidationError",
        },
        log_level="error",
        str_coerce_fields=_JOB_ID_FIELDS,
    )
    _assert_no_log_event(log_output, EVENT_JOB_COMPLETED)


def test_tc_14_worker_preserves_topic_hierarchy_required_items_and_empty_branches() -> (
    None
):
    payload = _make_branch_preserving_payload(_SECOND_TOPIC)
    llm_client = _RecordingLlmClient(
        [_to_json(payload)],
    )
    persistence = _RecordingPersistence()
    job_store = _RecordingJobStore()
    clock = _RecordingClock()

    _run_roadmap_generation_job(
        _JOB_ID,
        _SECOND_TOPIC,
        llm_client=llm_client,
        persistence=persistence,
        job_store=job_store,
        clock=clock,
    )

    assert llm_client.calls == [_SECOND_TOPIC]
    assert clock.calls == 1
    assert len(persistence.inputs) == 1
    _assert_saved_input_matches_required_tree(
        persistence.inputs[0],
        expected_topic=_SECOND_TOPIC,
        expected_created_at=_CREATED_AT,
        expected_items=payload["items"],  # type: ignore[arg-type]
    )
    assert job_store.mark_completed_calls == [
        {"job_id": _JOB_ID, "roadmap_id": _ROADMAP_ID},
    ]
    assert job_store.mark_failed_calls == []


def test_tc_20_create_queued_job_error_is_reraised_without_enqueue() -> None:
    original_error = RoadmapGenerationJobStoreError("queue record failed")
    operation_log: list[str] = []
    job_id_generator = _RecordingJobIdGenerator([_JOB_ID], operation_log=operation_log)
    scheduler = _RecordingScheduler(operation_log=operation_log)
    job_store = _RecordingJobStore(
        create_queued_job_error=original_error,
        operation_log=operation_log,
    )

    with (
        capture_logs() as log_output,
        pytest.raises(RoadmapGenerationJobStoreError) as exc_info,
    ):
        request_roadmap_generation(
            _TOPIC,
            job_id_generator=job_id_generator,
            scheduler=scheduler,
            job_store=job_store,
        )

    assert exc_info.value is original_error
    assert scheduler.calls == []
    assert job_store.mark_failed_calls == []
    assert operation_log == ["generate", "create_queued_job"]
    _assert_no_log_event(log_output, EVENT_ACCEPTED)
    _assert_no_log_event(log_output, EVENT_SCHEDULE_FAILED)


def test_tc_21_schedule_failure_marks_failed_then_reraises_original_error() -> None:
    original_error = RoadmapGenerationScheduleError("queue unavailable")
    operation_log: list[str] = []
    job_id_generator = _RecordingJobIdGenerator([_JOB_ID], operation_log=operation_log)
    scheduler = _RecordingScheduler(error=original_error, operation_log=operation_log)
    job_store = _RecordingJobStore(operation_log=operation_log)

    with (
        capture_logs() as log_output,
        pytest.raises(RoadmapGenerationScheduleError) as exc_info,
    ):
        request_roadmap_generation(
            _TOPIC,
            job_id_generator=job_id_generator,
            scheduler=scheduler,
            job_store=job_store,
        )

    assert exc_info.value is original_error
    assert job_store.mark_failed_calls == [
        {
            "job_id": _JOB_ID,
            "error_code": "schedule_failed",
            "error_message": "queue unavailable",
        },
    ]
    assert operation_log == [
        "generate",
        "create_queued_job",
        "enqueue_roadmap_generation",
        "mark_failed",
    ]
    _assert_single_log_event(
        log_output,
        EVENT_SCHEDULE_FAILED,
        {
            "job_id": str(_JOB_ID),
            "error_type": "RoadmapGenerationScheduleError",
        },
        log_level="error",
        str_coerce_fields=_JOB_ID_FIELDS,
    )
    _assert_no_log_event(log_output, EVENT_ACCEPTED)


def test_tc_22_mark_failed_store_error_overrides_schedule_error() -> None:
    schedule_error = RoadmapGenerationScheduleError("queue unavailable")
    store_error = RoadmapGenerationJobStoreError("mark_failed write failed")
    job_id_generator = _RecordingJobIdGenerator([_JOB_ID])
    scheduler = _RecordingScheduler(error=schedule_error)
    job_store = _RecordingJobStore(mark_failed_error=store_error)

    with (
        capture_logs() as log_output,
        pytest.raises(RoadmapGenerationJobStoreError) as exc_info,
    ):
        request_roadmap_generation(
            _TOPIC,
            job_id_generator=job_id_generator,
            scheduler=scheduler,
            job_store=job_store,
        )

    assert exc_info.value is store_error
    assert job_store.mark_failed_calls == [
        {
            "job_id": _JOB_ID,
            "error_code": "schedule_failed",
            "error_message": "queue unavailable",
        },
    ]
    _assert_single_log_event(
        log_output,
        EVENT_SCHEDULE_FAILED,
        {
            "job_id": str(_JOB_ID),
            "error_type": "RoadmapGenerationScheduleError",
        },
        log_level="error",
        str_coerce_fields=_JOB_ID_FIELDS,
    )
    _assert_no_log_event(log_output, EVENT_ACCEPTED)


def test_tc_23_worker_stops_immediately_when_mark_running_fails() -> None:
    original_error = RoadmapGenerationJobStoreError("mark_running failed")
    llm_client = _RecordingLlmClient([_to_json(_make_valid_payload(_TOPIC))])
    persistence = _RecordingPersistence()
    job_store = _RecordingJobStore(mark_running_error=original_error)
    clock = _RecordingClock()

    with (
        capture_logs() as log_output,
        pytest.raises(RoadmapGenerationJobStoreError) as exc_info,
    ):
        _run_roadmap_generation_job(
            _JOB_ID,
            _TOPIC,
            llm_client=llm_client,
            persistence=persistence,
            job_store=job_store,
            clock=clock,
        )

    assert exc_info.value is original_error
    assert job_store.mark_running_calls == [_JOB_ID]
    assert llm_client.calls == []
    assert persistence.inputs == []
    assert clock.calls == 0
    assert job_store.mark_failed_calls == []
    assert job_store.mark_completed_calls == []
    _assert_no_log_event(log_output, EVENT_JOB_STARTED)
    _assert_no_log_event(log_output, EVENT_JOB_COMPLETED)
    _assert_no_log_event(log_output, EVENT_JOB_FAILED)


def test_tc_24_mark_completed_error_is_propagated_without_failed_fallback() -> None:
    original_error = RoadmapGenerationJobStoreError("mark_completed failed")
    llm_client = _RecordingLlmClient([_to_json(_make_valid_payload(_TOPIC))])
    persistence = _RecordingPersistence()
    job_store = _RecordingJobStore(mark_completed_error=original_error)
    clock = _RecordingClock()

    with (
        capture_logs() as log_output,
        pytest.raises(RoadmapGenerationJobStoreError) as exc_info,
    ):
        _run_roadmap_generation_job(
            _JOB_ID,
            _TOPIC,
            llm_client=llm_client,
            persistence=persistence,
            job_store=job_store,
            clock=clock,
        )

    assert exc_info.value is original_error
    assert len(persistence.inputs) == 1
    assert job_store.mark_completed_calls == [
        {"job_id": _JOB_ID, "roadmap_id": _ROADMAP_ID},
    ]
    assert job_store.mark_failed_calls == []
    _assert_single_log_event(
        log_output,
        EVENT_JOB_STARTED,
        {"job_id": str(_JOB_ID), "topic": _TOPIC},
        log_level="info",
        str_coerce_fields=_JOB_ID_FIELDS,
    )
    _assert_no_log_event(log_output, EVENT_JOB_COMPLETED)
    _assert_no_log_event(log_output, EVENT_JOB_FAILED)


def test_tc_25_same_topic_can_be_accepted_as_two_distinct_jobs() -> None:
    job_id_generator = _RecordingJobIdGenerator([_JOB_ID, _SECOND_JOB_ID])
    scheduler = _RecordingScheduler()
    job_store = _RecordingJobStore()

    with capture_logs() as log_output:
        first_result = request_roadmap_generation(
            _TOPIC,
            job_id_generator=job_id_generator,
            scheduler=scheduler,
            job_store=job_store,
        )
        second_result = request_roadmap_generation(
            _TOPIC,
            job_id_generator=job_id_generator,
            scheduler=scheduler,
            job_store=job_store,
        )

    assert first_result == {"job_id": _JOB_ID, "status": "queued"}
    assert second_result == {"job_id": _SECOND_JOB_ID, "status": "queued"}
    assert job_store.create_queued_job_calls == [
        {"job_id": _JOB_ID, "topic": _TOPIC},
        {"job_id": _SECOND_JOB_ID, "topic": _TOPIC},
    ]
    assert scheduler.calls == [
        {"job_id": _JOB_ID, "topic": _TOPIC},
        {"job_id": _SECOND_JOB_ID, "topic": _TOPIC},
    ]
    accepted_events = find_log_events(log_output, EVENT_ACCEPTED, log_level="info")
    assert len(accepted_events) == 2
    assert [str(event["job_id"]) for event in accepted_events] == [
        str(_JOB_ID),
        str(_SECOND_JOB_ID),
    ]
    assert [event["topic"] for event in accepted_events] == [_TOPIC, _TOPIC]


@pytest.mark.parametrize(
    "original_error",
    [
        RoadmapGenerationJobStoreError("store unavailable"),
        RoadmapGenerationJobNotFoundError("job not found"),
    ],
    ids=["store_error", "not_found"],
)
def test_tc_30_get_job_reraises_store_exceptions_without_wrapping(
    original_error: Exception,
) -> None:
    job_store = _RecordingJobStore(get_job_error=original_error)

    with pytest.raises(type(original_error)) as exc_info:
        get_roadmap_generation_job(_JOB_ID, job_store=job_store)

    assert exc_info.value is original_error
    assert job_store.get_job_calls == [_JOB_ID]


@pytest.mark.parametrize(
    "mark_failed_error",
    [
        None,
        RoadmapGenerationJobStoreError("mark_failed store unavailable"),
    ],
    ids=["mark_failed_succeeds", "mark_failed_store_failure"],
)
def test_tc_31_worker_marks_llm_request_failures_without_retry(
    mark_failed_error: RoadmapGenerationJobStoreError | None,
) -> None:
    llm_error = RoadmapGenerationLlmError("llm timeout")
    llm_client = _RecordingLlmClient([llm_error])
    persistence = _RecordingPersistence()
    job_store = _RecordingJobStore(mark_failed_error=mark_failed_error)
    clock = _RecordingClock()

    with capture_logs() as log_output:
        if mark_failed_error is None:
            _run_roadmap_generation_job(
                _JOB_ID,
                _TOPIC,
                llm_client=llm_client,
                persistence=persistence,
                job_store=job_store,
                clock=clock,
            )
        else:
            with pytest.raises(RoadmapGenerationJobStoreError) as exc_info:
                _run_roadmap_generation_job(
                    _JOB_ID,
                    _TOPIC,
                    llm_client=llm_client,
                    persistence=persistence,
                    job_store=job_store,
                    clock=clock,
                )
            assert exc_info.value is mark_failed_error

    assert llm_client.calls == [_TOPIC]
    assert persistence.inputs == []
    assert clock.calls == 0
    assert job_store.mark_completed_calls == []
    assert job_store.mark_failed_calls == [
        {
            "job_id": _JOB_ID,
            "error_code": "llm_request_failed",
            "error_message": "llm timeout",
        },
    ]
    if mark_failed_error is None:
        _assert_single_log_event(
            log_output,
            EVENT_JOB_FAILED,
            {
                "job_id": str(_JOB_ID),
                "error_code": "llm_request_failed",
                "error_type": "RoadmapGenerationLlmError",
            },
            log_level="error",
            str_coerce_fields=_JOB_ID_FIELDS,
        )
    else:
        _assert_no_log_event(log_output, EVENT_JOB_FAILED)
    _assert_no_log_event(log_output, EVENT_LLM_RETRY)
    _assert_no_log_event(log_output, EVENT_JOB_COMPLETED)


@pytest.mark.parametrize(
    ("persistence_error", "mark_failed_error"),
    [
        (RoadmapPersistenceWriteError("db locked"), None),
        (
            RoadmapPersistenceWriteError("db locked"),
            RoadmapGenerationJobStoreError("mark_failed store unavailable"),
        ),
        (RoadmapPersistenceInputError("invalid title"), None),
        (
            RoadmapPersistenceInputError("invalid title"),
            RoadmapGenerationJobStoreError("mark_failed store unavailable"),
        ),
    ],
    ids=[
        "write_error_mark_failed_succeeds",
        "write_error_mark_failed_store_failure",
        "input_error_mark_failed_succeeds",
        "input_error_mark_failed_store_failure",
    ],
)
def test_tc_32_worker_marks_persistence_failures_without_retry(
    persistence_error: Exception,
    mark_failed_error: RoadmapGenerationJobStoreError | None,
) -> None:
    llm_client = _RecordingLlmClient([_to_json(_make_valid_payload(_TOPIC))])
    persistence = _RecordingPersistence(error=persistence_error)
    job_store = _RecordingJobStore(mark_failed_error=mark_failed_error)
    clock = _RecordingClock()

    with capture_logs() as log_output:
        if mark_failed_error is None:
            _run_roadmap_generation_job(
                _JOB_ID,
                _TOPIC,
                llm_client=llm_client,
                persistence=persistence,
                job_store=job_store,
                clock=clock,
            )
        else:
            with pytest.raises(RoadmapGenerationJobStoreError) as exc_info:
                _run_roadmap_generation_job(
                    _JOB_ID,
                    _TOPIC,
                    llm_client=llm_client,
                    persistence=persistence,
                    job_store=job_store,
                    clock=clock,
                )
            assert exc_info.value is mark_failed_error

    assert llm_client.calls == [_TOPIC]
    assert clock.calls == 1
    assert len(persistence.inputs) == 1
    assert job_store.mark_completed_calls == []
    assert job_store.mark_failed_calls == [
        {
            "job_id": _JOB_ID,
            "error_code": "persistence_failed",
            "error_message": str(persistence_error),
        },
    ]
    if mark_failed_error is None:
        _assert_single_log_event(
            log_output,
            EVENT_JOB_FAILED,
            {
                "job_id": str(_JOB_ID),
                "error_code": "persistence_failed",
                "error_type": type(persistence_error).__name__,
            },
            log_level="error",
            str_coerce_fields=_JOB_ID_FIELDS,
        )
    else:
        _assert_no_log_event(log_output, EVENT_JOB_FAILED)
    _assert_no_log_event(log_output, EVENT_LLM_RETRY)
    _assert_no_log_event(log_output, EVENT_JOB_COMPLETED)
