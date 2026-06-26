from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-064-practice',
    title='逆元を用いた多項式補間 を素直に実装する',
    unit_kind='foundation',
    target_skill='逆元を用いた多項式補間 を素直に実装する',
    concept_overview='等間隔な点での値から係数列を復元するときは、差分を段階的に作り、逆元で割りながら Newton 形の寄与を足し込みます。補間の実装を最後まで通す練習です。',
    problem_bank=[
        problem(
            problem_id='algo-064-practice-p1',
            title='逆元を用いた多項式補間 を素直に実装する / 値列から係数列を復元する',
            problem_statement='法 998244353 上の次数 N 未満の多項式 P(x) について、P(0), P(1), ..., P(N-1) の値が与えられる。P(x) を c_0 + c_1 x + ... + c_{N-1} x^{N-1} と表したとき、係数 c_0..c_{N-1} を出力せよ。',
            input_format='1 行目に N。\n2 行目に P(0), P(1), ..., P(N-1)。',
            output_format='c_0..c_{N-1} を空白区切りで出力する。',
            constraints='1 <= N <= 300\n0 <= P(i) < 998244353',
            examples=[{'input': '3\n5 10 19', 'output': '5 3 2'}],
            canonical_reference_solution="MOD = 998244353\n\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    values = list(map(int, input().split()))\n    diff = values[:]\n    inv = [0] * (n + 1)\n    for i in range(1, n + 1):\n        inv[i] = pow(i, MOD - 2, MOD)\n    for j in range(1, n):\n        for i in range(n - 1, j - 1, -1):\n            diff[i] = (diff[i] - diff[i - 1]) * inv[j] % MOD\n    coeffs = [0] * n\n    basis = [1]\n    for i in range(n):\n        for j, value in enumerate(basis):\n            coeffs[j] = (coeffs[j] + diff[i] * value) % MOD\n        new_basis = [0] * (len(basis) + 1)\n        for j, value in enumerate(basis):\n            new_basis[j] = (new_basis[j] - value * i) % MOD\n            new_basis[j + 1] = (new_basis[j + 1] + value) % MOD\n        basis = new_basis\n    print(*coeffs)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
