"""Flow and matching family templates."""

from __future__ import annotations

from .common import ProblemTemplate, array_template


def build_problem_template(
    *,
    theme_id: str,
    key: str,
    category: str,
) -> ProblemTemplate | None:
    del key
    if theme_id == "algo-123":
        return array_template(
            statement="容量付き有向グラフが与えられる。頂点 1 から頂点 N への最大フローを Ford-Fulkerson 法で求めよ。",
            input_format="1 行目に N M。\n続く M 行に u v c。",
            output_format="最大フロー値を出力する。",
            constraints="2 <= N <= 100\n1 <= M <= 1000\n1 <= c <= 10^9",
            examples=[{"input": "4 5\n1 2 2\n1 3 1\n2 3 1\n2 4 1\n3 4 2", "output": "3"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    import sys\n"
                "    sys.setrecursionlimit(10 ** 7)\n"
                "    input = sys.stdin.readline\n"
                "    n, m = map(int, input().split())\n"
                "    graph = [[] for _ in range(n)]\n\n"
                "    def add_edge(u: int, v: int, cap: int) -> None:\n"
                "        graph[u].append([v, cap, len(graph[v])])\n"
                "        graph[v].append([u, 0, len(graph[u]) - 1])\n\n"
                "    for _ in range(m):\n"
                "        u, v, c = map(int, input().split())\n"
                "        add_edge(u - 1, v - 1, c)\n\n"
                "    def dfs(node: int, goal: int, flow: int, seen: list[bool]) -> int:\n"
                "        if node == goal:\n"
                "            return flow\n"
                "        seen[node] = True\n"
                "        for edge in graph[node]:\n"
                "            nxt, cap, rev = edge\n"
                "            if cap == 0 or seen[nxt]:\n"
                "                continue\n"
                "            pushed = dfs(nxt, goal, min(flow, cap), seen)\n"
                "            if pushed:\n"
                "                edge[1] -= pushed\n"
                "                graph[nxt][rev][1] += pushed\n"
                "                return pushed\n"
                "        return 0\n\n"
                "    ans = 0\n"
                "    while True:\n"
                "        pushed = dfs(0, n - 1, 10 ** 18, [False] * n)\n"
                "        if pushed == 0:\n"
                "            break\n"
                "        ans += pushed\n"
                "    print(ans)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-124":
        return array_template(
            statement="容量付き有向グラフが与えられる。頂点 1 から頂点 N への最大フローを Dinic 法で求めよ。",
            input_format="1 行目に N M。\n続く M 行に u v c。",
            output_format="最大フロー値を出力する。",
            constraints="2 <= N <= 2 * 10^5\n1 <= M <= 2 * 10^5\n1 <= c <= 10^9",
            examples=[{"input": "4 5\n1 2 2\n1 3 1\n2 3 1\n2 4 1\n3 4 2", "output": "3"}],
            reference_solution=(
                "from collections import deque\n\n"
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n, m = map(int, input().split())\n"
                "    graph = [[] for _ in range(n)]\n\n"
                "    def add_edge(u: int, v: int, cap: int) -> None:\n"
                "        graph[u].append([v, cap, len(graph[v])])\n"
                "        graph[v].append([u, 0, len(graph[u]) - 1])\n\n"
                "    for _ in range(m):\n"
                "        u, v, c = map(int, input().split())\n"
                "        add_edge(u - 1, v - 1, c)\n\n"
                "    level = [0] * n\n"
                "    it = [0] * n\n\n"
                "    def bfs() -> bool:\n"
                "        level[:] = [-1] * n\n"
                "        dq = deque([0])\n"
                "        level[0] = 0\n"
                "        while dq:\n"
                "            node = dq.popleft()\n"
                "            for nxt, cap, _ in graph[node]:\n"
                "                if cap > 0 and level[nxt] == -1:\n"
                "                    level[nxt] = level[node] + 1\n"
                "                    dq.append(nxt)\n"
                "        return level[n - 1] != -1\n\n"
                "    def dfs(node: int, flow: int) -> int:\n"
                "        if node == n - 1:\n"
                "            return flow\n"
                "        while it[node] < len(graph[node]):\n"
                "            edge = graph[node][it[node]]\n"
                "            nxt, cap, rev = edge\n"
                "            if cap > 0 and level[node] + 1 == level[nxt]:\n"
                "                pushed = dfs(nxt, min(flow, cap))\n"
                "                if pushed:\n"
                "                    edge[1] -= pushed\n"
                "                    graph[nxt][rev][1] += pushed\n"
                "                    return pushed\n"
                "            it[node] += 1\n"
                "        return 0\n\n"
                "    ans = 0\n"
                "    while bfs():\n"
                "        it[:] = [0] * n\n"
                "        while True:\n"
                "            pushed = dfs(0, 10 ** 18)\n"
                "            if pushed == 0:\n"
                "                break\n"
                "            ans += pushed\n"
                "    print(ans)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-125":
        return array_template(
            statement="容量付き有向グラフが与えられる。頂点 1 から頂点 N への最小カット値を求めよ。",
            input_format="1 行目に N M。\n続く M 行に u v c。",
            output_format="最小カット値を出力する。",
            constraints="2 <= N <= 200\n1 <= M <= 2000\n1 <= c <= 10^9",
            examples=[{"input": "4 5\n1 2 2\n1 3 1\n2 3 1\n2 4 1\n3 4 2", "output": "3"}],
            reference_solution=(
                "from collections import deque\n\n"
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n, m = map(int, input().split())\n"
                "    graph = [[] for _ in range(n)]\n\n"
                "    def add_edge(u: int, v: int, cap: int) -> None:\n"
                "        graph[u].append([v, cap, len(graph[v])])\n"
                "        graph[v].append([u, 0, len(graph[u]) - 1])\n\n"
                "    for _ in range(m):\n"
                "        u, v, c = map(int, input().split())\n"
                "        add_edge(u - 1, v - 1, c)\n\n"
                "    level = [0] * n\n"
                "    it = [0] * n\n\n"
                "    def bfs() -> bool:\n"
                "        level[:] = [-1] * n\n"
                "        dq = deque([0])\n"
                "        level[0] = 0\n"
                "        while dq:\n"
                "            node = dq.popleft()\n"
                "            for nxt, cap, _ in graph[node]:\n"
                "                if cap > 0 and level[nxt] == -1:\n"
                "                    level[nxt] = level[node] + 1\n"
                "                    dq.append(nxt)\n"
                "        return level[n - 1] != -1\n\n"
                "    def dfs(node: int, flow: int) -> int:\n"
                "        if node == n - 1:\n"
                "            return flow\n"
                "        while it[node] < len(graph[node]):\n"
                "            edge = graph[node][it[node]]\n"
                "            nxt, cap, rev = edge\n"
                "            if cap > 0 and level[node] + 1 == level[nxt]:\n"
                "                pushed = dfs(nxt, min(flow, cap))\n"
                "                if pushed:\n"
                "                    edge[1] -= pushed\n"
                "                    graph[nxt][rev][1] += pushed\n"
                "                    return pushed\n"
                "            it[node] += 1\n"
                "        return 0\n\n"
                "    ans = 0\n"
                "    while bfs():\n"
                "        it[:] = [0] * n\n"
                "        while True:\n"
                "            pushed = dfs(0, 10 ** 18)\n"
                "            if pushed == 0:\n"
                "                break\n"
                "            ans += pushed\n"
                "    print(ans)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if category == "フロー・マッチング":
        return array_template(
            statement="左側 N 頂点、右側 M 頂点の二部グラフが与えられる。最大マッチング数を求めよ。",
            input_format="1 行目に N M E。\n続く E 行に u v。",
            output_format="最大マッチング数を出力する。",
            constraints="1 <= N, M <= 200\n1 <= E <= 2 * 10^4",
            examples=[{"input": "2 2 3\n1 1\n1 2\n2 2", "output": "2"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n, m, e = map(int, input().split())\n"
                "    graph = [[] for _ in range(n)]\n"
                "    for _ in range(e):\n"
                "        u, v = map(int, input().split())\n"
                "        graph[u - 1].append(v - 1)\n"
                "    match_to = [-1] * m\n"
                "    def dfs(v: int, seen: list[bool]) -> bool:\n"
                "        for nxt in graph[v]:\n"
                "            if seen[nxt]:\n"
                "                continue\n"
                "            seen[nxt] = True\n"
                "            if match_to[nxt] == -1 or dfs(match_to[nxt], seen):\n"
                "                match_to[nxt] = v\n"
                "                return True\n"
                "        return False\n"
                "    ans = 0\n"
                "    for v in range(n):\n"
                "        if dfs(v, [False] * m):\n"
                "            ans += 1\n"
                "    print(ans)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    return None
