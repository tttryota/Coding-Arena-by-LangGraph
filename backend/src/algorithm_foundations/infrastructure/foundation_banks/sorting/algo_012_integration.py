from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-012-integration',
    title='選択ソート の総合演習',
    unit_kind='integration',
    target_skill='選択ソート の総合演習',
    concept_overview='ソートは、要素を決まった順番に並べ替える知識です。比較や交換をどう進めると目的の順序になるかを手順として理解します。 この unit では、既習の 選択ソート の基本 と 選択ソート を素直に実装する を順に使いながら、1 問を分けて解く流れまで確認します。',
    problem_bank=[
        problem(
            problem_id='algo-012-integration-p1',
            title='選択ソート の総合演習 / 1 ケースをそのまま解く',
            problem_statement='長さ N の整数列 A が与えられる。選択ソートで昇順に並べ替えて出力せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='昇順の列を空白区切りで出力する。',
            constraints='1 <= N <= 2000\n使う知識は前提 unit までに限定すること。',
            examples=[
                {
                    'input': '5\n4 1 5 2 3',
                    'output': '1 2 3 4 5',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    for i in range(n):\n        best = i\n        for j in range(i + 1, n):\n            if a[j] < a[best]:\n                best = j\n        a[i], a[best] = a[best], a[i]\n    print(*a)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-012-integration-p2',
            title='選択ソート の総合演習 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A が与えられる。選択ソートで昇順に並べ替えて出力せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2000\n使う知識は前提 unit までに限定すること。\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n5\n4 1 5 2 3\n5\n4 1 5 2 3',
                    'output': '1 2 3 4 5\n1 2 3 4 5',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    for i in range(n):\n        best = i\n        for j in range(i + 1, n):\n            if a[j] < a[best]:\n                best = j\n        a[i], a[best] = a[best], a[i]\n    print(*a)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-012-integration-p3',
            title='選択ソート の総合演習 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A が与えられる。選択ソートで昇順に並べ替えて出力せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2000\n使う知識は前提 unit までに限定すること。\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n5\n4 1 5 2 3\n5\n4 1 5 2 3\n5\n4 1 5 2 3',
                    'output': '1 2 3 4 5\n1 2 3 4 5\n1 2 3 4 5',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    for i in range(n):\n        best = i\n        for j in range(i + 1, n):\n            if a[j] < a[best]:\n                best = j\n        a[i], a[best] = a[best], a[i]\n    print(*a)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
