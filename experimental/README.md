# Experimental candidates

This directory keeps two separate experimental editions. The
[modular candidate-1 guide](modular-candidate-1/README.md) covers proposal 0013,
its 26-case corpus and its independent Python and JavaScript readers. Their
integrated comparison at `90997464428ce7c3072179e1053cf2934fb80fef` has no
blocked case or mismatch. The candidate-2 experiment below retains its own
proposal 0012 marker, readers, 121-case corpus and comparison history.

Neither experimental edition is the adopted AgSDL edition. The official,
locally adopted 0.1.0 contract lives in [`spec/`](../spec/README.md) under the
`agsdl-0.1.0` marker. A passing experimental comparison shows agreement only on
its bounded corpus and report assertions. It does not prove runtime behavior,
engine support, evidence authenticity or interoperability.

## Try candidate-2

`proposal-0012-candidate-2` is an implementable experiment described in
[proposal 0012](../proposals/0012-minimal-0.1.0-contract.md), not an adopted
AgSDL specification. Version 0.0.2 is the latest published conceptual pre-draft;
0.1.0 is locally ready for its bounded first-draft scope but remains unpublished
and unstable. The Python and JavaScript readers are implemented
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

Run `./scripts/check-readers.sh` for the Python and JavaScript suites of both
experimental editions, using Python 3 and Node.js with `node --test` support.
The general `./scripts/check.sh` includes both Python suites and keeps its
Python-only runtime requirement.

Run `./scripts/check-readers.sh --compare` to compare both full corpora, using
Python 3.9 or newer and Node.js. Add `candidate-2` or `modular` after `--compare`
to select one. This mode prints each summary, preserves a nonzero comparator
exit and cleans its separate temporary report directories on exit. It does not
run the test suites.

## Retain comparison reports

Give each comparator a new or empty directory when you need to retain
`summary.json` and raw stdout/stderr:

```sh
agsdl_candidate2_reports=$(mktemp -d)
python3 experimental/candidate-2/compare-readers.py \
  --reader '["python", "python3", "experimental/readers/python/cli.py"]' \
  --reader '["javascript", "node", "experimental/readers/javascript/cli.mjs"]' \
  --reports "$agsdl_candidate2_reports"

agsdl_modular_reports=$(mktemp -d)
python3 experimental/modular-candidate-1/compare-readers.py \
  --reader '["python", "python3", "experimental/modular-candidate-1/readers/python/cli.py"]' \
  --reader '["javascript", "node", "experimental/modular-candidate-1/readers/javascript/cli.mjs"]' \
  --reports "$agsdl_modular_reports"
```

A nonzero exit reports a failed assertion, invalid response or reader mismatch.
Read each `summary.json` and the unchanged stdout/stderr files. The
[candidate-2 comparison contract](candidate-2/README.md#comparing-reader-commands)
and [modular comparison contract](modular-candidate-1/README.md#compare-the-readers)
describe report assertions and evidence limits.

For embedding rather than CLI use, see the [Python API](readers/python/README.md)
and [JavaScript API](readers/javascript/README.md), including their lossless
number serializers. Inputs are caller-supplied bytes; direct annex resolution
uses only those inputs. Inspection, validation and exchange perform no described
agent execution, approval intake or deployment, and provide no execution-equivalence
or interoperability guarantee.
