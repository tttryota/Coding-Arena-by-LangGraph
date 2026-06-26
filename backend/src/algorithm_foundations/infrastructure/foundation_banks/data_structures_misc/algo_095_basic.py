from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-095-basic',
    title='優先度付きキュー（ヒープ） の基本',
    unit_kind='foundation',
    target_skill='優先度付きキュー（ヒープ） の基本',
    concept_overview='優先度付きキュー（ヒープ）は、値を追加しながら「いまある中で最小の値」をすばやく取り出すための知識です。まずは push と pop をそのまま使う最小値管理の基本形を押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-095-basic-p1',
            title='優先度付きキュー（ヒープ） の基本 / 1 x は整数 x を追加し、2 は現在入っている値のうち最小値を出力して削除せよ',
            problem_statement='Q 個の操作が与えられる。`1 x` は整数 x を追加し、`2` は現在入っている値のうち最小値を出力して削除せよ。',
            input_format='1 行目に Q。\n続く Q 行に操作。',
            output_format='type=2 のたびに、取り出した最小値を 1 行ずつ出力する。',
            constraints='1 <= Q <= 2 * 10^5\n-10^9 <= x <= 10^9\ntype=2 の時点で優先度付きキューは空でない',
            examples=[{'input': '6\n1 5\n1 2\n2\n1 4\n2\n2', 'output': '2\n4\n5'}],
            canonical_reference_solution="import heapq\n\n\ndef solve() -> None:\n    import sys\n\n    input = sys.stdin.readline\n    q = int(input())\n    heap = []\n    out = []\n\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        if parts[0] == 1:\n            heapq.heappush(heap, parts[1])\n        else:\n            out.append(str(heapq.heappop(heap)))\n\n    sys.stdout.write('\\n'.join(out))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
