from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-020-practice',
    title='転倒数の計算 を素直に実装する',
    unit_kind='foundation',
    target_skill='転倒数の計算 を素直に実装する',
    concept_overview='転倒数の考え方は、列全体の合計だけでなく「各位置が何回転倒に参加するか」にも広げられます。ここでは各要素の右側にある自分より小さい要素数を求めます。',
    problem_bank=[
        problem(
            problem_id='algo-020-practice-p1',
            title='転倒数の計算 を素直に実装する / 各要素について右側にある自分より小さい要素数を求める',
            problem_statement='長さ N の整数列 A が与えられる。各位置 i について、j > i かつ A_j < A_i を満たす j の個数を求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='N 個の答えを空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5\n-10^18 <= A_i <= 10^18',
            examples=[{'input': '4\n3 1 4 2', 'output': '2 0 1 0'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    sys.setrecursionlimit(10 ** 7)\n    input = sys.stdin.readline\n    n = int(input())\n    a = list(map(int, input().split()))\n    counts = [0] * n\n    indexed = [(value, idx) for idx, value in enumerate(a)]\n\n    def merge_sort(items: list[tuple[int, int]]) -> list[tuple[int, int]]:\n        if len(items) <= 1:\n            return items\n        mid = len(items) // 2\n        left = merge_sort(items[:mid])\n        right = merge_sort(items[mid:])\n        merged: list[tuple[int, int]] = []\n        i = j = 0\n        moved_from_right = 0\n        while i < len(left) and j < len(right):\n            if left[i][0] <= right[j][0]:\n                counts[left[i][1]] += moved_from_right\n                merged.append(left[i])\n                i += 1\n            else:\n                merged.append(right[j])\n                moved_from_right += 1\n                j += 1\n        while i < len(left):\n            counts[left[i][1]] += moved_from_right\n            merged.append(left[i])\n            i += 1\n        merged.extend(right[j:])\n        return merged\n\n    merge_sort(indexed)\n    print(*counts)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
