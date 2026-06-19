"""競プロクイズ LLM アダプタの Codex app-server concrete 実装。

2つのアダプタを提供する:
- CodexCompetitiveProblemGenerationLlm: 問題 + 模範解答 + rubric 同時生成
- CodexCompetitiveSolutionEvaluationLlm: 保存済み rubric に基づく採点
"""

from __future__ import annotations

import json
import random
from typing import TYPE_CHECKING, Any, TypedDict

import structlog

from competitive.domain.competitive_types import (
    ProblemGenerationError,
    QuestionResponseError,
    SolutionEvaluationError,
)
from infrastructure.llm.codex_transport import (
    CodexLlmTransport,
    CodexMessage,
    CodexTransportHttpError,
    CodexTransportResponseError,
)

if TYPE_CHECKING:
    from competitive.application.question_response_types import CompetitiveChatMessage
    from competitive.domain.competitive_types import (
        ProblemExample,
        ProgrammingLanguage,
        RubricItem,
    )

logger = structlog.get_logger(__name__)

_JSON_INSTRUCTION = (
    "必ず JSON のみで回答してください。JSON の外にテキストを含めないでください。"
)
_COMPETITIVE_MODEL = "gpt-5.3-codex-spark"
_LANGUAGES: list[ProgrammingLanguage] = ["python", "typescript"]


def _parse_json(text: str) -> dict[str, Any]:
    """LLM レスポンスから JSON を抽出してパースする。"""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    result = json.loads(cleaned)
    if not isinstance(result, dict):
        msg = f"expected JSON object, got {type(result).__name__}"
        raise TypeError(msg)
    return result


def _validate_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        msg = f"{field} must be str, got {type(value).__name__}"
        raise TypeError(msg)
    return value


def _validate_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{field} must be int, got {type(value).__name__}"
        raise TypeError(msg)
    return value


def _validate_score(value: object, field: str) -> int:
    score = _validate_int(value, field)
    if score < 0 or score > 100:
        msg = f"{field} must be 0-100, got {score}"
        raise ValueError(msg)
    return score


def _error_code_for(exc: Exception) -> str:
    if isinstance(exc, CodexTransportHttpError):
        return "llm_request_failed"
    if isinstance(exc, (CodexTransportResponseError, json.JSONDecodeError, KeyError)):
        return "llm_response_parse_failed"
    if isinstance(exc, (TypeError, ValueError)):
        return "llm_response_parse_failed"
    return "llm_request_failed"


def _validate_example(item: object) -> ProblemExample:
    if not isinstance(item, dict):
        msg = f"example must be dict, got {type(item).__name__}"
        raise TypeError(msg)
    return {
        "input": _validate_str(item.get("input"), "example.input"),
        "output": _validate_str(item.get("output"), "example.output"),
    }


def _validate_rubric_item(item: object) -> RubricItem:
    if not isinstance(item, dict):
        msg = f"rubric item must be dict, got {type(item).__name__}"
        raise TypeError(msg)
    return {
        "criterion": _validate_str(item.get("criterion"), "rubric.criterion"),
        "points": _validate_int(item.get("points"), "rubric.points"),
        "description": _validate_str(
            item.get("description"),
            "rubric.description",
        ),
    }


def _validate_rubric_score_item(item: object) -> RubricScoreItem:
    if not isinstance(item, dict):
        msg = f"rubric_score item must be dict, got {type(item).__name__}"
        raise TypeError(msg)
    return {
        "criterion": _validate_str(item.get("criterion"), "rubric_score.criterion"),
        "points_awarded": _validate_int(
            item.get("points_awarded"),
            "rubric_score.points_awarded",
        ),
        "points_max": _validate_int(
            item.get("points_max"),
            "rubric_score.points_max",
        ),
    }


def _rebuild_rubric_scores(
    rubric_scores: list[RubricScoreItem],
    grading_rubric: list[RubricItem],
) -> None:
    """criteria 不一致時に保存済み rubric から rubric_scores を再構成する。"""
    score_map = {rs["criterion"]: rs["points_awarded"] for rs in rubric_scores}
    rubric_scores.clear()
    for r in grading_rubric:
        awarded = score_map.get(r["criterion"], 0)
        awarded = min(max(awarded, 0), r["points"])
        rubric_scores.append(
            {
                "criterion": r["criterion"],
                "points_awarded": awarded,
                "points_max": r["points"],
            },
        )


def _validate_rubric_scores_consistency(
    rubric_scores: list[RubricScoreItem],
    grading_rubric: list[RubricItem],
) -> None:
    """rubric_scores が保存済み grading_rubric と同じ観点・配点か検証する。"""
    if not rubric_scores:
        msg = "rubric_scores must not be empty"
        raise ValueError(msg)
    expected_criteria = {r["criterion"]: r["points"] for r in grading_rubric}
    actual_criteria = [rs["criterion"] for rs in rubric_scores]
    seen: set[str] = set()
    for c in actual_criteria:
        if c in seen:
            msg = f"duplicate criterion in rubric_scores: {c}"
            raise ValueError(msg)
        seen.add(c)
    if set(actual_criteria) != set(expected_criteria.keys()):
        logger.warning(
            "rubric_scores criteria mismatch, rebuilding from saved rubric",
            expected=list(expected_criteria.keys()),
            actual=actual_criteria,
        )
        _rebuild_rubric_scores(rubric_scores, grading_rubric)
        return
    for rs in rubric_scores:
        expected_max = expected_criteria[rs["criterion"]]
        rs["points_max"] = expected_max
        rs["points_awarded"] = min(max(rs["points_awarded"], 0), expected_max)


def _pick_language() -> ProgrammingLanguage:
    """Python または TypeScript をランダムに選択する。"""
    return random.choice(_LANGUAGES)  # noqa: S311


def _history_to_text(history: list[CompetitiveChatMessage]) -> str:
    if not history:
        return "なし"
    return "\n".join(
        f"{'ユーザー' if item['role'] == 'user' else 'アシスタント'}: {item['content']}"
        for item in history
    )


# ---------------------------------------------------------------------------
# Problem Generation (問題 + 模範解答 + rubric 同時生成)
# ---------------------------------------------------------------------------


class ProblemGenerationResult:
    """問題生成の結果を保持する値オブジェクト。"""

    __slots__ = (
        "constraints",
        "examples",
        "grading_rubric",
        "input_format",
        "output_format",
        "problem_statement",
        "programming_language",
        "reference_solution",
    )

    def __init__(  # noqa: PLR0913
        self,
        *,
        programming_language: ProgrammingLanguage,
        problem_statement: str,
        input_format: str,
        output_format: str,
        constraints: str,
        examples: list[ProblemExample],
        reference_solution: str,
        grading_rubric: list[RubricItem],
    ) -> None:
        self.programming_language = programming_language
        self.problem_statement = problem_statement
        self.input_format = input_format
        self.output_format = output_format
        self.constraints = constraints
        self.examples = examples
        self.reference_solution = reference_solution
        self.grading_rubric = grading_rubric


def _validate_problem_response(
    data: dict[str, Any],
    language: ProgrammingLanguage,
) -> ProblemGenerationResult:
    """LLM レスポンスを検証して ProblemGenerationResult を構築する。"""
    problem_statement = _validate_str(
        data["problem_statement"],
        "problem_statement",
    )
    input_format = _validate_str(data["input_format"], "input_format")
    output_format = _validate_str(data["output_format"], "output_format")
    constraints = _validate_str(data["constraints"], "constraints")
    examples = [_validate_example(e) for e in data["examples"]]
    if len(examples) < 2:
        msg = f"examples must have >= 2 items, got {len(examples)}"
        raise ValueError(msg)
    reference_solution = _validate_str(
        data["reference_solution"],
        "reference_solution",
    )
    grading_rubric = [_validate_rubric_item(r) for r in data["grading_rubric"]]
    if len(grading_rubric) < 3:
        msg = f"grading_rubric must have >= 3 items, got {len(grading_rubric)}"
        raise ValueError(msg)
    total_points = sum(r["points"] for r in grading_rubric)
    if total_points != 100:
        msg = f"grading_rubric points must sum to 100, got {total_points}"
        raise ValueError(msg)
    return ProblemGenerationResult(
        programming_language=language,
        problem_statement=problem_statement,
        input_format=input_format,
        output_format=output_format,
        constraints=constraints,
        examples=examples,
        reference_solution=reference_solution,
        grading_rubric=grading_rubric,
    )


class CodexCompetitiveProblemGenerationLlm:
    """テーマから問題・模範解答・rubric を同時生成する LLM アダプタ。"""

    def __init__(self, transport: CodexLlmTransport) -> None:
        self._transport = transport

    def generate_problem(
        self,
        theme_label: str,
        theme_category: str,
    ) -> ProblemGenerationResult:
        language = _pick_language()
        system = (
            "あなたは競技プログラミングの問題作成AIです。\n"
            "指定されたアルゴリズムテーマに基づき、以下を同時に生成してください:\n"
            "1. 問題文(problem_statement): テーマのアルゴリズムを使って解く問題\n"
            "2. 入力形式(input_format): 入力の形式説明\n"
            "3. 出力形式(output_format): 出力の形式説明\n"
            "4. 制約(constraints): 入力値の制約条件\n"
            "5. 入出力例(examples): 2〜3個の入出力例(input, output)\n"
            f"6. 模範解答(reference_solution): {language} で書かれた正しい解答コード\n"
            "7. 採点基準(grading_rubric): 3〜5項目の採点基準(criterion, points, description)\n\n"
            "問題設計ルール:\n"
            "- AtCoder の ABC〜ARC 程度の難易度にしてください\n"
            "- 問題文は明確で曖昧さがないようにしてください\n"
            "- 入出力例は問題の理解を助けるものにしてください\n"
            "- 模範解答は正しく動作し、適切な計算量のコードにしてください\n"
            "- 採点基準の points の合計が 100 になるようにしてください\n"
            "- 各採点基準は独立した観点(正しさ、効率性、コード品質など)で評価してください\n\n"
            f"{_JSON_INSTRUCTION}\n"
            "形式:\n"
            "{\n"
            '  "problem_statement": "問題文",\n'
            '  "input_format": "入力形式",\n'
            '  "output_format": "出力形式",\n'
            '  "constraints": "制約",\n'
            '  "examples": [{"input": "入力例", "output": "出力例"}],\n'
            '  "reference_solution": "模範解答コード",\n'
            '  "grading_rubric": [{"criterion": "基準名", "points": 配点, '
            '"description": "説明"}]\n'
            "}"
        )
        user = (
            f"テーマ: {theme_label}\nカテゴリ: {theme_category}\n出題言語: {language}"
        )
        try:
            raw = self._transport.call(
                model=_COMPETITIVE_MODEL,
                messages=[
                    CodexMessage(role="system", content=system),
                    CodexMessage(role="user", content=user),
                ],
            )
            return _validate_problem_response(_parse_json(raw), language)
        except ProblemGenerationError:
            raise
        except Exception as exc:
            raise ProblemGenerationError(
                error_code=_error_code_for(exc),
                message=f"problem generation failed: {exc}",
            ) from exc


# ---------------------------------------------------------------------------
# Solution Evaluation (保存済み rubric ベース採点)
# ---------------------------------------------------------------------------


class RubricScoreItem(TypedDict):
    """rubric 項目別の得点。"""

    criterion: str
    points_awarded: int
    points_max: int


class SolutionEvaluationResult:
    """採点結果を保持する値オブジェクト。"""

    __slots__ = (
        "feedback",
        "improvement_suggestions",
        "rubric_scores",
        "score",
        "space_complexity",
        "time_complexity",
    )

    def __init__(  # noqa: PLR0913
        self,
        *,
        score: int,
        feedback: str,
        time_complexity: str,
        space_complexity: str,
        improvement_suggestions: str,
        rubric_scores: list[RubricScoreItem],
    ) -> None:
        self.score = score
        self.feedback = feedback
        self.time_complexity = time_complexity
        self.space_complexity = space_complexity
        self.improvement_suggestions = improvement_suggestions
        self.rubric_scores = rubric_scores


class CodexCompetitiveSolutionEvaluationLlm:
    """保存済み rubric に基づいてユーザーコードを採点する LLM アダプタ。"""

    def __init__(self, transport: CodexLlmTransport) -> None:
        self._transport = transport

    def evaluate_solution(  # noqa: PLR0913
        self,
        *,
        problem_statement: str,
        input_format: str,
        output_format: str,
        constraints: str,
        examples: list[ProblemExample],
        reference_solution: str,
        grading_rubric: list[RubricItem],
        user_code: str,
        programming_language: ProgrammingLanguage,
    ) -> SolutionEvaluationResult:
        rubric_text = "\n".join(
            f"- {r['criterion']} ({r['points']}点): {r['description']}"
            for r in grading_rubric
        )
        examples_text = "\n".join(
            f"入力:\n{e['input']}\n出力:\n{e['output']}" for e in examples
        )
        system = (
            "あなたは競技プログラミングの採点AIです。\n"
            "以下の採点基準に基づいてユーザーの解答コードを評価してください。\n\n"
            f"採点基準:\n{rubric_text}\n\n"
            "評価ルール:\n"
            "- 各基準について配点内で部分点を付け、rubric_scores に内訳を返してください\n"
            "- score は rubric_scores の points_awarded の合計 (0-100)\n"
            "- feedback は良い点と改善点を含めてください\n"
            "- time_complexity は時間計算量をO記法で示してください\n"
            "- space_complexity は空間計算量をO記法で示してください\n"
            "- improvement_suggestions は具体的な改善提案を書いてください\n"
            "- コードが空の場合: score=0 とし、解答を促す feedback を返してください\n\n"
            f"{_JSON_INSTRUCTION}\n"
            "形式:\n"
            "{\n"
            '  "score": 0-100,\n'
            '  "feedback": "フィードバック",\n'
            '  "time_complexity": "O(...)",\n'
            '  "space_complexity": "O(...)",\n'
            '  "improvement_suggestions": "改善提案",\n'
            '  "rubric_scores": [{"criterion": "基準名", '
            '"points_awarded": 得点, "points_max": 配点}]\n'
            "}"
        )
        user = (
            f"問題文:\n{problem_statement}\n\n"
            f"入力形式:\n{input_format}\n\n"
            f"出力形式:\n{output_format}\n\n"
            f"制約:\n{constraints}\n\n"
            f"入出力例:\n{examples_text}\n\n"
            f"出題言語: {programming_language}\n\n"
            f"模範解答:\n{reference_solution}\n\n"
            f"ユーザーの解答:\n{user_code}"
        )
        try:
            raw = self._transport.call(
                model=_COMPETITIVE_MODEL,
                messages=[
                    CodexMessage(role="system", content=system),
                    CodexMessage(role="user", content=user),
                ],
            )
            data = _parse_json(raw)
            rubric_scores = [
                _validate_rubric_score_item(rs) for rs in data["rubric_scores"]
            ]
            _validate_rubric_scores_consistency(
                rubric_scores,
                grading_rubric,
            )
            reported_score = _validate_score(data["score"], "score")
            computed_score = sum(rs["points_awarded"] for rs in rubric_scores)
            score = min(max(computed_score, 0), 100)
            if reported_score != score:
                logger.warning(
                    "LLM reported score differs from rubric_scores sum",
                    reported=reported_score,
                    computed=score,
                )
            return SolutionEvaluationResult(
                score=score,
                feedback=_validate_str(data["feedback"], "feedback"),
                time_complexity=_validate_str(
                    data["time_complexity"],
                    "time_complexity",
                ),
                space_complexity=_validate_str(
                    data["space_complexity"],
                    "space_complexity",
                ),
                improvement_suggestions=_validate_str(
                    data["improvement_suggestions"],
                    "improvement_suggestions",
                ),
                rubric_scores=rubric_scores,
            )
        except SolutionEvaluationError:
            raise
        except Exception as exc:
            raise SolutionEvaluationError(
                error_code=_error_code_for(exc),
                message=f"solution evaluation failed: {exc}",
            ) from exc


class CodexCompetitiveQuestionResponseLlm:
    """競プロ問題に対する質問へヒントまたは解説を返す LLM アダプタ。"""

    def __init__(self, transport: CodexLlmTransport) -> None:
        self._transport = transport

    def generate_chat_response(  # noqa: PLR0913
        self,
        *,
        problem_statement: str,
        input_format: str,
        output_format: str,
        constraints: str,
        examples: list[ProblemExample],
        programming_language: ProgrammingLanguage,
        user_input: str,
        history: list[CompetitiveChatMessage],
    ) -> str:
        examples_text = "\n".join(
            f"入力:\n{e['input']}\n出力:\n{e['output']}" for e in examples
        )
        history_text = _history_to_text(history)
        system = (
            "あなたは競技プログラミングのメンターAIです。\n"
            "与えられた問題について、ユーザーの質問に日本語で簡潔かつ正確に答えてください。\n"
            "- 問題文・制約・入出力例の範囲で説明してください\n"
            "- 箇条書きや短い段落で読みやすくしてください\n"
            "- まだ未提出です。正解コード、完成済みの実装、直接的な解法の言い切りは避けてください\n"
            "- ヒント、考える観点、落とし穴、計算量の考え方に留めてください\n"
        )
        system += (
            f"\n{_JSON_INSTRUCTION}\n"
            "形式:\n"
            "{\n"
            '  "chat_response_text": "質問への応答"\n'
            "}"
        )
        user = (
            f"問題文:\n{problem_statement}\n\n"
            f"入力形式:\n{input_format}\n\n"
            f"出力形式:\n{output_format}\n\n"
            f"制約:\n{constraints}\n\n"
            f"入出力例:\n{examples_text}\n\n"
            f"出題言語: {programming_language}\n\n"
            f"会話履歴:\n{history_text}\n\n"
        )
        user += f"ユーザーの質問:\n{user_input}"
        try:
            raw = self._transport.call(
                model=_COMPETITIVE_MODEL,
                messages=[
                    CodexMessage(role="system", content=system),
                    CodexMessage(role="user", content=user),
                ],
            )
            data = _parse_json(raw)
            return _validate_str(
                data["chat_response_text"],
                "chat_response_text",
            )
        except QuestionResponseError:
            raise
        except Exception as exc:
            raise QuestionResponseError(
                error_code=_error_code_for(exc),
                message=f"question response generation failed: {exc}",
            ) from exc


__all__ = [
    "CodexCompetitiveProblemGenerationLlm",
    "CodexCompetitiveQuestionResponseLlm",
    "CodexCompetitiveSolutionEvaluationLlm",
    "ProblemGenerationResult",
    "RubricScoreItem",
    "SolutionEvaluationResult",
]
