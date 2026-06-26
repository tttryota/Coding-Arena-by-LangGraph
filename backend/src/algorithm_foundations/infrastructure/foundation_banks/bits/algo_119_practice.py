from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-119-practice',
    title='部分集合の列挙（ビット演算） を素直に実装する',
    unit_kind='foundation',
    target_skill='部分集合の列挙（ビット演算） を素直に実装する',
    concept_overview='部分集合の列挙では、mask の各 bit を見て、その要素を選ぶかどうかを決めます。全列挙した各部分集合をただ出力するのではなく、条件を満たすものだけを評価して最良値を更新する状態管理を確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-119-practice-p1',
            title='部分集合の列挙（ビット演算） を素直に実装する / K 以下の最大部分集合和を求めよ',
            problem_statement='長さ N の非負整数列 A と整数 K が与えられる。部分集合の和のうち、K 以下であるものの最大値を求めよ。',
            input_format='1 行目に N K。\n2 行目に A1..AN。',
            output_format='答えを出力する。',
            constraints='1 <= N <= 20\n0 <= Ai <= 10^9\n0 <= K <= 10^18',
            examples=[{'input': '4 8\n2 5 6 9', 'output': '8'}],
            canonical_reference_solution="def solve() -> None:\n    n, k = map(int, input().split())\n    a = list(map(int, input().split()))\n    best = 0\n    for mask in range(1 << n):\n        total = 0\n        for i in range(n):\n            if mask >> i & 1:\n                total += a[i]\n        if total <= k and total > best:\n            best = total\n    print(best)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
