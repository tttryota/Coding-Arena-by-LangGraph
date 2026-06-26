from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-079-practice',
    title='最大公約数・最小公倍数（GCD/LCM） を素直に実装する',
    unit_kind='foundation',
    target_skill='最大公約数・最小公倍数（GCD/LCM） を素直に実装する',
    concept_overview='2 数の最大公約数を求められれば、列全体の最大公約数も左から順にたたみ込んで求められます。ここでは複数要素への拡張を確認します。',
    problem_bank=[
        problem(
            problem_id='algo-079-practice-p1',
            title='最大公約数・最小公倍数（GCD/LCM） を素直に実装する / 全要素の最大公約数を求める',
            problem_statement='長さ N の整数列 A が与えられる。全要素の最大公約数を求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='最大公約数を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= Ai <= 10^9',
            examples=[{'input': '3\n12 18 30', 'output': '6'}],
            canonical_reference_solution="def gcd(a: int, b: int) -> int:\n    while b:\n        a, b = b, a % b\n    return a\n\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    _ = int(input())\n    a = list(map(int, input().split()))\n    ans = 0\n    for value in a:\n        ans = gcd(ans, value)\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
