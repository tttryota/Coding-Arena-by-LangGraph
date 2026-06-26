from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-094-deque-basics',
    title='デックの基本操作',
    unit_kind='foundation',
    target_skill='デックの基本操作',
    concept_overview='デックは、前後どちらの端にも追加・削除できる入れ物です。どちらの端を使う操作なのかを整理して扱う練習をします。',
    problem_bank=[
        problem(
            problem_id='algo-094-deque-basics-p1',
            title='デックの基本操作 / 前後から追加して取り出す',
            problem_statement='Q 個の操作が与えられる。`1 x` は先頭に追加、`2 x` は末尾に追加、`3` は先頭を出力して削除、`4` は末尾を出力して削除せよ。',
            input_format='1 行目に Q。\n続く Q 行に操作。',
            output_format='type=3,4 のたびに取り出した値を 1 行ずつ出力する。',
            constraints='1 <= Q <= 2 * 10^5\ntype=3,4 の時点でデックは空でない',
            examples=[
                {
                    'input': '6\n1 3\n2 8\n3\n1 2\n4\n3',
                    'output': '3\n8\n2',
                },
            ],
            canonical_reference_solution="from collections import deque\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    q = int(input())\n    dq = deque()\n    out = []\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        t = parts[0]\n        if t == 1:\n            dq.appendleft(parts[1])\n        elif t == 2:\n            dq.append(parts[1])\n        elif t == 3:\n            out.append(str(dq.popleft()))\n        else:\n            out.append(str(dq.pop()))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-094-deque-basics-p2',
            title='デックの基本操作 / 先頭と末尾を覗き分ける',
            problem_statement='Q 個の操作が与えられる。`1 x` は先頭に追加、`2 x` は末尾に追加、`3` は先頭の値を出力、`4` は末尾の値を出力せよ。type=3,4 では削除しない。',
            input_format='1 行目に Q。\n続く Q 行に操作。',
            output_format='type=3,4 のたびに答えを 1 行ずつ出力する。',
            constraints='1 <= Q <= 2 * 10^5\ntype=3,4 の時点でデックは空でない',
            examples=[
                {
                    'input': '6\n1 3\n2 8\n3\n4\n1 2\n3',
                    'output': '3\n8\n2',
                },
            ],
            canonical_reference_solution="from collections import deque\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    q = int(input())\n    dq = deque()\n    out = []\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        t = parts[0]\n        if t == 1:\n            dq.appendleft(parts[1])\n        elif t == 2:\n            dq.append(parts[1])\n        elif t == 3:\n            out.append(str(dq[0]))\n        else:\n            out.append(str(dq[-1]))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-094-deque-basics-p3',
            title='デックの基本操作 / 前後に追加したあとの並びを前から読む',
            problem_statement='Q 個の操作が与えられる。`1 x` は先頭に追加、`2 x` は末尾に追加する。すべての操作を終えたあと、先頭から順に並びを空白区切りで出力せよ。空なら `Empty` を出力する。',
            input_format='1 行目に Q。\n続く Q 行に操作。',
            output_format='先頭から順の並びを出力し、空なら `Empty` を出力する。',
            constraints='1 <= Q <= 2 * 10^5',
            examples=[
                {
                    'input': '5\n1 3\n2 8\n1 2\n2 5\n1 1',
                    'output': '1 2 3 8 5',
                },
            ],
            canonical_reference_solution="from collections import deque\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    q = int(input())\n    dq = deque()\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        if parts[0] == 1:\n            dq.appendleft(parts[1])\n        else:\n            dq.append(parts[1])\n    if not dq:\n        print('Empty')\n        return\n    print(*dq)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
