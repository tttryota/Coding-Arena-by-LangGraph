from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-002-practice',
    title='二分探索 を素直に実装する',
    unit_kind='foundation',
    target_skill='二分探索 を素直に実装する',
    concept_overview='二分探索は、条件を満たす境目や値を、探索範囲を半分ずつ絞りながら見つける解き方です。単調性を見つけて mid で判定する流れを身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-002-practice-p1',
            title='二分探索 を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='昇順に並んだ長さ N の整数列 A と Q 個の値 x が与えられる。 各 x について、A の中で x 以上となる最初の位置を 1-indexed で求め、 存在しない場合は -1 を出力せよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に x。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\nA は昇順',
            examples=[
                {
                    'input': '5 3\n1 3 5 8 13\n4\n13\n20',
                    'output': '3\n5\n-1',
                },
            ],
            canonical_reference_solution="from bisect import bisect_left\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    out = []\n    for _ in range(q):\n        x = int(input())\n        idx = bisect_left(a, x)\n        out.append(str(idx + 1) if idx < n else '-1')\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-002-practice-p2',
            title='二分探索 を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、昇順に並んだ長さ N の整数列 A と Q 個の値 x が与えられる。 各 x について、A の中で x 以上となる最初の位置を 1-indexed で求め、 存在しない場合は -1 を出力せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に x。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\nA は昇順\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n5 3\n1 3 5 8 13\n4\n13\n20\n5 3\n1 3 5 8 13\n4\n13\n20',
                    'output': '3\n5\n-1\n3\n5\n-1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom bisect import bisect_left\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    out = []\n    for _ in range(q):\n        x = int(input())\n        idx = bisect_left(a, x)\n        out.append(str(idx + 1) if idx < n else '-1')\n    sys.stdout.write('\\n'.join(out))\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-002-practice-p3',
            title='二分探索 を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、昇順に並んだ長さ N の整数列 A と Q 個の値 x が与えられる。 各 x について、A の中で x 以上となる最初の位置を 1-indexed で求め、 存在しない場合は -1 を出力せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に x。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\nA は昇順\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n5 3\n1 3 5 8 13\n4\n13\n20\n5 3\n1 3 5 8 13\n4\n13\n20\n5 3\n1 3 5 8 13\n4\n13\n20',
                    'output': '3\n5\n-1\n3\n5\n-1\n3\n5\n-1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom bisect import bisect_left\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    out = []\n    for _ in range(q):\n        x = int(input())\n        idx = bisect_left(a, x)\n        out.append(str(idx + 1) if idx < n else '-1')\n    sys.stdout.write('\\n'.join(out))\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-002-practice-p4',
            title='二分探索 を素直に実装する / T ケースをまとめて解く',
            problem_statement='1 行目にケース数 T が与えられる。続く T ケースについて、それぞれ 昇順に並んだ長さ N の整数列 A と Q 個の値 x が与えられる。 各 x について、A の中で x 以上となる最初の位置を 1-indexed で求め、 存在しない場合は -1 を出力せよ。',
            input_format='1 行目に T。\n続く T ケースについて:\n1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に x。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\nA は昇順\n1 <= T\n全ケースの合計サイズでも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n5 3\n1 3 5 8 13\n4\n13\n20\n5 3\n1 3 5 8 13\n4\n13\n20\n5 3\n1 3 5 8 13\n4\n13\n20',
                    'output': '3\n5\n-1\n3\n5\n-1\n3\n5\n-1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom bisect import bisect_left\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    out = []\n    for _ in range(q):\n        x = int(input())\n        idx = bisect_left(a, x)\n        out.append(str(idx + 1) if idx < n else '-1')\n    sys.stdout.write('\\n'.join(out))\n\ndef solve() -> None:\n    t = int(input())\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-002-practice-p5',
            title='二分探索 を素直に実装する / 4 ケースを連続して解く',
            problem_statement='4 ケース分の入力が続けて与えられる。それぞれについて、昇順に並んだ長さ N の整数列 A と Q 個の値 x が与えられる。 各 x について、A の中で x 以上となる最初の位置を 1-indexed で求め、 存在しない場合は -1 を出力せよ。',
            input_format='1 行目に 4。\n続く 4 ケースについて:\n1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に x。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\nA は昇順\n4 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '4\n5 3\n1 3 5 8 13\n4\n13\n20\n5 3\n1 3 5 8 13\n4\n13\n20\n5 3\n1 3 5 8 13\n4\n13\n20\n5 3\n1 3 5 8 13\n4\n13\n20',
                    'output': '3\n5\n-1\n3\n5\n-1\n3\n5\n-1\n3\n5\n-1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom bisect import bisect_left\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    out = []\n    for _ in range(q):\n        x = int(input())\n        idx = bisect_left(a, x)\n        out.append(str(idx + 1) if idx < n else '-1')\n    sys.stdout.write('\\n'.join(out))\n\ndef solve() -> None:\n    t = 4\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-002-practice-p6',
            title='二分探索 を素直に実装する / 5 ケースを連続して解く',
            problem_statement='5 ケース分の入力が続けて与えられる。それぞれについて、昇順に並んだ長さ N の整数列 A と Q 個の値 x が与えられる。 各 x について、A の中で x 以上となる最初の位置を 1-indexed で求め、 存在しない場合は -1 を出力せよ。',
            input_format='1 行目に 5。\n続く 5 ケースについて:\n1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に x。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\nA は昇順\n5 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '5\n5 3\n1 3 5 8 13\n4\n13\n20\n5 3\n1 3 5 8 13\n4\n13\n20\n5 3\n1 3 5 8 13\n4\n13\n20\n5 3\n1 3 5 8 13\n4\n13\n20\n5 3\n1 3 5 8 13\n4\n13\n20',
                    'output': '3\n5\n-1\n3\n5\n-1\n3\n5\n-1\n3\n5\n-1\n3\n5\n-1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom bisect import bisect_left\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    out = []\n    for _ in range(q):\n        x = int(input())\n        idx = bisect_left(a, x)\n        out.append(str(idx + 1) if idx < n else '-1')\n    sys.stdout.write('\\n'.join(out))\n\ndef solve() -> None:\n    t = 5\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
