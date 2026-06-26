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
            title='スタックの基本操作 / size 問い合わせを含む操作列を処理する',
            problem_statement='Q 個の操作が与えられる。`1 x` は x を積み、`2` は一番上を取り除き、`3` は一番上の値を出力し、`4` は現在の要素数を出力せよ。',
            input_format='1 行目に Q。\n続く Q 行に操作。',
            output_format='type=3,4 のたびに答えを 1 行ずつ出力する。',
            constraints='1 <= Q <= 2 * 10^5\ntype=2,3 の時点でスタックは空でない',
            examples=[
                {
                    'input': '8\n1 4\n1 8\n4\n3\n2\n4\n1 5\n3',
                    'output': '2\n8\n1\n5',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    q = int(input())\n    stack = []\n    out = []\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        t = parts[0]\n        if t == 1:\n            stack.append(parts[1])\n        elif t == 2:\n            stack.pop()\n        elif t == 3:\n            out.append(str(stack[-1]))\n        else:\n            out.append(str(len(stack)))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=default_rubric("foundation"),
        ),
        problem(
            problem_id='algo-093-stack-basics-p3',
            title='スタックの基本操作 / empty 判定を含む操作列を処理する',
            problem_statement='Q 個の操作が与えられる。`1 x` は x を積み、`2` は一番上を取り除き、`3` は一番上の値を出力し、`4` は空なら Yes、空でなければ No を出力せよ。',
            input_format='1 行目に Q。\n続く Q 行に操作。',
            output_format='type=3,4 のたびに答えを 1 行ずつ出力する。',
            constraints='1 <= Q <= 2 * 10^5\ntype=2,3 の時点でスタックは空でない',
            examples=[
                {
                    'input': '9\n4\n1 7\n4\n3\n2\n4\n1 1\n1 2\n3',
                    'output': 'Yes\nNo\n7\nYes\n2',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    q = int(input())\n    stack = []\n    out = []\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        t = parts[0]\n        if t == 1:\n            stack.append(parts[1])\n        elif t == 2:\n            stack.pop()\n        elif t == 3:\n            out.append(str(stack[-1]))\n        else:\n            out.append('Yes' if not stack else 'No')\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
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
            title='スタックの基本操作 / 連続した top 問い合わせを処理する',
            problem_statement='Q 個の操作が与えられる。`1 x` は x を積み、`2 k` は一番上の値を消さずに k 回連続で出力せよ。',
            input_format='1 行目に Q。\n続く Q 行に操作。',
            output_format='type=2 のたびに指定回数ぶんの値を 1 行ずつ出力する。',
            constraints='1 <= Q <= 2 * 10^5\n1 <= k <= 10\ntype=2 の時点でスタックは空でない',
            examples=[
                {
                    'input': '5\n1 6\n1 9\n2 2\n1 4\n2 3',
                    'output': '9\n9\n4\n4\n4',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    q = int(input())\n    stack = []\n    out = []\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        if parts[0] == 1:\n            stack.append(parts[1])\n        else:\n            out.extend([str(stack[-1])] * parts[1])\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=default_rubric("foundation"),
        ),
        problem(
            problem_id='algo-093-stack-basics-p6',
            title='スタックの基本操作 / 2 本の操作列を順に適用する',
            problem_statement='Q1 個の操作列と Q2 個の操作列が与えられる。どちらも `1 x` は push、`2` は pop、`3` は top の出力を表す。最初の操作列を終えた状態を引き継いで 2 本目を処理し、type=3 の答えを順に出力せよ。',
            input_format='1 行目に Q1 Q2。\n続く Q1 行に 1 本目の操作。\n続く Q2 行に 2 本目の操作。',
            output_format='type=3 のたびに一番上の値を 1 行ずつ出力する。',
            constraints='1 <= Q1, Q2 <= 10^5\n各 type=2,3 の時点でスタックは空でない',
            examples=[
                {
                    'input': '4 4\n1 2\n1 7\n3\n2\n1 9\n3\n2\n3',
                    'output': '7\n9\n2',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    q1, q2 = map(int, input().split())\n    stack = []\n    out = []\n    for _ in range(q1 + q2):\n        parts = list(map(int, input().split()))\n        t = parts[0]\n        if t == 1:\n            stack.append(parts[1])\n        elif t == 2:\n            stack.pop()\n        else:\n            out.append(str(stack[-1]))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=default_rubric("foundation"),
        ),
    ],
)
