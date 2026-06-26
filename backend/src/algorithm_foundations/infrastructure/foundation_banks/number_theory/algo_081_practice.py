from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-081-practice',
    title='エラトステネスの篩 を素直に実装する',
    unit_kind='foundation',
    target_skill='エラトステネスの篩 を素直に実装する',
    concept_overview='篩で素数表を作れば、列挙するだけでなく個々の整数が素数かどうかもすぐ判定できます。ここでは前計算した表で複数クエリへ答えます。',
    problem_bank=[
        problem(
            problem_id='algo-081-practice-p1',
            title='エラトステネスの篩 を素直に実装する / 1 以上 N 以下の整数について素数判定クエリに答える',
            problem_statement='整数 N と Q 個の整数 x_i が与えられる。1 以上 N 以下の整数について篩で素数表を前計算し、各 x_i が素数なら Yes、そうでなければ No を出力せよ。',
            input_format='1 行目に N Q。\n続く Q 行に x_i。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='2 <= N <= 10^7\n1 <= Q <= 2 * 10^5\n1 <= x_i <= N',
            examples=[{'input': '20 4\n2\n15\n17\n18', 'output': 'Yes\nNo\nYes\nNo'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    is_prime = bytearray(b'\\x01') * (n + 1)\n    is_prime[0] = 0\n    if n >= 1:\n        is_prime[1] = 0\n    p = 2\n    while p * p <= n:\n        if is_prime[p]:\n            for multiple in range(p * p, n + 1, p):\n                is_prime[multiple] = 0\n        p += 1\n    out = []\n    for _ in range(q):\n        x = int(input())\n        out.append('Yes' if is_prime[x] else 'No')\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
