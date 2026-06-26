from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-095-integration',
    title='優先度付きキュー（ヒープ） の総合演習',
    unit_kind='integration',
    target_skill='優先度付きキュー（ヒープ） の総合演習',
    concept_overview='ヒープに入っている全要素へ一括で同じ値を足すと、各要素を更新し直すのは重いです。この unit では、ヒープの最小値管理に「全体オフセット」を組み合わせて、値の見かけと内部表現を分けて扱います。',
    problem_bank=[
        problem(
            problem_id='algo-095-integration-p1',
            title='優先度付きキュー（ヒープ） の総合演習 / 全体加算つきで最小値を取り出す',
            problem_statement='Q 個の操作が与えられる。`1 x` は整数 x を追加し、`2 x` は現在優先度付きキューに入っているすべての値に x を加算する。`3` は現在入っている値のうち最小値を出力して削除せよ。',
            input_format='1 行目に Q。\n続く Q 行に操作。',
            output_format='type=3 のたびに、取り出した最小値を 1 行ずつ出力する。',
            constraints='1 <= Q <= 2 * 10^5\n-10^9 <= x <= 10^9\ntype=3 の時点で優先度付きキューは空でない',
            examples=[{'input': '8\n1 5\n1 2\n2 3\n1 4\n3\n2 -2\n3\n3', 'output': '4\n3\n6'}],
            canonical_reference_solution="import heapq\n\n\ndef solve() -> None:\n    import sys\n\n    input = sys.stdin.readline\n    q = int(input())\n    heap = []\n    offset = 0\n    out = []\n\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        if parts[0] == 1:\n            heapq.heappush(heap, parts[1] - offset)\n        elif parts[0] == 2:\n            offset += parts[1]\n        else:\n            out.append(str(heapq.heappop(heap) + offset))\n\n    sys.stdout.write('\\n'.join(out))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
