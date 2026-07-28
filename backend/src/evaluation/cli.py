"""Command-line entry point for LangGraph evaluation suites."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from evaluation.datasets import load_cases
from evaluation.publisher import publish_run
from evaluation.runner import (
    EvaluationRun,
    run_benchmark,
    run_contract,
    run_quality,
)
from infrastructure.config.settings import Settings
from infrastructure.llm.codex_transport import CodexLlmTransport
from infrastructure.observability import create_observability


def main() -> int:  # noqa: PLR0915
    args = _parse_args()
    cases = load_cases()
    output_root = Path(".eval-results")
    quality_baseline = Path("evals/baselines/quality.json")
    benchmark_baseline = output_root / "benchmark-baseline.json"

    observability = None
    transport = None
    try:
        if args.suite == "contract":
            run = run_contract(cases)
        else:
            settings = Settings()
            if args.suite == "quality":
                settings = settings.model_copy(
                    update={"langfuse_tracing_environment": "evaluation"},
                )
            observability = create_observability(settings)
            transport = CodexLlmTransport(observability=observability)
            if args.suite == "quality":
                run = run_quality(
                    cases,
                    repeat=args.repeat,
                    transport=transport,
                    baseline_path=quality_baseline,
                )
            else:
                run = run_benchmark(
                    cases,
                    repeat=args.repeat,
                    transport=transport,
                    baseline_path=benchmark_baseline,
                )
        paths = _write_results(output_root, run)
        if args.publish:
            publish_run(cases, run)
        _print_summary(run, paths)
        return 0 if run.summary.passed else 1
    finally:
        if transport is not None:
            transport.close()
        if observability is not None:
            observability.flush()
            observability.shutdown()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run LangGraph evaluation suites")
    parser.add_argument("suite", choices=("contract", "quality", "benchmark"))
    parser.add_argument("--repeat", type=int, default=None)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    if args.repeat is None:
        args.repeat = 3 if args.suite == "quality" else 5
    if args.repeat < 1:
        parser.error("--repeat must be at least 1")
    return args


def _write_results(root: Path, run: EvaluationRun) -> tuple[Path, Path]:
    root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    stem = f"{run.summary.suite}-{timestamp}"
    json_path = root / f"{stem}.json"
    markdown_path = root / f"{stem}.md"
    payload = {
        "summary": run.summary.model_dump(mode="json"),
        "results": [result.model_dump(mode="json") for result in run.results],
    }
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(run), encoding="utf-8")
    return json_path, markdown_path


def _render_markdown(run: EvaluationRun) -> str:
    summary = run.summary
    lines = [
        f"# {summary.suite} evaluation",
        "",
        f"- passed: `{summary.passed}`",
        f"- cases: `{summary.case_count}`",
        f"- results: `{summary.result_count}`",
        f"- score band accuracy: `{summary.score_band_accuracy:.3f}`",
        f"- route accuracy: `{summary.route_accuracy:.3f}`",
        f"- latency p50: `{summary.latency_p50_ms:.1f} ms`",
        f"- latency p95: `{summary.latency_p95_ms:.1f} ms`",
    ]
    if summary.semantic_correctness_mean is not None:
        lines.append(
            f"- semantic correctness: `{summary.semantic_correctness_mean:.3f}`",
        )
    lines.extend(["", "## Failures", ""])
    failures = [
        result for result in run.results
        if result.error is not None or not result.route_match or not result.score_band_match
    ]
    lines.extend(
        f"- `{result.case_id}`: {result.error or 'expectation mismatch'}"
        for result in failures
    )
    if not failures:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def _print_summary(run: EvaluationRun, paths: tuple[Path, Path]) -> None:
    summary = run.summary
    print(  # noqa: T201
        f"{summary.suite}: passed={summary.passed} "
        f"band={summary.score_band_accuracy:.3f} "
        f"route={summary.route_accuracy:.3f} "
        f"p95={summary.latency_p95_ms:.1f}ms",
    )
    print(f"results: {paths[0]} and {paths[1]}")  # noqa: T201
    for warning in summary.warnings:
        print(f"warning: {warning}")  # noqa: T201


if __name__ == "__main__":
    raise SystemExit(main())
