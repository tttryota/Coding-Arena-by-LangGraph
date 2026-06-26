from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-093-stack-basics',
    title='スタックの基本操作',
    unit_kind='foundation',
    target_skill='スタックの基本操作',
    concept_overview='スタックは、最後に入れたものから先に取り出す入れ物です。まずは push・pop・top を順番どおりに扱えるようになることを目指します。',
    problem_bank=[
        problem(
            problem_id='algo-093-stack-basics-p1',
            title='スタックの基本操作 / push・pop・top を順に処理する',
            problem_statement='Q 個の操作が与えられる。`1 x` は x を積み、`2` は一番上を取り除き、`3` は一番上の値を出力せよ。',
            input_format='1 行目に Q。\n続く Q 行に操作。',
            output_format='type=3 のたびに一番上の値を 1 行ずつ出力する。',
            constraints='1 <= Q <= 2 * 10^5\ntype=2,3 の時点でスタックは空でない',
            examples=[
                {
                    'input': '7\n1 3\n1 5\n3\n2\n3\n1 9\n3',
                    'output': '5\n3\n9',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    q = int(input())\n    stack = []\n    out = []\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        if parts[0] == 1:\n            stack.append(parts[1])\n        elif parts[0] == 2:\n            stack.pop()\n        else:\n            out.append(str(stack[-1]))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=default_rubric("foundation"),
        ),
        problem(
            problem_id='algo-093-stack-basics-p2',
            title='スタックの基本操作 / pop した値を順に出力する',
            problem_statement='Q 個の操作が与えられる。`1 x` は x を積み、`2` は一番上の値を取り出して出力せよ。',
            input_format='1 行目に Q。\n続く Q 行に操作。',
            output_format='type=2 のたびに取り出した値を 1 行ずつ出力する。',
            constraints='1 <= Q <= 2 * 10^5\ntype=2 の時点でスタックは空でない',
            examples=[
                {
                    'input': '7\n1 4\n1 8\n2\n1 5\n2\n1 2\n2',
                    'output': '8\n5\n2',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    q = int(input())\n    stack = []\n    out = []\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        if parts[0] == 1:\n            stack.append(parts[1])\n        else:\n            out.append(str(stack.pop()))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=default_rubric("foundation"),
        ),
        problem(
            problem_id='algo-093-stack-basics-p3',
            title='スタックの基本操作 / 操作後に残った要素を上から並べる',
            problem_statement='Q 個の操作が与えられる。`1 x` は x を積み、`2` は一番上を取り除く。すべての操作を終えたあと、残っている要素を上から順に空白区切りで出力せよ。空なら `Empty` を出力する。',
            input_format='1 行目に Q。\n続く Q 行に操作。',
            output_format='残っている要素を上から順に出力し、空なら `Empty` を出力する。',
            constraints='1 <= Q <= 2 * 10^5\ntype=2 の時点でスタックは空でない',
            examples=[
                {
                    'input': '7\n1 7\n1 3\n2\n1 5\n1 2\n2\n1 9',
                    'output': '9 5 7',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    q = int(input())\n    stack = []\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        if parts[0] == 1:\n            stack.append(parts[1])\n        else:\n            stack.pop()\n    if not stack:\n        print('Empty')\n        return\n    print(*reversed(stack))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=default_rubric("foundation"),
        ),
        problem(
            problem_id='algo-093-stack-basics-p4',
            title='スタックの基本操作 / 取り出し順をまとめて出力する',
            problem_statement='長さ N の整数列 A が与えられる。左から順に stack に積み、最後に空になるまで pop したときの出力順を空白区切りで出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='pop される順を空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[
                {
                    'input': '5\n3 1 4 1 5',
                    'output': '5 1 4 1 3',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    input()\n    a = list(map(int, input().split()))\n    stack = []\n    for value in a:\n        stack.append(value)\n    out = []\n    while stack:\n        out.append(str(stack.pop()))\n    print(*out)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=default_rubric("foundation"),
        ),
        problem(
            problem_id='algo-093-stack-basics-p5',
            title='スタックの基本操作 / 上の 2 個をまとめて 1 個にする',
            problem_statement='Q 個の操作が与えられる。`1 x` は x を積み、`2` は一番上の 2 個を取り出してその和を 1 個だけ積み直す。すべての操作を終えたあとの一番上の値を出力せよ。',
            input_format='1 行目に Q。\n続く Q 行に操作。',
            output_format='最後に残った一番上の値を出力する。',
            constraints='1 <= Q <= 2 * 10^5\ntype=2 の時点でスタックの要素数は 2 以上\n最後の時点でスタックは空でない',
            examples=[
                {
                    'input': '6\n1 6\n1 9\n2\n1 4\n2\n1 3',
                    'output': '3',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    q = int(input())\n    stack = []\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        if parts[0] == 1:\n            stack.append(parts[1])\n        else:\n            a = stack.pop()\n            b = stack.pop()\n            stack.append(a + b)\n    print(stack[-1])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=default_rubric("foundation"),
        ),
    ],
)
