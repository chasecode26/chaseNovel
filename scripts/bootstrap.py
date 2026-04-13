#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    script_path = Path(__file__).with_name("project_bootstrap.py")
    completed = subprocess.run([sys.executable, str(script_path), *sys.argv[1:]])
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
