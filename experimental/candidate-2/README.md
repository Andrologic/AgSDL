# Candidate-2 experimental corpus

This corpus derives from [proposal 0012 candidate-2](../../proposals/0012-minimal-0.1.0-contract.md)
at base `b02c7933f33e439bc45c94e01e96dfb7b77c6eb4`. It is an experiment, not
an adopted language, conformance suite, release or execution contract. The
manifest pins the proposal bytes by SHA-256 so a changed contract cannot silently
reuse these oracles. No reader implementation was consulted to construct them.

[fixtures/manifest.json](fixtures/manifest.json) lists named byte inputs and
text-derived observations for D, G, R, inspection and exchange.
[The three shape schemas](schemas/README.md) have distinct entry points and
cannot enforce the semantic contract on their own.

## Running the corpus check

Run from any directory with Python 3.9 or newer:

```sh
python3 experimental/candidate-2/check-fixtures.py
```

The checker verifies manifest references, file digests, the pinned proposal,
rule-level positive/negative coverage, the six-review witness index and local
schema structure/references. It does not parse fixture inputs as AgSDL, derive
verdicts, invoke readers or validate described behavior. Invalid JSON bytes are
intentional fixtures. The repository's `scripts/check.sh` is a separate
maintenance check and does not run this corpus checker.

An optional `--jsonschema` flag additionally checks the three schemas against
the Draft 2020-12 metaschema using an already installed `jsonschema` package.
It performs no installation. The default check reports explicitly that this
metaschema check was not requested. JSON Schema's dialect and local-reference
rules were checked against the [official Draft 2020-12 core document](https://json-schema.org/draft/2020-12/json-schema-core).

## Manifest format for a future comparison harness

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
are not comparison keys. No comparison harness or reader is included in this lot.

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

These historical reviews examined proposal text. The new corpus needs its own
independent review and subsequent execution against independently written readers.
