# Independent experimental JavaScript reader

This local, non-normative reader implements the proposed experimental edition
`proposal-0012-candidate-2` from
[proposal 0012](../../../proposals/0012-minimal-0.1.0-contract.md).
The exact semantic source is repository commit
`40f9a8b28a957c6dad7fdd065fd10e29fa611eae`, integrated in
`06d0e8554ba1242b2fef24b9b6125af1fca07139`. The proposal file SHA-256 is
`c2247e8b821544a34eeb93c9c2d75f42777f5a5ac2c9cb62bd6eebcfd4748c9a`.
The original implementation was written independently from the proposal at
`b02c7933f33e439bc45c94e01e96dfb7b77c6eb4`. Subsequent corrections use shared
comparison fixtures and reports, without reading the other reader's code or
sharing its engine or SDK. This is not an adopted AgSDL specification or an
execution engine.

## API and CLI

Node.js with ES modules and the standard library is sufficient. Development
and tests used Node.js 26.8.1; no package installation is needed.

`run` exported by `reader.mjs` accepts `{operation, primary, annexes, losses?}`.
`primary` and annex values are Buffers. Annex keys are dependency IDs. It returns
`{report, artifacts}`, with output Buffers indexed by `primary` or `annex/<id>`.
Only the supplied byte boundary is read. No files, URLs, credentials, model
services or described agents are accessed by the API.

The CLI reads one JSON object from stdin and writes one JSON object to stdout:

```sh
node experimental/readers/javascript/cli.mjs < request.json > response.json
```

The transport adapts primary and annex bytes to canonical base64 strings:

```json
{"operation":"inspect","primary":"e30=","annexes":{}}
```

The response has `report` and `artifacts`; artifact values are base64. Invalid
host requests write an error to stderr and exit 2. A valid request returning a
validation failure still writes a report and exits successfully. The transport
is an experimental test adapter, not AgSDL syntax.

The API represents JSON numbers with `NumberToken.raw`. Use the exported
`stringify` for a lossless JSON response, rather than `JSON.stringify`, which
would expose these host objects. The CLI already uses this serializer. An
ordinary floating-point JSON consumer can still lose precision after receiving
the response; raw opaque slices and original input bytes are the comparison
source. Object maps have ordinary data keys, including `__proto__`.

## Coverage

- `inspect`: strict UTF-8 JSON scanning, source tree, byte spans and D inventory.
- `validateD`: closed D grammar, identities, ownership, references, relations,
  containment, exports, Agent minima, the one Fragment deferral, dependency
  accounting/integrity and extension classification.
- `validateG`: D prerequisite, local typed targets and selected payloads,
  acyclic paths, port bindings, success-edge availability and approval gates;
  external target-dependent checks remain excluded.
- `resolveG`: direct supplied-annex resolution, separate annex D and selected
  payload G results, exports, hashes and selected identity collisions. Selected
  transitive references report unsupported; no recursive retrieval occurs.
- `validateR`: runtime declaration grammar, requirements, optional selection and
  unassessed evidence. No default engine, readiness or support verdict exists.
- `exchange`: exact supplied bytes, including invalid JSON, unless readable
  dependency accounting or required integrity refuses output.
- `lossyExchange`: refusal with prospective loss records and no output.

Results retain separate completed, blocked and excluded checks and aggregate
prerequisite verdicts. Opaque values stay opaque outside the requested unit.
This is static validation only. It does not establish model conformance,
execution equivalence, policy enforcement or evidence authenticity.

## Verification and limits

```sh
node --test experimental/readers/javascript/reader.test.mjs
./scripts/check.sh
git diff --check
```

Tests are constructed from the candidate text, including its 17 exact Unicode
byte witnesses, and defects identified during report comparison. They cover
encoding, decoded duplicate keys, mathematical integer bounds, opaque numbers,
source spans, invalid-byte exchange, accounting refusal, D checks/deferral,
extensions, local and external G, approval and data-flow failures, annex
payload errors, transitive exclusions, R states and prerequisite aggregation.
A JavaScript-only run passed the report validation and targeted assertions for
all 121 shared corpus cases with the harness integrated at
`ef9659fb221b3f6e1f0a468f54dad6810f81e058`. The orchestrator owns the separate
two-reader comparison; this result does not establish cross-reader agreement.
No external integration has been run.

The parser and graph walkers run in memory. Resource exhaustion on adversarial
input beyond host capacity is not a candidate diagnostic. No input size,
opaque-number magnitude, or graph-size limit is silently imposed by a schema.
The implementation has no semantic extension interpreter, transitive resolver,
normalized codec or lossy transform, as bounded by candidate-2.
