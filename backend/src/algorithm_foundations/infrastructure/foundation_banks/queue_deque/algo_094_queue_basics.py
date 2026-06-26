from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-094-queue-basics',
    title='キューの基本操作',
    unit_kind='foundation',
    target_skill='キューの基本操作',
    concept_overview='キューは、先に入れたものから先に取り出す入れ物です。まずは末尾に追加し、先頭から取り出す流れを素直に扱えるようにします。',
    problem_bank=[
        problem(
            problem_id='algo-094-queue-basics-p1',
            title='キューの基本操作 / 追加して先頭を見る',
            problem_statement='Q 個の操作が与えられる。`1 x` は末尾に x を追加し、`2` は先頭を取り除き、`3` は先頭の値を出力せよ。',
            input_format='1 行目に Q。\n続く Q 行に操作。',
            output_format='type=3 のたびに先頭の値を 1 行ずつ出力する。',
            constraints='1 <= Q <= 2 * 10^5',
            examples=[
                {
                    'input': '6\n1 4\n1 7\n3\n2\n1 9\n3',
                    'output': '4\n7',
                },
            ],
            canonical_reference_solution="from collections import deque\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    q = int(input())\n    queue = deque()\n    out = []\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        if parts[0] == 1:\n            queue.append(parts[1])\n        elif parts[0] == 2:\n            queue.popleft()\n        else:\n            out.append(str(queue[0]))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-094-queue-basics-p2',
            title='キューの基本操作 / size 問い合わせを含む操作列を処理する',
            problem_statement='Q 個の操作が与えられる。`1 x` は末尾に x を追加し、`2` は先頭を取り除き、`3` は先頭の値を出力し、`4` は現在の要素数を出力せよ。',
            input_format='1 行目に Q。\n続く Q 行に操作。',
            output_format='type=3,4 のたびに答えを 1 行ずつ出力する。',
            constraints='1 <= Q <= 2 * 10^5',
            examples=[
                {
                    'input': '8\n1 4\n1 7\n4\n2\n1 9\n3\n4\n3',
                    'output': '2\n7\n2\n9',
                },
            ],
            canonical_reference_solution="from collections import deque\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    q = int(input())\n    queue = deque()\n    out = []\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        t = parts[0]\n        if t == 1:\n            queue.append(parts[1])\n        elif t == 2:\n            queue.popleft()\n        elif t == 3:\n            out.append(str(queue[0]))\n        else:\n            out.append(str(len(queue)))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-094-queue-basics-p3',
            title='キューの基本操作 / 取り出した順番をそのまま並べる',
            problem_statement='長さ N の整数列 A が与えられる。A を左から順にキューへ入れ、すべて入れ終わったら空になるまで先頭から取り出す。取り出した順番を空白区切りで出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='取り出した順番を空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[
                {
                    'input': '5\n3 1 4 1 5',
                    'output': '3 1 4 1 5',
                },
            ],
            canonical_reference_solution="from collections import deque\n\ndef solve() -> None:\n    input()\n    queue = deque(map(int, input().split()))\n    out = []\n    while queue:\n        out.append(str(queue.popleft()))\n    print(*out)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
