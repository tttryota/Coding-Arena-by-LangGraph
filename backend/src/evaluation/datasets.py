"""Load and validate version-controlled JSONL evaluation datasets."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from evaluation.models import EvalCase, FlowName

_EXPECTED_CASES_PER_FLOW = 12
_EXPECTED_E2E_PER_FLOW = 3
_EXPECTED_CASES_PER_ANSWER_CLASS = 4
_ANSWER_CLASSES = frozenset({"correct", "partial", "incorrect"})
_REQUIRED_STATE_KEYS: dict[FlowName, frozenset[str]] = {
    "quiz": frozenset({"answer_text"}),
    "coding": frozenset({"user_code"}),
    "competitive": frozenset({"user_code"}),
}


def default_dataset_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "evals" / "datasets"


def load_cases(dataset_dir: Path | None = None) -> list[EvalCase]:
    root = dataset_dir or default_dataset_dir()
    cases: list[EvalCase] = []
    for path in sorted(root.glob("*.jsonl")):
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    cases.append(EvalCase.model_validate_json(line))
                except Exception as exc:
                    msg = f"{path}:{line_number}: invalid evaluation case: {exc}"
                    raise ValueError(msg) from exc
    validate_case_collection(cases)
    return cases


def validate_case_collection(cases: list[EvalCase]) -> None:
    if not cases:
        msg = "no evaluation cases found"
        raise ValueError(msg)
    ids = [case.id for case in cases]
    duplicates = sorted(case_id for case_id, count in Counter(ids).items() if count > 1)
    if duplicates:
        msg = f"duplicate evaluation case ids: {duplicates}"
        raise ValueError(msg)

    counts = Counter(case.flow for case in cases)
    e2e_counts = Counter(case.flow for case in cases if case.end_to_end)
    for flow in _REQUIRED_STATE_KEYS:
        _validate_flow_distribution(cases, flow, counts[flow], e2e_counts[flow])
    for case in cases:
        missing = _REQUIRED_STATE_KEYS[case.flow] - case.initial_state.keys()
        if missing:
            msg = f"{case.id} is missing state keys: {sorted(missing)}"
            raise ValueError(msg)


def _validate_flow_distribution(
    cases: list[EvalCase],
    flow: FlowName,
    count: int,
    e2e_count: int,
) -> None:
    if count != _EXPECTED_CASES_PER_FLOW:
        msg = f"{flow} must have {_EXPECTED_CASES_PER_FLOW} cases, got {count}"
        raise ValueError(msg)
    if e2e_count != _EXPECTED_E2E_PER_FLOW:
        msg = f"{flow} must have {_EXPECTED_E2E_PER_FLOW} end-to-end cases"
        raise ValueError(msg)
    answer_classes = Counter(
        answer_class
        for case in cases
        if case.flow == flow
        for answer_class in _ANSWER_CLASSES & set(case.tags)
    )
    if any(
        answer_classes[answer_class] != _EXPECTED_CASES_PER_ANSWER_CLASS
        for answer_class in _ANSWER_CLASSES
    ):
        msg = f"{flow} cases must be balanced across answer classes"
        raise ValueError(msg)


def serialize_cases(cases: list[EvalCase]) -> str:
    """Stable serialization used when publishing dataset inputs."""
    return json.dumps(
        [case.model_dump(mode="json") for case in cases],
        ensure_ascii=False,
        sort_keys=True,
    )


__all__ = [
    "default_dataset_dir",
    "load_cases",
    "serialize_cases",
    "validate_case_collection",
]
