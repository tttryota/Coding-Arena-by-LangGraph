from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-084-basic',
    title='モジュラ逆元（mod上の逆数） の基本',
    unit_kind='foundation',
    target_skill='モジュラ逆元（mod上の逆数） の基本',
    concept_overview='剰余は、値をある法で割ったあまりとして扱い、巨大な数でも性質を保ったまま計算する考え方です。足し算・掛け算・逆元の基本を押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-084-basic-p1',
            title='モジュラ逆元（mod上の逆数） の基本 / 1 ケースをそのまま解く',
            problem_statement='整数 a, m が与えられる。a の mod m における逆元が存在すれば最小の非負整数で出力し、存在しなければ -1 を出力せよ。',
            input_format='1 行目に a m。',
            output_format='逆元、存在しなければ -1 を出力する。',
            constraints='1 <= a, m <= 10^18',
            examples=[
                {
                    'input': '3 11',
                    'output': '4',
                },
            ],
            canonical_reference_solution="def extgcd(a: int, b: int) -> tuple[int, int, int]:\n    if b == 0:\n        return a, 1, 0\n    g, x1, y1 = extgcd(b, a % b)\n    return g, y1, x1 - (a // b) * y1\n\ndef solve() -> None:\n    a, m = map(int, input().split())\n    g, x, _ = extgcd(a, m)\n    if g != 1:\n        print(-1)\n        return\n    print(x % m)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-084-basic-p2',
            title='モジュラ逆元（mod上の逆数） の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、整数 a, m が与えられる。a の mod m における逆元が存在すれば最小の非負整数で出力し、存在しなければ -1 を出力せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に a m。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= a, m <= 10^18\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n3 11\n3 11',
                    'output': '4\n4',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef extgcd(a: int, b: int) -> tuple[int, int, int]:\n    if b == 0:\n        return a, 1, 0\n    g, x1, y1 = extgcd(b, a % b)\n    return g, y1, x1 - (a // b) * y1\n\ndef solve_one() -> None:\n    a, m = map(int, input().split())\n    g, x, _ = extgcd(a, m)\n    if g != 1:\n        print(-1)\n        return\n    print(x % m)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-084-basic-p3',
            title='モジュラ逆元（mod上の逆数） の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、整数 a, m が与えられる。a の mod m における逆元が存在すれば最小の非負整数で出力し、存在しなければ -1 を出力せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に a m。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= a, m <= 10^18\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n3 11\n3 11\n3 11',
                    'output': '4\n4\n4',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef extgcd(a: int, b: int) -> tuple[int, int, int]:\n    if b == 0:\n        return a, 1, 0\n    g, x1, y1 = extgcd(b, a % b)\n    return g, y1, x1 - (a // b) * y1\n\ndef solve_one() -> None:\n    a, m = map(int, input().split())\n    g, x, _ = extgcd(a, m)\n    if g != 1:\n        print(-1)\n        return\n    print(x % m)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
