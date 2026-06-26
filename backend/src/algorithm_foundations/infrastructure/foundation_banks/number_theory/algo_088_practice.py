from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-088-practice',
    title='中国剰余定理（CRT） を素直に実装する',
    unit_kind='foundation',
    target_skill='中国剰余定理（CRT） を素直に実装する',
    concept_overview='剰余は、値をある法で割ったあまりとして扱い、巨大な数でも性質を保ったまま計算する考え方です。足し算・掛け算・逆元の基本を押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-088-practice-p1',
            title='中国剰余定理（CRT） を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='整数 a, m, b, n が与えられる。`x ≡ a (mod m)` かつ `x ≡ b (mod n)` を満たす最小の非負整数 x を求めよ。 存在しない場合は -1 を出力せよ。',
            input_format='1 行目に a m b n。',
            output_format='解があれば最小の非負整数 x、なければ -1 を出力する。',
            constraints='0 <= a < m <= 10^18\n0 <= b < n <= 10^18',
            examples=[
                {
                    'input': '2 3 3 5',
                    'output': '8',
                },
            ],
            canonical_reference_solution="def extgcd(a: int, b: int) -> tuple[int, int, int]:\n    if b == 0:\n        return a, 1, 0\n    g, x1, y1 = extgcd(b, a % b)\n    return g, y1, x1 - (a // b) * y1\n\ndef solve() -> None:\n    a, m, b, n = map(int, input().split())\n    g, x, _ = extgcd(m, n)\n    diff = b - a\n    if diff % g != 0:\n        print(-1)\n        return\n    mod = n // g\n    t = (diff // g * x) % mod\n    lcm = m // g * n\n    ans = (a + m * t) % lcm\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-088-practice-p2',
            title='中国剰余定理（CRT） を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、整数 a, m, b, n が与えられる。`x ≡ a (mod m)` かつ `x ≡ b (mod n)` を満たす最小の非負整数 x を求めよ。 存在しない場合は -1 を出力せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に a m b n。',
            output_format='各ケースの答えを順に出力する。',
            constraints='0 <= a < m <= 10^18\n0 <= b < n <= 10^18\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n2 3 3 5\n2 3 3 5',
                    'output': '8\n8',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef extgcd(a: int, b: int) -> tuple[int, int, int]:\n    if b == 0:\n        return a, 1, 0\n    g, x1, y1 = extgcd(b, a % b)\n    return g, y1, x1 - (a // b) * y1\n\ndef solve_one() -> None:\n    a, m, b, n = map(int, input().split())\n    g, x, _ = extgcd(m, n)\n    diff = b - a\n    if diff % g != 0:\n        print(-1)\n        return\n    mod = n // g\n    t = (diff // g * x) % mod\n    lcm = m // g * n\n    ans = (a + m * t) % lcm\n    print(ans)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-088-practice-p3',
            title='中国剰余定理（CRT） を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、整数 a, m, b, n が与えられる。`x ≡ a (mod m)` かつ `x ≡ b (mod n)` を満たす最小の非負整数 x を求めよ。 存在しない場合は -1 を出力せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に a m b n。',
            output_format='各ケースの答えを順に出力する。',
            constraints='0 <= a < m <= 10^18\n0 <= b < n <= 10^18\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n2 3 3 5\n2 3 3 5\n2 3 3 5',
                    'output': '8\n8\n8',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef extgcd(a: int, b: int) -> tuple[int, int, int]:\n    if b == 0:\n        return a, 1, 0\n    g, x1, y1 = extgcd(b, a % b)\n    return g, y1, x1 - (a // b) * y1\n\ndef solve_one() -> None:\n    a, m, b, n = map(int, input().split())\n    g, x, _ = extgcd(m, n)\n    diff = b - a\n    if diff % g != 0:\n        print(-1)\n        return\n    mod = n // g\n    t = (diff // g * x) % mod\n    lcm = m // g * n\n    ans = (a + m * t) % lcm\n    print(ans)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
