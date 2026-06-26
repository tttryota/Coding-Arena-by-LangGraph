from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-060-integration',
    title='イベントソートによる走査 の総合演習',
    unit_kind='integration',
    target_skill='イベントソートによる走査 の総合演習',
    concept_overview='ソートは、要素を決まった順番に並べ替える知識です。比較や交換をどう進めると目的の順序になるかを手順として理解します。 この unit では、既習の イベントソートによる走査 の基本 と イベントソートによる走査 を素直に実装する を順に使いながら、1 問を分けて解く流れまで確認します。',
    problem_bank=[
        problem(
            problem_id='algo-060-integration-p1',
            title='イベントソートによる走査 の総合演習 / 1 ケースをそのまま解く',
            problem_statement='N 個のイベントの開始時刻 L_i と終了時刻 R_i が与えられる。各イベントは区間 [L_i, R_i) の間だけ存在する。ある時刻に同時に存在するイベント数の最大値を求めよ。',
            input_format='1 行目に N。\n続く N 行に L_i R_i。',
            output_format='同時に存在するイベント数の最大値を出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[
                {
                    'input': '4\n1 4\n2 6\n4 7\n5 8',
                    'output': '2',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    events = []\n    for _ in range(n):\n        l, r = map(int, input().split())\n        events.append((l, 1))\n        events.append((r, -1))\n    events.sort(key=lambda item: (item[0], item[1]))\n    current = 0\n    best = 0\n    for _, delta in events:\n        current += delta\n        best = max(best, current)\n    print(best)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-060-integration-p2',
            title='イベントソートによる走査 の総合演習 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、N 個のイベントの開始時刻 L_i と終了時刻 R_i が与えられる。各イベントは区間 [L_i, R_i) の間だけ存在する。ある時刻に同時に存在するイベント数の最大値を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n続く N 行に L_i R_i。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n4\n1 4\n2 6\n4 7\n5 8\n4\n1 4\n2 6\n4 7\n5 8',
                    'output': '2\n2',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n = int(input())\n    events = []\n    for _ in range(n):\n        l, r = map(int, input().split())\n        events.append((l, 1))\n        events.append((r, -1))\n    events.sort(key=lambda item: (item[0], item[1]))\n    current = 0\n    best = 0\n    for _, delta in events:\n        current += delta\n        best = max(best, current)\n    print(best)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-060-integration-p3',
            title='イベントソートによる走査 の総合演習 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、N 個のイベントの開始時刻 L_i と終了時刻 R_i が与えられる。各イベントは区間 [L_i, R_i) の間だけ存在する。ある時刻に同時に存在するイベント数の最大値を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n続く N 行に L_i R_i。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n4\n1 4\n2 6\n4 7\n5 8\n4\n1 4\n2 6\n4 7\n5 8\n4\n1 4\n2 6\n4 7\n5 8',
                    'output': '2\n2\n2',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n = int(input())\n    events = []\n    for _ in range(n):\n        l, r = map(int, input().split())\n        events.append((l, 1))\n        events.append((r, -1))\n    events.sort(key=lambda item: (item[0], item[1]))\n    current = 0\n    best = 0\n    for _, delta in events:\n        current += delta\n        best = max(best, current)\n    print(best)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
