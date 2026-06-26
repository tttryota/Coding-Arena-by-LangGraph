from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-048-practice',
    title='ゲーム理論DP（Grundy数） を素直に実装する',
    unit_kind='foundation',
    target_skill='ゲーム理論DP（Grundy数） を素直に実装する',
    concept_overview='動的計画法は、小さい状態の答えを先に求め、その結果を使って大きい状態の答えを作る考え方です。状態・遷移・初期値を整理する基本を身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-048-practice-p1',
            title='ゲーム理論DP（Grundy数） を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='石が N 個あり、1 回で 1 個または 3 個取れるゲームを考える。 先手後手が最善を尽くすとして、先手が勝つなら First、負けるなら Second を出力せよ。',
            input_format='1 行目に N。',
            output_format='First / Second を出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[
                {
                    'input': '2',
                    'output': 'Second',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    win = [False] * (max(4, n + 1))\n    for stones in range(1, n + 1):\n        for move in (1, 3):\n            if stones >= move and not win[stones - move]:\n                win[stones] = True\n                break\n    print('First' if win[n] else 'Second')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-048-practice-p2',
            title='ゲーム理論DP（Grundy数） を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、石が N 個あり、1 回で 1 個または 3 個取れるゲームを考える。 先手後手が最善を尽くすとして、先手が勝つなら First、負けるなら Second を出力せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n2\n2',
                    'output': 'Second\nSecond',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n = int(input())\n    win = [False] * (max(4, n + 1))\n    for stones in range(1, n + 1):\n        for move in (1, 3):\n            if stones >= move and not win[stones - move]:\n                win[stones] = True\n                break\n    print('First' if win[n] else 'Second')\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-048-practice-p3',
            title='ゲーム理論DP（Grundy数） を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、石が N 個あり、1 回で 1 個または 3 個取れるゲームを考える。 先手後手が最善を尽くすとして、先手が勝つなら First、負けるなら Second を出力せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n2\n2\n2',
                    'output': 'Second\nSecond\nSecond',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n = int(input())\n    win = [False] * (max(4, n + 1))\n    for stones in range(1, n + 1):\n        for move in (1, 3):\n            if stones >= move and not win[stones - move]:\n                win[stones] = True\n                break\n    print('First' if win[n] else 'Second')\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
