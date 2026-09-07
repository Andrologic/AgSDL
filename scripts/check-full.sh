#!/usr/bin/env bash
# Full local/CI verification with retained logs and comparator responses.
set -uo pipefail
if [[ $# -ne 1 ]]; then
  echo "Usage: $0 NEW_EVIDENCE_DIRECTORY" >&2
  exit 2
fi
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$1" || exit 2
verification_reports=$(cd "$1" && pwd) || exit 2
if [[ -n $(ls -A "$verification_reports") ]]; then
  echo "Evidence directory must be empty: $verification_reports" >&2
  exit 2
fi
python3 - "$verification_reports/revision.json" <<'PYTHON'
import hashlib, json, platform, subprocess, sys
from pathlib import Path
metadata = {
    'python': platform.python_version(),
    'manifestSha256': hashlib.sha256(Path('conformance/fixtures/manifest.json').read_bytes()).hexdigest(),
}
if Path('.git').exists():
    metadata['sha'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    metadata['status'] = subprocess.check_output(['git', 'status', '--short'], text=True)
else:
    metadata['sha'] = None
    metadata['status'] = 'Archive without Git; revision not independently established'
Path(sys.argv[1]).write_text(json.dumps(metadata, indent=2) + '\n')
PYTHON
if [[ $? -ne 0 ]]; then exit 2; fi
verification_exit=0
run_check() {
  local name=$1
  shift
  "$@" 2>&1 | tee "$verification_reports/$name.log"
  local pipeline_status=("${PIPESTATUS[@]}")
  local result=0
  if [[ ${pipeline_status[0]} -ne 0 || ${pipeline_status[1]} -ne 0 ]]; then result=1; fi
  printf '%s %s\n' "$name" "$result" >> "$verification_reports/status.txt"
  if [[ $result -ne 0 ]]; then verification_exit=1; fi
}
run_check repository ./scripts/check.sh
run_check readers ./scripts/check-readers.sh
run_check comparisons env AGSDL_REPORTS_DIR="$verification_reports/comparisons" ./scripts/check-readers.sh --compare
run_check corpus-schemas python3 conformance/check-corpus.py --jsonschema
run_check report-schemas python3 scripts/check-report-schemas.py "$verification_reports/comparisons/official-0.1.0"
run_check examples python3 scripts/check-examples.py --jsonschema
exit "$verification_exit"
