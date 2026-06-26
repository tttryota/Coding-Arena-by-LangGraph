from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-056-basic',
    title='マッチングの貪欲構成 の基本',
    unit_kind='foundation',
    target_skill='マッチングの貪欲構成 の基本',
    concept_overview='マッチングの貪欲構成は、小さい要求から順に、それを満たせる最小の相手を割り当てると組数を最大化しやすい知識です。2 列を整列して前から対応づける基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-056-basic-p1',
            title='マッチングの貪欲構成 の基本 / 作れる組数の最大値を求める',
            problem_statement='長さ N の整数列 A と長さ M の整数列 B が与えられる。各 A_i を、自分以上の B_j と高々 1 回ずつ組にできるとする。作れる組数の最大値を求めよ。',
            input_format='1 行目に N M。\n2 行目に A1..AN。\n3 行目に B1..BM。',
            output_format='作れる組数の最大値を出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n0 <= Ai, Bj <= 10^9',
            examples=[{'input': '4 5\n2 4 8 9\n1 3 4 10 10', 'output': '4'}],
            canonical_reference_solution="def solve() -> None:\n    input()\n    a = sorted(map(int, input().split()))\n    b = sorted(map(int, input().split()))\n    i = j = ans = 0\n    while i < len(a) and j < len(b):\n        if b[j] >= a[i]:\n            ans += 1\n            i += 1\n            j += 1\n        else:\n            j += 1\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
