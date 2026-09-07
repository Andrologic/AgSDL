# Official AgSDL 0.1.0 Python reader

This directory implements the seven static operations defined by the adopted
[AgSDL 0.1.0 specification](../../../spec/README.md). It emits reports with
`contract:"agsdl-0.1.0"` and processor Edition
`agsdl-reference/python-reader` version `0.1.0`.

The implemented feature Editions are:

| Feature identity | Version | Operation |
| --- | --- | --- |
| `agsdl/inspect` | `0.1.0` | `inspect` |
| `agsdl/validateD` | `0.1.0` | `validateD` |
| `agsdl/validateG` | `0.1.0` | `validateG` |
| `agsdl/resolveG` | `0.1.0` | `resolveG` |
| `agsdl/validateR` | `0.1.0` | `validateR` |
| `agsdl/exchange` | `0.1.0` | `exchange` |
| `agsdl/lossyExchange` | `0.1.0` | `lossyExchange` |

The `agsdl_reader` package contains the official grammar, lossless JSON parser
and rule engine. These started as local copies of the modular candidate engine
and are maintained for the current contract only. Runtime imports and reads do
not depend on `experimental/`. No JavaScript reader is loaded or consulted.

For Python callers, add `tooling/readers/python` to the module search path,
then use the qualified package API:

```python
from agsdl_reader import read

response = read("validateD", primary_bytes, annexes={})
```

Distribute `agsdl_reader/` and `cli.py` together to use the reader outside this
repository. No installation or third-party package is needed. Historical
readers retain their own imports and contract markers; importing this package
before or after either historical reader does not configure their modules.
The thin `reader.py` facade retains existing callers when this directory is on
the module search path. Callers loading it by filename may use a distinct module
name. Two unqualified imports named `reader` still share Python's module cache;
use `agsdl_reader` when a historical reader is loaded in the same process.

Run the standard-library CLI from the repository root without installation:

```sh
python3 tooling/readers/python/cli.py < request.json
```

The request is one JSON object with `operation`, base64 `primary`, and an
`annexes` object mapping direct dependency ids to base64 bytes. An optional
`losses` array is accepted only for `lossyExchange`. The response contains
`report` and `artifacts`. Host, request and resource errors use stderr and exit
status 2. Document findings are returned in the official report with exit
status 0.

Run the focused suite with:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tooling/readers/python -v
```

All input bytes come from the caller. The reader performs no fetching, engine or
adapter execution, approval intake, authentication, evidence retrieval, state
migration or fallback selection. Its results cover only the requested operation
and phase. The local comparison before these diagnostic corrections covers all 138
existing official cases without a blocked case, failure or mismatch. This is
bounded static evidence, not exhaustive correctness.


## Partial diagnostic regressions

The [0.1.1 diagnostic dossier](../../../docs/reviews/0009-0.1.1-diagnostic-expectations.md)
indexes the witnesses and their normative sources. `test_diagnostics.py` asserts
individual obligations from the specification, never a peer's entire report.
The contract marker and feature Editions remain `agsdl-0.1.0` and `0.1.0`.
This maintenance work does not publish a new contract.

Cases for the common conformance lot, each deleting only the named member from
`examples/0.1.0/general-purpose-system.json`:

| Deleted member | Required Python regression |
| --- | --- |
| `/root/key` | D-EXPORT completes the readable root form and empty export domain without a blocked `/exports`. Nonempty exports still block root identity comparison. |
| `/root/kind` | D-EXPORT retains blocked `/exports` and completed for the empty export domain. |
| `/runtime/configurations` | R-SELECTION and dependent R rules block at `/runtime`, without invented completion. |
| `/runtime/configurations/0/id` | R-SELECTION blocks at `/runtime` and the Configuration, retaining independent completed checks. |
| `/runtime/configurations/0/agents` | R-COMPATIBILITY blocks at the selected Configuration, without empty assessment completion. |
| `/runtime/configurations/0/agents/0/agent` | R-CONTENT blocks required coverage at the binding and reachability at its Applications. R-BINDING and R-TOOL retain their determined blocked locations and sibling checks. |
| `/runtime/configurations/0/agents/0/engine` or `/claims` | R-COMPATIBILITY blocks at the binding without interpreting absence as null engine or empty claims. Independent ToolBinding and omission findings remain observable. |
| `/graphs/0/steps/0/resources` | G-TARGET blocks at the Step while readable target checks complete. |
| Instructions `/definitions/11/payload/body` | No R-CONTENT or binding compatibility blockage from this field alone. |
| Instructions `/definitions/11/payload/format` | No R-CONTENT blockage; compatibility blocks at both selected bindings and keeps readable capability findings. |
| Skill `/definitions/12/payload/inputs`, `/outputs`, `/preconditions`, `/completion` | No R-CONTENT or binding compatibility blockage from these fields alone. |
| Tool `/definitions/9/payload/action`, `/failures`, `/requires` | R-TOOL blocks at the payload and retains completed independent checks. |
| Tool `/definitions/9/payload/inputs` or `/outputs` | No ToolBinding compatibility blockage from port shape alone. |

Every deletion requires P-SHAPE at its immediate parent. Tests also combine
selected deletions with known incompatibilities or wrong-kind references to
verify that independent failures survive partial checks.

The dossier leaves these exact diagnostic choices open: sibling aggregate
assessment with a missing Agent identity; extra-field diagnostics with missing
Step.kind; Instructions target/at as prerequisites; and Skill.tools as a
prerequisite for Agent aggregate assessment. The reader retains its existing
choices and tests only the determined obligations for those witnesses.
Unicode sorting is unchanged; no exact ordering oracle for U+E000 versus
U+10000 is asserted. The common corpus must preserve these limits.
