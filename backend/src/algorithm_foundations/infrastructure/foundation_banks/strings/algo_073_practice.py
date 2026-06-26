from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-073-practice',
    title='Suffix Array を素直に実装する',
    unit_kind='foundation',
    target_skill='Suffix Array を素直に実装する',
    concept_overview='Suffix Array や LCP は、文字列の suffix を順序づけて管理し、部分文字列の比較や共通部分を扱いやすくする知識です。並べ替えた構造で文字列を見る基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-073-practice-p1',
            title='Suffix Array を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='文字列 S が与えられる。Suffix Array を構成し、各接尾辞の開始位置を 1-indexed で出力せよ。',
            input_format='1 行目に S。',
            output_format='開始位置を空白区切りで出力する。',
            constraints='1 <= |S| <= 2000',
            examples=[
                {
                    'input': 'banana',
                    'output': '6 4 2 1 5 3',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    s = input().strip()\n    order = sorted(range(len(s)), key=lambda i: s[i:])\n    print(*[i + 1 for i in order])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-073-practice-p2',
            title='Suffix Array を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、文字列 S が与えられる。Suffix Array を構成し、各接尾辞の開始位置を 1-indexed で出力せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に S。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= |S| <= 2000\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\nbanana\nbanana',
                    'output': '6 4 2 1 5 3\n6 4 2 1 5 3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    s = input().strip()\n    order = sorted(range(len(s)), key=lambda i: s[i:])\n    print(*[i + 1 for i in order])\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-073-practice-p3',
            title='Suffix Array を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、文字列 S が与えられる。Suffix Array を構成し、各接尾辞の開始位置を 1-indexed で出力せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に S。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= |S| <= 2000\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\nbanana\nbanana\nbanana',
                    'output': '6 4 2 1 5 3\n6 4 2 1 5 3\n6 4 2 1 5 3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    s = input().strip()\n    order = sorted(range(len(s)), key=lambda i: s[i:])\n    print(*[i + 1 for i in order])\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
