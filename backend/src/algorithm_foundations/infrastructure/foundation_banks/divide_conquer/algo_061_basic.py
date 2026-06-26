from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-061-basic',
    title='マージソートによる分割統治 の基本',
    unit_kind='foundation',
    target_skill='マージソートによる分割統治 の基本',
    concept_overview='マージソートによる分割統治では、最後に「2 つの昇順列を 1 つに併合する」操作を繰り返して全体を整列します。まずは再帰に入る前に、併合そのものを線形時間で正しく実装する基本を押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-061-basic-p1',
            title='マージソートによる分割統治 の基本 / 2 つの昇順列 A, B をマージして 1 つの昇順列を作れ',
            problem_statement='長さ N の昇順整数列 A と、長さ M の昇順整数列 B が与えられる。A と B を先頭から見比べながらマージし、長さ N+M の昇順列を出力せよ。',
            input_format='1 行目に N M。\n2 行目に A1..AN。\n3 行目に B1..BM。',
            output_format='マージ後の列を空白区切りで出力する。',
            constraints='1 <= N, M <= 2 * 10^5, -10^9 <= Ai, Bi <= 10^9',
            examples=[{'input': '3 4\n1 4 7\n2 3 8 9', 'output': '1 2 3 4 7 8 9'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n\n    n, m = map(int, input().split())\n    a = list(map(int, input().split()))\n    b = list(map(int, input().split()))\n    i = 0\n    j = 0\n    merged = []\n    while i < n and j < m:\n        if a[i] <= b[j]:\n            merged.append(a[i])\n            i += 1\n        else:\n            merged.append(b[j])\n            j += 1\n    merged.extend(a[i:])\n    merged.extend(b[j:])\n    print(*merged)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
