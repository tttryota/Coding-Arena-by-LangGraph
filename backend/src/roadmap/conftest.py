from __future__ import annotations

import sys
from pathlib import Path

_SRC_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT_STR = str(_SRC_ROOT)

if _SRC_ROOT_STR not in sys.path:
    sys.path.insert(0, _SRC_ROOT_STR)
