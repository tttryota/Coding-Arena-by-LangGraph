from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-063-practice',
    title='カラツバ法（高速乗算） を素直に実装する',
    unit_kind='foundation',
    target_skill='カラツバ法（高速乗算） を素直に実装する',
    concept_overview='長い整数の乗算では、桁列を半分ずつに分けて 3 回の再帰計算で合成します。桁列への変換、再帰計算、繰り上がり処理をまとめて実装します。',
    problem_bank=[
        problem(
            problem_id='algo-063-practice-p1',
            title='カラツバ法（高速乗算） を素直に実装する / 長い 10 進整数の積を求める',
            problem_statement='10 進表記の非負整数 A, B が文字列で与えられる。A x B を出力せよ。',
            input_format='1 行目に A。\n2 行目に B。',
            output_format='A x B を 10 進表記で出力する。',
            constraints='1 <= |A|, |B| <= 5000\nA, B は 0 以上の整数文字列',
            examples=[{'input': '12345678\n9012345', 'output': '111263509394910'}],
            canonical_reference_solution="BASE = 1000\nWIDTH = 3\n\n\ndef naive(a: list[int], b: list[int]) -> list[int]:\n    res = [0] * (len(a) + len(b) - 1)\n    for i, x in enumerate(a):\n        for j, y in enumerate(b):\n            res[i + j] += x * y\n    return res\n\n\ndef karatsuba(a: list[int], b: list[int]) -> list[int]:\n    n = max(len(a), len(b))\n    if n <= 32:\n        return naive(a, b)\n    size = 1\n    while size < n:\n        size <<= 1\n    a = a + [0] * (size - len(a))\n    b = b + [0] * (size - len(b))\n    half = size // 2\n    a0, a1 = a[:half], a[half:]\n    b0, b1 = b[:half], b[half:]\n    z0 = karatsuba(a0, b0)\n    z2 = karatsuba(a1, b1)\n    a01 = [a0[i] + a1[i] for i in range(half)]\n    b01 = [b0[i] + b1[i] for i in range(half)]\n    z1 = karatsuba(a01, b01)\n    res = [0] * (size * 2)\n    for i, value in enumerate(z0):\n        res[i] += value\n    for i, value in enumerate(z2):\n        res[i + size] += value\n    for i, value in enumerate(z1):\n        res[i + half] += value\n    for i, value in enumerate(z0):\n        res[i + half] -= value\n    for i, value in enumerate(z2):\n        res[i + half] -= value\n    return res\n\n\ndef to_digits(s: str) -> list[int]:\n    digits = []\n    for right in range(len(s), 0, -WIDTH):\n        left = max(0, right - WIDTH)\n        digits.append(int(s[left:right]))\n    return digits\n\n\ndef solve() -> None:\n    a = input().strip()\n    b = input().strip()\n    if a == '0' or b == '0':\n        print(0)\n        return\n    da = to_digits(a)\n    db = to_digits(b)\n    prod = karatsuba(da, db)\n    carry = 0\n    for i in range(len(prod)):\n        total = prod[i] + carry\n        prod[i] = total % BASE\n        carry = total // BASE\n    while carry:\n        prod.append(carry % BASE)\n        carry //= BASE\n    while len(prod) > 1 and prod[-1] == 0:\n        prod.pop()\n    answer = str(prod[-1])\n    for value in reversed(prod[:-1]):\n        answer += f'{value:0{WIDTH}d}'\n    print(answer)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
