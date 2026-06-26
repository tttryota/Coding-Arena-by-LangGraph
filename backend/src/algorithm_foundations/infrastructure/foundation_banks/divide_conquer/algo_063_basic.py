from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-063-basic',
    title='カラツバ法（高速乗算） の基本',
    unit_kind='foundation',
    target_skill='カラツバ法（高速乗算） の基本',
    concept_overview='カラツバ法は、積を 4 回に分ける代わりに 3 回の再帰計算へ減らす分割統治です。まずは多項式の係数列を掛ける形で、分け方と合体のしかたを確認します。',
    problem_bank=[
        problem(
            problem_id='algo-063-basic-p1',
            title='カラツバ法（高速乗算） の基本 / 2 つの多項式を掛け合わせる',
            problem_statement='長さ N の整数列 A, B が与えられる。A_i を x^i の係数、B_i を x^i の係数とみなしたとき、多項式 A(x) と B(x) の積の係数列を出力せよ。',
            input_format='1 行目に N。\n2 行目に A_0..A_{N-1}。\n3 行目に B_0..B_{N-1}。',
            output_format='積の係数 c_0..c_{2N-2} を空白区切りで出力する。',
            constraints='1 <= N <= 256\n-10^4 <= A_i, B_i <= 10^4',
            examples=[{'input': '4\n1 2 0 1\n3 1 4 1', 'output': '3 7 6 12 3 4 1'}],
            canonical_reference_solution="def naive(a: list[int], b: list[int]) -> list[int]:\n    res = [0] * (len(a) + len(b) - 1)\n    for i, x in enumerate(a):\n        for j, y in enumerate(b):\n            res[i + j] += x * y\n    return res\n\n\ndef karatsuba(a: list[int], b: list[int]) -> list[int]:\n    n = max(len(a), len(b))\n    if n <= 32:\n        return naive(a, b)\n    size = 1\n    while size < n:\n        size <<= 1\n    a = a + [0] * (size - len(a))\n    b = b + [0] * (size - len(b))\n    half = size // 2\n    a0, a1 = a[:half], a[half:]\n    b0, b1 = b[:half], b[half:]\n    z0 = karatsuba(a0, b0)\n    z2 = karatsuba(a1, b1)\n    a01 = [a0[i] + a1[i] for i in range(half)]\n    b01 = [b0[i] + b1[i] for i in range(half)]\n    z1 = karatsuba(a01, b01)\n    res = [0] * (size * 2)\n    for i, value in enumerate(z0):\n        res[i] += value\n    for i, value in enumerate(z2):\n        res[i + size] += value\n    for i, value in enumerate(z1):\n        res[i + half] += value\n    for i, value in enumerate(z0):\n        res[i + half] -= value\n    for i, value in enumerate(z2):\n        res[i + half] -= value\n    return res\n\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    a = list(map(int, input().split()))\n    b = list(map(int, input().split()))\n    ans = karatsuba(a, b)[: 2 * n - 1]\n    print(*ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
