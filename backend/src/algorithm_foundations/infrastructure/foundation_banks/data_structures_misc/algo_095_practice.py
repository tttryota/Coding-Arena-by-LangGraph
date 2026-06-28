from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-095-practice',
    title='優先度付きキュー（ヒープ） を素直に実装する',
    unit_kind='foundation',
    target_skill='優先度付きキュー（ヒープ） を素直に実装する',
    concept_overview='ヒープでは、最小値を「見る」操作と「取り出して削除する」操作を分けて扱えます。最小値を参照しても状態は変わらない、削除すると次の候補が先頭に来る、という状態管理の違いを確認します。',
    problem_bank=[
        problem(
            problem_id='algo-095-practice-p1',
            title='優先度付きキュー（ヒープ） を素直に実装する / 最小値の参照と削除を分けて扱う',
            problem_statement='Q 個の操作が与えられる。`1 x` は整数 x を追加し、`2` は現在入っている値のうち最小値を出力するが削除はしない。`3` は現在入っている値のうち最小値を削除せよ。',
            input_format='1 行目に Q。\n続く Q 行に操作。',
            output_format='type=2 のたびに、現在の最小値を 1 行ずつ出力する。',
            constraints='1 <= Q <= 2 * 10^5\n-10^9 <= x <= 10^9\ntype=2,3 の時点で優先度付きキューは空でない',
            examples=[{'input': '8\n1 5\n1 2\n2\n3\n2\n1 4\n2\n3', 'output': '2\n5\n4'}],
            canonical_reference_solution="import heapq\n\n\ndef solve() -> None:\n    import sys\n\n    input = sys.stdin.readline\n    q = int(input())\n    heap = []\n    out = []\n\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        if parts[0] == 1:\n            heapq.heappush(heap, parts[1])\n        elif parts[0] == 2:\n            out.append(str(heap[0]))\n        else:\n            heapq.heappop(heap)\n\n    sys.stdout.write('\\n'.join(out))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-095-practice-p2',
            title='優先度付きキュー（ヒープ） を素直に実装する / 上位 K 個だけを保ちながら K 番目に大きい値を求める',
            problem_statement='長さ N の整数列 A と整数 K が与えられる。A を左から 1 つずつ読み込み、その時点までに現れた値のうち大きい方から K 個だけをヒープで保ちながら、最後に列全体で K 番目に大きい値を求めよ。',
            input_format='1 行目に N K。\n2 行目に A1..AN。',
            output_format='K 番目に大きい値を出力する。',
            constraints='1 <= K <= N <= 2 * 10^5\n-10^9 <= A_i <= 10^9',
            examples=[{'input': '7 3\n5 1 9 3 7 8 2', 'output': '7'}],
            canonical_reference_solution="import heapq\n\n\ndef solve() -> None:\n    _, k = map(int, input().split())\n    a = list(map(int, input().split()))\n    heap = []\n    for value in a:\n        if len(heap) < k:\n            heapq.heappush(heap, value)\n        elif value > heap[0]:\n            heapq.heapreplace(heap, value)\n    print(heap[0])\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
