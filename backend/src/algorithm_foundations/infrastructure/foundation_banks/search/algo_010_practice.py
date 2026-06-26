from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-010-practice',
    title='ランダム探索（モンテカルロ法） を素直に実装する',
    unit_kind='foundation',
    target_skill='ランダム探索（モンテカルロ法） を素直に実装する',
    concept_overview='ランダム探索（モンテカルロ法）は、入力の構造や候補を整理し、決まった手順で答えを作る知識です。まずは典型の使い方を自分の手で追える状態を目指します。',
    problem_bank=[
        problem(
            problem_id='algo-010-practice-p1',
            title='ランダム探索（モンテカルロ法） を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='整数 N と目標値 T が与えられる。乱数 seed=0 を用いて 5000 回 0..N をランダムに試し、 T に最も近い値を出力せよ。差が同じなら小さい方を採用する。',
            input_format='1 行目に N T。',
            output_format='選ばれた値を出力する。',
            constraints='1 <= N <= 10^9',
            examples=[
                {
                    'input': '10 7',
                    'output': '7',
                },
            ],
            canonical_reference_solution="import random\n\ndef solve() -> None:\n    n, target = map(int, input().split())\n    random.seed(0)\n    best = 0\n    best_diff = abs(target)\n    for _ in range(5000):\n        cand = random.randint(0, n)\n        diff = abs(cand - target)\n        if diff < best_diff or (diff == best_diff and cand < best):\n            best = cand\n            best_diff = diff\n    print(best)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-010-practice-p2',
            title='ランダム探索（モンテカルロ法） を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、整数 N と目標値 T が与えられる。乱数 seed=0 を用いて 5000 回 0..N をランダムに試し、 T に最も近い値を出力せよ。差が同じなら小さい方を採用する。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N T。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 10^9\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n10 7\n10 7',
                    'output': '7\n7',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nimport random\n\ndef solve_one() -> None:\n    n, target = map(int, input().split())\n    random.seed(0)\n    best = 0\n    best_diff = abs(target)\n    for _ in range(5000):\n        cand = random.randint(0, n)\n        diff = abs(cand - target)\n        if diff < best_diff or (diff == best_diff and cand < best):\n            best = cand\n            best_diff = diff\n    print(best)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-010-practice-p3',
            title='ランダム探索（モンテカルロ法） を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、整数 N と目標値 T が与えられる。乱数 seed=0 を用いて 5000 回 0..N をランダムに試し、 T に最も近い値を出力せよ。差が同じなら小さい方を採用する。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N T。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 10^9\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n10 7\n10 7\n10 7',
                    'output': '7\n7\n7',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nimport random\n\ndef solve_one() -> None:\n    n, target = map(int, input().split())\n    random.seed(0)\n    best = 0\n    best_diff = abs(target)\n    for _ in range(5000):\n        cand = random.randint(0, n)\n        diff = abs(cand - target)\n        if diff < best_diff or (diff == best_diff and cand < best):\n            best = cand\n            best_diff = diff\n    print(best)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
