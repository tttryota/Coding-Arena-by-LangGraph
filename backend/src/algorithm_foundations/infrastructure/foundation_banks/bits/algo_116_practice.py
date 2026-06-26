from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-116-practice',
    title='XORの性質と応用 を素直に実装する',
    unit_kind='foundation',
    target_skill='XORの性質と応用 を素直に実装する',
    concept_overview='XOR の「同じ値を 2 回足すと消える」性質を使うと、0..N の全体集合から一部が欠けたときも、残りとの打ち消しで欠けた値を取り出せます。ここでは missing number を復元する別視点を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-116-practice-p1',
            title='XORの性質と応用 を素直に実装する / 0..N から 1 つ欠けた値を求める',
            problem_statement='0 以上 N 以下の整数が本来 1 回ずつ現れるはずだが、そのうち 1 つだけ欠けた長さ N の列 A が与えられる。欠けている値を求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='答えを出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai <= N\n0..N のうちちょうど 1 つだけが欠け、他は 1 回ずつ現れる',
            examples=[{'input': '5\n0 1 3 5 2', 'output': '4'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    ans = 0\n    for value in range(n + 1):\n        ans ^= value\n    for value in map(int, input().split()):\n        ans ^= value\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
