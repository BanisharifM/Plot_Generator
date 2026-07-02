#!/usr/bin/env bash
# Install real-data leak guards into a git repo:
#   - .gitignore rules for every data shape (keeps examples/)
#   - .pre-commit-config.yaml (gitleaks + a data-file blocker)
#   - scripts/check_no_data.py (refuses staged data files)
# Usage:  bash install_data_guards.sh [TARGET_REPO_DIR]   (default: cwd)
set -euo pipefail
TARGET="${1:-$PWD}"
cd "$TARGET"
[ -d .git ] || { echo "ERROR: $TARGET is not a git repo"; exit 1; }

if ! grep -q "Real data guard" .gitignore 2>/dev/null; then
cat >> .gitignore <<'GI'

# --- Real data guard ---
*.parquet
*.csv
*.xlsx
*.xls
data/
Plaid/
plaid_*/
!examples/**
GI
fi

cat > .pre-commit-config.yaml <<'PC'
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks
  - repo: local
    hooks:
      - id: block-data-files
        name: block real data files
        entry: python scripts/check_no_data.py
        language: system
        pass_filenames: true
PC

mkdir -p scripts
cat > scripts/check_no_data.py <<'PY'
#!/usr/bin/env python3
"""Refuse to commit real data files (belt-and-suspenders behind .gitignore)."""
import sys
from pathlib import Path
BLOCKED = {".parquet", ".csv", ".xlsx", ".xls"}
def main(paths):
    bad = [p for p in paths if Path(p).suffix.lower() in BLOCKED
           and not p.replace("\\", "/").startswith("examples/")]
    if bad:
        print("BLOCKED: real data must never enter git. Unstage:")
        for b in bad:
            print(f"  - {b}")
        return 1
    return 0
if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
PY
chmod +x scripts/check_no_data.py
echo "Guards installed in $TARGET"
echo "Next: pre-commit install ; then audit history (see the steps you were given)"
