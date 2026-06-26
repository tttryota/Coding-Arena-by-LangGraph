from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-081-integration',
    title='エラトステネスの篩 の総合演習',
    unit_kind='integration',
    target_skill='エラトステネスの篩 の総合演習',
    concept_overview='篩で作った素数表は、そのまま累積すると「ある区間に素数が何個あるか」にも答えられます。ここでは素数判定表に前計算を 1 段足して区間クエリへ広げます。',
    problem_bank=[
        problem(
            problem_id='algo-081-integration-p1',
            title='エラトステネスの篩 の総合演習 / 区間 [L, R] に含まれる素数の個数を答える',
            problem_statement='整数 N と Q 個の区間 [L_i, R_i] が与えられる。1 以上 N 以下の整数について篩で素数表を前計算し、各区間に含まれる素数の個数を求めよ。',
            input_format='1 行目に N Q。\n続く Q 行に L_i R_i。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='2 <= N <= 10^7\n1 <= Q <= 2 * 10^5\n1 <= L_i <= R_i <= N',
            examples=[{'input': '20 3\n1 10\n11 20\n8 14', 'output': '4\n4\n2'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    is_prime = bytearray(b'\\x01') * (n + 1)\n    is_prime[0] = 0\n    if n >= 1:\n        is_prime[1] = 0\n    p = 2\n    while p * p <= n:\n        if is_prime[p]:\n            for multiple in range(p * p, n + 1, p):\n                is_prime[multiple] = 0\n        p += 1\n    prefix = [0] * (n + 1)\n    for i in range(1, n + 1):\n        prefix[i] = prefix[i - 1] + is_prime[i]\n    out = []\n    for _ in range(q):\n        left, right = map(int, input().split())\n        out.append(str(prefix[right] - prefix[left - 1]))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
