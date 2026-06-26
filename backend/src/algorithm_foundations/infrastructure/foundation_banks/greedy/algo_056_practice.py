from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-056-practice',
    title='マッチングの貪欲構成 を素直に実装する',
    unit_kind='foundation',
    target_skill='マッチングの貪欲構成 を素直に実装する',
    concept_overview='使える最小の相手を選ぶ貪欲は、組数を最大化するだけでなく、「必要以上に大きい相手を使わない」ことで余りの総量も抑えます。ここでは最大組数を保ちながら、余りの総和を最小化します。',
    problem_bank=[
        problem(
            problem_id='algo-056-practice-p1',
            title='マッチングの貪欲構成 を素直に実装する / 最大組数の中で余り総和を最小化する',
            problem_statement='長さ N の整数列 A と長さ M の整数列 B が与えられる。各 A_i を、自分以上の B_j と高々 1 回ずつ組にできるとする。まず作れる組数を最大化し、その中で `Σ (B_j - A_i)` を最小化せよ。',
            input_format='1 行目に N M。\n2 行目に A1..AN。\n3 行目に B1..BM。',
            output_format='1 行目に最大組数 K、2 行目にその条件での余り総和の最小値を出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n0 <= Ai, Bj <= 10^9',
            examples=[{'input': '4 5\n2 4 8 9\n1 3 4 10 10', 'output': '4\n4'}],
            canonical_reference_solution="def solve() -> None:\n    input()\n    a = sorted(map(int, input().split()))\n    b = sorted(map(int, input().split()))\n    i = j = 0\n    count = 0\n    slack = 0\n    while i < len(a) and j < len(b):\n        if b[j] >= a[i]:\n            count += 1\n            slack += b[j] - a[i]\n            i += 1\n            j += 1\n        else:\n            j += 1\n    print(count)\n    print(slack)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
