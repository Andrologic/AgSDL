# Candidate-2 experimental corpus

This corpus derives from [proposal 0012 candidate-2](../../proposals/0012-minimal-0.1.0-contract.md)
at base `b02c7933f33e439bc45c94e01e96dfb7b77c6eb4`. It is an experiment, not
an adopted language, conformance suite, release or execution contract. The
manifest pins the proposal bytes by SHA-256 so a changed contract cannot silently
reuse these oracles. No reader implementation was consulted to construct them.

The report-boundary clarification uses integration base
`dbec97e64f37b6161eb69c6475e19ee7190e3618`; the manifest digest pins the clarified
proposal bytes. The two existing cases `external-transitive-selected` and
`selected-key-collision` now require the annex G result, independent completed
checks, the affected-record exclusion or identity-dependent block, and the
interpreted payload boundary. The transitive case forbids an invented payload
State in resolveG. Their exact finding sets retain the primary unsupported or
failed resolution result. These assertions clarify reports without adopting the
candidate or establishing agreement between readers.

[fixtures/manifest.json](fixtures/manifest.json) lists named byte inputs and
text-derived observations for D, G, R, inspection and exchange.
[The three shape schemas](schemas/README.md) have distinct entry points and
cannot enforce the semantic contract on their own.

## Start with existing inputs

Use the [local invocation graph](fixtures/local-invocation-resolve.json)
and [custom runtime declaration](fixtures/runtime-custom-evidence-unknown.json).
These are readable fixtures with expectations in the
[corpus manifest](fixtures/manifest.json). The graph describes one
invocation and success/failure paths. The runtime fixture names a custom engine
and carries an unverified capability claim with an unknown evidence hash.
Neither fixture runs an agent or loads an engine.

The [D/G/R shape schemas](schemas/README.md) have separate inputs:
D checks the Document envelope, G the `graphs` value and selected payload shapes,
and R the `runtime` value. Schema acceptance alone does not validate identities,
references, graph paths, evidence or byte preservation. Use the proposal for
meaning and the readers for their covered static checks.

## Run both local readers

From the repository root, use Python 3 and Node.js with ES module support;
the [Python](../readers/python/README.md) and
[JavaScript](../readers/javascript/README.md) guides describe their APIs, exact
number serializers and tested environments. No package installation, credentials or external engine is needed.
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

## Running the corpus check

Run from the repository root with Python 3.9 or newer:

```sh
python3 experimental/candidate-2/check-fixtures.py
```

The checker verifies manifest references, file digests, the pinned proposal,
rule-level positive/negative coverage, the six-review witness index and local
schema structure/references. It does not parse fixture inputs as AgSDL, derive
verdicts, invoke readers or validate described behavior. Invalid JSON bytes are
intentional fixtures. The repository's `scripts/check.sh` also runs Python
reader suites and comparator tests; see the
[verification guide](../../CONTRIBUTING.md#verification) for its full scope.

An optional `--jsonschema` flag additionally checks the three schemas against
the Draft 2020-12 metaschema using an already installed `jsonschema` package.
It performs no installation. The default check reports explicitly that this
metaschema check was not requested. JSON Schema's dialect and local-reference
rules were checked against the [official Draft 2020-12 core document](https://json-schema.org/draft/2020-12/json-schema-core).

## Manifest format

The manifest format identifier is `agsdl-candidate-corpus-1`; it is a local test
interface, not a product protocol. `contract`, `contractBase` and
`contractSha256` identify the oracle edition. All case artifact paths are relative
to `fixtures/`. Every artifact record has `path` and the SHA-256 of its exact
bytes. The harness reads those bytes without reserializing them.

Each case has:

- `name`, unique and stable within this manifest; `status`, currently `ready`;
- `primary`, an artifact record; `annexes`, a map from dependency id to artifact
  record; `operation`, one of the seven contract operations; optional `losses`;
- `source`, the proposal path relative to `fixtures/` and its relevant section;
- `coverage`, rule/variant pairs; `reviewWitnesses`, numbered references below;
- `expected`, the assertions described next. A future `blocked` case instead
  has `expected:null` and a `blocker` explaining the precise unresolved witness.
  A harness skips it and reports the block; it never invents a verdict.

For each ready case, invoke each independently implemented CLI once. Send one
JSON object on stdin with `operation`, `primary` as base64, `annexes` as the map
of base64 strings, and `losses` only if present. The CLI returns one JSON object
on stdout with `report` using the contract Report grammar and `artifacts` mapping
output id to base64. Output ids are the input ids, `primary` and `annex/<id>`.
This envelope is the agreed local adaptation of the byte-string host API.
Readers resolve only the supplied bytes; no fixture URL grants retrieval.

`expected` deliberately combines exact and targeted assertions:

| Member | Harness assertion |
| --- | --- |
| `results` | Each listed input/unit/phase has the stated verdict. This is a required subset, not a complete result list; validate complete result ordering and additional selected-annex results against the contract, then compare readers' full reports. |
| `findings` | `items` are input/unit/rule/location/outcome tuples. `contains` requires those tuples while permitting other contract-required findings from the same mutation. `exact` requires equality of the complete tuple set across all Results. Details are not compared. |
| `checks` | Each input/unit/rule/state entry must exist and contain the listed locations. Other entries/locations remain subject to the contract and full reader comparison. |
| `states` | Required input/pointer/state tuples. `detailRequirement`, when present, requires the detail to name exactly that Requirement id as its subject; other prose is ignored. |
| `absentStates` | No State for the given input may have a pointer beginning with `pointerPrefix`. Prefixes end in `/` when forbidding children only. |
| `opaque` | Require a maximal opaque Slice at each input/pointer. Its start/end must select the exact source value bytes, including original numeric lexemes; compare the slice bytes between readers. |
| `absentOpaque` | No opaque Slice may have that exact input/pointer. |
| `preservation` | `exact-input-boundary` requires exactly all supplied input ids, with byte-identical decoded artifacts and matching OutputRecord hashes. `no-output` requires empty artifacts and outputs. |
| `losses` | Require the listed prospective Loss records. A supplied loss includes its exact reason; the default loss omits reason here because the contract fixes information/location/permission but leaves reason prose free. |

Byte offsets in syntax findings are zero-based. JSON Pointer locations use the
contract's escaping. Inventory tree and numeric host representations are checked
against source slices rather than rounded or reserialized JSON. The harness
also verifies input hashes, output hashes and the closed Report shape. It
compares complete normalized result/check/state/finding sets between readers,
not just the targeted oracle assertions. Diagnostic prose and execution time
are not comparison keys. The comparison harness below implements these assertions. Reader implementations
are supplied separately.

## Coverage and limits

The manifest's `coverage` indexes every rule in the contract inventory.
Executing rules have positive and negative witnesses; E-LOSS always refuses,
P-PREREQUISITE only blocks, and the four X documentary rules only exclude.
Their inapplicable pass/fail variants are explained explicitly. Unknown hashes,
unsupported extensions/transitive references, deferrals and excluded operation
boundaries have separate cases where relevant.

Coverage is rule-level, not exhaustive coverage of every combination or every
prose subclause. In particular this corpus does not enumerate every missing
field, every alias of a malformed scalar, every cycle shape or every combination
of multiple defects. Targeted failure assertions avoid suppressing additional
findings that the contract requires. Positive cases use exact empty finding sets
unless a deferred finding is expected. No successful schema check substitutes
for a semantic verdict, and no experimental verdict establishes readiness.

The cases include strict encoding, duplicate keys, Unicode identity without
normalization, prototype-like map keys, opaque large numeric lexemes, exact
interpreted numeric bounds, Agent minima, external declarations, dependency
accounting/integrity, Fragment deferrals, direct G resolution, selected-key
collisions, unsupported transitive references, success-edge availability,
conditions, pre-invocation approval data, human gates and open runtime evidence.

## Witnesses from the six contract reviews

The source is the orchestrator's real report collection at
`/private/tmp/agsdl-010-orchestration/audit-complete-contract.md`, consulted during
preparation. The table records the witnesses, not new audit endorsements.

| Review | Witness cases in the manifest |
| --- | --- |
| 1, `review_complete_contract` | `local-invocation-resolve` and `external-resolved`: local G targets, including local references in selected annex payloads, need no export. |
| 2, `review_complete_contract_final` | `runtime-opaque-validateD`, `runtime-opaque-inspect`, `runtime-opaque-validateR`: opaque runtime has no synthesized selection state. |
| 3, `review_complete_contract_closed` | `runtime-no-selection`: exact documentary exclusions; `dependencies-scalar-inspect` and `dependencies-scalar-exchange`: shape probing is not validation. |
| 4, `review_complete_contract_reports` | `external-target-*`: D external-target states; `empty-object-inspect` and `empty-object-lossyExchange`: exact unit and phase. |
| 5, `review_complete_contract_attribution` | `dependencies-mixed-*`: a malformed dependency array stays wholly opaque outside validation; `runtime-external-hosting` retains declared and unchecked states. |
| 6, `review_dependency_inventory_fix` | Mixed, scalar, absent and syntax-invalid dependency inventory variants across inspection/exchange/lossy exchange, plus `dependencies-mixed-validateD` retaining a well-shaped child's unknown hash. |

These historical reviews examined proposal text. The subsequent independent
reader comparison is recorded in the
[adoption review](../../docs/reviews/0006-candidate-0.1.0-adoption.md#final-experimental-comparison).


## Comparing reader commands

Run [compare-readers.py](compare-readers.py) with at least two distinct labels
and explicit executable/argument arrays. The optional positional manifest defaults
to this corpus. This example shows placeholders, not available implementations:

```sh
python3 experimental/candidate-2/compare-readers.py \
  --reader '["first", "/absolute/path/to/first-reader", "--json"]' \
  --reader '["second", "/absolute/path/to/second-reader"]' \
  --reports /private/tmp/agsdl-candidate-comparison
```

Commands run without a shell. Each invocation has a 30-second timeout; override
with `--timeout SECONDS`, up to 300. Repeat `--case NAME` to select cases.
Reader labels and case names use letters, digits, underscores and hyphens,
starting with a letter or digit. Duplicate labels are rejected. The reports
directory must be new or empty, preserving prior evidence from accidental reuse.

The directory receives exact `CASE.LABEL.stdout` and `.stderr` bytes, including
partial output on timeout, plus `summary.json` with failures and visible blocked
cases. A nonzero reader exit, timeout, malformed response, failed assertion,
reader disagreement or blocked case makes the command fail. A timeout terminates
only the process group launched for that invocation. No AgSDL reference is
resolved by the harness.

The harness validates closed Report records, domains, input and output hashes,
Result stages, permitted rule sets, Check ordering/completeness, duplicate
records where uniqueness is required, and verdict aggregation from the supplied findings and prerequisites.
It does not derive findings from Agent, graph, dependency or runtime semantics.
The required-result and required-location assertions remain subsets. Complete
validated reports are then compared, retaining input/unit/phase and all rules.
Findings, State and Slice array order are insignificant; mandatory Result stages
and sorted Checks are validated before order-independent comparison. Processor
identity can differ; finding details and ordinary State prose are ignored.
Only the default Loss reason is free prose; supplied loss records must match
their oracle. Missing-claim detail must unambiguously name the Requirement id;
plain ids and unambiguous prose containing the id are supported, while ambiguous
wording is rejected instead of silently conflating claims.

The local JSON response adapter carries numbers as exact JSON numbers. The
harness parses them with Decimal and an exact lexeme fallback for exponents
beyond Decimal’s host limit, preserves Boolean/number distinctions and
compares the entire primary tree with the original JSON value, without binary
floating-point conversion. Alternative tagged host-number representations need
an explicit adapter before this CLI comparison; they are not inferred from an
arbitrary object or string. Original source lexemes remain authoritative for
opaque slices. This adapter restriction is not a new AgSDL semantic rule.

A syntax-only source index verifies each reported Slice's pointer and exact
UTF-8 byte span. It rejects duplicate, overlapping and nonmaximal slices, enforces
unconditionally opaque documentary boundaries, and rejects states inside them.
It does not resolve G references to decide whether a particular Interface or
ApprovalRequirement payload was selected: such a payload is either wholly
opaque or interpreted. That selection remains covered by corpus assertions and
full reader comparison. Likewise unreadable dependency inventory is asserted by
the corpus, without duplicating a dependency validator in the harness. These
boundaries prevent the harness from becoming a third semantic implementation.

Run the machinery tests alone with:

```sh
python3 experimental/candidate-2/test-compare-readers.py
```

These tests use fixed synthetic reports and subprocess stubs. Their success
verifies the harness, not AgSDL implementation support or interoperability.
The three schemas also passed the optional metaschema check with
`jsonschema 4.23.0` during preparation; that package is not a project dependency.
The boundary corrections below used saved reports from the first comparison.
Replaying those reports was a comparator check, distinct from the later
[full reader comparison](../../docs/reviews/0006-candidate-0.1.0-adoption.md#final-experimental-comparison).


### Missing prerequisites and State sets

The proposal's [location rules](../../proposals/0012-minimal-0.1.0-contract.md#exact-results-locations-and-experimental-diagnostics)
place a missing-field P-SHAPE finding at its observable parent. Its
[Check rules](../../proposals/0012-minimal-0.1.0-contract.md#rule-execution-and-exact-exclusion-records)
say that blocked locations name the affected record needing the value. These
are distinct from the missing prerequisite's own location. The harness keeps
requiring an observable affected record for a blocked pointer, while preserving
the whole-unit root location and exact documentary exclusions. It does not
infer which AgSDL record or rule needs the missing value. Absent-container
exclusions are limited to the contract-specific rule/location combinations.
Accepting any unavailable child of an observable parent would need a further
contract clarification; the comparator does not adopt that interpretation.

The same report section explicitly compares States as sets of
input/pointer/state, with Requirement identity retained for missing claims.
Repeated equivalent State tuples are therefore accepted and normalized for
validation and comparison, including repetitions with different permitted prose.
The original stdout remains unchanged in the evidence directory. Different
states at the same pointer and different missing-claim Requirement ids remain
distinct. This exception does not remove the explicit uniqueness checks for
Check rule/state pairs or their locations, nor the checks on other records.

Regression tests distinguish affected-record locations from missing values and
State repetition from a change in state or Requirement identity. During the
initial comparator correction, the saved `external-local-phase` JavaScript
report passed after State normalization. The saved `missing-relations` and
`g-prerequisite-failure` reports remained rejected for naming absent collections
as blocked locations. This describes those initial reports, not the later
integrated readers. Replaying saved reports tests report boundaries only; it
does not execute a reader or provide new semantic validation evidence.
