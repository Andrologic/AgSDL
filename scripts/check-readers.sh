#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 [--compare [candidate-2|modular] | --help]"
  echo "Default: run the Python and Node.js tests for both experimental editions."
  echo "--compare: compare both full corpora and remove temporary reports."
  echo "--compare candidate-2|modular: compare only the selected corpus."
}

if [[ $# -gt 2 ]]; then
  usage >&2
  exit 2
fi

reader_mode=tests
comparison_scope=all
case "${1:-}" in
  --help)
    [[ $# -eq 1 ]] || { usage >&2; exit 2; }
    usage
    exit 0
    ;;
  --compare)
    reader_mode=compare
    comparison_scope=${2:-all}
    case "$comparison_scope" in
      all|candidate-2|modular) ;;
      *) usage >&2; exit 2 ;;
    esac
    ;;
  '')
    [[ $# -eq 0 ]] || { usage >&2; exit 2; }
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac

for reader_tool in python3 node; do
  if ! command -v "$reader_tool" >/dev/null 2>&1; then
    echo "$reader_tool is required for experimental reader checks." >&2
    exit 2
  fi
done

cd "$(dirname "${BASH_SOURCE[0]}")/.."
export PYTHONDONTWRITEBYTECODE=1

if [[ $reader_mode == tests ]]; then
  python3 -m unittest discover -s experimental/readers/python -v
  python3 -m unittest discover -s experimental/modular-candidate-1/readers/python -v
  node --test experimental/readers/javascript/reader.test.mjs
  node --test experimental/modular-candidate-1/readers/javascript/reader.test.mjs
  exit 0
fi

if ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 9))'; then
  echo "Python 3.9 or newer is required for the comparison command." >&2
  exit 2
fi

reader_reports=$(mktemp -d "${TMPDIR:-/tmp}/agsdl-reader-comparisons.XXXXXX")
trap 'rm -rf -- "$reader_reports"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

comparison_exit=0
if [[ $comparison_scope == all || $comparison_scope == candidate-2 ]]; then
  candidate_reports="$reader_reports/candidate-2"
  mkdir "$candidate_reports"
  echo "Comparing the candidate-2 corpus."
  candidate_exit=0
  python3 experimental/candidate-2/compare-readers.py \
    --reader '["python", "python3", "experimental/readers/python/cli.py"]' \
    --reader '["javascript", "node", "experimental/readers/javascript/cli.mjs"]' \
    --reports "$candidate_reports" || candidate_exit=$?
  if [[ $candidate_exit -ne 0 && $comparison_exit -eq 0 ]]; then
    comparison_exit=$candidate_exit
  fi
fi

if [[ $comparison_scope == all || $comparison_scope == modular ]]; then
  modular_reports="$reader_reports/modular"
  mkdir "$modular_reports"
  echo "Comparing the modular candidate-1 corpus."
  modular_exit=0
  python3 experimental/modular-candidate-1/compare-readers.py \
    --reader '["python", "python3", "experimental/modular-candidate-1/readers/python/cli.py"]' \
    --reader '["javascript", "node", "experimental/modular-candidate-1/readers/javascript/cli.mjs"]' \
    --reports "$modular_reports" || modular_exit=$?
  if [[ $modular_exit -ne 0 && $comparison_exit -eq 0 ]]; then
    comparison_exit=$modular_exit
  fi
fi

exit "$comparison_exit"
