from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-089-practice',
    title='行列累乗 を素直に実装する',
    unit_kind='foundation',
    target_skill='行列累乗 を素直に実装する',
    concept_overview='2x2 行列で 1 本の漸化式が解けたら、遷移を 3x3 に広げて複数項の依存も同様に扱えます。ここではトリボナッチ数列を状態ベクトルで持ち、N ステップ先を求めます。',
    problem_bank=[
        problem(
            problem_id='algo-089-practice-p1',
            title='行列累乗 を素直に実装する / トリボナッチ数列の N 項目を求める',
            problem_statement='整数 N が与えられる。トリボナッチ数列 T_N を 10^9+7 で割った余りで求めよ。T_0=0, T_1=0, T_2=1, T_n=T_{n-1}+T_{n-2}+T_{n-3} とする。',
            input_format='1 行目に N。',
            output_format='T_N mod 1000000007 を出力する。',
            constraints='0 <= N <= 10^18',
            examples=[{'input': '6', 'output': '7'}],
            canonical_reference_solution="MOD = 10 ** 9 + 7\n\n\ndef mul(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:\n    n = len(a)\n    return [\n        [sum(a[i][k] * b[k][j] for k in range(n)) % MOD for j in range(n)]\n        for i in range(n)\n    ]\n\n\ndef solve() -> None:\n    n = int(input())\n    if n == 0:\n        print(0)\n        return\n    if n == 1:\n        print(0)\n        return\n    if n == 2:\n        print(1)\n        return\n    result = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]\n    base = [[1, 1, 1], [1, 0, 0], [0, 1, 0]]\n    power = n - 2\n    while power > 0:\n        if power & 1:\n            result = mul(result, base)\n        base = mul(base, base)\n        power >>= 1\n    t2, t1, t0 = 1, 0, 0\n    answer = (\n        result[0][0] * t2 + result[0][1] * t1 + result[0][2] * t0\n    ) % MOD\n    print(answer)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
