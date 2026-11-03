#!/usr/bin/env bash
# Repository checks. Requires Python 3.9 or newer and its standard library only.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONDONTWRITEBYTECODE=1

python3 scripts/test-check-trailing-whitespace.py
python3 scripts/check-trailing-whitespace.py
python3 scripts/test-check-markdown-links.py
python3 scripts/check-markdown-links.py
if command -v git >/dev/null 2>&1 && git rev-parse --git-dir >/dev/null 2>&1; then
  git diff --check
fi
python3 -m unittest discover -s tooling/tests
(cd tooling && python3 -m agsdl ../examples/*.json >/dev/null)
echo "AgSDL repository checks passed."
