# AgSDL 0.1.0 reference tooling

Reference readers are non-normative static tools. The specification defines the
operation contracts. A reader reports its observation of one requested
operation; it does not execute an Agent, engine, Tool, approval service or graph.

## Included readers and evidence

| Component | Local 0.1.0 status |
| --- | --- |
| Python reader | Integrated with a focused standard-library suite. |
| JavaScript reader | Integrated with a focused standard-library suite. |
| Official corpus and comparator | Integrated with 137 pinned cases. |
| Cross-reader comparison | 137 cases, no blocked case, failure or mismatch. |

The CLI entry points are `tooling/readers/python/cli.py` and
`tooling/readers/javascript/cli.mjs`. Their implementations are independent and
use the same request boundary and official corpus. Agreement on that corpus is
bounded evidence, not exhaustive correctness or runtime interoperability.

## Prepare a request without installation

From the repository root, this command encodes the official example's original
bytes and writes a `validateD` request:

```sh
agsdl_request=$(mktemp)
node - examples/0.1.0/general-purpose-system.json validateD > "$agsdl_request" <<'JS'
const fs = require('node:fs');
const [path, operation] = process.argv.slice(2);
const primary = fs.readFileSync(path).toString('base64');
process.stdout.write(JSON.stringify({ operation, primary, annexes: {} }));
JS
python3 tooling/readers/python/cli.py < "$agsdl_request"
node tooling/readers/javascript/cli.mjs < "$agsdl_request"
rm "$agsdl_request"
```

Replace `validateD` with `inspect`, `validateG`, `validateR`, `exchange` or
`lossyExchange` when that operation fits the intended observation. `resolveG`
also accepts base64 annex bytes keyed by dependency id. The complete request
boundary is in [serialization](../spec/serialization.md#operations-phases-and-supplied-inputs).

Each CLI writes `{report,artifacts}`. Exit status 0 means that a response was
produced, including when a Result verdict is `fail`. Inspect the Result unit,
phase, verdict, findings, checks and states instead of treating the process exit
as conformance.

## Run the checks

```sh
./scripts/check.sh
./scripts/check-readers.sh
./scripts/check-readers.sh --compare
```

Use `--compare official` or `--compare 0.1.0` to select only the official
corpus. The unqualified comparison also preserves the historical candidate-2
and modular comparisons. It uses temporary report directories. Follow the
[conformance guide](../conformance/README.md#reader-comparison) when retaining
official evidence.

Direct Draft 2020-12 schema checks are optional. They may use a project-local
environment:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install jsonschema
python3 conformance/check-corpus.py --jsonschema
```

Neither reader, `./scripts/check.sh` nor the normal corpus check requires that
package. Historical candidate reports keep their historical markers and cannot
be relabelled as official 0.1.0 evidence.
