from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-089-basic',
    title='行列累乗 の基本',
    unit_kind='foundation',
    target_skill='行列累乗 の基本',
    concept_overview='行列累乗は、漸化式や状態遷移を行列で表し、その行列を高速べき乗して N ステップ先の状態を求める知識です。まずはフィボナッチ数列を 2x2 行列へ直す基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-089-basic-p1',
            title='行列累乗 の基本 / フィボナッチ数列の N 項目 F_N を 10^9+7 で割った余りで求めよ',
            problem_statement='整数 N が与えられる。フィボナッチ数列の N 項目 F_N を 10^9+7 で割った余りで求めよ。F_0=0, F_1=1 とする。',
            input_format='1 行目に N。',
            output_format='F_N mod 1000000007 を出力する。',
            constraints='0 <= N <= 10^18',
            examples=[{'input': '10', 'output': '55'}],
            canonical_reference_solution="MOD = 10 ** 9 + 7\n\ndef mul(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:\n    return [\n        [\n            (a[i][0] * b[0][j] + a[i][1] * b[1][j]) % MOD\n            for j in range(2)\n        ]\n        for i in range(2)\n    ]\n\ndef solve() -> None:\n    n = int(input())\n    result = [[1, 0], [0, 1]]\n    base = [[1, 1], [1, 0]]\n    while n > 0:\n        if n & 1:\n            result = mul(result, base)\n        base = mul(base, base)\n        n >>= 1\n    print(result[0][1])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
