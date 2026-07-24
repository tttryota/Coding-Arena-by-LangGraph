"""Typed dataset and result models used by the evaluation CLI."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

FlowName = Literal["quiz", "coding", "competitive"]


class EvalTurn(BaseModel):
    user_input: str
    input_source: Literal["form", "chat"] = "form"


class EvalExpectation(BaseModel):
    required_nodes: list[str]
    forbidden_nodes: list[str] = Field(default_factory=list)
    score_min: int = Field(ge=0, le=100)
    score_max: int = Field(ge=0, le=100)
    max_questions: int = Field(default=20, ge=1)

    @model_validator(mode="after")
    def validate_expectation(self) -> EvalExpectation:
        if self.score_min > self.score_max:
            msg = "score_min must be less than or equal to score_max"
            raise ValueError(msg)
        overlap = set(self.required_nodes) & set(self.forbidden_nodes)
        if overlap:
            msg = f"required_nodes and forbidden_nodes overlap: {sorted(overlap)}"
            raise ValueError(msg)
        return self


class EvalCase(BaseModel):
    id: str = Field(min_length=1)
    flow: FlowName
    initial_state: dict[str, object]
    turns: list[EvalTurn] = Field(min_length=1)
    expected: EvalExpectation
    rubrics: list[str] = Field(min_length=1)
    tags: list[str] = Field(min_length=1)
    end_to_end: bool = False


class JudgeScores(BaseModel):
    correctness: int = Field(ge=1, le=5)
    feedback_actionability: int = Field(ge=1, le=5)
    reasoning: str


class CaseResult(BaseModel):
    case_id: str
    flow: FlowName
    repeat: int
    score: int
    score_band_match: bool
    route: list[str]
    route_match: bool
    duration_ms: float
    semantic_correctness: int | None = None
    feedback_actionability: int | None = None
    output: dict[str, object]
    error: str | None = None


class EvalSummary(BaseModel):
    suite: Literal["contract", "quality", "benchmark"]
    passed: bool
    case_count: int
    result_count: int
    score_band_accuracy: float
    route_accuracy: float
    semantic_correctness_mean: float | None
    feedback_actionability_mean: float | None
    latency_p50_ms: float
    latency_p95_ms: float
    warnings: list[str] = Field(default_factory=list)


__all__ = [
    "CaseResult",
    "EvalCase",
    "EvalExpectation",
    "EvalSummary",
    "EvalTurn",
    "FlowName",
    "JudgeScores",
]
