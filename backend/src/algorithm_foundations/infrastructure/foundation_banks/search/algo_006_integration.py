from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-006-integration',
    title='bit全探索 の総合演習',
    unit_kind='integration',
    target_skill='bit全探索 の総合演習',
    concept_overview='bit 全探索は、各要素を選ぶ・選ばないをビットで表し、部分集合を全部試す解き方です。整数のビット表現と集合の対応づけを使えるようにします。 この unit では、既習の bit全探索 の基本 と bit全探索 を素直に実装する を順に使いながら、1 問を分けて解く流れまで確認します。',
    problem_bank=[
        problem(
            problem_id='algo-006-integration-p1',
            title='bit全探索 の総合演習 / 1 ケースをそのまま解く',
            problem_statement='長さ N の整数列 A と目標値 S が与えられる。bit 全探索で部分集合の和が S になるか判定せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に N S。\n2 行目に A1..AN。',
            output_format='Yes / No を出力する。',
            constraints='1 <= N <= 20\n使う知識は前提 unit までに限定すること。',
            examples=[
                {
                    'input': '4 11\n2 5 9 4',
                    'output': 'Yes',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    n, s = map(int, input().split())\n    a = list(map(int, input().split()))\n    for mask in range(1 << n):\n        total = 0\n        for i in range(n):\n            if mask >> i & 1:\n                total += a[i]\n        if total == s:\n            print('Yes')\n            return\n    print('No')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-006-integration-p2',
            title='bit全探索 の総合演習 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A と目標値 S が与えられる。bit 全探索で部分集合の和が S になるか判定せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N S。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 20\n使う知識は前提 unit までに限定すること。\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n4 11\n2 5 9 4\n4 11\n2 5 9 4',
                    'output': 'Yes\nYes',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n, s = map(int, input().split())\n    a = list(map(int, input().split()))\n    for mask in range(1 << n):\n        total = 0\n        for i in range(n):\n            if mask >> i & 1:\n                total += a[i]\n        if total == s:\n            print('Yes')\n            return\n    print('No')\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-006-integration-p3',
            title='bit全探索 の総合演習 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A と目標値 S が与えられる。bit 全探索で部分集合の和が S になるか判定せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N S。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 20\n使う知識は前提 unit までに限定すること。\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n4 11\n2 5 9 4\n4 11\n2 5 9 4\n4 11\n2 5 9 4',
                    'output': 'Yes\nYes\nYes',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n, s = map(int, input().split())\n    a = list(map(int, input().split()))\n    for mask in range(1 << n):\n        total = 0\n        for i in range(n):\n            if mask >> i & 1:\n                total += a[i]\n        if total == s:\n            print('Yes')\n            return\n    print('No')\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
