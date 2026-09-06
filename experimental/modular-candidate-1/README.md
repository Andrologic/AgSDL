# Modular candidate-1 corpus and comparison support

`proposal-0013-candidate-1` is an experimental delta over proposal 0012 at
revision `009a51eb301688f06d29bb7e2f1784e3c4a4cc98`. It is not an adopted AgSDL
edition or a release. The [manifest](fixtures/manifest.json) pins the exact
proposal, inherited contract, schema and fixture bytes used by its oracles.
Candidate-2 keeps its own marker, 121 cases and evidence. No case is silently
upgraded between the two editions.

The modular corpus has 22 cases over 20 unique byte inputs. The same
[readable system](fixtures/modular-system.json) describes two Agents, two
configurations for one graph, different engine assignments, engine-specific
tool parameters, shared Instructions and a Skill dependency. Its Interface has
two addressable operations. Separate inputs cover sequential approval gates and
the negative or partial cases.

## What the corpus covers

The manifest indexes every rule added or changed by proposal 0013, plus exact
exchange for the new payloads:

| Rule | Witnesses |
| --- | --- |
| P-SHAPE | Valid replacement records and a malformed observed Skill prerequisite. |
| G-TARGET | An Interface with two operations and a missing selected operation. |
| G-DATA | Inputs available before two gates and inputs unavailable at both gates. |
| G-APPROVAL | A valid two-gate chain, refusal bypass and an invalid call link. |
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

## Reader interface for phases C and D

No modular reader is implemented in this delivery. Phase C and D implementers
should keep separate code paths and must not relabel candidate-2 reports.
For each ready case, invoke a reader once with this JSON object on stdin:

```json
{
  "operation": "validateR",
  "primary": "<base64 fixture bytes>",
  "annexes": {}
}
```

The reader writes one JSON object to stdout containing `report` and `artifacts`.
It must preserve the proposal 0013 marker and inherited Report grammar. Inputs
are exact caller-supplied bytes. A fixture path grants no network lookup.

The comparison command will be runnable after both reader paths exist:

```sh
agsdl_modular_reports=$(mktemp -d)
python3 experimental/modular-candidate-1/compare-readers.py \
  --reader '["python","python3","experimental/modular-candidate-1/readers/python/cli.py"]' \
  --reader '["javascript","node","experimental/modular-candidate-1/readers/javascript/cli.mjs"]' \
  --reports "$agsdl_modular_reports"
```

The destination must be new or empty. The comparator retains each reader's raw
stdout and stderr plus `summary.json`. It validates the Report envelope, closed
rule scope, prerequisite aggregation, verdict bookkeeping, targeted oracles,
exact and exhaustive exchange Slice boundaries, and exchange artifacts, then
compares complete normalized reports. It imports the
candidate-2 lossless JSON parser, canonicalizer, digest and process runner as
neutral utilities. It has its own proposal 0013 rule inventory and never derives
an Agent, graph, compatibility or approval verdict.

Phase C and D should first run one reader against the corpus and inspect every
oracle error. A complete two-reader success belongs to the later evidence phase.
Until then, this corpus proves neither reader support nor cross-reader agreement.
