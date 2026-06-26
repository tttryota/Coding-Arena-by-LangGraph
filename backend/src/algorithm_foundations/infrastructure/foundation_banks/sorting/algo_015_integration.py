from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-015-integration',
    title='クイックソート の総合演習',
    unit_kind='integration',
    target_skill='クイックソート の総合演習',
    concept_overview='クイックソートの partition は、整列を最後までやり切らなくても「欲しい順位が左・中央・右のどこにあるか」を判定するのに使えます。ここでは必要な側だけ再帰して K 番目の値を求めます。',
    problem_bank=[
        problem(
            problem_id='algo-015-integration-p1',
            title='クイックソート の総合演習 / K 番目に小さい値を求める',
            problem_statement='長さ N の整数列 A と整数 K が与えられる。クイックソートの partition と同じ考え方を使って、A を昇順に並べたときの K 番目に小さい値を求めよ。',
            input_format='1 行目に N K。\n2 行目に A1..AN。',
            output_format='K 番目に小さい値を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= K <= N',
            examples=[{'input': '8 5\n4 1 5 2 3 5 1 4', 'output': '4'}],
            canonical_reference_solution="def quick_select(arr: list[int], k: int) -> int:\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    mid = [x for x in arr if x == pivot]\n    if k <= len(left):\n        return quick_select(left, k)\n    if k <= len(left) + len(mid):\n        return pivot\n    right = [x for x in arr if x > pivot]\n    return quick_select(right, k - len(left) - len(mid))\n\n\ndef solve() -> None:\n    n, k = map(int, input().split())\n    a = list(map(int, input().split()))\n    print(quick_select(a, k))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
