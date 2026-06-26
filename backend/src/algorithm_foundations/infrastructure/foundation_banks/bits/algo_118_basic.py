from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-118-basic',
    title='ビットで集合を表現 の基本',
    unit_kind='foundation',
    target_skill='ビットで集合を表現 の基本',
    concept_overview='ビット演算は、整数を 2 進数として見て、立っている桁の有無で状態や条件を扱う知識です。集合や状態をコンパクトに表す基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-118-basic-p1',
            title='ビットで集合を表現 の基本 / 1 ケースをそのまま解く',
            problem_statement='集合 A, B が与えられる。bit で表現し、和集合と共通部分の要素数を求めよ。',
            input_format='1 行目に NA NB。\n2 行目に A の要素。\n3 行目に B の要素。',
            output_format='1 行に `union_size intersection_size` を出力する。',
            constraints='0 <= 要素 < 60',
            examples=[
                {
                    'input': '3 3\n1 3 5\n3 4 5',
                    'output': '4 2',
                },
            ],
            canonical_reference_solution="def build_mask(values: list[int]) -> int:\n    mask = 0\n    for value in values:\n        mask |= 1 << value\n    return mask\n\ndef solve() -> None:\n    na, nb = map(int, input().split())\n    a = list(map(int, input().split())) if na else []\n    b = list(map(int, input().split())) if nb else []\n    ma = build_mask(a)\n    mb = build_mask(b)\n    print((ma | mb).bit_count(), (ma & mb).bit_count())\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-118-basic-p2',
            title='ビットで集合を表現 の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、集合 A, B が与えられる。bit で表現し、和集合と共通部分の要素数を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に NA NB。\n2 行目に A の要素。\n3 行目に B の要素。',
            output_format='各ケースの答えを順に出力する。',
            constraints='0 <= 要素 < 60\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n3 3\n1 3 5\n3 4 5\n3 3\n1 3 5\n3 4 5',
                    'output': '4 2\n4 2',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef build_mask(values: list[int]) -> int:\n    mask = 0\n    for value in values:\n        mask |= 1 << value\n    return mask\n\ndef solve_one() -> None:\n    na, nb = map(int, input().split())\n    a = list(map(int, input().split())) if na else []\n    b = list(map(int, input().split())) if nb else []\n    ma = build_mask(a)\n    mb = build_mask(b)\n    print((ma | mb).bit_count(), (ma & mb).bit_count())\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-118-basic-p3',
            title='ビットで集合を表現 の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、集合 A, B が与えられる。bit で表現し、和集合と共通部分の要素数を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に NA NB。\n2 行目に A の要素。\n3 行目に B の要素。',
            output_format='各ケースの答えを順に出力する。',
            constraints='0 <= 要素 < 60\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n3 3\n1 3 5\n3 4 5\n3 3\n1 3 5\n3 4 5\n3 3\n1 3 5\n3 4 5',
                    'output': '4 2\n4 2\n4 2',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef build_mask(values: list[int]) -> int:\n    mask = 0\n    for value in values:\n        mask |= 1 << value\n    return mask\n\ndef solve_one() -> None:\n    na, nb = map(int, input().split())\n    a = list(map(int, input().split())) if na else []\n    b = list(map(int, input().split())) if nb else []\n    ma = build_mask(a)\n    mb = build_mask(b)\n    print((ma | mb).bit_count(), (ma & mb).bit_count())\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
