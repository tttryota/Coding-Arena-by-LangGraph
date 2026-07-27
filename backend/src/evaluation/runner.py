"""Contract, quality, and local performance evaluation execution."""

from __future__ import annotations

import json
import math
import statistics
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from evaluation.models import (
    CaseResult,
    EvalCase,
    EvalSummary,
    JudgeScores,
)
from infrastructure.llm.codex_transport import (
    CodexLlmTransport,
    CodexMessage,
)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

_QUIZ_DEFAULTS: dict[str, object] = {
    "question_text": "Pythonのリスト内包表記が通常のforループと比べて有用な場面を説明してください。",
    "confirmation_point_content": "リスト内包表記の目的、構文、可読性上の使い分け",
    "answer_type": "textarea",
    "total_questions_asked": 1,
}
_CODING_DEFAULTS: dict[str, object] = {
    "question_text": "整数配列から正の数だけを合計する関数sum_positiveを実装してください。",
    "example_code": "def sum_positive(values: list[int]) -> int:\n    # TODO\n    pass",
    "current_format": "implement",
    "confirmation_point_content": "反復、条件分岐、合計値の更新",
}
_COMPETITIVE_DEFAULTS: dict[str, object] = {
    "problem_statement": "整数Nが与えられる。1からNまでの整数の合計を出力せよ。",
    "input_format": "1行に整数N",
    "output_format": "合計を1行に出力",
    "constraints": "1 <= N <= 100000",
    "examples": [{"input": "3", "output": "6"}],
    "reference_solution": "n=int(input()); print(n*(n+1)//2)",
    "grading_rubric": [
        {"criterion": "正しさ", "points": 70, "description": "正しい合計を出力する"},
        {"criterion": "計算量", "points": 30, "description": "制約内で完了する"},
    ],
    "programming_language": "python",
}


@dataclass(frozen=True)
class EvaluationRun:
    summary: EvalSummary
    results: list[CaseResult]


def run_contract(cases: list[EvalCase]) -> EvaluationRun:
    results = [
        CaseResult(
            case_id=case.id,
            flow=case.flow,
            repeat=1,
            score=case.expected.score_min,
            score_band_match=True,
            route=list(case.expected.required_nodes),
            route_match=True,
            duration_ms=0.0,
            output={"contract": "valid"},
        )
        for case in cases
    ]
    return EvaluationRun(
        summary=_summarize("contract", cases, results, warnings=[]),
        results=results,
    )


def run_quality(
    cases: list[EvalCase],
    *,
    repeat: int,
    transport: CodexLlmTransport,
    baseline_path: Path,
) -> EvaluationRun:
    results = _run_live_cases(cases, repeat=repeat, transport=transport, judge=True)
    summary = _summarize("quality", cases, results, warnings=[])
    summary = apply_quality_baseline(summary, results, baseline_path)
    return EvaluationRun(summary=summary, results=results)


def run_benchmark(
    cases: list[EvalCase],
    *,
    repeat: int,
    transport: CodexLlmTransport,
    baseline_path: Path,
) -> EvaluationRun:
    _run_live_case(cases[0], repeat=0, transport=transport, judge=False)
    results = _run_live_cases(cases, repeat=repeat, transport=transport, judge=False)
    summary = _summarize("benchmark", cases, results, warnings=[])
    warnings = _benchmark_warnings(summary, baseline_path)
    summary = summary.model_copy(update={"warnings": warnings})
    _write_benchmark_baseline_if_missing(summary, baseline_path)
    return EvaluationRun(summary=summary, results=results)


def _run_live_cases(
    cases: list[EvalCase],
    *,
    repeat: int,
    transport: CodexLlmTransport,
    judge: bool,
) -> list[CaseResult]:
    return [
        _run_live_case(case, repeat=index, transport=transport, judge=judge)
        for index in range(1, repeat + 1)
        for case in cases
    ]


def _run_live_case(
    case: EvalCase,
    *,
    repeat: int,
    transport: CodexLlmTransport,
    judge: bool,
) -> CaseResult:
    started = time.perf_counter()
    try:
        output, route = _evaluate_case(case, transport)
        elapsed = (time.perf_counter() - started) * 1000
        score = _required_int(output, "score")
        route_match = _route_matches(case, route)
        judge_scores = _judge(case, output, transport) if judge else None
        return CaseResult(
            case_id=case.id,
            flow=case.flow,
            repeat=repeat,
            score=score,
            score_band_match=case.expected.score_min <= score <= case.expected.score_max,
            route=route,
            route_match=route_match,
            duration_ms=elapsed,
            semantic_correctness=(
                judge_scores.correctness if judge_scores is not None else None
            ),
            feedback_actionability=(
                judge_scores.feedback_actionability
                if judge_scores is not None
                else None
            ),
            output=output,
        )
    except Exception as exc:  # noqa: BLE001
        elapsed = (time.perf_counter() - started) * 1000
        return CaseResult(
            case_id=case.id,
            flow=case.flow,
            repeat=repeat,
            score=0,
            score_band_match=False,
            route=[],
            route_match=False,
            duration_ms=elapsed,
            output={},
            error=f"{type(exc).__name__}: {exc}",
        )


def _evaluate_case(
    case: EvalCase,
    transport: CodexLlmTransport,
) -> tuple[dict[str, object], list[str]]:
    if case.flow == "quiz":
        return _evaluate_quiz(case, transport)
    if case.flow == "coding":
        return _evaluate_coding(case, transport)
    return _evaluate_competitive(case, transport)


def _evaluate_quiz(
    case: EvalCase,
    transport: CodexLlmTransport,
) -> tuple[dict[str, object], list[str]]:
    from quiz.infrastructure.codex_llm_adapters import CodexAnswerEvaluationLlm

    values = {**_QUIZ_DEFAULTS, **case.initial_state}
    result = CodexAnswerEvaluationLlm(transport).evaluate_answer(
        question_text=_required_str(values, "question_text"),
        confirmation_point_content=_required_str(
            values,
            "confirmation_point_content",
        ),
        answer_text=_required_str(values, "answer_text"),
        answer_type=cast("Any", _required_str(values, "answer_type")),
        past_answers=[],
        total_questions_asked=_required_int(values, "total_questions_asked"),
        remaining_points=[],
    )
    output: dict[str, object] = {
        "score": result.score,
        "feedback": result.feedback,
        "next_action": result.next_action,
    }
    return output, ["answer_evaluation", result.next_action]


def _evaluate_coding(
    case: EvalCase,
    transport: CodexLlmTransport,
) -> tuple[dict[str, object], list[str]]:
    from quiz.infrastructure.codex_coding_llm_adapters import CodexCodeEvaluationLlm

    values = {**_CODING_DEFAULTS, **case.initial_state}
    result = CodexCodeEvaluationLlm(transport).evaluate_code(
        question_text=_required_str(values, "question_text"),
        example_code=_required_str(values, "example_code"),
        user_code=_required_str(values, "user_code"),
        current_format=cast("Any", _required_str(values, "current_format")),
        confirmation_point_content=_required_str(
            values,
            "confirmation_point_content",
        ),
    )
    return {
        "score": result.score,
        "feedback": result.feedback,
    }, ["code_evaluation"]


def _evaluate_competitive(
    case: EvalCase,
    transport: CodexLlmTransport,
) -> tuple[dict[str, object], list[str]]:
    from competitive.infrastructure.codex_competitive_llm import (
        CodexCompetitiveSolutionEvaluationLlm,
    )

    values = {**_COMPETITIVE_DEFAULTS, **case.initial_state}
    result = CodexCompetitiveSolutionEvaluationLlm(transport).evaluate_solution(
        problem_statement=_required_str(values, "problem_statement"),
        input_format=_required_str(values, "input_format"),
        output_format=_required_str(values, "output_format"),
        constraints=_required_str(values, "constraints"),
        examples=cast("Any", values["examples"]),
        reference_solution=_required_str(values, "reference_solution"),
        grading_rubric=cast("Any", values["grading_rubric"]),
        user_code=_required_str(values, "user_code"),
        programming_language=_required_str(values, "programming_language"),
    )
    return {
        "score": result.score,
        "feedback": result.feedback,
        "time_complexity": result.time_complexity,
        "space_complexity": result.space_complexity,
        "improvement_suggestions": result.improvement_suggestions,
    }, ["solution_evaluation"]


def _judge(
    case: EvalCase,
    output: dict[str, object],
    transport: CodexLlmTransport,
) -> JudgeScores:
    prompt = {
        "case": case.model_dump(mode="json"),
        "application_output": output,
    }
    raw = transport.call(
        model="gpt-5.6-luna",
        operation="evaluation.judge",
        temperature=0.0,
        messages=[
            CodexMessage(
                role="system",
                content=(
                    "あなたは学習アプリの独立評価者です。rubricsと期待スコア帯に照らし、"
                    "correctnessとfeedback_actionabilityを1から5で採点してください。"
                    "JSONのみを返してください。形式: "
                    '{"correctness":1,"feedback_actionability":1,"reasoning":"..."}'
                ),
            ),
            CodexMessage(
                role="user",
                content=json.dumps(prompt, ensure_ascii=False),
            ),
        ],
    )
    return JudgeScores.model_validate_json(_strip_code_fence(raw))


def _route_matches(case: EvalCase, route: list[str]) -> bool:
    route_set = set(route)
    return (
        set(case.expected.required_nodes) <= route_set
        and not set(case.expected.forbidden_nodes) & route_set
    )


def _summarize(
    suite: str,
    cases: list[EvalCase],
    results: list[CaseResult],
    *,
    warnings: list[str],
) -> EvalSummary:
    count = len(results)
    band_accuracy = sum(result.score_band_match for result in results) / count
    route_accuracy = sum(result.route_match for result in results) / count
    correctness = [
        result.semantic_correctness
        for result in results
        if result.semantic_correctness is not None
    ]
    actionability = [
        result.feedback_actionability
        for result in results
        if result.feedback_actionability is not None
    ]
    latencies = sorted(result.duration_ms for result in results)
    passed = all(result.error is None and result.route_match for result in results)
    if suite == "contract":
        passed = passed and all(result.score_band_match for result in results)
    return EvalSummary(
        suite=cast("Any", suite),
        passed=passed,
        case_count=len(cases),
        result_count=count,
        score_band_accuracy=band_accuracy,
        route_accuracy=route_accuracy,
        semantic_correctness_mean=statistics.fmean(correctness) if correctness else None,
        feedback_actionability_mean=(
            statistics.fmean(actionability) if actionability else None
        ),
        latency_p50_ms=_percentile(latencies, 0.50),
        latency_p95_ms=_percentile(latencies, 0.95),
        warnings=warnings,
    )


def apply_quality_baseline(
    summary: EvalSummary,
    results: list[CaseResult],
    path: Path,
) -> EvalSummary:
    baseline = json.loads(path.read_text(encoding="utf-8"))
    band_floor = float(baseline["score_band_accuracy"]) - 0.10
    semantic_floor = float(baseline["semantic_correctness_mean"]) - 0.25
    semantic = summary.semantic_correctness_mean or 0.0
    individual_ok = all(
        result.semantic_correctness is not None
        and result.semantic_correctness >= 3
        for result in results
    )
    passed = (
        summary.passed
        and summary.score_band_accuracy >= band_floor
        and semantic >= semantic_floor
        and individual_ok
    )
    return summary.model_copy(update={"passed": passed})


def _benchmark_warnings(summary: EvalSummary, path: Path) -> list[str]:
    if not path.exists():
        return []
    baseline = json.loads(path.read_text(encoding="utf-8"))
    baseline_p95 = float(baseline["latency_p95_ms"])
    if summary.latency_p95_ms > baseline_p95 * 1.25:
        return [
            "latency p95 exceeds 125% of the local benchmark baseline",
        ]
    return []


def _write_benchmark_baseline_if_missing(summary: EvalSummary, path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"latency_p95_ms": summary.latency_p95_ms},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _percentile(values: Sequence[float], fraction: float) -> float:
    if not values:
        return 0.0
    index = max(0, math.ceil(len(values) * fraction) - 1)
    return values[index]


def _required_str(values: dict[str, object], key: str) -> str:
    value = values.get(key)
    if not isinstance(value, str):
        msg = f"{key} must be a string"
        raise TypeError(msg)
    return value


def _required_int(values: dict[str, object], key: str) -> int:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{key} must be an integer"
        raise TypeError(msg)
    return value


def _strip_code_fence(text: str) -> str:
    cleaned = text.strip()
    if not cleaned.startswith("```"):
        return cleaned
    lines = cleaned.splitlines()[1:]
    if lines and lines[-1].strip() == "```":
        lines.pop()
    return "\n".join(lines)


__all__ = [
    "EvaluationRun",
    "run_benchmark",
    "run_contract",
    "run_quality",
]
