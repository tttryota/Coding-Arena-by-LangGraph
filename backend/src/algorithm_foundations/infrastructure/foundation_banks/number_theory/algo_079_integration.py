from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-079-integration',
    title='最大公約数・最小公倍数（GCD/LCM） の総合演習',
    unit_kind='integration',
    target_skill='最大公約数・最小公倍数（GCD/LCM） の総合演習',
    concept_overview='最大公約数・最小公倍数は、整数の割り切れ方を使って共通する周期やまとまりを扱う知識です。互除法と関係式を使う基本を学びます。 この unit では、既習の 最大公約数・最小公倍数（GCD/LCM） の基本 と 最大公約数・最小公倍数（GCD/LCM） を素直に実装する を順に使いながら、1 問を分けて解く流れまで確認します。',
    problem_bank=[
        problem(
            problem_id='algo-079-integration-p1',
            title='最大公約数・最小公倍数（GCD/LCM） の総合演習 / 1 ケースをそのまま解く',
            problem_statement='長さ N の整数列 A が与えられる。全要素の最大公約数を求めよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='最大公約数を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= Ai <= 10^9\n使う知識は前提 unit までに限定すること。',
            examples=[
                {
                    'input': '3\n12 18 30',
                    'output': '6',
                },
            ],
            canonical_reference_solution="from math import gcd\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    _ = int(input())\n    a = list(map(int, input().split()))\n    ans = 0\n    for value in a:\n        ans = gcd(ans, value)\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-079-integration-p2',
            title='最大公約数・最小公倍数（GCD/LCM） の総合演習 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A が与えられる。全要素の最大公約数を求めよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= Ai <= 10^9\n使う知識は前提 unit までに限定すること。\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n3\n12 18 30\n3\n12 18 30',
                    'output': '6\n6',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom math import gcd\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    _ = int(input())\n    a = list(map(int, input().split()))\n    ans = 0\n    for value in a:\n        ans = gcd(ans, value)\n    print(ans)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-079-integration-p3',
            title='最大公約数・最小公倍数（GCD/LCM） の総合演習 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A が与えられる。全要素の最大公約数を求めよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= Ai <= 10^9\n使う知識は前提 unit までに限定すること。\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n3\n12 18 30\n3\n12 18 30\n3\n12 18 30',
                    'output': '6\n6\n6',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom math import gcd\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    _ = int(input())\n    a = list(map(int, input().split()))\n    ans = 0\n    for value in a:\n        ans = gcd(ans, value)\n    print(ans)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
