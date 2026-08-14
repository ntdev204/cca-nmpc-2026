from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
for _path in (PROJECT_ROOT / "src", PROJECT_ROOT / "scripts" / "python"):
    _text = str(_path)
    if _text not in sys.path:
        sys.path.insert(0, _text)
