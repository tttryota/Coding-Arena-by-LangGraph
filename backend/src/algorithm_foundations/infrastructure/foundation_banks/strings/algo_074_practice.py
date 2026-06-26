from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-074-practice',
    title='Manacher法（最長回文） を素直に実装する',
    unit_kind='foundation',
    target_skill='Manacher法（最長回文） を素直に実装する',
    concept_overview='文字列処理は、文字の並びを比較したり、部分文字列を見つけたり、規則性を前計算で利用したりする知識です。並びをそのまま走査して構造をつかむ基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-074-practice-p1',
            title='Manacher法（最長回文） を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='文字列 S が与えられる。回文部分文字列の最長長さを求めよ。',
            input_format='1 行目に S。',
            output_format='最長長さを出力する。',
            constraints='1 <= |S| <= 2 * 10^5',
            examples=[
                {
                    'input': 'abacaba',
                    'output': '7',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    s = input().strip()\n    t = '^#' + '#'.join(s) + '#$'\n    radius = [0] * len(t)\n    center = right = 0\n    ans = 0\n    for i in range(1, len(t) - 1):\n        mirror = 2 * center - i\n        if i < right:\n            radius[i] = min(right - i, radius[mirror])\n        while t[i + radius[i] + 1] == t[i - radius[i] - 1]:\n            radius[i] += 1\n        if i + radius[i] > right:\n            center = i\n            right = i + radius[i]\n        ans = max(ans, radius[i])\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-074-practice-p2',
            title='Manacher法（最長回文） を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、文字列 S が与えられる。回文部分文字列の最長長さを求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に S。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= |S| <= 2 * 10^5\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\nabacaba\nabacaba',
                    'output': '7\n7',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    s = input().strip()\n    t = '^#' + '#'.join(s) + '#$'\n    radius = [0] * len(t)\n    center = right = 0\n    ans = 0\n    for i in range(1, len(t) - 1):\n        mirror = 2 * center - i\n        if i < right:\n            radius[i] = min(right - i, radius[mirror])\n        while t[i + radius[i] + 1] == t[i - radius[i] - 1]:\n            radius[i] += 1\n        if i + radius[i] > right:\n            center = i\n            right = i + radius[i]\n        ans = max(ans, radius[i])\n    print(ans)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-074-practice-p3',
            title='Manacher法（最長回文） を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、文字列 S が与えられる。回文部分文字列の最長長さを求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に S。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= |S| <= 2 * 10^5\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\nabacaba\nabacaba\nabacaba',
                    'output': '7\n7\n7',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    s = input().strip()\n    t = '^#' + '#'.join(s) + '#$'\n    radius = [0] * len(t)\n    center = right = 0\n    ans = 0\n    for i in range(1, len(t) - 1):\n        mirror = 2 * center - i\n        if i < right:\n            radius[i] = min(right - i, radius[mirror])\n        while t[i + radius[i] + 1] == t[i - radius[i] - 1]:\n            radius[i] += 1\n        if i + radius[i] > right:\n            center = i\n            right = i + radius[i]\n        ans = max(ans, radius[i])\n    print(ans)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
