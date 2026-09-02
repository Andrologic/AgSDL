#!/usr/bin/env bash
set -euo pipefail

required_files=(
  README.md
  AGENTS.md
  CONTRIBUTING.md
  GOVERNANCE.md
  ROADMAP.md
  docs/scope.md
  spec/README.md
  proposals/README.md
)

for file in "${required_files[@]}"; do
  if [[ ! -s "$file" ]]; then
    echo "Missing or empty required file: $file" >&2
    exit 1
  fi
done

if command -v rg >/dev/null 2>&1; then
  if rg -n '[[:blank:]]+$' --glob '*.md' --glob '*.toml' --glob '*.yaml' .; then
    echo "Trailing whitespace found." >&2
    exit 1
  fi
fi

git diff --check
echo "AgSDL repository checks passed."
