from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-108-basic',
    title='線分の交差判定 の基本',
    unit_kind='foundation',
    target_skill='線分の交差判定 の基本',
    concept_overview='線分どうしの交差は、各端点が相手の線分の左右どちらにあるかを外積の符号で比べると判定できます。まずは端点の接触や重なりを除いた、内部どうしの交差だけを判定します。',
    problem_bank=[
        problem(
            problem_id='algo-108-basic-p1',
            title='線分の交差判定 の基本 / 2 本の線分の内部どうしが交差するかを判定する',
            problem_statement='線分 AB と線分 CD が与えられる。2 本の線分の内部どうしが交差するなら Yes、そうでなければ No を出力せよ。端点で接するだけ、または一直線上で重なるだけの場合は No とする。',
            input_format='1 行目に ax ay bx by cx cy dx dy。',
            output_format='Yes / No を出力する。',
            constraints='-10^9 <= 座標 <= 10^9\nA != B\nC != D',
            examples=[{'input': '0 0 4 0 4 0 4 3', 'output': 'No'}],
            canonical_reference_solution="def cross(ax: int, ay: int, bx: int, by: int, cx: int, cy: int) -> int:\n    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)\n\n\ndef solve() -> None:\n    ax, ay, bx, by, cx, cy, dx, dy = map(int, input().split())\n    c1 = cross(ax, ay, bx, by, cx, cy)\n    c2 = cross(ax, ay, bx, by, dx, dy)\n    c3 = cross(cx, cy, dx, dy, ax, ay)\n    c4 = cross(cx, cy, dx, dy, bx, by)\n    print('Yes' if c1 * c2 < 0 and c3 * c4 < 0 else 'No')\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
