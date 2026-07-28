"""Import shim so ``python -m evaluation.cli`` works from the backend root."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
_SOURCE_PACKAGE = _SRC / "evaluation"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
__path__.append(str(_SOURCE_PACKAGE))
