from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-002-integration',
    title='二分探索 の総合演習',
    unit_kind='integration',
    target_skill='二分探索 の総合演習',
    concept_overview='二分探索で境目の位置が分かると、その前後だけ比べれば「最も近い値」も求められます。境界を見つけたあとに候補を絞る流れまで含めて確認します。',
    problem_bank=[
        problem(
            problem_id='algo-002-integration-p1',
            title='二分探索 の総合演習 / x に最も近い配列要素との差を求める',
            problem_statement='昇順に並んだ長さ N の整数列 A と Q 個の値 x が与えられる。各 x について、`|A_i - x|` の最小値を求めよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に x。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\nA は昇順',
            examples=[{'input': '5 3\n1 3 5 8 13\n4\n13\n20', 'output': '1\n0\n7'}],
            canonical_reference_solution="from bisect import bisect_left\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    out = []\n    for _ in range(q):\n        x = int(input())\n        idx = bisect_left(a, x)\n        candidates = []\n        if idx < n:\n            candidates.append(abs(a[idx] - x))\n        if idx > 0:\n            candidates.append(abs(a[idx - 1] - x))\n        out.append(str(min(candidates)))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
