#!/usr/bin/env python3
"""Pre-commit guard: refuse to commit real data files.

A belt-and-suspenders backstop behind .gitignore: blocks any staged
.parquet/.csv/.xlsx/.xls outside examples/, so a real dataset can never
enter git history even if force-added with `git add -f`.
"""

import sys
from pathlib import Path

BLOCKED_SUFFIXES = {".parquet", ".csv", ".xlsx", ".xls"}
ALLOWED_PREFIX = "examples/"


def main(paths) -> int:
    blocked = [
        p for p in paths
        if Path(p).suffix.lower() in BLOCKED_SUFFIXES
        and not p.replace("\\", "/").startswith(ALLOWED_PREFIX)
    ]
    if blocked:
        print("BLOCKED: refusing to commit data files. Real data must never "
              "enter git. Unstage them, or place demo data under examples/:")
        for b in blocked:
            print(f"  - {b}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
