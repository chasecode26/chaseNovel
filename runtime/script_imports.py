from __future__ import annotations

import sys
from pathlib import Path


def ensure_scripts_on_path() -> Path:
    runtime_root = Path(__file__).resolve().parent.parent
    scripts_root = runtime_root / "scripts"
    scripts_path = str(scripts_root)
    if scripts_path not in sys.path:
        sys.path.insert(0, scripts_path)
    return scripts_root
