from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
for path in (PROJECT_ROOT, PROJECT_ROOT / "src", PROJECT_ROOT / "app"):
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)
