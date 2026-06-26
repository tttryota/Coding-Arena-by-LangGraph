from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-075-practice',
    title='ランレングス圧縮 を素直に実装する',
    unit_kind='foundation',
    target_skill='ランレングス圧縮 を素直に実装する',
    concept_overview='文字列処理は、文字の並びを比較したり、部分文字列を見つけたり、規則性を前計算で利用したりする知識です。並びをそのまま走査して構造をつかむ基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-075-practice-p1',
            title='ランレングス圧縮 を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='文字列 S をランレングス圧縮し、文字と個数を交互に出力せよ。',
            input_format='1 行目に S。',
            output_format='圧縮結果を 1 行で出力する。',
            constraints='1 <= |S| <= 2 * 10^5',
            examples=[
                {
                    'input': 'aaabbc',
                    'output': 'a3b2c1',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    s = input().strip()\n    out = []\n    i = 0\n    while i < len(s):\n        j = i\n        while j < len(s) and s[j] == s[i]:\n            j += 1\n        out.append(f'{s[i]}{j - i}')\n        i = j\n    print(''.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-075-practice-p2',
            title='ランレングス圧縮 を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、文字列 S をランレングス圧縮し、文字と個数を交互に出力せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に S。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= |S| <= 2 * 10^5\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\naaabbc\naaabbc',
                    'output': 'a3b2c1\na3b2c1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    s = input().strip()\n    out = []\n    i = 0\n    while i < len(s):\n        j = i\n        while j < len(s) and s[j] == s[i]:\n            j += 1\n        out.append(f'{s[i]}{j - i}')\n        i = j\n    print(''.join(out))\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-075-practice-p3',
            title='ランレングス圧縮 を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、文字列 S をランレングス圧縮し、文字と個数を交互に出力せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に S。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= |S| <= 2 * 10^5\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\naaabbc\naaabbc\naaabbc',
                    'output': 'a3b2c1\na3b2c1\na3b2c1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    s = input().strip()\n    out = []\n    i = 0\n    while i < len(s):\n        j = i\n        while j < len(s) and s[j] == s[i]:\n            j += 1\n        out.append(f'{s[i]}{j - i}')\n        i = j\n    print(''.join(out))\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
