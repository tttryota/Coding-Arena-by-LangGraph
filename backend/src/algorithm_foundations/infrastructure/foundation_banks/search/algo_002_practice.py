from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-002-practice',
    title='二分探索 を素直に実装する',
    unit_kind='foundation',
    target_skill='二分探索 を素直に実装する',
    concept_overview='二分探索では、左端を探すだけでなく右端も探せると、区間に入る要素数を高速に数えられます。lower_bound と upper_bound を使い分ける実装を確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-002-practice-p1',
            title='二分探索 を素直に実装する / 区間 [l, r] に入る要素数を求める',
            problem_statement='昇順に並んだ長さ N の整数列 A と Q 個の区間 [l, r] が与えられる。各区間について、A の中にある `l 以上 r 以下` の要素数を求めよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に l r。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\nA は昇順',
            examples=[{'input': '5 3\n1 3 5 8 13\n4 13\n2 2\n0 20', 'output': '3\n0\n5'}],
            canonical_reference_solution="from bisect import bisect_left, bisect_right\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    _, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    out = []\n    for _ in range(q):\n        l, r = map(int, input().split())\n        left = bisect_left(a, l)\n        right = bisect_right(a, r)\n        out.append(str(right - left))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
