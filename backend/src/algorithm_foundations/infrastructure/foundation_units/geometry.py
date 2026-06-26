"""Geometry family templates."""

from __future__ import annotations

from .common import ProblemTemplate, array_template


def build_problem_template(  # noqa: C901
    *,
    theme_id: str,
    key: str,
    category: str,
) -> ProblemTemplate | None:
    del key
    if theme_id == "algo-106":
        return array_template(
            statement="平面上の 2 ベクトル (ax, ay), (bx, by) が与えられる。内積と外積をこの順に出力せよ。",
            input_format="1 行目に ax ay bx by。",
            output_format="1 行に `dot cross` を出力する。",
            constraints="各値は整数",
            examples=[{"input": "1 2 3 4", "output": "11 -2"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    ax, ay, bx, by = map(int, input().split())\n"
                "    dot = ax * bx + ay * by\n"
                "    cross = ax * by - ay * bx\n"
                "    print(dot, cross)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-108":
        return array_template(
            statement="線分 AB と線分 CD が交差するなら Yes、そうでなければ No を出力せよ。",
            input_format="1 行目に ax ay bx by cx cy dx dy。",
            output_format="Yes / No を出力する。",
            constraints="座標は整数",
            examples=[{"input": "0 0 4 4 0 4 4 0", "output": "Yes"}],
            reference_solution=(
                "def ccw(ax: int, ay: int, bx: int, by: int, cx: int, cy: int) -> int:\n"
                "    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)\n\n"
                "def solve() -> None:\n"
                "    ax, ay, bx, by, cx, cy, dx, dy = map(int, input().split())\n"
                "    c1 = ccw(ax, ay, bx, by, cx, cy)\n"
                "    c2 = ccw(ax, ay, bx, by, dx, dy)\n"
                "    c3 = ccw(cx, cy, dx, dy, ax, ay)\n"
                "    c4 = ccw(cx, cy, dx, dy, bx, by)\n"
                "    print('Yes' if c1 * c2 <= 0 and c3 * c4 <= 0 else 'No')\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-107":
        return array_template(
            statement="平面上の N 点が与えられる。凸包に含まれる点数を求めよ。",
            input_format="1 行目に N。\n続く N 行に xi yi。",
            output_format="凸包上の点数を出力する。",
            constraints="3 <= N <= 2 * 10^5\n座標は整数",
            examples=[{"input": "5\n0 0\n2 0\n2 2\n0 2\n1 1", "output": "4"}],
            reference_solution=(
                "def cross(o: tuple[int, int], a: tuple[int, int], b: tuple[int, int]) -> int:\n"
                "    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])\n\n"
                "def solve() -> None:\n"
                "    n = int(input())\n"
                "    pts = sorted({tuple(map(int, input().split())) for _ in range(n)})\n"
                "    if len(pts) <= 1:\n"
                "        print(len(pts))\n"
                "        return\n"
                "    lower = []\n"
                "    for p in pts:\n"
                "        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:\n"
                "            lower.pop()\n"
                "        lower.append(p)\n"
                "    upper = []\n"
                "    for p in reversed(pts):\n"
                "        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:\n"
                "            upper.pop()\n"
                "        upper.append(p)\n"
                "    hull = lower[:-1] + upper[:-1]\n"
                "    print(len(hull))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-109":
        return array_template(
            statement="点 P と直線 AB が与えられる。P から直線 AB への距離を求めよ。",
            input_format="1 行目に px py ax ay bx by。",
            output_format="距離を出力する。",
            constraints="座標は整数",
            examples=[{"input": "0 2 -1 0 1 0", "output": "2.0"}],
            reference_solution=(
                "import math\n\n"
                "def solve() -> None:\n"
                "    px, py, ax, ay, bx, by = map(int, input().split())\n"
                "    cross = abs((bx - ax) * (py - ay) - (by - ay) * (px - ax))\n"
                "    length = math.hypot(bx - ax, by - ay)\n"
                "    print(cross / length)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-110":
        return array_template(
            statement="頂点が順に与えられる多角形の面積を求めよ。",
            input_format="1 行目に N。\n続く N 行に xi yi。",
            output_format="面積を出力する。",
            constraints="3 <= N <= 2 * 10^5\n座標は整数",
            examples=[{"input": "4\n0 0\n2 0\n2 1\n0 1", "output": "2.0"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    n = int(input())\n"
                "    points = [tuple(map(int, input().split())) for _ in range(n)]\n"
                "    total = 0\n"
                "    for i in range(n):\n"
                "        x1, y1 = points[i]\n"
                "        x2, y2 = points[(i + 1) % n]\n"
                "        total += x1 * y2 - y1 * x2\n"
                "    print(abs(total) / 2)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-111":
        return array_template(
            statement="多角形と点 P が与えられる。P が多角形の内部または辺上なら Yes、外部なら No を出力せよ。",
            input_format="1 行目に N。\n続く N 行に xi yi。\n最後に px py。",
            output_format="Yes / No を出力する。",
            constraints="3 <= N <= 2 * 10^5\n座標は整数",
            examples=[{"input": "4\n0 0\n4 0\n4 4\n0 4\n2 2", "output": "Yes"}],
            reference_solution=(
                "def on_segment(ax: int, ay: int, bx: int, by: int, px: int, py: int) -> bool:\n"
                "    cross = (bx - ax) * (py - ay) - (by - ay) * (px - ax)\n"
                "    if cross != 0:\n"
                "        return False\n"
                "    return min(ax, bx) <= px <= max(ax, bx) and min(ay, by) <= py <= max(ay, by)\n\n"
                "def solve() -> None:\n"
                "    n = int(input())\n"
                "    pts = [tuple(map(int, input().split())) for _ in range(n)]\n"
                "    px, py = map(int, input().split())\n"
                "    inside = False\n"
                "    for i in range(n):\n"
                "        ax, ay = pts[i]\n"
                "        bx, by = pts[(i + 1) % n]\n"
                "        if on_segment(ax, ay, bx, by, px, py):\n"
                "            print('Yes')\n"
                "            return\n"
                "        if ((ay > py) != (by > py)):\n"
                "            x = (bx - ax) * (py - ay) / (by - ay) + ax\n"
                "            if x >= px:\n"
                "                inside = not inside\n"
                "    print('Yes' if inside else 'No')\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-112":
        return array_template(
            statement="直線 AB と直線 CD が平行なら Parallel、そうでなければ Intersect を出力せよ。",
            input_format="1 行目に ax ay bx by cx cy dx dy。",
            output_format="Parallel または Intersect を出力する。",
            constraints="座標は整数",
            examples=[{"input": "0 0 1 1 0 1 1 2", "output": "Parallel"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    ax, ay, bx, by, cx, cy, dx, dy = map(int, input().split())\n"
                "    cross = (bx - ax) * (dy - cy) - (by - ay) * (dx - cx)\n"
                "    print('Parallel' if cross == 0 else 'Intersect')\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-113":
        return array_template(
            statement=(
                "点 (x, y) と Q 個の操作が与えられる。"
                " `T dx dy` は平行移動、`R` は原点まわりに 90 度反時計回り回転とする。"
                " すべて適用した後の座標を出力せよ。"
            ),
            input_format="1 行目に x y。\n2 行目に Q。\n続く Q 行に操作。",
            output_format="最終座標を `x y` で出力する。",
            constraints="1 <= Q <= 2 * 10^5\n座標は整数",
            examples=[{"input": "1 2\n3\nT 1 0\nR\nT 0 -1", "output": "-2 1"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    x, y = map(int, input().split())\n"
                "    q = int(input())\n"
                "    for _ in range(q):\n"
                "        parts = input().split()\n"
                "        if parts[0] == 'T':\n"
                "            x += int(parts[1])\n"
                "            y += int(parts[2])\n"
                "        else:\n"
                "            x, y = -y, x\n"
                "    print(x, y)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-114":
        return array_template(
            statement="円の中心 C と半径 r、直線 AB が与えられる。交点の個数を 0, 1, 2 のいずれかで出力せよ。",
            input_format="1 行目に cx cy r ax ay bx by。",
            output_format="交点の個数を出力する。",
            constraints="座標と半径は整数",
            examples=[{"input": "0 0 5 -10 0 10 0", "output": "2"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    import math\n"
                "    cx, cy, r, ax, ay, bx, by = map(int, input().split())\n"
                "    cross = abs((bx - ax) * (cy - ay) - (by - ay) * (cx - ax))\n"
                "    length = math.hypot(bx - ax, by - ay)\n"
                "    dist = cross / length\n"
                "    if dist > r:\n"
                "        print(0)\n"
                "    elif abs(dist - r) < 1e-9:\n"
                "        print(1)\n"
                "    else:\n"
                "        print(2)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if category == "幾何":
        return array_template(
            statement="平面上の 3 点 A, B, C が与えられる。ベクトル AB と AC の外積を求めよ。",
            input_format="1 行目に ax ay bx by cx cy。",
            output_format="外積の値を出力する。",
            constraints="座標は整数",
            examples=[{"input": "0 0 1 0 0 1", "output": "1"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    ax, ay, bx, by, cx, cy = map(int, input().split())\n"
                "    abx, aby = bx - ax, by - ay\n"
                "    acx, acy = cx - ax, cy - ay\n"
                "    print(abx * acy - aby * acx)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    return None
