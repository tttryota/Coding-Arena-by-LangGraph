"""Range-query and coordinate-compression family templates."""

from __future__ import annotations

from .common import ProblemTemplate, array_template


def build_problem_template(
    *,
    theme_id: str,
    key: str,
    category: str,
) -> ProblemTemplate | None:
    del theme_id, category
    if "座標圧縮" in key:
        return array_template(
            statement="長さ N の整数列 A を座標圧縮し、各要素の圧縮後の値を出力せよ。",
            input_format="1 行目に N。\n2 行目に A1..AN。",
            output_format="圧縮後の列を空白区切りで出力する。",
            constraints="1 <= N <= 2 * 10^5",
            examples=[{"input": "5\n100 50 1000 50 200", "output": "1 0 3 0 2"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    input()\n"
                "    a = list(map(int, input().split()))\n"
                "    values = {value: idx for idx, value in enumerate(sorted(set(a)))}\n"
                "    print(*[values[value] for value in a])\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if "転倒数" in key:
        return array_template(
            statement="長さ N の整数列 A が与えられる。転倒数を求めよ。",
            input_format="1 行目に N。\n2 行目に A1..AN。",
            output_format="転倒数を出力する。",
            constraints="1 <= N <= 2 * 10^5",
            examples=[{"input": "4\n3 1 4 2", "output": "3"}],
            reference_solution=(
                "def merge_count(arr: list[int]) -> tuple[list[int], int]:\n"
                "    if len(arr) <= 1:\n"
                "        return arr, 0\n"
                "    mid = len(arr) // 2\n"
                "    left, lc = merge_count(arr[:mid])\n"
                "    right, rc = merge_count(arr[mid:])\n"
                "    merged = []\n"
                "    i = j = 0\n"
                "    inv = lc + rc\n"
                "    while i < len(left) and j < len(right):\n"
                "        if left[i] <= right[j]:\n"
                "            merged.append(left[i]); i += 1\n"
                "        else:\n"
                "            merged.append(right[j]); j += 1\n"
                "            inv += len(left) - i\n"
                "    merged.extend(left[i:])\n"
                "    merged.extend(right[j:])\n"
                "    return merged, inv\n\n"
                "def solve() -> None:\n"
                "    input()\n"
                "    a = list(map(int, input().split()))\n"
                "    print(merge_count(a)[1])\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if "遅延評価セグメント木" in key:
        return array_template(
            statement=(
                "長さ N の整数列 A と Q 個の操作が与えられる。"
                " `1 l r x` は区間 [l, r] の全要素に x を加算し、`2 l r` は区間 [l, r] の最小値を求めよ。"
            ),
            input_format="1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に操作。",
            output_format="type=2 のたびに区間最小値を 1 行ずつ出力する。",
            constraints="1 <= N, Q <= 2 * 10^5\n|Ai|, |x| <= 10^9",
            examples=[{"input": "5 5\n5 2 8 1 4\n2 1 5\n1 2 4 3\n2 1 3\n1 5 5 -2\n2 4 5", "output": "1\n5\n2"}],
            reference_solution=(
                "class LazySegTree:\n"
                "    def __init__(self, arr: list[int]) -> None:\n"
                "        self.n = 1\n"
                "        while self.n < len(arr):\n"
                "            self.n <<= 1\n"
                "        self.data = [10 ** 18] * (2 * self.n)\n"
                "        self.lazy = [0] * (2 * self.n)\n"
                "        for i, value in enumerate(arr):\n"
                "            self.data[self.n + i] = value\n"
                "        for i in range(self.n - 1, 0, -1):\n"
                "            self.data[i] = min(self.data[i * 2], self.data[i * 2 + 1])\n\n"
                "    def _push(self, idx: int) -> None:\n"
                "        if self.lazy[idx] == 0:\n"
                "            return\n"
                "        for child in (idx * 2, idx * 2 + 1):\n"
                "            self.data[child] += self.lazy[idx]\n"
                "            self.lazy[child] += self.lazy[idx]\n"
                "        self.lazy[idx] = 0\n\n"
                "    def _range_add(self, left: int, right: int, value: int, idx: int, seg_l: int, seg_r: int) -> None:\n"
                "        if right < seg_l or seg_r < left:\n"
                "            return\n"
                "        if left <= seg_l and seg_r <= right:\n"
                "            self.data[idx] += value\n"
                "            self.lazy[idx] += value\n"
                "            return\n"
                "        self._push(idx)\n"
                "        mid = (seg_l + seg_r) // 2\n"
                "        self._range_add(left, right, value, idx * 2, seg_l, mid)\n"
                "        self._range_add(left, right, value, idx * 2 + 1, mid + 1, seg_r)\n"
                "        self.data[idx] = min(self.data[idx * 2], self.data[idx * 2 + 1])\n\n"
                "    def range_add(self, left: int, right: int, value: int) -> None:\n"
                "        self._range_add(left, right, value, 1, 0, self.n - 1)\n\n"
                "    def _range_min(self, left: int, right: int, idx: int, seg_l: int, seg_r: int) -> int:\n"
                "        if right < seg_l or seg_r < left:\n"
                "            return 10 ** 18\n"
                "        if left <= seg_l and seg_r <= right:\n"
                "            return self.data[idx]\n"
                "        self._push(idx)\n"
                "        mid = (seg_l + seg_r) // 2\n"
                "        return min(\n"
                "            self._range_min(left, right, idx * 2, seg_l, mid),\n"
                "            self._range_min(left, right, idx * 2 + 1, mid + 1, seg_r),\n"
                "        )\n\n"
                "    def range_min(self, left: int, right: int) -> int:\n"
                "        return self._range_min(left, right, 1, 0, self.n - 1)\n\n"
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n, q = map(int, input().split())\n"
                "    a = list(map(int, input().split()))\n"
                "    seg = LazySegTree(a)\n"
                "    out = []\n"
                "    for _ in range(q):\n"
                "        parts = list(map(int, input().split()))\n"
                "        if parts[0] == 1:\n"
                "            _, l, r, x = parts\n"
                "            seg.range_add(l - 1, r - 1, x)\n"
                "        else:\n"
                "            _, l, r = parts\n"
                "            out.append(str(seg.range_min(l - 1, r - 1)))\n"
                "    sys.stdout.write('\\n'.join(out))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if "Fenwick木" in key or "BIT/Fenwick木" in key:
        return array_template(
            statement=(
                "長さ N の整数列 A と Q 個の操作が与えられる。"
                " `1 i x` は A_i に x を加算し、`2 l r` は区間 [l, r] の総和を求めよ。"
            ),
            input_format="1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に操作。",
            output_format="type=2 のたびに区間和を 1 行ずつ出力する。",
            constraints="1 <= N, Q <= 2 * 10^5\n|Ai|, |x| <= 10^9",
            examples=[{"input": "5 4\n1 2 3 4 5\n2 2 4\n1 3 10\n2 1 3\n2 3 5", "output": "9\n16\n22"}],
            reference_solution=(
                "class Fenwick:\n"
                "    def __init__(self, n: int) -> None:\n"
                "        self.n = n\n"
                "        self.data = [0] * (n + 1)\n\n"
                "    def add(self, idx: int, value: int) -> None:\n"
                "        while idx <= self.n:\n"
                "            self.data[idx] += value\n"
                "            idx += idx & -idx\n\n"
                "    def sum(self, idx: int) -> int:\n"
                "        total = 0\n"
                "        while idx > 0:\n"
                "            total += self.data[idx]\n"
                "            idx -= idx & -idx\n"
                "        return total\n\n"
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n, q = map(int, input().split())\n"
                "    a = list(map(int, input().split()))\n"
                "    bit = Fenwick(n)\n"
                "    for i, value in enumerate(a, start=1):\n"
                "        bit.add(i, value)\n"
                "    out = []\n"
                "    for _ in range(q):\n"
                "        parts = list(map(int, input().split()))\n"
                "        if parts[0] == 1:\n"
                "            _, i, x = parts\n"
                "            bit.add(i, x)\n"
                "        else:\n"
                "            _, l, r = parts\n"
                "            out.append(str(bit.sum(r) - bit.sum(l - 1)))\n"
                "    sys.stdout.write('\\n'.join(out))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if "スパーステーブル" in key or "RMQ" in key:
        return array_template(
            statement="長さ N の整数列 A と Q 個の区間 [L, R] が与えられる。前処理を行い、各区間の最小値を求めよ。",
            input_format="1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に L R。",
            output_format="各問い合わせの最小値を 1 行ずつ出力する。",
            constraints="1 <= N, Q <= 2 * 10^5",
            examples=[{"input": "5 3\n5 2 8 1 4\n1 3\n2 5\n4 4", "output": "2\n1\n1"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n, q = map(int, input().split())\n"
                "    a = list(map(int, input().split()))\n"
                "    log = [0] * (n + 1)\n"
                "    for i in range(2, n + 1):\n"
                "        log[i] = log[i // 2] + 1\n"
                "    st = [a[:]]\n"
                "    j = 1\n"
                "    while (1 << j) <= n:\n"
                "        prev = st[-1]\n"
                "        width = 1 << j\n"
                "        half = width >> 1\n"
                "        row = [0] * (n - width + 1)\n"
                "        for i in range(n - width + 1):\n"
                "            row[i] = min(prev[i], prev[i + half])\n"
                "        st.append(row)\n"
                "        j += 1\n"
                "    out = []\n"
                "    for _ in range(q):\n"
                "        l, r = map(int, input().split())\n"
                "        l -= 1\n"
                "        r -= 1\n"
                "        length = r - l + 1\n"
                "        j = log[length]\n"
                "        out.append(str(min(st[j][l], st[j][r - (1 << j) + 1])))\n"
                "    sys.stdout.write('\\n'.join(out))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if "セグメント木" in key:
        return array_template(
            statement=(
                "長さ N の整数列 A と Q 個の操作が与えられる。"
                " `1 i x` は A_i を x に更新し、`2 l r` は区間 [l, r] の最小値を求めよ。"
            ),
            input_format="1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に操作。",
            output_format="type=2 のたびに区間最小値を 1 行ずつ出力する。",
            constraints="1 <= N, Q <= 2 * 10^5",
            examples=[{"input": "5 4\n5 2 8 1 4\n2 1 5\n1 3 0\n2 2 4\n2 3 3", "output": "1\n0\n0"}],
            reference_solution=(
                "class SegTree:\n"
                "    def __init__(self, arr: list[int]) -> None:\n"
                "        self.n = 1\n"
                "        while self.n < len(arr):\n"
                "            self.n <<= 1\n"
                "        self.data = [10 ** 18] * (2 * self.n)\n"
                "        for i, value in enumerate(arr):\n"
                "            self.data[self.n + i] = value\n"
                "        for i in range(self.n - 1, 0, -1):\n"
                "            self.data[i] = min(self.data[i * 2], self.data[i * 2 + 1])\n"
                "    def update(self, idx: int, value: int) -> None:\n"
                "        idx += self.n\n"
                "        self.data[idx] = value\n"
                "        idx >>= 1\n"
                "        while idx:\n"
                "            self.data[idx] = min(self.data[idx * 2], self.data[idx * 2 + 1])\n"
                "            idx >>= 1\n\n"
                "    def query(self, left: int, right: int) -> int:\n"
                "        left += self.n\n"
                "        right += self.n\n"
                "        ans = 10 ** 18\n"
                "        while left <= right:\n"
                "            if left & 1:\n"
                "                ans = min(ans, self.data[left]); left += 1\n"
                "            if not (right & 1):\n"
                "                ans = min(ans, self.data[right]); right -= 1\n"
                "            left >>= 1\n"
                "            right >>= 1\n"
                "        return ans\n\n"
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n, q = map(int, input().split())\n"
                "    a = list(map(int, input().split()))\n"
                "    seg = SegTree(a)\n"
                "    out = []\n"
                "    for _ in range(q):\n"
                "        parts = list(map(int, input().split()))\n"
                "        if parts[0] == 1:\n"
                "            _, i, x = parts\n"
                "            seg.update(i - 1, x)\n"
                "        else:\n"
                "            _, l, r = parts\n"
                "            out.append(str(seg.query(l - 1, r - 1)))\n"
                "    sys.stdout.write('\\n'.join(out))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    return None

