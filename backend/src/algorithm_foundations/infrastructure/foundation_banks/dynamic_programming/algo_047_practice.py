from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-047-practice',
    title='確率DP・期待値DP を素直に実装する',
    unit_kind='foundation',
    target_skill='確率DP・期待値DP を素直に実装する',
    concept_overview='期待値DPでは、状態 i からゴールまでに必要な平均手数を、次に進む状態の平均から逆向きに求めます。1 手ぶん足して次状態の平均をならす形を実装で確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-047-practice-p1',
            title='確率DP・期待値DP を素直に実装する / 1 歩か 2 歩で進むとき、ゴールまでの期待手数を求める',
            problem_statement='0 から始めて、各手番で確率 1/2 で 1 歩、確率 1/2 で 2 歩進む。位置が N 以上になったら終了するとき、ゴールまでの期待手数を求めよ。',
            input_format='1 行目に N。',
            output_format='期待値を小数で出力する。絶対誤差または相対誤差 1e-9 まで許容する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[{'input': '2', 'output': '1.5'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    dp = [0.0] * (n + 2)\n    for pos in range(n - 1, -1, -1):\n        dp[pos] = 1.0 + (dp[min(n, pos + 1)] + dp[min(n, pos + 2)]) / 2.0\n    print(dp[0])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
