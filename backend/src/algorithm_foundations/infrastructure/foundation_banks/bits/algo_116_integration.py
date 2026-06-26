from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-116-integration',
    title='XORの性質と応用 の総合演習',
    unit_kind='integration',
    target_skill='XORの性質と応用 の総合演習',
    concept_overview='XOR は全体を 1 回集約しておくと、そこから一部を外した結果を復元できます。全体 XOR と各要素の寄与を組み合わせ、問い合わせごとに別の答えを作る流れを確認します。',
    problem_bank=[
        problem(
            problem_id='algo-116-integration-p1',
            title='XORの性質と応用 の総合演習 / 指定要素を除いた全体 XOR を求める',
            problem_statement='長さ N の整数列 A と Q 個の問い合わせが与えられる。各問い合わせでは 1 つの添字 i が与えられるので、A_i を除いた残りすべての要素の XOR を求めよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に i。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n0 <= Ai < 2^60\n1 <= i <= N',
            examples=[{'input': '4 3\n1 2 3 4\n1\n3\n4', 'output': '5\n7\n0'}],
            canonical_reference_solution="def solve() -> None:\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    total = 0\n    for value in a:\n        total ^= value\n    out = []\n    for _ in range(q):\n        i = int(input()) - 1\n        out.append(str(total ^ a[i]))\n    print('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
