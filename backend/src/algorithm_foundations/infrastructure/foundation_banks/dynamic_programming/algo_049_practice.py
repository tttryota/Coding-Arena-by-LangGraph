from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-049-practice',
    title='累積和を用いたDP高速化 を素直に実装する',
    unit_kind='foundation',
    target_skill='累積和を用いたDP高速化 を素直に実装する',
    concept_overview='累積和は、左上や左から順に合計をためておき、あとで区間や長方形の和を差で取り出す考え方です。前計算して問い合わせを軽くする基本形を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-049-practice-p1',
            title='累積和を用いたDP高速化 を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='整数 N, K が与えられる。1 歩で 1 以上 K 以下進めるとき、 ちょうど N に到達する方法数を 10^9+7 で割った余りで求めよ。',
            input_format='1 行目に N K。',
            output_format='方法数を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= K <= 2 * 10^5',
            examples=[
                {
                    'input': '4 2',
                    'output': '5',
                },
            ],
            canonical_reference_solution="MOD = 10 ** 9 + 7\n\ndef solve() -> None:\n    n, k = map(int, input().split())\n    dp = [0] * (n + 1)\n    pref = [0] * (n + 2)\n    dp[0] = 1\n    pref[1] = 1\n    for i in range(1, n + 1):\n        left = max(0, i - k)\n        dp[i] = (pref[i] - pref[left]) % MOD\n        pref[i + 1] = (pref[i] + dp[i]) % MOD\n    print(dp[n])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-049-practice-p2',
            title='累積和を用いたDP高速化 を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、整数 N, K が与えられる。1 歩で 1 以上 K 以下進めるとき、 ちょうど N に到達する方法数を 10^9+7 で割った余りで求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N K。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= K <= 2 * 10^5\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n4 2\n4 2',
                    'output': '5\n5',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nMOD = 10 ** 9 + 7\n\ndef solve_one() -> None:\n    n, k = map(int, input().split())\n    dp = [0] * (n + 1)\n    pref = [0] * (n + 2)\n    dp[0] = 1\n    pref[1] = 1\n    for i in range(1, n + 1):\n        left = max(0, i - k)\n        dp[i] = (pref[i] - pref[left]) % MOD\n        pref[i + 1] = (pref[i] + dp[i]) % MOD\n    print(dp[n])\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-049-practice-p3',
            title='累積和を用いたDP高速化 を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、整数 N, K が与えられる。1 歩で 1 以上 K 以下進めるとき、 ちょうど N に到達する方法数を 10^9+7 で割った余りで求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N K。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= K <= 2 * 10^5\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n4 2\n4 2\n4 2',
                    'output': '5\n5\n5',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nMOD = 10 ** 9 + 7\n\ndef solve_one() -> None:\n    n, k = map(int, input().split())\n    dp = [0] * (n + 1)\n    pref = [0] * (n + 2)\n    dp[0] = 1\n    pref[1] = 1\n    for i in range(1, n + 1):\n        left = max(0, i - k)\n        dp[i] = (pref[i] - pref[left]) % MOD\n        pref[i + 1] = (pref[i] + dp[i]) % MOD\n    print(dp[n])\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
