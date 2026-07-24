from pathlib import Path

import pytest
from pydantic import ValidationError

from evaluation.datasets import load_cases, validate_case_collection
from evaluation.models import (
    CaseResult,
    EvalCase,
    EvalExpectation,
    EvalSummary,
    JudgeScores,
)
from evaluation.runner import apply_quality_baseline, run_contract


def test_default_dataset_has_balanced_versioned_cases() -> None:
    cases = load_cases()

    assert len(cases) == 36
    assert {case.flow for case in cases} == {"quiz", "coding", "competitive"}
    assert sum(case.end_to_end for case in cases) == 9
    for flow in ("quiz", "coding", "competitive"):
        flow_cases = [case for case in cases if case.flow == flow]
        assert sum("correct" in case.tags for case in flow_cases) == 4
        assert sum("partial" in case.tags for case in flow_cases) == 4
        assert sum("incorrect" in case.tags for case in flow_cases) == 4


def test_contract_suite_passes_all_dataset_contracts() -> None:
    cases = load_cases()

    run = run_contract(cases)

    assert run.summary.passed is True
    assert run.summary.case_count == 36
    assert run.summary.route_accuracy == 1.0
    assert run.summary.score_band_accuracy == 1.0


def test_duplicate_case_ids_are_rejected() -> None:
    cases = load_cases()

    with pytest.raises(ValueError, match="duplicate evaluation case ids"):
        validate_case_collection([*cases, cases[0]])


def test_overlapping_required_and_forbidden_nodes_are_rejected() -> None:
    with pytest.raises(ValidationError, match="overlap"):
        EvalExpectation(
            required_nodes=["answer_evaluation"],
            forbidden_nodes=["answer_evaluation"],
            score_min=0,
            score_max=100,
        )


def test_invalid_jsonl_reports_file_and_line(tmp_path: Path) -> None:
    dataset = tmp_path / "broken.jsonl"
    dataset.write_text("{not-json}\n", encoding="utf-8")

    with pytest.raises(ValueError, match=r"broken\.jsonl:1"):
        load_cases(tmp_path)


def test_missing_flow_state_key_is_rejected() -> None:
    cases = load_cases()
    invalid = EvalCase.model_validate(
        {
            **cases[0].model_dump(mode="json"),
            "initial_state": {},
        },
    )
    replacement = [invalid, *cases[1:]]

    with pytest.raises(ValueError, match="missing state keys"):
        validate_case_collection(replacement)


def test_quality_baseline_allows_ten_point_score_band_regression(
    tmp_path: Path,
) -> None:
    baseline = tmp_path / "quality.json"
    baseline.write_text(
        '{"score_band_accuracy": 0.75, "semantic_correctness_mean": 3.5}\n',
        encoding="utf-8",
    )
    summary = EvalSummary(
        suite="quality",
        passed=True,
        case_count=10,
        result_count=10,
        score_band_accuracy=0.70,
        route_accuracy=1.0,
        semantic_correctness_mean=3.5,
        feedback_actionability_mean=4.0,
        latency_p50_ms=1.0,
        latency_p95_ms=2.0,
    )
    results = [
        CaseResult(
            case_id=f"case-{index}",
            flow="quiz",
            repeat=1,
            score=80,
            score_band_match=index < 7,
            route=["answer_evaluation"],
            route_match=True,
            duration_ms=1.0,
            semantic_correctness=4,
            feedback_actionability=4,
            output={},
        )
        for index in range(10)
    ]

    compared = apply_quality_baseline(summary, results, baseline)

    assert compared.passed is True


def test_invalid_judge_score_is_rejected() -> None:
    with pytest.raises(ValidationError):
        JudgeScores(
            correctness=2,
            feedback_actionability=6,
            reasoning="invalid range",
        )
