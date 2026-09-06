#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 [--compare | --help]"
  echo "Default: run Python and Node.js reader tests."
  echo "--compare: compare the full corpus; print results and remove temporary reports."
}

if [[ $# -gt 1 ]]; then
  usage >&2
  exit 2
fi
case "${1:-}" in
  --help) usage; exit 0 ;;
  ''|--compare) ;;
  *) usage >&2; exit 2 ;;
esac

for reader_tool in python3 node; do
  if ! command -v "$reader_tool" >/dev/null 2>&1; then
    echo "$reader_tool is required for experimental reader checks." >&2
    exit 2
  fi
done

cd "$(dirname "${BASH_SOURCE[0]}")/.."
export PYTHONDONTWRITEBYTECODE=1

if [[ ${1:-} != --compare ]]; then
  python3 -m unittest discover -s experimental/readers/python -v
  node --test experimental/readers/javascript/reader.test.mjs
  exit 0
fi

if ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 9))'; then
  echo "Python 3.9 or newer is required for the comparison command." >&2
  exit 2
fi

reader_reports=$(mktemp -d "${TMPDIR:-/tmp}/agsdl-reader-comparison.XXXXXX")
trap 'rm -rf -- "$reader_reports"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
reader_exit=0
python3 experimental/candidate-2/compare-readers.py \
  --reader '["python", "python3", "experimental/readers/python/cli.py"]' \
  --reader '["javascript", "node", "experimental/readers/javascript/cli.mjs"]' \
  --reports "$reader_reports" || reader_exit=$?
exit "$reader_exit"
