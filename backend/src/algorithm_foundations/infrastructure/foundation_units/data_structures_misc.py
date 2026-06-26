"""Misc data-structure family templates."""

from __future__ import annotations

from .common import ProblemTemplate, array_template


def build_problem_template(
    *,
    theme_id: str,
    key: str,
    category: str,
) -> ProblemTemplate | None:
    del key, category
    if theme_id == "algo-095":
        return array_template(
            statement=(
                "Q 個の操作が与えられる。"
                " `1 x` は整数 x を追加し、`2` は現在入っている値のうち最小値を出力して削除せよ。"
            ),
            input_format="1 行目に Q。\n続く Q 行に操作。",
            output_format="type=2 のたびに取り出した最小値を 1 行ずつ出力する。",
            constraints="1 <= Q <= 2 * 10^5\ntype=2 の時点で優先度付きキューは空でない",
            examples=[{"input": "6\n1 5\n1 2\n2\n1 4\n2\n2", "output": "2\n4\n5"}],
            reference_solution=(
                "import heapq\n\n"
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    q = int(input())\n"
                "    heap = []\n"
                "    out = []\n"
                "    for _ in range(q):\n"
                "        parts = list(map(int, input().split()))\n"
                "        if parts[0] == 1:\n"
                "            heapq.heappush(heap, parts[1])\n"
                "        else:\n"
                "            out.append(str(heapq.heappop(heap)))\n"
                "    sys.stdout.write('\\n'.join(out))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-100":
        return array_template(
            statement=(
                "長さ N の配列に対して Q 個の加算操作 `[l, r] に x を足す` が与えられる。"
                " すべて適用した後の配列を出力せよ。"
            ),
            input_format="1 行目に N Q。\n続く Q 行に l r x。",
            output_format="最終的な配列を空白区切りで出力する。",
            constraints="1 <= N, Q <= 2 * 10^5\n|x| <= 10^9",
            examples=[{"input": "5 3\n1 3 2\n2 5 1\n4 4 -2", "output": "2 3 3 -1 1"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n, q = map(int, input().split())\n"
                "    diff = [0] * (n + 1)\n"
                "    for _ in range(q):\n"
                "        l, r, x = map(int, input().split())\n"
                "        diff[l - 1] += x\n"
                "        if r < n:\n"
                "            diff[r] -= x\n"
                "    ans = []\n"
                "    cur = 0\n"
                "    for i in range(n):\n"
                "        cur += diff[i]\n"
                "        ans.append(cur)\n"
                "    print(*ans)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-101":
        return array_template(
            statement=(
                "Q 個の操作が与えられる。`1 x` は x を集合に追加し、`2 x` は x を削除し、"
                " `3 x` は x が存在するなら Yes、そうでなければ No を出力せよ。"
            ),
            input_format="1 行目に Q。\n続く Q 行に操作。",
            output_format="type=3 のたびに Yes / No を出力する。",
            constraints="1 <= Q <= 2 * 10^5\n0 <= x <= 10^9",
            examples=[{"input": "6\n1 5\n1 2\n3 2\n2 2\n3 2\n3 5", "output": "Yes\nNo\nYes"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    q = int(input())\n"
                "    values = set()\n"
                "    out = []\n"
                "    for _ in range(q):\n"
                "        t, x = map(int, input().split())\n"
                "        if t == 1:\n"
                "            values.add(x)\n"
                "        elif t == 2:\n"
                "            values.discard(x)\n"
                "        else:\n"
                "            out.append('Yes' if x in values else 'No')\n"
                "    sys.stdout.write('\\n'.join(out))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-104":
        return array_template(
            statement=(
                "長さ N の整数列 A が与えられる。各 i について、i より左で `A_j < A_i` を満たす最も近い位置 j を求め、"
                " 存在しなければ -1 を出力せよ。"
            ),
            input_format="1 行目に N。\n2 行目に A1..AN。",
            output_format="N 個の答えを空白区切りで出力する。",
            constraints="1 <= N <= 2 * 10^5",
            examples=[{"input": "5\n3 7 4 6 2", "output": "-1 1 1 3 -1"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    input()\n"
                "    a = list(map(int, input().split()))\n"
                "    stack = []\n"
                "    ans = []\n"
                "    for i, value in enumerate(a, start=1):\n"
                "        while stack and stack[-1][0] >= value:\n"
                "            stack.pop()\n"
                "        ans.append(stack[-1][1] if stack else -1)\n"
                "        stack.append((value, i))\n"
                "    print(*ans)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-105":
        return array_template(
            statement=(
                "長さ N の整数列 A と幅 K が与えられる。"
                " 各長さ K の連続部分列について最小値を求めよ。"
            ),
            input_format="1 行目に N K。\n2 行目に A1..AN。",
            output_format="各区間の最小値を空白区切りで出力する。",
            constraints="1 <= K <= N <= 2 * 10^5",
            examples=[{"input": "7 3\n4 2 5 1 6 3 7", "output": "2 1 1 1 3"}],
            reference_solution=(
                "from collections import deque\n\n"
                "def solve() -> None:\n"
                "    n, k = map(int, input().split())\n"
                "    a = list(map(int, input().split()))\n"
                "    dq = deque()\n"
                "    ans = []\n"
                "    for i, value in enumerate(a):\n"
                "        while dq and a[dq[-1]] >= value:\n"
                "            dq.pop()\n"
                "        dq.append(i)\n"
                "        if dq[0] <= i - k:\n"
                "            dq.popleft()\n"
                "        if i >= k - 1:\n"
                "            ans.append(a[dq[0]])\n"
                "    print(*ans)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    return None
