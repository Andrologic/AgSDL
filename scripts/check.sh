#!/usr/bin/env bash
set -euo pipefail

required_files=(
  README.md
  AGENTS.md
  CONTRIBUTING.md
  GOVERNANCE.md
  LICENSE
  ROADMAP.md
  docs/decisions/0002-version-0.0.1.md
  docs/scope.md
  examples/README.md
  spec/README.md
  proposals/README.md
  docs/research/a2a-v1.0.1.sha256
  scripts/verify-a2a-1.0.1-sources.sh
  scripts/test-verify-a2a-1.0.1-sources.sh
  scripts/check-markdown-links.py
  scripts/test-check-markdown-links.py
)

for file in "${required_files[@]}"; do
  if [[ ! -s "$file" ]]; then
    echo "Missing or empty required file: $file" >&2
    exit 1
  fi
done

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required for repository checks." >&2
  exit 1
fi

if command -v rg >/dev/null 2>&1; then
  if rg -n '[[:blank:]]+$' --glob '*.md' --glob '*.toml' --glob '*.yaml' .; then
    echo "Trailing whitespace found." >&2
    exit 1
  fi
fi

git diff --check
bash -n scripts/verify-a2a-1.0.1-sources.sh
bash -n scripts/test-verify-a2a-1.0.1-sources.sh
./scripts/test-verify-a2a-1.0.1-sources.sh
python3 scripts/test-check-markdown-links.py
python3 scripts/check-markdown-links.py
python3 experimental/candidate-2/check-fixtures.py
python3 experimental/candidate-2/test-compare-readers.py
echo "AgSDL repository checks passed."
