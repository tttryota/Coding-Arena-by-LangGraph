from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-055-practice',
    title='交換による証明（exchange argument） を素直に実装する',
    unit_kind='foundation',
    target_skill='交換による証明（exchange argument） を素直に実装する',
    concept_overview='貪欲法は、その時点で最もよさそうな選択を順に確定していく考え方です。後戻りせずに決めてよい条件を見抜く基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-055-practice-p1',
            title='交換による証明（exchange argument） を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='N 個の仕事があり、i 番目の処理時間は Ti である。1 台の機械で 1 つずつ順番に処理するとき、完了時刻の総和を最小にせよ。',
            input_format='1 行目に N。\n2 行目に T1..TN。',
            output_format='完了時刻の総和の最小値を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= Ti <= 10^9',
            examples=[
                {
                    'input': '3\n5 1 2',
                    'output': '12',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    input()\n    times = sorted(map(int, input().split()))\n    current = 0\n    total = 0\n    for time in times:\n        current += time\n        total += current\n    print(total)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-055-practice-p2',
            title='交換による証明（exchange argument） を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、N 個の仕事があり、i 番目の処理時間は Ti である。1 台の機械で 1 つずつ順番に処理するとき、完了時刻の総和を最小にせよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n2 行目に T1..TN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= Ti <= 10^9\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n3\n5 1 2\n3\n5 1 2',
                    'output': '12\n12',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    input()\n    times = sorted(map(int, input().split()))\n    current = 0\n    total = 0\n    for time in times:\n        current += time\n        total += current\n    print(total)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-055-practice-p3',
            title='交換による証明（exchange argument） を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、N 個の仕事があり、i 番目の処理時間は Ti である。1 台の機械で 1 つずつ順番に処理するとき、完了時刻の総和を最小にせよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n2 行目に T1..TN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= Ti <= 10^9\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n3\n5 1 2\n3\n5 1 2\n3\n5 1 2',
                    'output': '12\n12\n12',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    input()\n    times = sorted(map(int, input().split()))\n    current = 0\n    total = 0\n    for time in times:\n        current += time\n        total += current\n    print(total)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
