# 0017 comparison corpus

This is experimental evidence for [proposal 0017](../../../proposals/0017-agent-only-kiss-0.2.md),
not normative conformance or execution evidence. The [manifest](expectations.json)
contains 42 exact expectations: 15 examples and 27 additional witnesses.
The previous 38 cases were adapted to the new marker and actor-free rules before
running either reader. Four cases reject removed fields and the old edition.
Expected observations come from the candidate, never from reader output. The
manifest records the previous c2 corpus hash and Git revision as provenance;
that history does not claim agreement on 0017.

Each case gives all six presences, exact diagnostic tuples and exact gap tuples.
An unlisted observation must be absent. Only outcomes are calculated, using
section 7's fixed precedence. The manifest pins the candidate and every exact
input with SHA-256. Its sources identify the candidate clauses used. The comparator
validates the expanded oracle against the same closed report grammar as outputs.
It imports no reader and does not infer expectations from input semantics.

## Run and retain evidence

From the repository root with Python 3.9+ and Node.js available:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 experimental/kiss-0.2/compare.py /tmp/agsdl-kiss-0017-new-run
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s experimental/kiss-0.2 -p test_compare.py -v
```

The first command is the dedicated comparison command. Its output directory must
not exist, even empty, and must resolve outside the checkout. Nothing is deleted.
It runs the two CLIs sequentially against the same retained bytes and path, with a
30-second timeout per invocation. It retains raw stdout/stderr, process statuses,
normalized reports, exact expanded expectations and a summary for every case.
Negative, unsupported and inconclusive fixtures pass when observations match.
Exit 0 means all 42 passed; 1 means a comparison/process/report failed; 2 means
setup or evidence writing failed. In the latter case existing partial evidence
remains and must not be interpreted as a complete run.

A valid report must contain exactly the six units and closed fields. Duplicate
JSON members, result keys, diagnostic keys, gap keys and causes are rejected.
The decoder rejects invalid UTF-8, non-scalar strings, BOM and stdout parasites.
The comparator checks hashes, phase, subjects, enums, codes and aggregate outcomes.
It compares every semantic field to the exact oracle and to the other reader.
Only processor and optional message wording are removed, after grammar validation.
Allowed collection reordering has no effect. Rule-specific location and CHECKS
gate correctness are enforced by the oracle, not inferred by a third reader.

The summary counts cases passed, invalid/failed reports, valid reports that miss
the oracle and cases with unequal valid reports. Counts can overlap: two readers
can agree on a wrong report and contribute two oracle mismatches. Missing or
invalid reports cannot count as agreement. Metadata retains Git SHA, dirty state,
runtime versions, candidate/oracle hashes and source hashes including both lexical
parsers. Source hashes identify the actual files run; old c2 review SHAs are
not presented as baselines for the changed implementations. Rerun on a clean commit before citing its SHA alone.
This explicit command leaves the Python-only repository check unchanged.

## Input provenance and review

All paths are relative to the experiment directory. Cases referencing examples use the exact current bytes. Mutation witnesses retain their base path/hash and ordered replace or
remove operations on JSON Pointers. They were materialized once with Python
`json.dumps(value, ensure_ascii=False, indent=2) + "\n"`, encoded as UTF-8.
The test reconstructs those bytes and verifies every mutation. Raw witnesses
retain a hexadecimal spelling, including malformed UTF-8 and the empty input.
These are deliberately `.input` files, not claims of valid JSON.

| Cases | Review basis and complete observation intent |
| --- | --- |
| agent-embedded, agent-named | Sections 1–2, 5–7: named and embedded values have the same payload obligations; optional units absent. |
| two-agent-sequence, two-configurations, governed-call | Sections 2–7: data availability, complete ordered Applications, declared claims and sequential gates all satisfy the bounded rules. |
| tool-incompatible, unknown-support | Sections 4–5: declared unsupported versus missing claim, scoped to selected compatibility. |
| governed-missing-scope | Sections 3 and 5 SCOPE: the governed call fails for absent scope, and both gates retain APPROVAL-DATA shape gaps. |
| required-extension, independent-errors | Section 5 REQUIRED and independent checks: unsupported interpretation and its gap coexist with unrelated core errors. |
| missing-reference, ambiguous-reference | Sections 1 and 5 REF/ID: absent target fails; conflicting identities fail at both declarations and block lookup. |
| conflicting-bindings | Section 5 identity projections: duplicate parent bindings block only their dependent subjects, with reference causes. |
| application-order-conflict | Section 5 exact witness: CONTENT fails and ENGINE coverage remains incomplete; declared instruction order is unchanged. |
| duplicate-step-assign | Section 5 c2 exact witness: duplicate step ids do not block known empty ASSIGN projection. |
| binding-ambiguous, unreadable-binding-keeps-sibling-failure, malformed-claim-keeps-known-failure, missing-applications-coverage, missing-tool-coverage | Section 5 exact witness table, including the survival of readable sibling failures. |
| missing-step-kind, approval-target-missing | Section 5 exact witness paragraphs, including all lower-precedence gaps and the second gate's chain failure. |
| root-null, root-array, root-string, root-number, root-boolean | Section 6 whole-root gate: syntax passes, core SHAPE fails, all five nonsyntax units retain CHECKS gaps. |
| syntax-empty, syntax-duplicate, syntax-bom, syntax-surrogate, syntax-utf8, syntax-trailing | Sections 1, 5–6: syntax fails, five whole-unit CHECKS gaps, undetermined nonsyntax presence. |
| empty-requirements-malformed-claims | Sections 4–5 c2 exact witness: complete empty requirements skip claim lookup, configuration still reports malformed claims. |
| scope-resources-unreadable, scope-resources-empty | Sections 3 and 5: resources must be a nonempty array; UNIQUE needs full shape and SCOPE needs readable scope. |
| missing-call-unreadable-timeout | Section 5 actor-removal witnesses: missing call completes APPROVAL with failure, independently malformed timeout creates SHAPE; APPROVAL-DATA keeps its reference gap. |
| removed-principals, removed-agent-principal, removed-approvers, previous-edition | Sections 2 and 5 actor-removal witnesses, 6: removed fields fail shape without actor lookups; the old marker is rejected. |
| duplicate-and-unreadable-slots | Section 5 SLOT-ID, CONTENT and ENGINE: observed duplicate survives an unreadable sibling; dependent gaps union shape and reference while a known claim failure survives. |

Coverage is deliberately finite. It is not exhaustive over graph shapes, Unicode,
opaque numbers, all malformed fields or resource exhaustion. The separate reader
suites cover additional cases. The comparison does not certify all candidate
semantics, engine support, permission, execution or interoperability.
