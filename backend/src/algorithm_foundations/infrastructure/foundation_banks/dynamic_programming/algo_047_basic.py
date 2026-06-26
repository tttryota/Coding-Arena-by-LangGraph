from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-047-basic',
    title='確率DP・期待値DP の基本',
    unit_kind='foundation',
    target_skill='確率DP・期待値DP の基本',
    concept_overview='確率・期待値は、各結果がどれだけ起こりやすいかを数で扱い、平均的な値を求める知識です。場合の数と重みづけを整理する基本を押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-047-basic-p1',
            title='確率DP・期待値DP の基本 / 1 ケースをそのまま解く',
            problem_statement='コインを投げて表が出る確率 p が与えられる。初めて表が出るまでの期待手数を求めよ。',
            input_format='1 行目に p。',
            output_format='期待値を小数で出力する。',
            constraints='0 < p <= 1',
            examples=[
                {
                    'input': '0.25',
                    'output': '4.0',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    p = float(input())\n    print(1.0 / p)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-047-basic-p2',
            title='確率DP・期待値DP の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、コインを投げて表が出る確率 p が与えられる。初めて表が出るまでの期待手数を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に p。',
            output_format='各ケースの答えを順に出力する。',
            constraints='0 < p <= 1\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n0.25\n0.25',
                    'output': '4.0\n4.0',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    p = float(input())\n    print(1.0 / p)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-047-basic-p3',
            title='確率DP・期待値DP の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、コインを投げて表が出る確率 p が与えられる。初めて表が出るまでの期待手数を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に p。',
            output_format='各ケースの答えを順に出力する。',
            constraints='0 < p <= 1\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n0.25\n0.25\n0.25',
                    'output': '4.0\n4.0\n4.0',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    p = float(input())\n    print(1.0 / p)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
