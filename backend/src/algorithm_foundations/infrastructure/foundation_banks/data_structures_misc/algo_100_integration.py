from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-100-integration',
    title='いもす法 の総合演習',
    unit_kind='integration',
    target_skill='いもす法 の総合演習',
    concept_overview='いもす法は、区間への加算を差分として記録し、最後に累積して各位置の値を復元する考え方です。更新をまとめて遅延処理する形を押さえます。 この unit では、既習の いもす法 の基本 と いもす法 を素直に実装する を順に使いながら、1 問を分けて解く流れまで確認します。',
    problem_bank=[
        problem(
            problem_id='algo-100-integration-p1',
            title='いもす法 の総合演習 / 1 ケースをそのまま解く',
            problem_statement='長さ N の配列に対して Q 個の加算操作 `[l, r] に x を足す` が与えられる。 すべて適用した後の配列を出力せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に N Q。\n続く Q 行に l r x。',
            output_format='最終的な配列を空白区切りで出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n|x| <= 10^9\n使う知識は前提 unit までに限定すること。',
            examples=[
                {
                    'input': '5 3\n1 3 2\n2 5 1\n4 4 -2',
                    'output': '2 3 3 -1 1',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    diff = [0] * (n + 1)\n    for _ in range(q):\n        l, r, x = map(int, input().split())\n        diff[l - 1] += x\n        if r < n:\n            diff[r] -= x\n    ans = []\n    cur = 0\n    for i in range(n):\n        cur += diff[i]\n        ans.append(cur)\n    print(*ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-100-integration-p2',
            title='いもす法 の総合演習 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、長さ N の配列に対して Q 個の加算操作 `[l, r] に x を足す` が与えられる。 すべて適用した後の配列を出力せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N Q。\n続く Q 行に l r x。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n|x| <= 10^9\n使う知識は前提 unit までに限定すること。\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n5 3\n1 3 2\n2 5 1\n4 4 -2\n5 3\n1 3 2\n2 5 1\n4 4 -2',
                    'output': '2 3 3 -1 1\n2 3 3 -1 1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    diff = [0] * (n + 1)\n    for _ in range(q):\n        l, r, x = map(int, input().split())\n        diff[l - 1] += x\n        if r < n:\n            diff[r] -= x\n    ans = []\n    cur = 0\n    for i in range(n):\n        cur += diff[i]\n        ans.append(cur)\n    print(*ans)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-100-integration-p3',
            title='いもす法 の総合演習 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、長さ N の配列に対して Q 個の加算操作 `[l, r] に x を足す` が与えられる。 すべて適用した後の配列を出力せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N Q。\n続く Q 行に l r x。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n|x| <= 10^9\n使う知識は前提 unit までに限定すること。\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n5 3\n1 3 2\n2 5 1\n4 4 -2\n5 3\n1 3 2\n2 5 1\n4 4 -2\n5 3\n1 3 2\n2 5 1\n4 4 -2',
                    'output': '2 3 3 -1 1\n2 3 3 -1 1\n2 3 3 -1 1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    diff = [0] * (n + 1)\n    for _ in range(q):\n        l, r, x = map(int, input().split())\n        diff[l - 1] += x\n        if r < n:\n            diff[r] -= x\n    ans = []\n    cur = 0\n    for i in range(n):\n        cur += diff[i]\n        ans.append(cur)\n    print(*ans)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
