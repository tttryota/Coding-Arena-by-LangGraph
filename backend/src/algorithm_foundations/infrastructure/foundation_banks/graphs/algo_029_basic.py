from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-029-basic',
    title='木の直径 の基本',
    unit_kind='foundation',
    target_skill='木の直径 の基本',
    concept_overview='木の直径は、入力の構造や候補を整理し、決まった手順で答えを作る知識です。まずは典型の使い方を自分の手で追える状態を目指します。',
    problem_bank=[
        problem(
            problem_id='algo-029-basic-p1',
            title='木の直径 の基本 / 1 ケースをそのまま解く',
            problem_statement='重みのない木が与えられる。木の直径の長さを求めよ。',
            input_format='1 行目に N。\n続く N-1 行に辺 u v。',
            output_format='直径の長さを出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[
                {
                    'input': '5\n1 2\n2 3\n2 4\n4 5',
                    'output': '3',
                },
            ],
            canonical_reference_solution="from collections import deque\n\ndef farthest(start: int, graph: list[list[int]]) -> tuple[int, int]:\n    dist = [-1] * len(graph)\n    dist[start] = 0\n    dq = deque([start])\n    while dq:\n        node = dq.popleft()\n        for nxt in graph[node]:\n            if dist[nxt] != -1:\n                continue\n            dist[nxt] = dist[node] + 1\n            dq.append(nxt)\n    best = max(range(len(graph)), key=lambda idx: dist[idx])\n    return best, dist[best]\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    graph = [[] for _ in range(n)]\n    for _ in range(n - 1):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        graph[v].append(u)\n    node, _ = farthest(0, graph)\n    _, diameter = farthest(node, graph)\n    print(diameter)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-029-basic-p2',
            title='木の直径 の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、重みのない木が与えられる。木の直径の長さを求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n続く N-1 行に辺 u v。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n5\n1 2\n2 3\n2 4\n4 5\n5\n1 2\n2 3\n2 4\n4 5',
                    'output': '3\n3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom collections import deque\n\ndef farthest(start: int, graph: list[list[int]]) -> tuple[int, int]:\n    dist = [-1] * len(graph)\n    dist[start] = 0\n    dq = deque([start])\n    while dq:\n        node = dq.popleft()\n        for nxt in graph[node]:\n            if dist[nxt] != -1:\n                continue\n            dist[nxt] = dist[node] + 1\n            dq.append(nxt)\n    best = max(range(len(graph)), key=lambda idx: dist[idx])\n    return best, dist[best]\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    graph = [[] for _ in range(n)]\n    for _ in range(n - 1):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        graph[v].append(u)\n    node, _ = farthest(0, graph)\n    _, diameter = farthest(node, graph)\n    print(diameter)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-029-basic-p3',
            title='木の直径 の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、重みのない木が与えられる。木の直径の長さを求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n続く N-1 行に辺 u v。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n5\n1 2\n2 3\n2 4\n4 5\n5\n1 2\n2 3\n2 4\n4 5\n5\n1 2\n2 3\n2 4\n4 5',
                    'output': '3\n3\n3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom collections import deque\n\ndef farthest(start: int, graph: list[list[int]]) -> tuple[int, int]:\n    dist = [-1] * len(graph)\n    dist[start] = 0\n    dq = deque([start])\n    while dq:\n        node = dq.popleft()\n        for nxt in graph[node]:\n            if dist[nxt] != -1:\n                continue\n            dist[nxt] = dist[node] + 1\n            dq.append(nxt)\n    best = max(range(len(graph)), key=lambda idx: dist[idx])\n    return best, dist[best]\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    graph = [[] for _ in range(n)]\n    for _ in range(n - 1):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        graph[v].append(u)\n    node, _ = farthest(0, graph)\n    _, diameter = farthest(node, graph)\n    print(diameter)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
