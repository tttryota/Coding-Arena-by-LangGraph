from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-111-practice',
    title='点の多角形内包判定 を素直に実装する',
    unit_kind='foundation',
    target_skill='点の多角形内包判定 を素直に実装する',
    concept_overview='1 点の内包判定ができたら、同じ凸多角形に対する複数の点問い合わせも同じ外積判定を繰り返して処理できます。ここでは basic と同じ判定を複数回まわし、辺上判定を含めて安定に実装する練習に広げます。',
    problem_bank=[
        problem(
            problem_id='algo-111-practice-p1',
            title='点の多角形内包判定 を素直に実装する / 凸多角形に対する複数の点問い合わせを処理する',
            problem_statement='反時計回り順に頂点が与えられる凸多角形と Q 個の点が与えられる。各点について、内部または辺上なら Yes、外部なら No を出力せよ。',
            input_format='1 行目に N Q。\n続く N 行に xi yi。\n続く Q 行に px py。',
            output_format='各問い合わせについて Yes / No を 1 行ずつ出力する。',
            constraints='3 <= N <= 2000\n1 <= Q <= 2000\n-10^9 <= x_i, y_i, p_x, p_y <= 10^9\n多角形は反時計回り順の凸多角形',
            examples=[{'input': '4 4\n0 0\n4 0\n4 4\n0 4\n2 2\n5 1\n4 2\n0 0', 'output': 'Yes\nNo\nYes\nYes'}],
            canonical_reference_solution="def cross(ax: int, ay: int, bx: int, by: int, cx: int, cy: int) -> int:\n    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)\n\n\ndef on_segment(ax: int, ay: int, bx: int, by: int, px: int, py: int) -> bool:\n    if cross(ax, ay, bx, by, px, py) != 0:\n        return False\n    return min(ax, bx) <= px <= max(ax, bx) and min(ay, by) <= py <= max(ay, by)\n\n\ndef contains(points: list[tuple[int, int]], px: int, py: int) -> bool:\n    n = len(points)\n    sign = 0\n    for i in range(n):\n        ax, ay = points[i]\n        bx, by = points[(i + 1) % n]\n        if on_segment(ax, ay, bx, by, px, py):\n            return True\n        value = cross(ax, ay, bx, by, px, py)\n        if value == 0:\n            continue\n        if sign == 0:\n            sign = 1 if value > 0 else -1\n        elif (value > 0) != (sign > 0):\n            return False\n    return True\n\n\ndef solve() -> None:\n    import sys\n\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    points = [tuple(map(int, input().split())) for _ in range(n)]\n    out = []\n    for _ in range(q):\n        px, py = map(int, input().split())\n        out.append('Yes' if contains(points, px, py) else 'No')\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-111-practice-p2',
            title='点の多角形内包判定 を素直に実装する / 凸性を使って各点を高速に内包判定する',
            problem_statement='反時計回り順に頂点が与えられる凸多角形と Q 個の点が与えられる。各点について、内部または辺上なら Yes、外部なら No を出力せよ。凸性を使って 1 点あたり高速に判定せよ。',
            input_format='1 行目に N Q。\n続く N 行に xi yi。\n続く Q 行に px py。',
            output_format='各問い合わせについて Yes / No を 1 行ずつ出力する。',
            constraints='3 <= N, Q <= 2 * 10^5\n-10^9 <= x_i, y_i, p_x, p_y <= 10^9\n多角形は反時計回り順の凸多角形',
            examples=[{'input': '4 5\n0 0\n4 0\n4 4\n0 4\n2 2\n5 1\n4 2\n0 0\n2 5', 'output': 'Yes\nNo\nYes\nYes\nNo'}],
            canonical_reference_solution="def cross(ax: int, ay: int, bx: int, by: int, cx: int, cy: int) -> int:\n    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)\n\n\ndef on_segment(ax: int, ay: int, bx: int, by: int, px: int, py: int) -> bool:\n    if cross(ax, ay, bx, by, px, py) != 0:\n        return False\n    return min(ax, bx) <= px <= max(ax, bx) and min(ay, by) <= py <= max(ay, by)\n\n\ndef in_triangle(a: tuple[int, int], b: tuple[int, int], c: tuple[int, int], p: tuple[int, int]) -> bool:\n    return (\n        cross(a[0], a[1], b[0], b[1], p[0], p[1]) >= 0\n        and cross(b[0], b[1], c[0], c[1], p[0], p[1]) >= 0\n        and cross(c[0], c[1], a[0], a[1], p[0], p[1]) >= 0\n    )\n\n\ndef contains(points: list[tuple[int, int]], p: tuple[int, int]) -> bool:\n    n = len(points)\n    if p == points[0]:\n        return True\n    first = cross(points[0][0], points[0][1], points[1][0], points[1][1], p[0], p[1])\n    last = cross(points[0][0], points[0][1], points[-1][0], points[-1][1], p[0], p[1])\n    if first < 0 or last > 0:\n        return False\n    if first == 0:\n        return on_segment(points[0][0], points[0][1], points[1][0], points[1][1], p[0], p[1])\n    if last == 0:\n        return on_segment(points[0][0], points[0][1], points[-1][0], points[-1][1], p[0], p[1])\n    left = 1\n    right = n - 1\n    while right - left > 1:\n        mid = (left + right) // 2\n        value = cross(points[0][0], points[0][1], points[mid][0], points[mid][1], p[0], p[1])\n        if value >= 0:\n            left = mid\n        else:\n            right = mid\n    return in_triangle(points[0], points[left], points[left + 1], p)\n\n\ndef solve() -> None:\n    import sys\n\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    points = [tuple(map(int, input().split())) for _ in range(n)]\n    out = []\n    for _ in range(q):\n        point = tuple(map(int, input().split()))\n        out.append('Yes' if contains(points, point) else 'No')\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
