from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-102-hashmap-duplicate',
    title='既出状態をハッシュで追跡する',
    unit_kind='foundation',
    target_skill='既出状態をハッシュで追跡する',
    concept_overview='左から順に見ながら「この値は初登場か」「前にも出たならいつだったか」を表で管理する考え方です。単なる存在判定ではなく、流れてくる列に対して seen 状態を更新し続ける感覚を身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-102-hashmap-duplicate-p1',
            title='既出状態をハッシュで追跡する / 各位置が初登場か再登場かを判定する',
            problem_statement='長さ N の整数列 A が与えられる。各 i について、A_i が `A_1..A_{i-1}` に 1 回でも現れていれば Yes、そうでなければ No を出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='N 個の答えを空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai <= 10^9',
            examples=[
                {
                    'input': '7\n8 3 5 3 8 1 5',
                    'output': 'No No No Yes Yes No Yes',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    input()\n    seen = set()\n    ans = []\n    for value in map(int, input().split()):\n        ans.append('Yes' if value in seen else 'No')\n        seen.add(value)\n    print(*ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-102-hashmap-duplicate-p2',
            title='既出状態をハッシュで追跡する / 最初に再登場した値を出力する',
            problem_statement='長さ N の整数列 A が与えられる。左から見て、はじめて「2 回目の出現」になった値を出力せよ。そのような値がなければ -1 を出力する。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='条件を満たす値、なければ -1 を出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai <= 10^9',
            examples=[
                {
                    'input': '7\n8 3 5 3 8 1 5',
                    'output': '3',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    input()\n    seen = set()\n    for value in map(int, input().split()):\n        if value in seen:\n            print(value)\n            return\n        seen.add(value)\n    print(-1)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-102-hashmap-duplicate-p3',
            title='既出状態をハッシュで追跡する / 各位置でその値が何回目の出現かを出力する',
            problem_statement='長さ N の整数列 A が与えられる。各 i について、A_i が列の中で何回目の出現かを出力せよ。たとえば同じ値が 3 回現れるなら、その 3 か所では 1, 2, 3 を出力する。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='N 個の答えを空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai <= 10^9',
            examples=[
                {
                    'input': '7\n8 3 5 3 8 1 5',
                    'output': '1 1 1 2 2 1 2',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    input()\n    count = {}\n    ans = []\n    for value in map(int, input().split()):\n        count[value] = count.get(value, 0) + 1\n        ans.append(str(count[value]))\n    print(*ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-102-hashmap-duplicate-p4',
            title='既出状態をハッシュで追跡する / 接頭辞ごとの異なる値の個数を出す',
            problem_statement='長さ N の整数列 A が与えられる。各 i について、接頭辞 `A_1..A_i` に含まれる異なる値の個数を出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='N 個の答えを空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai <= 10^9',
            examples=[
                {
                    'input': '7\n8 3 5 3 8 1 5',
                    'output': '1 2 3 3 3 4 4',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    input()\n    seen = set()\n    ans = []\n    for value in map(int, input().split()):\n        seen.add(value)\n        ans.append(str(len(seen)))\n    print(*ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-102-hashmap-duplicate-p5',
            title='既出状態をハッシュで追跡する / 前回の出現から何個空いたかを出力する',
            problem_statement='長さ N の整数列 A が与えられる。各 i について、A_i が前にも現れていれば、その直前の出現位置との差 `i - j` を出力せよ。ただし j は A_i と同じ値が最後に現れた位置とする。前に現れていなければ -1 を出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='N 個の答えを空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai <= 10^9',
            examples=[
                {
                    'input': '7\n10 20 10 30 20 40 10',
                    'output': '-1 -1 2 -1 3 -1 4',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    input()\n    last = {}\n    ans = []\n    for idx, value in enumerate(map(int, input().split()), start=1):\n        if value in last:\n            ans.append(str(idx - last[value]))\n        else:\n            ans.append('-1')\n        last[value] = idx\n    print(*ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-102-hashmap-duplicate-p6',
            title='既出状態をハッシュで追跡する / 同じ区間で重複しないように列を分ける',
            problem_statement='長さ N の整数列 A が与えられる。列を左から順にいくつかの連続部分列に分け、各部分列の中では同じ値が 2 回以上現れないようにしたい。必要な部分列の最小個数を求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='必要な部分列の最小個数を出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai <= 10^9',
            examples=[
                {
                    'input': '8\n1 2 3 2 4 4 5 1',
                    'output': '3',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    if n == 0:\n        print(0)\n        return\n    segments = 1\n    seen = set()\n    for value in a:\n        if value in seen:\n            segments += 1\n            seen = {value}\n        else:\n            seen.add(value)\n    print(segments)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
