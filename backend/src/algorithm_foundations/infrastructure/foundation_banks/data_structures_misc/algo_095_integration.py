from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-095-integration',
    title='優先度付きキュー（ヒープ） の総合演習',
    unit_kind='integration',
    target_skill='優先度付きキュー（ヒープ） の総合演習',
    concept_overview='キューは、先に入れたものを先に取り出す考え方です。到着順の処理や、近い順に広げる探索で基本になります。 この unit では、既習の 優先度付きキュー（ヒープ） の基本 と 優先度付きキュー（ヒープ） を素直に実装する を順に使いながら、1 問を分けて解く流れまで確認します。',
    problem_bank=[
        problem(
            problem_id='algo-095-integration-p1',
            title='優先度付きキュー（ヒープ） の総合演習 / 1 ケースをそのまま解く',
            problem_statement='Q 個の操作が与えられる。 `1 x` は整数 x を追加し、`2` は現在入っている値のうち最小値を出力して削除せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に Q。\n続く Q 行に操作。',
            output_format='type=2 のたびに取り出した最小値を 1 行ずつ出力する。',
            constraints='1 <= Q <= 2 * 10^5\ntype=2 の時点で優先度付きキューは空でない\n使う知識は前提 unit までに限定すること。',
            examples=[
                {
                    'input': '6\n1 5\n1 2\n2\n1 4\n2\n2',
                    'output': '2\n4\n5',
                },
            ],
            canonical_reference_solution="import heapq\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    q = int(input())\n    heap = []\n    out = []\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        if parts[0] == 1:\n            heapq.heappush(heap, parts[1])\n        else:\n            out.append(str(heapq.heappop(heap)))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-095-integration-p2',
            title='優先度付きキュー（ヒープ） の総合演習 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、Q 個の操作が与えられる。 `1 x` は整数 x を追加し、`2` は現在入っている値のうち最小値を出力して削除せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に Q。\n続く Q 行に操作。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= Q <= 2 * 10^5\ntype=2 の時点で優先度付きキューは空でない\n使う知識は前提 unit までに限定すること。\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n6\n1 5\n1 2\n2\n1 4\n2\n2\n6\n1 5\n1 2\n2\n1 4\n2\n2',
                    'output': '2\n4\n5\n2\n4\n5',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nimport heapq\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    q = int(input())\n    heap = []\n    out = []\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        if parts[0] == 1:\n            heapq.heappush(heap, parts[1])\n        else:\n            out.append(str(heapq.heappop(heap)))\n    sys.stdout.write('\\n'.join(out))\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-095-integration-p3',
            title='優先度付きキュー（ヒープ） の総合演習 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、Q 個の操作が与えられる。 `1 x` は整数 x を追加し、`2` は現在入っている値のうち最小値を出力して削除せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に Q。\n続く Q 行に操作。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= Q <= 2 * 10^5\ntype=2 の時点で優先度付きキューは空でない\n使う知識は前提 unit までに限定すること。\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n6\n1 5\n1 2\n2\n1 4\n2\n2\n6\n1 5\n1 2\n2\n1 4\n2\n2\n6\n1 5\n1 2\n2\n1 4\n2\n2',
                    'output': '2\n4\n5\n2\n4\n5\n2\n4\n5',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nimport heapq\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    q = int(input())\n    heap = []\n    out = []\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        if parts[0] == 1:\n            heapq.heappush(heap, parts[1])\n        else:\n            out.append(str(heapq.heappop(heap)))\n    sys.stdout.write('\\n'.join(out))\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
