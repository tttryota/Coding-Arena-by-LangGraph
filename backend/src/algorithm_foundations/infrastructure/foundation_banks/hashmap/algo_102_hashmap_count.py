from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-102-hashmap-count',
    title='出現回数カウント',
    unit_kind='foundation',
    target_skill='出現回数カウント',
    concept_overview='値ごとの出現回数を連想配列にため、あとで必要な回数をすぐ取り出せるようにする考え方です。数え上げを map の更新に置き換える形を身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-102-hashmap-count-p1',
            title='出現回数カウント / 指定された値の回数を答える',
            problem_statement='長さ N の整数列 A と Q 個の問い合わせ x が与えられる。各問い合わせについて x の出現回数を出力せよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に x。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n0 <= Ai, x <= 10^9',
            examples=[
                {
                    'input': '6 3\n1 4 2 4 7 4\n4\n3\n1',
                    'output': '3\n0\n1',
                },
            ],
            canonical_reference_solution="from collections import Counter\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    counter = Counter(map(int, input().split()))\n    out = []\n    for _ in range(q):\n        x = int(input())\n        out.append(str(counter[x]))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-102-hashmap-count-p2',
            title='出現回数カウント / 初登場順に値と回数を並べる',
            problem_statement='長さ N の整数列 A が与えられる。各値について、最初に現れた順に `値 回数` を 1 行ずつ出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='各行に `value count` を出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai <= 10^9',
            examples=[
                {
                    'input': '7\n4 2 4 7 2 2 9',
                    'output': '4 2\n2 3\n7 1\n9 1',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    input()\n    order = []\n    counter = {}\n    for value in map(int, input().split()):\n        if value not in counter:\n            order.append(value)\n            counter[value] = 0\n        counter[value] += 1\n    for value in order:\n        print(value, counter[value])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-102-hashmap-count-p3',
            title='出現回数カウント / 最頻値を 1 つ選ぶ',
            problem_statement='長さ N の整数列 A が与えられる。最も多く現れる値を出力せよ。複数あるときは最小の値を選べ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='条件を満たす値を出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai <= 10^9',
            examples=[
                {
                    'input': '8\n4 2 4 7 2 2 9 4',
                    'output': '2',
                },
            ],
            canonical_reference_solution="from collections import Counter\n\ndef solve() -> None:\n    input()\n    counter = Counter(map(int, input().split()))\n    best_count = max(counter.values())\n    ans = min(value for value, count in counter.items() if count == best_count)\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
