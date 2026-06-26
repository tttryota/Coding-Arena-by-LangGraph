"""Dynamic-programming family templates."""

from __future__ import annotations

from .common import ProblemTemplate, array_template


def build_problem_template(  # noqa: C901
    *,
    theme_id: str,
    key: str,
    category: str,
) -> ProblemTemplate | None:
    if any(token in key for token in ("LIS", "最長増加部分列")):
        return array_template(
            statement="長さ N の整数列 A が与えられる。最長増加部分列の長さを求めよ。",
            input_format="1 行目に N。\n2 行目に A1..AN。",
            output_format="LIS の長さを出力する。",
            constraints="1 <= N <= 2 * 10^5",
            examples=[{"input": "6\n3 1 4 1 5 9", "output": "4"}],
            reference_solution=(
                "from bisect import bisect_left\n\n"
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    _ = int(input())\n"
                "    a = list(map(int, input().split()))\n"
                "    dp = []\n"
                "    for value in a:\n"
                "        i = bisect_left(dp, value)\n"
                "        if i == len(dp):\n"
                "            dp.append(value)\n"
                "        else:\n"
                "            dp[i] = value\n"
                "    print(len(dp))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if "編集距離" in key:
        return array_template(
            statement="2 つの文字列 S, T が与えられる。編集距離を求めよ。",
            input_format="1 行目に S。\n2 行目に T。",
            output_format="編集距離を出力する。",
            constraints="1 <= |S|, |T| <= 2000",
            examples=[{"input": "kitten\nsitting", "output": "3"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    s = input().strip()\n"
                "    t = input().strip()\n"
                "    dp = [[0] * (len(t) + 1) for _ in range(len(s) + 1)]\n"
                "    for i in range(len(s) + 1):\n"
                "        dp[i][0] = i\n"
                "    for j in range(len(t) + 1):\n"
                "        dp[0][j] = j\n"
                "    for i, ch in enumerate(s, start=1):\n"
                "        for j, tch in enumerate(t, start=1):\n"
                "            cost = 0 if ch == tch else 1\n"
                "            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)\n"
                "    print(dp[-1][-1])\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if "LCS" in key:
        return array_template(
            statement="2 つの文字列 S, T が与えられる。最長共通部分列の長さを求めよ。",
            input_format="1 行目に S。\n2 行目に T。",
            output_format="LCS の長さを出力する。",
            constraints="1 <= |S|, |T| <= 2000",
            examples=[{"input": "abcde\nace", "output": "3"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    s = input().strip()\n"
                "    t = input().strip()\n"
                "    dp = [0] * (len(t) + 1)\n"
                "    for ch in s:\n"
                "        prev = 0\n"
                "        for j, tch in enumerate(t, start=1):\n"
                "            saved = dp[j]\n"
                "            if ch == tch:\n"
                "                dp[j] = prev + 1\n"
                "            else:\n"
                "                dp[j] = max(dp[j], dp[j - 1])\n"
                "            prev = saved\n"
                "    print(dp[-1])\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-049":
        return array_template(
            statement=(
                "整数 N, K が与えられる。1 歩で 1 以上 K 以下進めるとき、"
                " ちょうど N に到達する方法数を 10^9+7 で割った余りで求めよ。"
            ),
            input_format="1 行目に N K。",
            output_format="方法数を出力する。",
            constraints="1 <= N <= 2 * 10^5\n1 <= K <= 2 * 10^5",
            examples=[{"input": "4 2", "output": "5"}],
            reference_solution=(
                "MOD = 10 ** 9 + 7\n\n"
                "def solve() -> None:\n"
                "    n, k = map(int, input().split())\n"
                "    dp = [0] * (n + 1)\n"
                "    pref = [0] * (n + 2)\n"
                "    dp[0] = 1\n"
                "    pref[1] = 1\n"
                "    for i in range(1, n + 1):\n"
                "        left = max(0, i - k)\n"
                "        dp[i] = (pref[i] - pref[left]) % MOD\n"
                "        pref[i + 1] = (pref[i] + dp[i]) % MOD\n"
                "    print(dp[n])\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-040":
        return array_template(
            statement=(
                "長さ N の正整数列 A が与えられる。"
                " 隣り合う区間を順に併合するとき、併合コストを区間和とする。"
                " 列全体を 1 つにする最小コストを求めよ。"
            ),
            input_format="1 行目に N。\n2 行目に A1..AN。",
            output_format="最小コストを出力する。",
            constraints="1 <= N <= 400\n1 <= Ai <= 10^9",
            examples=[{"input": "4\n4 1 3 2", "output": "20"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n = int(input())\n"
                "    a = list(map(int, input().split()))\n"
                "    prefix = [0]\n"
                "    for value in a:\n"
                "        prefix.append(prefix[-1] + value)\n"
                "    dp = [[0] * n for _ in range(n)]\n"
                "    for length in range(2, n + 1):\n"
                "        for left in range(n - length + 1):\n"
                "            right = left + length - 1\n"
                "            total = prefix[right + 1] - prefix[left]\n"
                "            best = 10 ** 30\n"
                "            for mid in range(left, right):\n"
                "                best = min(best, dp[left][mid] + dp[mid + 1][right] + total)\n"
                "            dp[left][right] = best\n"
                "    print(dp[0][n - 1])\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-041":
        return array_template(
            statement="整数 N が与えられる。0 以上 N 以下で 10 進表記に数字 4 を含まない整数の個数を求めよ。",
            input_format="1 行目に N。",
            output_format="個数を出力する。",
            constraints="0 <= N <= 10^18",
            examples=[{"input": "20", "output": "19"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    n = input().strip()\n"
                "    equal = 1\n"
                "    less = 0\n"
                "    for ch in n:\n"
                "        digit = ord(ch) - ord('0')\n"
                "        next_equal = 0\n"
                "        next_less = less * 9\n"
                "        for value in range(digit):\n"
                "            if value != 4:\n"
                "                next_less += equal\n"
                "        if digit != 4:\n"
                "            next_equal = equal\n"
                "        equal = next_equal\n"
                "        less = next_less\n"
                "    print(equal + less)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-043":
        return array_template(
            statement="木が与えられる。隣接頂点を同時に選ばないように頂点を選ぶとき、選べる頂点数の最大値を求めよ。",
            input_format="1 行目に N。\n続く N-1 行に辺 u v。",
            output_format="最大値を出力する。",
            constraints="1 <= N <= 2 * 10^5",
            examples=[{"input": "5\n1 2\n1 3\n3 4\n3 5", "output": "3"}],
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
                "        graph[v].append(u)\n\n"
                "    def dfs(node: int, parent: int) -> tuple[int, int]:\n"
                "        take = 1\n"
                "        skip = 0\n"
                "        for nxt in graph[node]:\n"
                "            if nxt == parent:\n"
                "                continue\n"
                "            child_take, child_skip = dfs(nxt, node)\n"
                "            take += child_skip\n"
                "            skip += max(child_take, child_skip)\n"
                "        return take, skip\n\n"
                "    take, skip = dfs(0, -1)\n"
                "    print(max(take, skip))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-047":
        return array_template(
            statement="コインを投げて表が出る確率 p が与えられる。初めて表が出るまでの期待手数を求めよ。",
            input_format="1 行目に p。",
            output_format="期待値を小数で出力する。",
            constraints="0 < p <= 1",
            examples=[{"input": "0.25", "output": "4.0"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    p = float(input())\n"
                "    print(1.0 / p)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-048":
        return array_template(
            statement=(
                "石が N 個あり、1 回で 1 個または 3 個取れるゲームを考える。"
                " 先手後手が最善を尽くすとして、先手が勝つなら First、負けるなら Second を出力せよ。"
            ),
            input_format="1 行目に N。",
            output_format="First / Second を出力する。",
            constraints="1 <= N <= 2 * 10^5",
            examples=[{"input": "2", "output": "Second"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    n = int(input())\n"
                "    win = [False] * (max(4, n + 1))\n"
                "    for stones in range(1, n + 1):\n"
                "        for move in (1, 3):\n"
                "            if stones >= move and not win[stones - move]:\n"
                "                win[stones] = True\n"
                "                break\n"
                "    print('First' if win[n] else 'Second')\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if any(token in key for token in ("部分和", "ナップサック", "コイン", "DP")) or category == "動的計画法":
        return array_template(
            statement=(
                "N 個の正整数 A と目標値 S が与えられる。"
                " いくつかを選んで合計をちょうど S にできるなら Yes、できなければ No を出力せよ。"
            ),
            input_format="1 行目に N S。\n2 行目に A1..AN。",
            output_format="Yes / No を出力する。",
            constraints="1 <= N <= 200\n1 <= S <= 2 * 10^5",
            examples=[{"input": "4 11\n2 5 9 4", "output": "Yes"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n, s = map(int, input().split())\n"
                "    a = list(map(int, input().split()))\n"
                "    possible = [False] * (s + 1)\n"
                "    possible[0] = True\n"
                "    for value in a:\n"
                "        for cur in range(s, value - 1, -1):\n"
                "            if possible[cur - value]:\n"
                "                possible[cur] = True\n"
                "    print('Yes' if possible[s] else 'No')\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    return None
