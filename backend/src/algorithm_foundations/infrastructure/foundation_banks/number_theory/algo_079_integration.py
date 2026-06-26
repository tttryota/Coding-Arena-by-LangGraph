from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-079-integration',
    title='最大公約数・最小公倍数（GCD/LCM） の総合演習',
    unit_kind='integration',
    target_skill='最大公約数・最小公倍数（GCD/LCM） の総合演習',
    concept_overview='最大公約数と最小公倍数は `gcd(a, b) * lcm(a, b) = a * b` の関係でも結びつきます。ここでは列全体の最小公倍数を順に更新して求めます。',
    problem_bank=[
        problem(
            problem_id='algo-079-integration-p1',
            title='最大公約数・最小公倍数（GCD/LCM） の総合演習 / 全要素の最小公倍数を求める',
            problem_statement='長さ N の正整数列 A が与えられる。全要素の最小公倍数を求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='最小公倍数を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= A_i <= 10^9\n答えは 10^18 以下',
            examples=[{'input': '3\n4 6 10', 'output': '60'}],
            canonical_reference_solution="def gcd(a: int, b: int) -> int:\n    while b:\n        a, b = b, a % b\n    return a\n\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    _ = int(input())\n    a = list(map(int, input().split()))\n    ans = 1\n    for value in a:\n        ans = ans // gcd(ans, value) * value\n    print(ans)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
