# Try the experimental candidate

`proposal-0012-candidate-2` is an implementable experiment described in
[proposal 0012](../proposals/0012-minimal-0.1.0-contract.md), not an adopted
AgSDL specification. Version 0.0.2 is the published conceptual pre-draft;
0.1.0 has not been delivered. The Python and JavaScript readers are implemented
and reviewed within their documented scope. Their full report comparison passes all 121 corpus cases at the
[recorded source revision](../docs/reviews/0006-candidate-0.1.0-adoption.md#final-experimental-comparison),
with no blocked cases or mismatches. That evidence does not adopt the candidate
or prove exhaustive semantic correctness.

## Start with existing inputs

Use the [local invocation graph](candidate-2/fixtures/local-invocation-resolve.json)
and [custom runtime declaration](candidate-2/fixtures/runtime-custom-evidence-unknown.json).
These are readable fixtures with expectations in the
[corpus manifest](candidate-2/fixtures/manifest.json). The graph describes one
invocation and success/failure paths. The runtime fixture names a custom engine
and carries an unverified capability claim with an unknown evidence hash.
Neither fixture runs an agent or loads an engine.

The [D/G/R shape schemas](candidate-2/schemas/README.md) have separate inputs:
D checks the Document envelope, G the `graphs` value and selected payload shapes,
and R the `runtime` value. Schema acceptance alone does not validate identities,
references, graph paths, evidence or byte preservation. Use the proposal for
meaning and the readers for their covered static checks.

## Run both local readers

From the repository root, use Python 3 and Node.js with ES module support;
the reader READMEs describe their tested environments. No package installation, credentials or external engine is needed.
Create requests by encoding the fixture bytes, rather than reserializing them:

```sh
agsdl_demo_dir=$(mktemp -d)
python3 - "$agsdl_demo_dir" <<'PY'
import base64, json, sys
from pathlib import Path
fixtures = Path('experimental/candidate-2/fixtures')
output = Path(sys.argv[1])
for name, operation, filename in [
    ('graph', 'resolveG', 'local-invocation-resolve.json'),
    ('runtime', 'validateR', 'runtime-custom-evidence-unknown.json'),
    ('exchange', 'exchange', 'local-invocation-resolve.json'),
]:
    request = {'operation': operation,
               'primary': base64.b64encode((fixtures / filename).read_bytes()).decode(),
               'annexes': {}}
    (output / (name + '.request.json')).write_text(json.dumps(request))
PY
for sample in graph runtime exchange; do
  python3 experimental/readers/python/cli.py \
    < "$agsdl_demo_dir/$sample.request.json" > "$agsdl_demo_dir/$sample.python.response.json"
  node experimental/readers/javascript/cli.mjs \
    < "$agsdl_demo_dir/$sample.request.json" > "$agsdl_demo_dir/$sample.javascript.response.json"
done
```

Each response contains `report` and base64 `artifacts`. Read the separate Results
and verify that exchange returns the original graph bytes:

```sh
python3 - "$agsdl_demo_dir" <<'PY'
import base64, json, sys
from pathlib import Path
folder = Path(sys.argv[1])
original = Path('experimental/candidate-2/fixtures/local-invocation-resolve.json').read_bytes()
for path in sorted(folder.glob('*.response.json')):
    response = json.loads(path.read_text())
    print(path.name, [(r['unit'], r['phase'], r['verdict']) for r in response['report']['results']])
    if path.name.startswith('exchange.'):
        assert base64.b64decode(response['artifacts']['primary']) == original
PY
```

A successful CLI exit means a response was produced, not that validation passed.
Inspect each Result's unit, phase, findings and checks. `pass` covers only the
requested rules; `fail` records a covered violation; `unsupported` records required
interpretation that is unavailable; `inconclusive` records insufficient evidence
or blocked checks. Unknown hashes remain visible in inventory states. Excluded
checks are outside the operation, not successes. G/R also report their D
prerequisite separately.

R declares requirements and an optional engine selection. Engine identities are
open, including custom implementations, with no engine enum or default. An R
pass neither proves engine support nor evaluates a capability claim. Exact
exchange preserves bytes and accounts for supplied dependencies independently
of semantic validity; lossy exchange is refused by this edition.

## Automated reader checks

Run `./scripts/check-readers.sh` for both existing reader test suites, using
Python 3 and Node.js with `node --test` support. The general
`./scripts/check.sh` includes the Python suite and keeps its Python-only runtime
requirement.

Run `./scripts/check-readers.sh --compare` for the complete corpus comparison,
using Python 3.9 or newer and Node.js. This mode prints the summary, preserves
the comparator's exit code and cleans its temporary reports on exit. It does
not run the test suites. Discrepancies produce a nonzero exit; the command does
not convert known differences into success. Use the explicit commands below
when you need to retain raw reports.

## Compare reports, then inspect discrepancies

Reuse the temporary directory to compare just the two examples:

```sh
python3 experimental/candidate-2/compare-readers.py \
  --reader '["python", "python3", "experimental/readers/python/cli.py"]' \
  --reader '["javascript", "node", "experimental/readers/javascript/cli.mjs"]' \
  --case local-invocation-resolve --case runtime-custom-evidence-unknown \
  --reports "$agsdl_demo_dir/comparison"
```

A nonzero exit reports a failed assertion, invalid response or reader mismatch.
Read `summary.json` and the unchanged stdout/stderr files in that directory.
A rerun needs a new or empty reports directory. Passing these selected cases
does not reproduce the recorded full-corpus evidence. The
[comparison guide](candidate-2/README.md#comparing-reader-commands) explains full
corpus runs, timeouts, report assertions and evidence limits.

For embedding rather than CLI use, see the [Python API](readers/python/README.md)
and [JavaScript API](readers/javascript/README.md), including their lossless
number serializers. Inputs are caller-supplied bytes; direct annex resolution
uses only those inputs. Inspection, validation and exchange perform no described
agent execution, approval intake or deployment, and provide no execution-equivalence
or interoperability guarantee.
