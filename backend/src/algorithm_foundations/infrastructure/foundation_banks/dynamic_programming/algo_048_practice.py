from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-048-practice',
    title='ゲーム理論DP（Grundy数） を素直に実装する',
    unit_kind='foundation',
    target_skill='ゲーム理論DP（Grundy数） を素直に実装する',
    concept_overview='勝敗 DP を一歩進めると、各状態に Grundy 数を割り当てられます。到達できる次状態の Grundy 数の mex を取る形を、1 山のゲームで確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-048-practice-p1',
            title='ゲーム理論DP（Grundy数） を素直に実装する / 1 山ゲームの Grundy 数を求める',
            problem_statement='石が N 個ある 1 山ゲームを考える。1 回の手では、あらかじめ与えられた手数 d_1, d_2, ..., d_K のいずれかだけ石を取れる。状態 x の Grundy 数を、その状態から到達できる状態の Grundy 数集合の mex として定めるとき、石が N 個ある状態の Grundy 数を求めよ。',
            input_format='1 行目に N K。\n2 行目に d_1..d_K。',
            output_format='Grundy(N) を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= K <= 20\n1 <= d_i <= N',
            examples=[{'input': '7 3\n1 3 4', 'output': '0'}],
            canonical_reference_solution="def solve() -> None:\n    n, k = map(int, input().split())\n    moves = list(map(int, input().split()))\n    grundy = [0] * (n + 1)\n    for stones in range(1, n + 1):\n        seen = set()\n        for move in moves:\n            if stones >= move:\n                seen.add(grundy[stones - move])\n        mex = 0\n        while mex in seen:\n            mex += 1\n        grundy[stones] = mex\n    print(grundy[n])\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
