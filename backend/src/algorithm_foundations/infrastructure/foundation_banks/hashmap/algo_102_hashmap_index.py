from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-102-hashmap-index',
    title='値から位置を引く対応表',
    unit_kind='foundation',
    target_skill='値から位置を引く対応表',
    concept_overview='値をキーにして位置や番号を保存しておき、必要になったときに逆引きする考え方です。「探す」を「表から引く」に変える練習をします。',
    problem_bank=[
        problem(
            problem_id='algo-102-hashmap-index-p1',
            title='値から位置を引く対応表 / 値が何番目にあるか答える',
            problem_statement='長さ N の整数列 A はすべて異なる。Q 個の問い合わせ x について、x が A の何番目にあるかを 1-indexed で出力し、含まれなければ -1 を出力せよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に x。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n0 <= Ai, x <= 10^9',
            examples=[
                {
                    'input': '5 3\n10 20 30 40 50\n40\n15\n10',
                    'output': '4\n-1\n1',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    pos = {value: idx for idx, value in enumerate(map(int, input().split()), start=1)}\n    out = []\n    for _ in range(q):\n        x = int(input())\n        out.append(str(pos.get(x, -1)))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-102-hashmap-index-p2',
            title='値から位置を引く対応表 / 最初の出現位置だけを覚える',
            problem_statement='長さ N の整数列 A が与えられる。同じ値が複数回現れてもよい。Q 個の問い合わせ x について、x が最初に現れる位置を 1-indexed で出力し、含まれなければ -1 を出力せよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に x。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n0 <= Ai, x <= 10^9',
            examples=[
                {
                    'input': '7 4\n10 20 10 30 20 40 50\n20\n50\n15\n10',
                    'output': '2\n7\n-1\n1',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    first = {}\n    for idx, value in enumerate(map(int, input().split()), start=1):\n        first.setdefault(value, idx)\n    out = []\n    for _ in range(q):\n        x = int(input())\n        out.append(str(first.get(x, -1)))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-102-hashmap-index-p3',
            title='値から位置を引く対応表 / 直前の出現位置を列として出す',
            problem_statement='長さ N の整数列 A が与えられる。各 i について、Ai と同じ値が直前に現れた位置を 1-indexed で出力し、存在しなければ -1 を出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='N 個の答えを空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai <= 10^9',
            examples=[
                {
                    'input': '7\n10 20 10 30 20 40 10',
                    'output': '-1 -1 1 -1 2 -1 3',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    input()\n    last = {}\n    ans = []\n    for idx, value in enumerate(map(int, input().split()), start=1):\n        ans.append(str(last.get(value, -1)))\n        last[value] = idx\n    print(*ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
