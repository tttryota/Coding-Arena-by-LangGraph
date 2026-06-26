from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-117-practice',
    title='ポップカウント（立っているビット数） を素直に実装する',
    unit_kind='foundation',
    target_skill='ポップカウント（立っているビット数） を素直に実装する',
    concept_overview='ポップカウントは、各整数が何個のフラグを持つかを特徴量として使えます。各要素の bit 数を調べ、条件に合うものだけを数える視点へ広げます。',
    problem_bank=[
        problem(
            problem_id='algo-117-practice-p1',
            title='ポップカウント（立っているビット数） を素直に実装する / 立っている bit 数がちょうど K 個の要素数を求める',
            problem_statement='長さ N の整数列 A と整数 K が与えられる。2 進表現で立っている bit 数がちょうど K 個である要素が何個あるかを求めよ。',
            input_format='1 行目に N K。\n2 行目に A1..AN。',
            output_format='答えを出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= K <= 60\n0 <= Ai < 2^60',
            examples=[{'input': '5 2\n3 5 6 7 8', 'output': '3'}],
            canonical_reference_solution="def solve() -> None:\n    n, k = map(int, input().split())\n    a = map(int, input().split())\n    ans = 0\n    for value in a:\n        if value.bit_count() == k:\n            ans += 1\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
