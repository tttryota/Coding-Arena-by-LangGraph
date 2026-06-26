from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-122-basic',
    title='ビット畳み込み（AND/OR畳み込み） の基本',
    unit_kind='foundation',
    target_skill='ビット畳み込み（AND/OR畳み込み） の基本',
    concept_overview='ビット演算は、整数を 2 進数として見て、立っている桁の有無で状態や条件を扱う知識です。集合や状態をコンパクトに表す基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-122-basic-p1',
            title='ビット畳み込み（AND/OR畳み込み） の基本 / 1 ケースをそのまま解く',
            problem_statement='長さ 2^N の配列 A, B が与えられる。 OR 畳み込み C を `C[s] = Σ A[x]B[y] (x OR y = s)` で定義する。 すべての C[s] を求めよ。',
            input_format='1 行目に N。\n2 行目に A。\n3 行目に B。',
            output_format='C を空白区切りで出力する。',
            constraints='1 <= N <= 17\n0 <= Ai, Bi <= 10^9+7',
            examples=[
                {
                    'input': '2\n1 2 3 4\n5 6 7 8',
                    'output': '5 28 43 184',
                },
            ],
            canonical_reference_solution="def zeta(arr: list[int], n: int) -> None:\n    for bit in range(n):\n        for mask in range(1 << n):\n            if not (mask >> bit & 1):\n                arr[mask | (1 << bit)] += arr[mask]\n\ndef mobius(arr: list[int], n: int) -> None:\n    for bit in range(n):\n        for mask in range(1 << n):\n            if not (mask >> bit & 1):\n                arr[mask | (1 << bit)] -= arr[mask]\n\ndef solve() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    b = list(map(int, input().split()))\n    zeta(a, n)\n    zeta(b, n)\n    c = [x * y for x, y in zip(a, b, strict=False)]\n    mobius(c, n)\n    print(*c)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-122-basic-p2',
            title='ビット畳み込み（AND/OR畳み込み） の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、長さ 2^N の配列 A, B が与えられる。 OR 畳み込み C を `C[s] = Σ A[x]B[y] (x OR y = s)` で定義する。 すべての C[s] を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n2 行目に A。\n3 行目に B。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 17\n0 <= Ai, Bi <= 10^9+7\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n2\n1 2 3 4\n5 6 7 8\n2\n1 2 3 4\n5 6 7 8',
                    'output': '5 28 43 184\n5 28 43 184',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef zeta(arr: list[int], n: int) -> None:\n    for bit in range(n):\n        for mask in range(1 << n):\n            if not (mask >> bit & 1):\n                arr[mask | (1 << bit)] += arr[mask]\n\ndef mobius(arr: list[int], n: int) -> None:\n    for bit in range(n):\n        for mask in range(1 << n):\n            if not (mask >> bit & 1):\n                arr[mask | (1 << bit)] -= arr[mask]\n\ndef solve_one() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    b = list(map(int, input().split()))\n    zeta(a, n)\n    zeta(b, n)\n    c = [x * y for x, y in zip(a, b, strict=False)]\n    mobius(c, n)\n    print(*c)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-122-basic-p3',
            title='ビット畳み込み（AND/OR畳み込み） の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、長さ 2^N の配列 A, B が与えられる。 OR 畳み込み C を `C[s] = Σ A[x]B[y] (x OR y = s)` で定義する。 すべての C[s] を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n2 行目に A。\n3 行目に B。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 17\n0 <= Ai, Bi <= 10^9+7\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n2\n1 2 3 4\n5 6 7 8\n2\n1 2 3 4\n5 6 7 8\n2\n1 2 3 4\n5 6 7 8',
                    'output': '5 28 43 184\n5 28 43 184\n5 28 43 184',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef zeta(arr: list[int], n: int) -> None:\n    for bit in range(n):\n        for mask in range(1 << n):\n            if not (mask >> bit & 1):\n                arr[mask | (1 << bit)] += arr[mask]\n\ndef mobius(arr: list[int], n: int) -> None:\n    for bit in range(n):\n        for mask in range(1 << n):\n            if not (mask >> bit & 1):\n                arr[mask | (1 << bit)] -= arr[mask]\n\ndef solve_one() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    b = list(map(int, input().split()))\n    zeta(a, n)\n    zeta(b, n)\n    c = [x * y for x, y in zip(a, b, strict=False)]\n    mobius(c, n)\n    print(*c)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
