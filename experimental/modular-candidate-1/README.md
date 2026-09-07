# Modular candidate-1 corpus and comparison support

`proposal-0013-candidate-1` is an experimental delta over proposal 0012 at
revision `009a51eb301688f06d29bb7e2f1784e3c4a4cc98`. It is not an adopted AgSDL
edition or a release. The [manifest](fixtures/manifest.json) pins the exact
proposal, inherited contract, schema and fixture bytes used by its oracles.
Candidate-2 keeps its own marker, 121 cases and evidence. No case is silently
upgraded between the two editions.

The modular corpus has 26 cases over 28 unique byte inputs. The same
[readable system](fixtures/modular-system.json) describes two Agents, two
configurations for one graph, different engine assignments, engine-specific
tool parameters, shared Instructions and a Skill dependency. Its Interface has
two addressable operations. Separate inputs cover sequential approval gates and
the negative or partial cases.

Four focused `resolveG` cases add direct annex coverage. They select the second
operation of an exported Interface, reject an unexported target, retain the
explicit transitive-resolution limit and preserve observable annex payload
checks during a cross-boundary key collision.

## What the corpus covers

The manifest indexes every rule added or changed by proposal 0013, the inherited
G-RESOLVE boundary exercised by its Interface payload, and exact exchange for
the new payloads:

| Rule | Witnesses |
| --- | --- |
| P-SHAPE | Valid replacement records and a malformed observed Skill prerequisite. |
| G-TARGET | An Interface with two operations and a missing selected operation. |
| G-DATA | Inputs available before two gates and inputs unavailable at both gates. |
| G-APPROVAL | A valid two-gate chain, refusal bypass and an invalid call link. |
| G-RESOLVE | A direct exported Interface operation, an unexported target, a transitive Ref and a selected-key collision. |
| R-SELECTION | Explicit selection, absent selection and an unknown id. |
| R-BINDING | Exact two-Agent coverage and a missing binding. |
| R-TOOL | A selected implementation with opaque parameters and a missing ToolBinding. |
| R-CONTENT | Shared ordered content, a late prerequisite, a cycle, an external target and a malformed partial prerequisite. |
| R-COMPATIBILITY | Declared-supported, incompatible, unknown, not-provided, blocked and excluded assessments. |
| E-PRESERVE | Byte-identical exchange and refusal for inconsistent dependency accounting. |

The F1 witness removes required Applications while retaining an independently
known unsupported capability. Its oracle requires R-CONTENT failure,
R-COMPATIBILITY fail and inconclusive findings, and the aggregate incompatible
State. The omission cannot turn the requirement set into an empty one.

These are targeted text-derived oracles. Coverage is not every combination of
malformed input, semantic correctness, runtime readiness or interoperability.
An assessment reports declarations only. The corpus never starts an engine,
loads an adapter, applies content, requests approval or invokes an Agent.

## Check the corpus and schemas

Run the repository-only checks from the project root:

```sh
python3 experimental/modular-candidate-1/check-fixtures.py
python3 experimental/modular-candidate-1/test_compare_readers.py
./scripts/check.sh
```

The checker validates metadata, source revisions, SHA-256 hashes, scenario and
rule coverage, oracle shapes and traceable proposal headings. It does not parse
AgSDL semantics or call a reader. `scripts/check.sh` also preserves the full
candidate-2 checker and its 121 historical cases.

An optional Draft 2020-12 pass uses an already installed `jsonschema` package:

```sh
/private/tmp/agsdl-010-orchestration/schema-env/bin/python \
  experimental/modular-candidate-1/check-fixtures.py --jsonschema
```

The path above records the local preparation environment. The repository has no
runtime dependency on that package. The scoped checks validate the Document,
Graphs, RuntimeDeclaration and reached modular payload entry points. A schema
result checks shapes only.

`fixtures/build-fixtures.py` is the reviewed authoring helper for these exact
inputs. It refuses to run after a proposal or schema digest change. Updating a
pin requires renewed review of the oracles; running the helper alone is not that
review.

## Use the modular experiment

Run commands from the repository root. Python 3 and Node.js are sufficient; the
readers use their standard libraries and do not install packages. The
[Python reader](readers/python/README.md) and
[JavaScript reader](readers/javascript/README.md) keep separate implementation
paths for the modular marker.

Start with the readable [modular system](fixtures/modular-system.json). Encode
its exact bytes in a request, then send that JSON object on stdin:

```sh
agsdl_modular_demo=$(mktemp -d)
python3 - "$agsdl_modular_demo/request.json" <<'PY'
import base64
import json
import sys
from pathlib import Path

source = Path('experimental/modular-candidate-1/fixtures/modular-system.json')
request = {
    'operation': 'validateR',
    'primary': base64.b64encode(source.read_bytes()).decode(),
    'annexes': {},
}
Path(sys.argv[1]).write_text(json.dumps(request))
PY
python3 experimental/modular-candidate-1/readers/python/cli.py \
  < "$agsdl_modular_demo/request.json" \
  > "$agsdl_modular_demo/python.response.json"
node experimental/modular-candidate-1/readers/javascript/cli.mjs \
  < "$agsdl_modular_demo/request.json" \
  > "$agsdl_modular_demo/javascript.response.json"
```

Each request contains `operation`, base64 `primary` bytes and an `annexes` map
from dependency id to base64 bytes. `lossyExchange` alone may also carry
`losses`. Each successful host invocation returns one object with `report` and
`artifacts`. Request-envelope failures use stderr and exit status 2. A status 0
means that the reader produced a report; read the requested Result to distinguish
`pass`, `fail`, `unsupported` and `inconclusive`.

The Report keeps D prerequisites and requested G or R results separate. Its
findings identify rule, location and outcome. Checks record completed, blocked
or excluded work. Inventory States and opaque Slices retain observations without
turning unknown or excluded material into success. Exchange artifacts remain
base64 so callers can compare their decoded bytes with the original input.

## Read configurations and graphs

The readable system contains two configurations, `portable` and `alternate`,
for the same graph. `runtime.selected` chooses `portable`. Each AgentBinding
names its engine Edition, parameters, required capabilities, claims, Tool
choices and ordered content Applications. The alternate configuration changes
engine assignments and selected Tool implementations without changing the
Agent or graph definitions. The reader checks this declaration; it does not
start the selected engine, apply content or decide an unrecorded fallback.

The same fixture exposes Interface operations `ask` and `notify`. Each invoke
step names its operation, Action and ports. See
[operation-not-found](fixtures/operation-not-found.json) for a rejected id and
[annex-interface-operation](fixtures/annex-interface-operation.json) for direct
selection from caller-supplied annex bytes.

The [two-gate approval example](fixtures/approval-two-gates.json) links `legal`
approval to `finance` approval and then to one call. Its refusal and failure
paths terminate without reaching the call. The declared timeouts and expiry
requirements are static data. The readers do not request approval, authenticate
an approver or prove that a deadline can be met.

These examples help inspect configuration, graph and report behavior. They do
not prescribe an engine, model provider, Tool product, content adapter or
runtime. No command here executes a described Agent, Tool, approval flow or
deployment.

## Check both implementations

Run all historical and modular reader tests:

```sh
./scripts/check-readers.sh
```

`./scripts/check.sh` runs both Python suites, including the 40 modular Python
tests, and does not require Node.js. The reader-specific command also runs the
two JavaScript suites.

## Compare the readers

Compare both complete corpora, or select one:

```sh
./scripts/check-readers.sh --compare
./scripts/check-readers.sh --compare modular
./scripts/check-readers.sh --compare candidate-2
```

Comparison mode uses separate temporary report directories, prints each summary
and preserves any nonzero comparator exit. It removes the temporary directories
on exit. To retain modular reports, provide a new or empty destination directly:

```sh
agsdl_modular_reports=$(mktemp -d)
python3 experimental/modular-candidate-1/compare-readers.py \
  --reader '["python","python3","experimental/modular-candidate-1/readers/python/cli.py"]' \
  --reader '["javascript","node","experimental/modular-candidate-1/readers/javascript/cli.mjs"]' \
  --reports "$agsdl_modular_reports"
```

The comparator retains raw stdout and stderr plus `summary.json`. It validates
the Report envelope, rule scope, prerequisite aggregation, verdict bookkeeping,
targeted oracles, Slice boundaries and exchange bytes before comparing complete
normalized reports. It does not derive semantic verdicts.

## Integrated evidence, 2026-09-06

The integrated comparison is pinned to these sources:

| Source | Revision or SHA-256 |
| --- | --- |
| Integrated checkout | `90997464428ce7c3072179e1053cf2934fb80fef` |
| Python modular reader | `512056a8e5e324651ab40d5f4e29541098ea5129` |
| JavaScript modular reader | `ef4ac52ef6efcf9af50f49e488fa008dc0932d80` |
| Corpus with 26 cases | `1c796de9c457a4166064c7f5555a052b09f893ff` |
| Proposal 0013 source revision | `280347eec4e2e051d296f9271bfccc86c98d4d40` |
| Proposal 0013 file SHA-256 | `7c9e2aa8e5c6d7c8c0b419aaf3afb666f9ad3510057c98dc7f0f3ac3e904773b` |

The retained integrated report is
`/private/tmp/agsdl-010-mvp-orchestration/comparison-root-integrated-9099746/summary.json`.
It records 26 cases, `blocked:[]` and `failures:[]`. The independent JavaScript
audit at
`/private/tmp/agsdl-010-mvp-orchestration/audit-D-comparison-corrected.md`
also records successful 26-case modular and 121-case candidate-2 comparisons,
plus 96 passing JavaScript tests across the two editions.

The first modular cross-reader run remains at
`/private/tmp/agsdl-010-mvp-orchestration/comparison-1/`. It records 21 component
differences across 14 cases: 14 opaque Slice sets, three State sets, two Check
sets and two Finding sets. The separate `comparison-2/` result is also retained;
neither directory is overwritten by the integrated run.

This evidence shows agreement for the bounded experimental corpus. It does not
adopt proposal 0013, establish principal identity semantics, prove exhaustive
correctness, execute a runtime or demonstrate interoperability. Normative
application, adoption, release, publication and push remain separate work.
