from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-102-hashmap-exists',
    title='存在判定をハッシュで高速化',
    unit_kind='foundation',
    target_skill='存在判定をハッシュで高速化',
    concept_overview='値を見たかどうかをハッシュ集合に記録し、あとで同じ値があるかをすぐ調べる考え方です。探索を繰り返さず membership 判定で済ませる形を身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-102-hashmap-exists-p1',
            title='存在判定をハッシュで高速化 / 配列に含まれるかを即答する',
            problem_statement='長さ N の整数列 A と Q 個の問い合わせ x が与えられる。各問い合わせについて x が A に含まれるなら Yes、含まれないなら No を出力せよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に x。',
            output_format='各問い合わせごとに Yes / No を 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n0 <= Ai, x <= 10^9',
            examples=[
                {
                    'input': '5 3\n1 4 2 4 7\n4\n3\n7',
                    'output': 'Yes\nNo\nYes',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    values = set(map(int, input().split()))\n    out = []\n    for _ in range(q):\n        x = int(input())\n        out.append('Yes' if x in values else 'No')\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-102-hashmap-exists-p2',
            title='存在判定をハッシュで高速化 / 追加と照会を同じ集合で処理する',
            problem_statement='Q 個の操作が与えられる。`1 x` は x を集合に追加し、`2 x` は x が集合にあれば Yes、なければ No を出力せよ。',
            input_format='1 行目に Q。\n続く Q 行に `t x`。',
            output_format='型 2 の操作ごとに Yes / No を 1 行ずつ出力する。',
            constraints='1 <= Q <= 2 * 10^5\n0 <= x <= 10^9',
            examples=[
                {
                    'input': '7\n1 5\n1 2\n2 5\n2 4\n1 4\n2 4\n2 2',
                    'output': 'Yes\nNo\nYes\nYes',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    q = int(input())\n    values = set()\n    out = []\n    for _ in range(q):\n        t, x = map(int, input().split())\n        if t == 1:\n            values.add(x)\n        else:\n            out.append('Yes' if x in values else 'No')\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-102-hashmap-exists-p3',
            title='存在判定をハッシュで高速化 / 左側の接頭辞に含まれているかを各位置で判定する',
            problem_statement='長さ N の整数列 A, B が与えられる。各 i について、`B_i` が `A_1..A_i` の中に 1 回でも現れていれば Yes、そうでなければ No を出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。\n3 行目に B1..BN。',
            output_format='N 個の答えを空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai, Bi <= 10^9',
            examples=[
                {
                    'input': '5\n3 1 4 1 5\n3 4 1 5 9',
                    'output': 'Yes No Yes No No',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    input()\n    a = list(map(int, input().split()))\n    b = list(map(int, input().split()))\n    seen = set()\n    out = []\n    for value_a, value_b in zip(a, b, strict=False):\n        seen.add(value_a)\n        out.append('Yes' if value_b in seen else 'No')\n    print(*out)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-102-hashmap-exists-p4',
            title='存在判定をハッシュで高速化 / 2 つの配列に共通要素があるか調べる',
            problem_statement='長さ N の整数列 A と長さ M の整数列 B が与えられる。両方に現れる値が 1 つでもあれば Yes、なければ No を出力せよ。',
            input_format='1 行目に N M。\n2 行目に A1..AN。\n3 行目に B1..BM。',
            output_format='Yes / No を出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n0 <= Ai, Bi <= 10^9',
            examples=[
                {
                    'input': '4 5\n1 4 7 9\n3 5 7 8 10',
                    'output': 'Yes',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    input()\n    a = set(map(int, input().split()))\n    for value in map(int, input().split()):\n        if value in a:\n            print('Yes')\n            return\n    print('No')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-102-hashmap-exists-p5',
            title='存在判定をハッシュで高速化 / 2 本目の列から含まれる値だけを抜き出す',
            problem_statement='長さ N の整数列 A と長さ M の整数列 B が与えられる。B を左から見て、A に含まれる値だけを順番そのままに空白区切りで出力せよ。1 つもなければ `None` を出力する。',
            input_format='1 行目に N M。\n2 行目に A1..AN。\n3 行目に B1..BM。',
            output_format='条件を満たす B の要素を空白区切りで出力し、1 つもなければ None を出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n0 <= Ai, Bi <= 10^9',
            examples=[
                {
                    'input': '5 5\n1 4 2 4 7\n4 3 7 4 1',
                    'output': '4 7 4 1',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    input()\n    values = set(map(int, input().split()))\n    ans = [str(value) for value in map(int, input().split()) if value in values]\n    print(' '.join(ans) if ans else 'None')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-102-hashmap-exists-p6',
            title='存在判定をハッシュで高速化 / 追加・削除・照会を同じ集合で処理する',
            problem_statement='Q 個の操作が与えられる。`1 x` は x を集合に追加し、`2 x` は x を集合から削除し、`3 x` は x が集合にあれば Yes、なければ No を出力せよ。存在しない値の削除は何もしない。',
            input_format='1 行目に Q。\n続く Q 行に `t x`。',
            output_format='型 3 の操作ごとに Yes / No を 1 行ずつ出力する。',
            constraints='1 <= Q <= 2 * 10^5\n0 <= x <= 10^9',
            examples=[
                {
                    'input': '9\n1 5\n1 2\n3 5\n2 5\n3 5\n2 9\n1 9\n3 9\n3 2',
                    'output': 'Yes\nNo\nYes\nYes',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    q = int(input())\n    values = set()\n    out = []\n    for _ in range(q):\n        t, x = map(int, input().split())\n        if t == 1:\n            values.add(x)\n        elif t == 2:\n            values.discard(x)\n        else:\n            out.append('Yes' if x in values else 'No')\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
