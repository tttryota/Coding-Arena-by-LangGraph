from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-032-basic',
    title='二部グラフ判定 の基本',
    unit_kind='foundation',
    target_skill='二部グラフ判定 の基本',
    concept_overview='二部グラフ判定は、頂点を 2 色に分け、隣り合う頂点が同じ色にならないかを見る考え方です。制約を色分けとして扱う基本形を押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-032-basic-p1',
            title='二部グラフ判定 の基本 / 1 ケースをそのまま解く',
            problem_statement='N 頂点 M 辺の無向グラフが与えられる。二部グラフなら Yes、そうでなければ No を出力せよ。',
            input_format='1 行目に N M。\n続く M 行に辺 u v。',
            output_format='Yes / No を出力する。',
            constraints='1 <= N, M <= 2 * 10^5',
            examples=[
                {
                    'input': '4 4\n1 2\n2 3\n3 4\n4 1',
                    'output': 'Yes',
                },
            ],
            canonical_reference_solution="from collections import deque\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        graph[v].append(u)\n    color = [-1] * n\n    for start in range(n):\n        if color[start] != -1:\n            continue\n        color[start] = 0\n        dq = deque([start])\n        while dq:\n            node = dq.popleft()\n            for nxt in graph[node]:\n                if color[nxt] == -1:\n                    color[nxt] = color[node] ^ 1\n                    dq.append(nxt)\n                elif color[nxt] == color[node]:\n                    print('No')\n                    return\n    print('Yes')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-032-basic-p2',
            title='二部グラフ判定 の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、N 頂点 M 辺の無向グラフが与えられる。二部グラフなら Yes、そうでなければ No を出力せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N M。\n続く M 行に辺 u v。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n4 4\n1 2\n2 3\n3 4\n4 1\n4 4\n1 2\n2 3\n3 4\n4 1',
                    'output': 'Yes\nYes',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom collections import deque\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        graph[v].append(u)\n    color = [-1] * n\n    for start in range(n):\n        if color[start] != -1:\n            continue\n        color[start] = 0\n        dq = deque([start])\n        while dq:\n            node = dq.popleft()\n            for nxt in graph[node]:\n                if color[nxt] == -1:\n                    color[nxt] = color[node] ^ 1\n                    dq.append(nxt)\n                elif color[nxt] == color[node]:\n                    print('No')\n                    return\n    print('Yes')\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-032-basic-p3',
            title='二部グラフ判定 の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、N 頂点 M 辺の無向グラフが与えられる。二部グラフなら Yes、そうでなければ No を出力せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N M。\n続く M 行に辺 u v。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n4 4\n1 2\n2 3\n3 4\n4 1\n4 4\n1 2\n2 3\n3 4\n4 1\n4 4\n1 2\n2 3\n3 4\n4 1',
                    'output': 'Yes\nYes\nYes',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom collections import deque\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        graph[v].append(u)\n    color = [-1] * n\n    for start in range(n):\n        if color[start] != -1:\n            continue\n        color[start] = 0\n        dq = deque([start])\n        while dq:\n            node = dq.popleft()\n            for nxt in graph[node]:\n                if color[nxt] == -1:\n                    color[nxt] = color[node] ^ 1\n                    dq.append(nxt)\n                elif color[nxt] == color[node]:\n                    print('No')\n                    return\n    print('Yes')\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
