# Independent declaration-reader comparison

This corpus checks the candidate [document rules](../../../spec/0.2/validation.md#static-checks-and-evidence-limits).
It is non-normative tooling. Candidate semantics remain in `spec/0.2/`.

The Python and JavaScript readers consume the same original document bytes.
The JavaScript semantic implementation was written from the candidate contract,
schema and examples before comparing it with Python. It shares the schema as
data and the official JavaScript `json.mjs` scanner, number-token class and
serializer as lexical utilities. It does not import or invoke a Python reader,
reuse Python graph/constraint/URI algorithms, or import official semantic rules.
Python source was inspected afterward to diagnose proven report differences.

[cases.py](cases.py) authors 107 reproducible cases independently of the readers,
including the 11 maintained examples. It constructs fixture bytes and explicit
expected rule-code sets, plus selected source, support and expansion observations.
Every one of the 18 document rule codes has a failing witness. The corpus covers
literal/reference boundaries, exact numbers, malformed Unicode, special object
keys, steering and Join declarations, composition origins, gate chains,
constraints, URI bases and exact support claims. Cases are not generated from
reader output. They are bounded evidence, not exhaustive rule-combination coverage.
The JavaScript [focused tests](../javascript/reader.test.mjs) add independent
lexical, numeric, URI and composition assertions.

## Run and retain evidence

Python 3.9+ and Node.js with `node --test` support are sufficient. Only standard
libraries are used. No command installs packages, accesses the network, reads
URI content or executes an Agent, Call or graph.

```sh
node --test experimental/agent-flow-0.2/javascript/reader.test.mjs
python3 experimental/agent-flow-0.2/conformance/test_compare.py -v
python3 experimental/agent-flow-0.2/conformance/compare.py --reports /tmp/agsdl-flow-comparison
```

The output directory must be empty. The comparator preserves every input byte
stream, each reader's stdout and stderr, input hashes, contract/schema/corpus
source hashes, expected code sets, observation assertions and `summary.json`.
A nonzero exit means an oracle failure, invalid response, reader failure,
timeout or report disagreement. Malformed responses cannot prevent subsequent
cases from running. Keep the tested Git revision and any uncommitted diff with
these files. `scripts/check-full.sh` records the revision and dirty status.

`./scripts/check-readers.sh --compare flow` selects this corpus. The unqualified
comparison also retains the three official and historical comparisons. The
ordinary repository check remains Python-only and runs the comparator's fault
tests; executing the independent reader requires the separate Node.js command.

## Report interchange conventions

These conventions describe the tools' diagnostic representation; they add no
candidate execution or document semantics. Reports have the candidate contract,
`valid`, `scope`, `executionSupport` and `findings`. Parse failures use scope
`parse`; other reports use `document-shape-and-declared-references`. Parse and
shape failures omit declaration observations. Shape-valid documents include
`sources`, `support`, `coreNeeds` and `unassessed`, even when semantic checks fail.
`expandedFlow` appears when a document declares a nonempty composition catalog
and a flow, including for invalid graphs.

Findings contain `code` and `path`, with `invocation` only for diagnostics on an
expanded body. Optional `message` is human prose and is the only ignored field.
Both template diagnostics and distinct invocation diagnostics remain visible.
Constraint-enum and requirement/claim duplicates point to the later array item;
resource collisions point to Agent `skills`; graph-route duplicates and Join
errors point to the affected step. Approval-chain defects are reported on the
chain's gates. Missing composition parameter/output coverage points to the use.
Whole-shape and parse failures point to the root. JSON Pointers escape `~` and
`/` in property names.

Invalid expansion is a diagnostic projection, never a usable default. A missing
Agent argument is represented by `agent: ""` in that projection, with both
`COMPOSITION` at the use and `REFERENCE` at the invoked Agent field. Missing
output mappings produce empty diagnostic routes. An unavailable composition
body contributes no expanded steps; references to its missing entry still fail.
These placeholders cannot make `valid` true and must not be executed. Retaining
this existing Python reporting convention resolved the independent reader's
initial choice to omit invalid projections; no accepted input was changed.

An invalid supplied URI base emits `URI` at the base and is unavailable for source
resolution. Relative sources then retain null base/resolution and their
unassessed locations. Support reports retain repeated authored requirements on
invalid declarations. Skill requirements are added only if not already present;
dynamic cases selecting the same configuration produce one conditional assessment.
Claims never clear structural findings or unassessed execution needs.

Object order is ignored and strings compare by exact Unicode scalar sequences.
Numbers compare mathematically and exactly; Booleans remain distinct from numbers.
Top-level `findings`, `sources`, `support`, `coreNeeds` and `unassessed` are compared
as unordered multisets, preserving duplicate observations. Expanded step records
are ordered for comparison by their address arrays. All fields are compared,
including finding paths/invocations, original URI/base/resolution, conditional
selection, each requirement assessment, core needs, addresses and authored steps.
Arrays inside declarations, requirements, routes, parameters and literal values
retain their order. The comparator uses Python's scalar string order for
canonical keys; JavaScript UTF-16 sorting does not select a semantic winner.

## Limits

Agreement covers declaration semantics and diagnostic observations only. The
Python supplied completion, delivery, preparation and admission checkers are
not independently reimplemented here. Their tests continue separately. No
comparison establishes actual content availability, queueing, stopping, response
attribution, approval authority, runtime support, conformance beyond these inputs,
adoption or publication. Independent review remains a separate requirement.
