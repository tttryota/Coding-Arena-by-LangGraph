from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-077-basic',
    title='部分文字列の列挙 の基本',
    unit_kind='foundation',
    target_skill='部分文字列の列挙 の基本',
    concept_overview='文字列処理は、文字の並びを比較したり、部分文字列を見つけたり、規則性を前計算で利用したりする知識です。並びをそのまま走査して構造をつかむ基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-077-basic-p1',
            title='部分文字列の列挙 の基本 / 1 ケースをそのまま解く',
            problem_statement='文字列 S が与えられる。異なる部分文字列の個数を求めよ。',
            input_format='1 行目に S。',
            output_format='異なる部分文字列の個数を出力する。',
            constraints='1 <= |S| <= 2000',
            examples=[
                {
                    'input': 'aba',
                    'output': '5',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    s = input().strip()\n    seen = set()\n    for left in range(len(s)):\n        for right in range(left + 1, len(s) + 1):\n            seen.add(s[left:right])\n    print(len(seen))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-077-basic-p2',
            title='部分文字列の列挙 の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、文字列 S が与えられる。異なる部分文字列の個数を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に S。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= |S| <= 2000\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\naba\naba',
                    'output': '5\n5',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    s = input().strip()\n    seen = set()\n    for left in range(len(s)):\n        for right in range(left + 1, len(s) + 1):\n            seen.add(s[left:right])\n    print(len(seen))\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-077-basic-p3',
            title='部分文字列の列挙 の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、文字列 S が与えられる。異なる部分文字列の個数を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に S。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= |S| <= 2000\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\naba\naba\naba',
                    'output': '5\n5\n5',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    s = input().strip()\n    seen = set()\n    for left in range(len(s)):\n        for right in range(left + 1, len(s) + 1):\n            seen.add(s[left:right])\n    print(len(seen))\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
