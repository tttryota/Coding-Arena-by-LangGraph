from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-114-practice',
    title='円と直線の交点 を素直に実装する',
    unit_kind='foundation',
    target_skill='円と直線の交点 を素直に実装する',
    concept_overview='円と直線の交点では、中心から直線への射影点を基準にすると交点座標を復元できます。交点数の判定に加えて、接点・2 交点を同じ式で扱う実装まで進めて、距離判定を座標計算へつなげます。',
    problem_bank=[
        problem(
            problem_id='algo-114-practice-p1',
            title='円と直線の交点 を素直に実装する / 交点の座標を求めよ',
            problem_statement='円の中心 C と半径 r、直線 AB が与えられる。円と直線 AB の交点をすべて求めよ。交点が 2 個あるときは、直線上を A から B へ進む向きで先に現れる点を先に出力せよ。交点が 1 個ならその 1 点だけを出力し、交点がないなら `NA` を出力せよ。',
            input_format='1 行目に cx cy r ax ay bx by。',
            output_format='交点が 2 個あるときは 1 行ずつ `x y` を出力する。交点が 1 個なら 1 行だけ `x y` を出力する。誤差は絶対誤差または相対誤差 10^-6 まで許容する。交点がないなら `NA` を出力する。',
            constraints='座標と半径は整数\nA と B は異なる点',
            examples=[{'input': '0 0 5 -10 0 10 0', 'output': '-5.0000000000 0.0000000000\n5.0000000000 0.0000000000'}],
            canonical_reference_solution="def solve() -> None:\n    import math\n\n    cx, cy, r, ax, ay, bx, by = map(int, input().split())\n    dx = bx - ax\n    dy = by - ay\n    length2 = dx * dx + dy * dy\n    t = ((cx - ax) * dx + (cy - ay) * dy) / length2\n    px = ax + t * dx\n    py = ay + t * dy\n    dist2 = (px - cx) * (px - cx) + (py - cy) * (py - cy)\n    eps = 1e-9\n    if dist2 > r * r + eps:\n        print('NA')\n        return\n    offset = math.sqrt(max(r * r - dist2, 0.0))\n    length = math.sqrt(length2)\n    ux = dx / length\n    uy = dy / length\n    if offset < eps:\n        print(f'{px:.10f} {py:.10f}')\n        return\n    x1 = px - ux * offset\n    y1 = py - uy * offset\n    x2 = px + ux * offset\n    y2 = py + uy * offset\n    print(f'{x1:.10f} {y1:.10f}')\n    print(f'{x2:.10f} {y2:.10f}')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
