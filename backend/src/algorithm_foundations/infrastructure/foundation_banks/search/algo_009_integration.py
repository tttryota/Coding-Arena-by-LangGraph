from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-009-integration',
    title='尺取り法 の総合演習',
    unit_kind='integration',
    target_skill='尺取り法 の総合演習',
    concept_overview='尺取り法は、左右の端を動かしながら連続区間を保ち、条件を満たす最短・最長・個数を求める考え方です。区間を伸ばすときと縮めるときの役割分担を押さえます。 この unit では、既習の 尺取り法 の基本 と 尺取り法 を素直に実装する を順に使いながら、1 問を分けて解く流れまで確認します。',
    problem_bank=[
        problem(
            problem_id='algo-009-integration-p1',
            title='尺取り法 の総合演習 / 1 ケースをそのまま解く',
            problem_statement='長さ N の正整数列 A と整数 S が与えられる。 総和が S 以上となる連続部分列のうち、長さの最小値を求めよ。存在しなければ 0 を出力せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に N S。\n2 行目に A1..AN。',
            output_format='最小長を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= Ai, S <= 10^9\n使う知識は前提 unit までに限定すること。',
            examples=[
                {
                    'input': '6 11\n2 3 1 2 4 3',
                    'output': '3',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    n, s = map(int, input().split())\n    a = list(map(int, input().split()))\n    ans = n + 1\n    total = 0\n    left = 0\n    for right, value in enumerate(a):\n        total += value\n        while total >= s:\n            ans = min(ans, right - left + 1)\n            total -= a[left]\n            left += 1\n    print(0 if ans == n + 1 else ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-009-integration-p2',
            title='尺取り法 の総合演習 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、長さ N の正整数列 A と整数 S が与えられる。 総和が S 以上となる連続部分列のうち、長さの最小値を求めよ。存在しなければ 0 を出力せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N S。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= Ai, S <= 10^9\n使う知識は前提 unit までに限定すること。\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n6 11\n2 3 1 2 4 3\n6 11\n2 3 1 2 4 3',
                    'output': '3\n3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n, s = map(int, input().split())\n    a = list(map(int, input().split()))\n    ans = n + 1\n    total = 0\n    left = 0\n    for right, value in enumerate(a):\n        total += value\n        while total >= s:\n            ans = min(ans, right - left + 1)\n            total -= a[left]\n            left += 1\n    print(0 if ans == n + 1 else ans)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-009-integration-p3',
            title='尺取り法 の総合演習 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、長さ N の正整数列 A と整数 S が与えられる。 総和が S 以上となる連続部分列のうち、長さの最小値を求めよ。存在しなければ 0 を出力せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N S。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= Ai, S <= 10^9\n使う知識は前提 unit までに限定すること。\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n6 11\n2 3 1 2 4 3\n6 11\n2 3 1 2 4 3\n6 11\n2 3 1 2 4 3',
                    'output': '3\n3\n3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n, s = map(int, input().split())\n    a = list(map(int, input().split()))\n    ans = n + 1\n    total = 0\n    left = 0\n    for right, value in enumerate(a):\n        total += value\n        while total >= s:\n            ans = min(ans, right - left + 1)\n            total -= a[left]\n            left += 1\n    print(0 if ans == n + 1 else ans)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
