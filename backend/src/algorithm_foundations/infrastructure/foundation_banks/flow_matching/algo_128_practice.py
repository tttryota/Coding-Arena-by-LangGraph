from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-128-practice',
    title='最小費用流 を素直に実装する',
    unit_kind='foundation',
    target_skill='最小費用流 を素直に実装する',
    concept_overview='最大流・マッチングは、通せる量や組み合わせをグラフの辺として表し、制約つきでどれだけ流せるか・結べるかを考える知識です。問題をネットワークに置き換える基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-128-practice-p1',
            title='最小費用流 を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='左側 N 頂点、右側 M 頂点の二部グラフが与えられる。最大マッチング数を求めよ。',
            input_format='1 行目に N M E。\n続く E 行に u v。',
            output_format='最大マッチング数を出力する。',
            constraints='1 <= N, M <= 200\n1 <= E <= 2 * 10^4',
            examples=[
                {
                    'input': '2 2 3\n1 1\n1 2\n2 2',
                    'output': '2',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m, e = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(e):\n        u, v = map(int, input().split())\n        graph[u - 1].append(v - 1)\n    match_to = [-1] * m\n    def dfs(v: int, seen: list[bool]) -> bool:\n        for nxt in graph[v]:\n            if seen[nxt]:\n                continue\n            seen[nxt] = True\n            if match_to[nxt] == -1 or dfs(match_to[nxt], seen):\n                match_to[nxt] = v\n                return True\n        return False\n    ans = 0\n    for v in range(n):\n        if dfs(v, [False] * m):\n            ans += 1\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-128-practice-p2',
            title='最小費用流 を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、左側 N 頂点、右側 M 頂点の二部グラフが与えられる。最大マッチング数を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N M E。\n続く E 行に u v。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, M <= 200\n1 <= E <= 2 * 10^4\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n2 2 3\n1 1\n1 2\n2 2\n2 2 3\n1 1\n1 2\n2 2',
                    'output': '2\n2',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m, e = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(e):\n        u, v = map(int, input().split())\n        graph[u - 1].append(v - 1)\n    match_to = [-1] * m\n    def dfs(v: int, seen: list[bool]) -> bool:\n        for nxt in graph[v]:\n            if seen[nxt]:\n                continue\n            seen[nxt] = True\n            if match_to[nxt] == -1 or dfs(match_to[nxt], seen):\n                match_to[nxt] = v\n                return True\n        return False\n    ans = 0\n    for v in range(n):\n        if dfs(v, [False] * m):\n            ans += 1\n    print(ans)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-128-practice-p3',
            title='最小費用流 を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、左側 N 頂点、右側 M 頂点の二部グラフが与えられる。最大マッチング数を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N M E。\n続く E 行に u v。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, M <= 200\n1 <= E <= 2 * 10^4\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n2 2 3\n1 1\n1 2\n2 2\n2 2 3\n1 1\n1 2\n2 2\n2 2 3\n1 1\n1 2\n2 2',
                    'output': '2\n2\n2',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m, e = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(e):\n        u, v = map(int, input().split())\n        graph[u - 1].append(v - 1)\n    match_to = [-1] * m\n    def dfs(v: int, seen: list[bool]) -> bool:\n        for nxt in graph[v]:\n            if seen[nxt]:\n                continue\n            seen[nxt] = True\n            if match_to[nxt] == -1 or dfs(match_to[nxt], seen):\n                match_to[nxt] = v\n                return True\n        return False\n    ans = 0\n    for v in range(n):\n        if dfs(v, [False] * m):\n            ans += 1\n    print(ans)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
