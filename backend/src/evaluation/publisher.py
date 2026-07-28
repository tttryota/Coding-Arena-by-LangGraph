"""Best-effort publication of local evaluation results to Langfuse."""

from __future__ import annotations

import subprocess
from collections import defaultdict
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

import structlog

if TYPE_CHECKING:
    from evaluation.models import EvalCase
    from evaluation.runner import EvaluationRun

logger = structlog.get_logger(__name__)

_DATASET_NAME = "obsidian-langgraph-v1"


def publish_run(cases: list[EvalCase], run: EvaluationRun) -> None:
    """Publish idempotent dataset items and a comparable experiment run."""
    try:
        from langfuse import get_client

        client = get_client()
        _ensure_dataset(client)
        for case in cases:
            client.create_dataset_item(
                id=case.id,
                dataset_name=_DATASET_NAME,
                input=case.model_dump(mode="json"),
                expected_output=case.expected.model_dump(mode="json"),
            )

        dataset = client.get_dataset(_DATASET_NAME)
        grouped = _group_results(run)
        timestamp = datetime.now(tz=UTC)
        dataset.run_experiment(
            name=f"obsidian-{run.summary.suite}",
            run_name=f"{run.summary.suite}-{timestamp:%Y%m%dT%H%M%SZ}",
            description="Local LangGraph evaluation results",
            task=lambda *, item, **_: {
                "case_id": item.id,
                "results": grouped.get(item.id, []),
            },
            evaluators=[
                _boolean_evaluator("score_band_match"),
                _boolean_evaluator("route_match"),
                _numeric_evaluator("semantic_correctness"),
                _numeric_evaluator("feedback_actionability"),
            ],
            metadata={
                "suite": run.summary.suite,
                "git_sha": _git_sha(),
                "executed_at": timestamp.isoformat(),
            },
        )
        client.flush()
    except Exception:
        logger.exception("evaluation_publish_failed")


def _ensure_dataset(client: Any) -> None:
    try:
        client.get_dataset(_DATASET_NAME, fetch_items_page_size=1)
    except Exception:  # noqa: BLE001
        client.create_dataset(
            name=_DATASET_NAME,
            description="Versioned local cases for quiz, coding, and competitive flows",
            metadata={"owner": "local", "version": 1},
        )


def _group_results(run: EvaluationRun) -> dict[str, list[dict[str, object]]]:
    grouped: defaultdict[str, list[dict[str, object]]] = defaultdict(list)
    for result in run.results:
        grouped[result.case_id].append(result.model_dump(mode="json"))
    return dict(grouped)


def _boolean_evaluator(field: str) -> Any:
    def evaluate(*, output: dict[str, object], **_: object) -> dict[str, object]:
        results = _result_rows(output)
        values = [bool(result[field]) for result in results]
        return {
            "name": field,
            "value": sum(values) / len(values) if values else 0.0,
        }

    return evaluate


def _numeric_evaluator(field: str) -> Any:
    def evaluate(*, output: dict[str, object], **_: object) -> dict[str, object]:
        results = _result_rows(output)
        values = [
            value
            for result in results
            if isinstance((value := result.get(field)), int)
        ]
        return {
            "name": field,
            "value": sum(values) / len(values) if values else 0.0,
        }

    return evaluate


def _result_rows(output: dict[str, object]) -> list[dict[str, object]]:
    results = output.get("results")
    if not isinstance(results, list):
        return []
    return cast("list[dict[str, object]]", results)


def _git_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],  # noqa: S607
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


__all__ = ["publish_run"]
