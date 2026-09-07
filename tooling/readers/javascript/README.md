# Official-edition JavaScript reader

This non-normative reference tool reads the adopted AgSDL 0.1.0 contract.
Validation operations require primary documents and required `resolveG` annexes
to carry `agsdl-0.1.0`. `inspect` and `exchange` also accept other edition
markers without relabelling the source bytes. All operations emit new reports
with the official marker. The Processor Edition is
`{"identity":"agsdl/reference-javascript-reader","version":"0.1.1"}`.

The reader implements the seven operation entry points named by the
specification:

| Feature Edition | Operation |
| --- | --- |
| `agsdl/inspect` 0.1.0 | `inspect` |
| `agsdl/validateD` 0.1.0 | `validateD` |
| `agsdl/validateG` 0.1.0 | `validateG` |
| `agsdl/resolveG` 0.1.0 | `resolveG` |
| `agsdl/validateR` 0.1.0 | `validateR` |
| `agsdl/exchange` 0.1.0 | `exchange` |
| `agsdl/lossyExchange` 0.1.0 | `lossyExchange` |

These identities name separate operation contracts. A report remains an
observation for its requested operation, not a whole-model, execution,
readiness or runtime claim.

## Run

Node.js and its standard library are sufficient. No installation step or
Python process is used.

```sh
node tooling/readers/javascript/cli.mjs < request.json
```

The CLI reads one JSON request from standard input. The request has `operation`,
canonical-base64 `primary` bytes and an `annexes` object whose values are also
canonical base64. `losses` is optional and valid only for `lossyExchange`.
The operation names and request boundary match
[`spec/serialization.md`](../../../spec/serialization.md#operations-phases-and-supplied-inputs).

Successful host handling writes `{report,artifacts}` to standard output and
exits with status 0, including when a validation report has verdict `fail`.
Malformed host requests write `host request error: ...` to standard error and
exit with status 2. Artifact values in the response are canonical base64.

`exchange` can preserve arbitrary source bytes, including documents carrying
another edition marker. It never edits those bytes. Validation requires the
official marker, and `resolveG` applies that requirement independently to every
required annex. Historical candidate inputs and reports keep their historical
identity.

## Boundaries and verification

The implementation owns local copies of the lossless JavaScript scanner and
D/G/R modules adopted from the retained readers. All runtime imports stay in
this directory or use the Node.js standard library; `experimental/` is not
needed to use the API or CLI. The historical readers remain separate.
It does not import or execute a Python reader. It performs no network access,
transitive resolution, Agent execution, engine invocation, approval intake or
runtime action.

Run the official regression suite and both retained JavaScript ancestor suites:

```sh
node --test tooling/readers/javascript/reader.test.mjs
node --test experimental/readers/javascript/reader.test.mjs
node --test experimental/modular-candidate-1/readers/javascript/reader.test.mjs
./scripts/check.sh
git diff --check
```

The independent Python reader and official corpus are integrated. The final
0.1.0 delivery comparison covered all 137 official cases without a blocked case, failure
or mismatch. The focused and retained regression suites establish additional
local boundaries, but none of these checks proves exhaustive correctness,
execution support or interoperability.

## Maintenance diagnostics

The focused tests use the specification's independent-check and affected-record
rules to cover missing root kind, configuration enumeration, configuration id
and Agent identity. Empty exports retain a completed D-EXPORT portion. Missing
configuration enumeration does not complete R-SELECTION. Missing configuration
id blocks both its record and selected lookup. Missing Agent identity blocks
configuration coverage and supplied Tool membership, including in unselected
configurations. Readable sibling checks and capability findings still run.

The [diagnostic dossier](../../../docs/reviews/0009-0.1.1-diagnostic-expectations.md)
records the unresolved aggregate dependencies for missing Agent identity,
Instructions target/application point and Skill Tool closure. Missing Step kind
also leaves an unresolved choice of additional-field diagnostics. These choices
are retained, not promoted to normative requirements. Unicode report ordering
is unchanged; the known U+E000/U+10000 comparison disagreement remains outside
this maintenance correction.
