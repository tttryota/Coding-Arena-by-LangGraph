"""Graph family templates."""

from __future__ import annotations

from .common import ProblemTemplate, array_template


def build_problem_template(  # noqa: C901
    *,
    theme_id: str,
    key: str,
    category: str,
) -> ProblemTemplate | None:
    if theme_id == "algo-004":
        return array_template(
            statement=(
                "N 頂点 M 辺の無向グラフが与えられる。"
                " 深さ優先探索を用いて、頂点 1 から到達できる頂点数を求めよ。"
            ),
            input_format="1 行目に N M。\n続く M 行に辺 u v。",
            output_format="頂点 1 から到達できる頂点数を出力する。",
            constraints="1 <= N, M <= 2 * 10^5",
            examples=[{"input": "5 3\n1 2\n2 3\n4 5", "output": "3"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    import sys\n"
                "    sys.setrecursionlimit(10 ** 7)\n"
                "    input = sys.stdin.readline\n"
                "    n, m = map(int, input().split())\n"
                "    graph = [[] for _ in range(n)]\n"
                "    for _ in range(m):\n"
                "        u, v = map(int, input().split())\n"
                "        u -= 1\n"
                "        v -= 1\n"
                "        graph[u].append(v)\n"
                "        graph[v].append(u)\n"
                "    seen = [False] * n\n"
                "    def dfs(node: int) -> int:\n"
                "        seen[node] = True\n"
                "        total = 1\n"
                "        for nxt in graph[node]:\n"
                "            if not seen[nxt]:\n"
                "                total += dfs(nxt)\n"
                "        return total\n"
                "    print(dfs(0))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-032":
        return array_template(
            statement="N 頂点 M 辺の無向グラフが与えられる。二部グラフなら Yes、そうでなければ No を出力せよ。",
            input_format="1 行目に N M。\n続く M 行に辺 u v。",
            output_format="Yes / No を出力する。",
            constraints="1 <= N, M <= 2 * 10^5",
            examples=[{"input": "4 4\n1 2\n2 3\n3 4\n4 1", "output": "Yes"}],
            reference_solution=(
                "from collections import deque\n\n"
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n, m = map(int, input().split())\n"
                "    graph = [[] for _ in range(n)]\n"
                "    for _ in range(m):\n"
                "        u, v = map(int, input().split())\n"
                "        u -= 1\n"
                "        v -= 1\n"
                "        graph[u].append(v)\n"
                "        graph[v].append(u)\n"
                "    color = [-1] * n\n"
                "    for start in range(n):\n"
                "        if color[start] != -1:\n"
                "            continue\n"
                "        color[start] = 0\n"
                "        dq = deque([start])\n"
                "        while dq:\n"
                "            node = dq.popleft()\n"
                "            for nxt in graph[node]:\n"
                "                if color[nxt] == -1:\n"
                "                    color[nxt] = color[node] ^ 1\n"
                "                    dq.append(nxt)\n"
                "                elif color[nxt] == color[node]:\n"
                "                    print('No')\n"
                "                    return\n"
        "    print('Yes')\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if any(token in key for token in ("DFS", "幅優先探索", "BFS", "二部グラフ")):
        return array_template(
            statement=(
                "N 頂点 M 辺の無向グラフが与えられる。"
                " 頂点 1 から到達できる頂点数を求めよ。"
            ),
            input_format="1 行目に N M。\n続く M 行に辺 u v。",
            output_format="頂点 1 から到達できる頂点数を出力する。",
            constraints="1 <= N, M <= 2 * 10^5",
            examples=[{"input": "5 3\n1 2\n2 3\n4 5", "output": "3"}],
            reference_solution=(
                "from collections import deque\n\n"
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n, m = map(int, input().split())\n"
                "    graph = [[] for _ in range(n)]\n"
                "    for _ in range(m):\n"
                "        u, v = map(int, input().split())\n"
                "        u -= 1\n"
                "        v -= 1\n"
                "        graph[u].append(v)\n"
                "        graph[v].append(u)\n"
                "    seen = [False] * n\n"
                "    queue = deque([0])\n"
                "    seen[0] = True\n"
                "    count = 0\n"
                "    while queue:\n"
                "        node = queue.popleft()\n"
                "        count += 1\n"
                "        for nxt in graph[node]:\n"
                "            if seen[nxt]:\n"
                "                continue\n"
                "            seen[nxt] = True\n"
                "            queue.append(nxt)\n"
                "    print(count)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-024":
        return array_template(
            statement=(
                "N 頂点 M 辺の有向重み付きグラフと Q 個の問い合わせ s, t が与えられる。"
                " 各問い合わせについて s から t への最短距離を求め、到達できなければ -1 を出力せよ。"
            ),
            input_format="1 行目に N M Q。\n続く M 行に u v w。\n続く Q 行に s t。",
            output_format="各問い合わせの答えを 1 行ずつ出力する。",
            constraints="1 <= N <= 300\n1 <= M <= 2 * 10^5\n1 <= Q <= 2 * 10^5",
            examples=[{"input": "3 3 2\n1 2 4\n2 3 5\n1 3 20\n1 3\n3 1", "output": "9\n-1"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n, m, q = map(int, input().split())\n"
                "    INF = 10 ** 18\n"
                "    dist = [[INF] * n for _ in range(n)]\n"
                "    for i in range(n):\n"
                "        dist[i][i] = 0\n"
                "    for _ in range(m):\n"
                "        u, v, w = map(int, input().split())\n"
                "        u -= 1\n"
                "        v -= 1\n"
                "        dist[u][v] = min(dist[u][v], w)\n"
                "    for k in range(n):\n"
                "        for i in range(n):\n"
                "            dik = dist[i][k]\n"
                "            if dik == INF:\n"
                "                continue\n"
                "            row_i = dist[i]\n"
                "            row_k = dist[k]\n"
                "            for j in range(n):\n"
                "                nd = dik + row_k[j]\n"
                "                if nd < row_i[j]:\n"
                "                    row_i[j] = nd\n"
                "    out = []\n"
                "    for _ in range(q):\n"
                "        s, t = map(int, input().split())\n"
                "        ans = dist[s - 1][t - 1]\n"
                "        out.append(str(-1 if ans == INF else ans))\n"
                "    sys.stdout.write('\\n'.join(out))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-023":
        return array_template(
            statement=(
                "N 頂点 M 辺の有向重み付きグラフが与えられる。"
                " 頂点 1 から各頂点への最短距離をベルマンフォード法で求め、頂点 N の距離を出力せよ。"
                " 到達できなければ -1 を出力する。"
            ),
            input_format="1 行目に N M。\n続く M 行に u v w。",
            output_format="頂点 1 から頂点 N までの最短距離を出力する。",
            constraints="1 <= N <= 500\n1 <= M <= 2 * 10^5\n-10^9 <= w <= 10^9",
            examples=[{"input": "4 4\n1 2 3\n2 4 5\n1 3 10\n3 4 1", "output": "8"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n, m = map(int, input().split())\n"
                "    edges = [tuple(map(int, input().split())) for _ in range(m)]\n"
                "    INF = 10 ** 18\n"
                "    dist = [INF] * n\n"
                "    dist[0] = 0\n"
                "    for _ in range(n - 1):\n"
                "        updated = False\n"
                "        for u, v, w in edges:\n"
                "            if dist[u - 1] == INF:\n"
                "                continue\n"
                "            nd = dist[u - 1] + w\n"
                "            if nd < dist[v - 1]:\n"
                "                dist[v - 1] = nd\n"
                "                updated = True\n"
                "        if not updated:\n"
                "            break\n"
                "    print(-1 if dist[-1] == INF else dist[-1])\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if any(token in key for token in ("ダイクストラ", "ベルマンフォード", "ワーシャルフロイド")):
        return array_template(
            statement=(
                "N 頂点 M 辺の有向重み付きグラフが与えられる。"
                " 頂点 1 から頂点 N への最短距離を求め、到達できないなら -1 を出力せよ。"
            ),
            input_format="1 行目に N M。\n続く M 行に u v w。",
            output_format="頂点 1 から頂点 N までの最短距離を出力する。",
            constraints="1 <= N, M <= 2 * 10^5\n1 <= w <= 10^9",
            examples=[{"input": "4 4\n1 2 3\n2 4 5\n1 3 10\n3 4 1", "output": "8"}],
            reference_solution=(
                "import heapq\n\n"
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n, m = map(int, input().split())\n"
                "    graph = [[] for _ in range(n)]\n"
                "    for _ in range(m):\n"
                "        u, v, w = map(int, input().split())\n"
                "        graph[u - 1].append((v - 1, w))\n"
                "    INF = 10 ** 30\n"
                "    dist = [INF] * n\n"
                "    dist[0] = 0\n"
                "    heap = [(0, 0)]\n"
                "    while heap:\n"
                "        cost, node = heapq.heappop(heap)\n"
                "        if cost != dist[node]:\n"
                "            continue\n"
                "        for nxt, w in graph[node]:\n"
                "            nd = cost + w\n"
                "            if nd < dist[nxt]:\n"
                "                dist[nxt] = nd\n"
                "                heapq.heappush(heap, (nd, nxt))\n"
                "    print(-1 if dist[-1] == INF else dist[-1])\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if any(token in key for token in ("隣接リスト", "隣接行列")):
        return array_template(
            statement="N 頂点 M 辺の無向グラフが与えられる。各頂点の次数を求めよ。",
            input_format="1 行目に N M。\n続く M 行に辺 u v。",
            output_format="1 行に N 個、各頂点の次数を出力する。",
            constraints="1 <= N, M <= 2 * 10^5",
            examples=[{"input": "4 3\n1 2\n2 3\n2 4", "output": "1 3 1 1"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n, m = map(int, input().split())\n"
                "    deg = [0] * n\n"
                "    for _ in range(m):\n"
                "        u, v = map(int, input().split())\n"
                "        deg[u - 1] += 1\n"
                "        deg[v - 1] += 1\n"
                "    print(*deg)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if "Union-Find" in key:
        return array_template(
            statement=(
                "N 個の頂点と Q 個の操作が与えられる。"
                " `1 a b` は a と b を連結し、`2 a b` は同じ連結成分なら Yes そうでなければ No を出力せよ。"
            ),
            input_format="1 行目に N Q。\n続く Q 行に type a b。",
            output_format="type=2 の操作ごとに Yes / No を出力する。",
            constraints="1 <= N, Q <= 2 * 10^5",
            examples=[{"input": "4 5\n1 1 2\n2 1 2\n2 1 3\n1 2 3\n2 1 3", "output": "Yes\nNo\nYes"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n, q = map(int, input().split())\n"
                "    parent = list(range(n + 1))\n"
                "    size = [1] * (n + 1)\n"
                "    def find(x: int) -> int:\n"
                "        while parent[x] != x:\n"
                "            parent[x] = parent[parent[x]]\n"
                "            x = parent[x]\n"
                "        return x\n"
                "    def unite(a: int, b: int) -> None:\n"
                "        ra = find(a)\n"
                "        rb = find(b)\n"
                "        if ra == rb:\n"
                "            return\n"
                "        if size[ra] < size[rb]:\n"
                "            ra, rb = rb, ra\n"
                "        parent[rb] = ra\n"
                "        size[ra] += size[rb]\n"
                "    out = []\n"
                "    for _ in range(q):\n"
                "        t, a, b = map(int, input().split())\n"
                "        if t == 1:\n"
                "            unite(a, b)\n"
                "        else:\n"
                "            out.append('Yes' if find(a) == find(b) else 'No')\n"
                "    sys.stdout.write('\\n'.join(out))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-033":
        return array_template(
            statement=(
                "N 頂点 M 辺の無向グラフが与えられる。"
                " すべての辺をちょうど 1 回ずつ通る道が存在するなら Yes、存在しなければ No を出力せよ。"
            ),
            input_format="1 行目に N M。\n続く M 行に辺 u v。",
            output_format="Yes / No を出力する。",
            constraints="1 <= N, M <= 2 * 10^5",
            examples=[{"input": "4 3\n1 2\n2 3\n3 4", "output": "Yes"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n, m = map(int, input().split())\n"
                "    parent = list(range(n))\n"
                "    size = [1] * n\n"
                "    degree = [0] * n\n\n"
                "    def find(x: int) -> int:\n"
                "        while parent[x] != x:\n"
                "            parent[x] = parent[parent[x]]\n"
                "            x = parent[x]\n"
                "        return x\n\n"
                "    def unite(a: int, b: int) -> None:\n"
                "        ra = find(a)\n"
                "        rb = find(b)\n"
                "        if ra == rb:\n"
                "            return\n"
                "        if size[ra] < size[rb]:\n"
                "            ra, rb = rb, ra\n"
                "        parent[rb] = ra\n"
                "        size[ra] += size[rb]\n\n"
                "    for _ in range(m):\n"
                "        u, v = map(int, input().split())\n"
                "        u -= 1\n"
                "        v -= 1\n"
                "        degree[u] += 1\n"
                "        degree[v] += 1\n"
                "        unite(u, v)\n"
                "    active = [i for i, deg in enumerate(degree) if deg > 0]\n"
                "    if active:\n"
                "        root = find(active[0])\n"
                "        if any(find(node) != root for node in active):\n"
                "            print('No')\n"
                "            return\n"
                "    odd = sum(deg % 2 for deg in degree)\n"
                "    print('Yes' if odd in (0, 2) else 'No')\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-034":
        return array_template(
            statement="根 1 の木が与えられる。深さ優先探索によるオイラーツアーの訪問順を出力せよ。",
            input_format="1 行目に N。\n続く N-1 行に辺 u v。",
            output_format="訪問順を空白区切りで出力する。",
            constraints="1 <= N <= 2 * 10^5",
            examples=[{"input": "4\n1 2\n1 3\n3 4", "output": "1 2 1 3 4 3 1"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    import sys\n"
                "    sys.setrecursionlimit(10 ** 7)\n"
                "    input = sys.stdin.readline\n"
                "    n = int(input())\n"
                "    graph = [[] for _ in range(n)]\n"
                "    for _ in range(n - 1):\n"
                "        u, v = map(int, input().split())\n"
                "        u -= 1\n"
                "        v -= 1\n"
                "        graph[u].append(v)\n"
                "        graph[v].append(u)\n"
                "    for adj in graph:\n"
                "        adj.sort()\n"
                "    order = []\n\n"
                "    def dfs(node: int, parent: int) -> None:\n"
                "        order.append(node + 1)\n"
                "        for nxt in graph[node]:\n"
                "            if nxt == parent:\n"
                "                continue\n"
                "            dfs(nxt, node)\n"
                "            order.append(node + 1)\n\n"
                "    dfs(0, -1)\n"
                "    print(*order)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-025":
        return array_template(
            statement="重み付き無向連結グラフが与えられる。プリム法で最小全域木の重みを求めよ。",
            input_format="1 行目に N M。\n続く M 行に u v w。",
            output_format="最小全域木の重みを出力する。",
            constraints="1 <= N <= 2 * 10^5\nN-1 <= M <= 2 * 10^5",
            examples=[{"input": "4 5\n1 2 1\n1 3 4\n2 3 2\n2 4 5\n3 4 1", "output": "4"}],
            reference_solution=(
                "import heapq\n\n"
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n, m = map(int, input().split())\n"
                "    graph = [[] for _ in range(n)]\n"
                "    for _ in range(m):\n"
                "        u, v, w = map(int, input().split())\n"
                "        u -= 1\n"
                "        v -= 1\n"
                "        graph[u].append((w, v))\n"
                "        graph[v].append((w, u))\n"
                "    used = [False] * n\n"
                "    pq = [(0, 0)]\n"
                "    total = 0\n"
                "    while pq:\n"
                "        cost, node = heapq.heappop(pq)\n"
                "        if used[node]:\n"
                "            continue\n"
                "        used[node] = True\n"
                "        total += cost\n"
                "        for edge_cost, nxt in graph[node]:\n"
                "            if not used[nxt]:\n"
                "                heapq.heappush(pq, (edge_cost, nxt))\n"
                "    print(total)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-026":
        return array_template(
            statement="重み付き無向連結グラフが与えられる。クラスカル法で最小全域木の重みを求めよ。",
            input_format="1 行目に N M。\n続く M 行に u v w。",
            output_format="最小全域木の重みを出力する。",
            constraints="1 <= N <= 2 * 10^5\nN-1 <= M <= 2 * 10^5",
            examples=[{"input": "4 5\n1 2 1\n1 3 4\n2 3 2\n2 4 5\n3 4 1", "output": "4"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n, m = map(int, input().split())\n"
                "    edges = []\n"
                "    for _ in range(m):\n"
                "        u, v, w = map(int, input().split())\n"
                "        edges.append((w, u - 1, v - 1))\n"
                "    edges.sort()\n"
                "    parent = list(range(n))\n"
                "    size = [1] * n\n\n"
                "    def find(x: int) -> int:\n"
                "        while parent[x] != x:\n"
                "            parent[x] = parent[parent[x]]\n"
                "            x = parent[x]\n"
                "        return x\n\n"
                "    total = 0\n"
                "    for w, u, v in edges:\n"
                "        ru = find(u)\n"
                "        rv = find(v)\n"
                "        if ru == rv:\n"
                "            continue\n"
                "        if size[ru] < size[rv]:\n"
                "            ru, rv = rv, ru\n"
                "        parent[rv] = ru\n"
                "        size[ru] += size[rv]\n"
                "        total += w\n"
                "    print(total)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-027":
        return array_template(
            statement=(
                "N 頂点 M 辺の有向非巡回グラフが与えられる。"
                " 辞書順最小のトポロジカル順序を 1 つ出力せよ。"
            ),
            input_format="1 行目に N M。\n続く M 行に辺 u v。",
            output_format="トポロジカル順序を空白区切りで出力する。",
            constraints="1 <= N, M <= 2 * 10^5",
            examples=[{"input": "4 3\n1 2\n1 3\n3 4", "output": "1 2 3 4"}],
            reference_solution=(
                "import heapq\n\n"
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n, m = map(int, input().split())\n"
                "    graph = [[] for _ in range(n)]\n"
                "    indeg = [0] * n\n"
                "    for _ in range(m):\n"
                "        u, v = map(int, input().split())\n"
                "        u -= 1\n"
                "        v -= 1\n"
                "        graph[u].append(v)\n"
                "        indeg[v] += 1\n"
                "    pq = [i for i, deg in enumerate(indeg) if deg == 0]\n"
                "    heapq.heapify(pq)\n"
                "    order = []\n"
                "    while pq:\n"
                "        node = heapq.heappop(pq)\n"
                "        order.append(node + 1)\n"
                "        for nxt in graph[node]:\n"
                "            indeg[nxt] -= 1\n"
                "            if indeg[nxt] == 0:\n"
                "                heapq.heappush(pq, nxt)\n"
                "    print(*order)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-029":
        return array_template(
            statement="重みのない木が与えられる。木の直径の長さを求めよ。",
            input_format="1 行目に N。\n続く N-1 行に辺 u v。",
            output_format="直径の長さを出力する。",
            constraints="1 <= N <= 2 * 10^5",
            examples=[{"input": "5\n1 2\n2 3\n2 4\n4 5", "output": "3"}],
            reference_solution=(
                "from collections import deque\n\n"
                "def farthest(start: int, graph: list[list[int]]) -> tuple[int, int]:\n"
                "    dist = [-1] * len(graph)\n"
                "    dist[start] = 0\n"
                "    dq = deque([start])\n"
                "    while dq:\n"
                "        node = dq.popleft()\n"
                "        for nxt in graph[node]:\n"
                "            if dist[nxt] != -1:\n"
                "                continue\n"
                "            dist[nxt] = dist[node] + 1\n"
                "            dq.append(nxt)\n"
                "    best = max(range(len(graph)), key=lambda idx: dist[idx])\n"
                "    return best, dist[best]\n\n"
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n = int(input())\n"
                "    graph = [[] for _ in range(n)]\n"
                "    for _ in range(n - 1):\n"
                "        u, v = map(int, input().split())\n"
                "        u -= 1\n"
                "        v -= 1\n"
                "        graph[u].append(v)\n"
                "        graph[v].append(u)\n"
                "    node, _ = farthest(0, graph)\n"
                "    _, diameter = farthest(node, graph)\n"
                "    print(diameter)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-030":
        return array_template(
            statement="根 1 の木と Q 個の問い合わせ u v が与えられる。各問い合わせについて最小共通祖先を求めよ。",
            input_format="1 行目に N Q。\n続く N-1 行に辺 u v。\n続く Q 行に u v。",
            output_format="各問い合わせの答えを 1 行ずつ出力する。",
            constraints="1 <= N, Q <= 2 * 10^5",
            examples=[{"input": "5 3\n1 2\n1 3\n3 4\n3 5\n2 4\n4 5\n2 5", "output": "1\n3\n1"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    import sys\n"
                "    sys.setrecursionlimit(10 ** 7)\n"
                "    input = sys.stdin.readline\n"
                "    n, q = map(int, input().split())\n"
                "    graph = [[] for _ in range(n)]\n"
                "    for _ in range(n - 1):\n"
                "        u, v = map(int, input().split())\n"
                "        u -= 1\n"
                "        v -= 1\n"
                "        graph[u].append(v)\n"
                "        graph[v].append(u)\n"
                "    log = n.bit_length()\n"
                "    parent = [[-1] * n for _ in range(log)]\n"
                "    depth = [0] * n\n\n"
                "    def dfs(node: int, par: int) -> None:\n"
                "        parent[0][node] = par\n"
                "        for nxt in graph[node]:\n"
                "            if nxt == par:\n"
                "                continue\n"
                "            depth[nxt] = depth[node] + 1\n"
                "            dfs(nxt, node)\n\n"
                "    dfs(0, -1)\n"
                "    for k in range(1, log):\n"
                "        for node in range(n):\n"
                "            prev = parent[k - 1][node]\n"
                "            parent[k][node] = -1 if prev == -1 else parent[k - 1][prev]\n\n"
                "    def lca(u: int, v: int) -> int:\n"
                "        if depth[u] < depth[v]:\n"
                "            u, v = v, u\n"
                "        diff = depth[u] - depth[v]\n"
                "        for k in range(log):\n"
                "            if diff >> k & 1:\n"
                "                u = parent[k][u]\n"
                "        if u == v:\n"
                "            return u\n"
                "        for k in range(log - 1, -1, -1):\n"
                "            if parent[k][u] != parent[k][v]:\n"
                "                u = parent[k][u]\n"
                "                v = parent[k][v]\n"
                "        return parent[0][u]\n\n"
                "    out = []\n"
                "    for _ in range(q):\n"
                "        u, v = map(int, input().split())\n"
                "        out.append(str(lca(u - 1, v - 1) + 1))\n"
                "    sys.stdout.write('\\n'.join(out))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-031":
        return array_template(
            statement="有向グラフが与えられる。強連結成分の個数を求めよ。",
            input_format="1 行目に N M。\n続く M 行に辺 u v。",
            output_format="強連結成分の個数を出力する。",
            constraints="1 <= N, M <= 2 * 10^5",
            examples=[{"input": "5 6\n1 2\n2 1\n2 3\n3 4\n4 3\n4 5", "output": "3"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    import sys\n"
                "    sys.setrecursionlimit(10 ** 7)\n"
                "    input = sys.stdin.readline\n"
                "    n, m = map(int, input().split())\n"
                "    graph = [[] for _ in range(n)]\n"
                "    rev = [[] for _ in range(n)]\n"
                "    for _ in range(m):\n"
                "        u, v = map(int, input().split())\n"
                "        u -= 1\n"
                "        v -= 1\n"
                "        graph[u].append(v)\n"
                "        rev[v].append(u)\n"
                "    order = []\n"
                "    seen = [False] * n\n\n"
                "    def dfs(node: int) -> None:\n"
                "        seen[node] = True\n"
                "        for nxt in graph[node]:\n"
                "            if not seen[nxt]:\n"
                "                dfs(nxt)\n"
                "        order.append(node)\n\n"
                "    def rdfs(node: int) -> None:\n"
                "        seen[node] = True\n"
                "        for nxt in rev[node]:\n"
                "            if not seen[nxt]:\n"
                "                rdfs(nxt)\n\n"
                "    for node in range(n):\n"
                "        if not seen[node]:\n"
                "            dfs(node)\n"
                "    seen = [False] * n\n"
                "    count = 0\n"
                "    for node in reversed(order):\n"
                "        if seen[node]:\n"
                "            continue\n"
                "        rdfs(node)\n"
                "        count += 1\n"
                "    print(count)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-035":
        return array_template(
            statement="無向グラフが与えられる。橋の本数を求めよ。",
            input_format="1 行目に N M。\n続く M 行に辺 u v。",
            output_format="橋の本数を出力する。",
            constraints="1 <= N, M <= 2 * 10^5",
            examples=[{"input": "5 5\n1 2\n2 3\n3 1\n3 4\n4 5", "output": "2"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    import sys\n"
                "    sys.setrecursionlimit(10 ** 7)\n"
                "    input = sys.stdin.readline\n"
                "    n, m = map(int, input().split())\n"
                "    graph = [[] for _ in range(n)]\n"
                "    for idx in range(m):\n"
                "        u, v = map(int, input().split())\n"
                "        u -= 1\n"
                "        v -= 1\n"
                "        graph[u].append((v, idx))\n"
                "        graph[v].append((u, idx))\n"
                "    order = [-1] * n\n"
                "    low = [0] * n\n"
                "    timer = 0\n"
                "    bridges = 0\n\n"
                "    def dfs(node: int, parent_edge: int) -> None:\n"
                "        nonlocal timer, bridges\n"
                "        order[node] = low[node] = timer\n"
                "        timer += 1\n"
                "        for nxt, edge_id in graph[node]:\n"
                "            if edge_id == parent_edge:\n"
                "                continue\n"
                "            if order[nxt] == -1:\n"
                "                dfs(nxt, edge_id)\n"
                "                low[node] = min(low[node], low[nxt])\n"
                "                if order[node] < low[nxt]:\n"
                "                    bridges += 1\n"
                "            else:\n"
                "                low[node] = min(low[node], order[nxt])\n\n"
                "    for node in range(n):\n"
                "        if order[node] == -1:\n"
                "            dfs(node, -1)\n"
                "    print(bridges)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if category == "グラフ":
        return array_template(
            statement="N 頂点 M 辺の無向グラフが与えられる。頂点 1 から到達できる頂点数を求めよ。",
            input_format="1 行目に N M。\n続く M 行に辺 u v。",
            output_format="到達できる頂点数を出力する。",
            constraints="1 <= N, M <= 2 * 10^5",
            examples=[{"input": "4 2\n1 2\n3 4", "output": "2"}],
            reference_solution=(
                "from collections import deque\n\n"
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n, m = map(int, input().split())\n"
                "    graph = [[] for _ in range(n)]\n"
                "    for _ in range(m):\n"
                "        u, v = map(int, input().split())\n"
                "        u -= 1\n"
                "        v -= 1\n"
                "        graph[u].append(v)\n"
                "        graph[v].append(u)\n"
                "    seen = [False] * n\n"
                "    dq = deque([0])\n"
                "    seen[0] = True\n"
                "    ans = 0\n"
                "    while dq:\n"
                "        node = dq.popleft()\n"
                "        ans += 1\n"
                "        for nxt in graph[node]:\n"
                "            if seen[nxt]:\n"
                "                continue\n"
                "            seen[nxt] = True\n"
                "            dq.append(nxt)\n"
                "    print(ans)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if category == "グラフ":
        return array_template(
            statement="N 頂点 M 辺の無向グラフが与えられる。頂点 1 から到達できる頂点数を求めよ。",
            input_format="1 行目に N M。\n続く M 行に辺 u v。",
            output_format="到達できる頂点数を出力する。",
            constraints="1 <= N, M <= 2 * 10^5",
            examples=[{"input": "4 2\n1 2\n3 4", "output": "2"}],
            reference_solution=(
                "from collections import deque\n\n"
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n, m = map(int, input().split())\n"
                "    graph = [[] for _ in range(n)]\n"
                "    for _ in range(m):\n"
                "        u, v = map(int, input().split())\n"
                "        u -= 1\n"
                "        v -= 1\n"
                "        graph[u].append(v)\n"
                "        graph[v].append(u)\n"
                "    seen = [False] * n\n"
                "    dq = deque([0])\n"
                "    seen[0] = True\n"
                "    ans = 0\n"
                "    while dq:\n"
                "        node = dq.popleft()\n"
                "        ans += 1\n"
                "        for nxt in graph[node]:\n"
                "            if seen[nxt]:\n"
                "                continue\n"
                "            seen[nxt] = True\n"
                "            dq.append(nxt)\n"
                "    print(ans)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    return None
